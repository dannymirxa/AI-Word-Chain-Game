import time
from typing import Tuple

from backend.agent.session import ChainSession
from backend.game.core import score_word


def validate_player_word(session: ChainSession, player_word: str) -> Tuple[bool, str]:
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
    return True, "ok"


def judge_creativity(session: ChainSession, player_word: str) -> Tuple[bool, str]:
    w = (player_word or "").strip()
    if len(w) > 6:
        return True, "length-based creative placeholder"
    return False, "non-creative placeholder"


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
        session.game_status = "ended"
        return session, {"valid": False, "reason": reason}

    # Step 2: creativity judgement
    t2 = time.time()
    is_creative, _ = judge_creativity(session, player_word)
    t3 = time.time()
    session.step_traces.append(
        {
            "step_name": "creativity",
            "start_ts": t2,
            "end_ts": t3,
            "latency_ms": int((t3 - t2) * 1000),
            "outcome": "ok",
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
        "score_breakdown": {
            "base": breakdown.base,
            "creative_bonus": breakdown.creative_bonus,
            "length_bonus": breakdown.length_bonus,
            "cascade_multiplier": breakdown.cascade_multiplier,
            "total": breakdown.total,
        },
    }
