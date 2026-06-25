import time
from typing import Tuple

from backend.agent.session import ChainSession, Difficulty
from backend.game.core import score_word
from backend.mcp_tools.game_tools import word_lookup_tool
from backend.llm.openrouter_client import call_openrouter
from backend.observability.logging import log_llm_call


def validate_player_word(session: ChainSession, player_word: str) -> Tuple[bool, str]:
    """Validate the player's word using structural rules and Supabase word_list."""
    w = (player_word or "").strip()
    if not w:
        return False, "empty or whitespace word"
    if len(w) > 50:
        return False, "word too long"
    if not w.isalpha():
        return False, "word must contain only letters"
    if session.last_letter and w[0].lower() != session.last_letter.lower():
        return False, "word does not start with required letter"
    if w.lower() in {u.lower() for u in session.used_words}:
        return False, "word already used"

    lookup = word_lookup_tool(w)
    if not lookup.get("valid"):
        return False, lookup.get("reason", "not_in_dictionary")

    return True, "ok"


def judge_creativity(session: ChainSession, player_word: str) -> Tuple[bool, str, dict]:
    """Judge creativity based on frequency rank, with optional LLM explanation.

    Returns (is_creative, reason, llm_meta).
    """
    w = (player_word or "").strip()
    lookup = word_lookup_tool(w)
    freq = lookup.get("freq_rank")

    # Heuristic: thresholds by difficulty
    if freq is None:
        creative = len(w) > 6
        reason = "length-based fallback"
    else:
        if session.difficulty == Difficulty.EASY:
            creative = freq > 1000
        elif session.difficulty == Difficulty.MEDIUM:
            creative = freq > 5000
        else:  # HARD
            creative = freq > 10000
        reason = f"freq_rank={freq}"

    llm_meta: dict = {}

    # Optional LLM call for explanation; guard if key not set
    try:
        explanation, tokens_in, tokens_out, usd_cost, latency_ms = call_openrouter(
            prompt=(
                f"In one short sentence, explain why the word '{w}' is "
                f"{'creative' if creative else 'not very creative'} "
                f"for difficulty {session.difficulty.value} given freq_rank={freq}."
            ),
            system_prompt="You are a concise word-game judge.",
        )
        llm_meta = {
            "explanation": explanation,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "usd_cost": usd_cost,
            "latency_ms": latency_ms,
        }
    except Exception as exc:  # noqa: BLE001
        llm_meta = {"error": str(exc)}

    return creative, reason, llm_meta


def generate_ai_move(session: ChainSession, last_player_word: str) -> str:
    required_start = last_player_word[-1].lower()
    base_candidate = required_start * 4
    candidate = base_candidate
    while candidate.endswith("s"):
        candidate += required_start
    return candidate


def play_turn(session: ChainSession, player_word: str) -> tuple[ChainSession, dict]:
    """Run a full turn pipeline (validation -> creativity -> AI move).

    Returns updated session and a per-turn score breakdown dict.
    """
    turn_number = session.current_round + 1

    # Step 1: validation
    t0 = time.time()
    ok, reason = validate_player_word(session, player_word)
    t1 = time.time()
    session.step_traces.append(
        {
            "step_name": "validation",
            "start_ts": t0,
            "end_ts": t1,
            "latency_ms": int((t1 - t0) * 1000),
            "outcome": "ok" if ok else "invalid",
            "error": None if ok else reason,
        }
    )
    if not ok:
        session.validation_retries += 1
        session.game_status = "ended"
        return session, {"valid": False, "reason": reason}

    # Step 2: creativity judgement + LLM explanation
    t2 = time.time()
    is_creative, creativity_reason, llm_meta = judge_creativity(session, player_word)
    t3 = time.time()

    if "error" in llm_meta:
        session.creativity_retries += 1

    creativity_trace = {
        "step_name": "creativity",
        "start_ts": t2,
        "end_ts": t3,
        "latency_ms": int((t3 - t2) * 1000),
        "outcome": "ok",
        "payload": {"reason": creativity_reason, **({} if "explanation" not in llm_meta else {"explanation": llm_meta["explanation"]})},
    }

    # Attach LLM metrics if available
    if "tokens_in" in llm_meta:
        creativity_trace["tokens_in"] = llm_meta["tokens_in"]
    if "tokens_out" in llm_meta:
        creativity_trace["tokens_out"] = llm_meta["tokens_out"]
    if "usd_cost" in llm_meta:
        creativity_trace["usd_cost"] = llm_meta["usd_cost"]
    if "latency_ms" in llm_meta:
        # Overwrite latency_ms with LLM latency if present
        creativity_trace["latency_ms"] = llm_meta["latency_ms"]

    session.step_traces.append(creativity_trace)

    # Log LLM call if it succeeded
    if "explanation" in llm_meta and "tokens_in" in llm_meta:
        log_llm_call(
            {
                "game_id": session.game_id,
                "turn": turn_number,
                "step_name": "creativity",
                "model": os.getenv("OPENROUTER_MODEL"),
                "tokens_in": llm_meta["tokens_in"],
                "tokens_out": llm_meta["tokens_out"],
                "latency_ms": llm_meta["latency_ms"],
                "usd_cost": llm_meta["usd_cost"],
                "prompt_summary": f"creativity explanation for '{player_word}'",
            }
        )

    if is_creative:
        session.cascade_streak += 1
    else:
        session.cascade_streak = 0

    breakdown = score_word(player_word, is_creative, session.cascade_streak)
    session.total_score += breakdown.total

    session.current_round = turn_number
    session.used_words.append(player_word)
    session.last_letter = player_word[-1].lower()

    # Step 3: AI move generation
    t4 = time.time()
    ai_word = generate_ai_move(session, player_word)
    t5 = time.time()
    session.step_traces.append(
        {
            "step_name": "ai_move",
            "start_ts": t4,
            "end_ts": t5,
            "latency_ms": int((t5 - t4) * 1000),
            "outcome": "ok",
        }
    )
    session.used_words.append(ai_word)
    session.last_letter = ai_word[-1].lower()

    return session, {
        "valid": True,
        "player_word": player_word,
        "ai_word": ai_word,
        "is_creative": is_creative,
        "creativity_reason": creativity_reason,
        "llm_explanation": llm_meta.get("explanation"),
        "score_breakdown": {
            "base": breakdown.base,
            "creative_bonus": breakdown.creative_bonus,
            "length_bonus": breakdown.length_bonus,
            "cascade_multiplier": breakdown.cascade_multiplier,
            "total": breakdown.total,
        },
    }
