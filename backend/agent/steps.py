import time
from typing import Tuple

from backend.agent.session import ChainSession
from backend.game.core import score_word


def validate_player_word(session: ChainSession, player_word: str) -> Tuple[bool, str]:
    """Basic structural validation of the player's word.

    This does not call external tools yet; it guards against empty/whitespace,
    extreme lengths, and last-letter rule.
    """
    w = (player_word or "").strip()
    if not w:
        return False, "empty or whitespace word"

    if len(w) > 50:
        return False, "word too long"

    if not w.isalpha():
        return False, "word must contain only letters"

    # Last-letter rule: must match last letter of previous word if available.
    if session.last_letter and w[0].lower() != session.last_letter.lower():
        return False, "word does not start with required letter"

    if w.lower() in {u.lower() for u in session.used_words}:
        return False, "word already used"

    return True, "ok"


def judge_creativity(session: ChainSession, player_word: str) -> Tuple[bool, str]:
    """Placeholder creativity judgement.

    For now, we treat words longer than 6 letters as "creative".
    This will later incorporate frequency data and an LLM rubric.
    """
    w = (player_word or "").strip()
    if len(w) > 6:
        return True, "length-based creative placeholder"
    return False, "non-creative placeholder"


def generate_ai_move(session: ChainSession, last_player_word: str) -> str:
    """Placeholder AI move generation.

    For now, this uses a trivial deterministic strategy and DOES NOT
    call the LLM yet. It respects the no-`s` ending rule.
    """
    required_start = last_player_word[-1].lower()
    base_candidate = required_start * 4  # e.g. 'aaaa'
    candidate = base_candidate

    # Enforce no 's' ending via retry-style loop.
    while candidate.endswith("s"):
        candidate += required_start

    return candidate


def play_turn(session: ChainSession, player_word: str) -> ChainSession:
    """Run a full turn pipeline in-process (validation -> creativity -> AI move).

    This is a non-LLM placeholder that exercises the ChainSession flow.
    """
    turn_number = session.current_round + 1

    # Step 1: validation
    start = time.time()
    ok, reason = validate_player_word(session, player_word)
    end = time.time()

    if not ok:
        session.game_status = "ended"
        return session

    # Step 2: creativity judgement
    is_creative, _ = judge_creativity(session, player_word)

    # Update cascade streak
    if is_creative:
        session.cascade_streak += 1
    else:
        session.cascade_streak = 0

    # Score player's word
    breakdown = score_word(player_word, is_creative, session.cascade_streak)
    session.total_score += breakdown.total

    # Update state
    session.current_round = turn_number
    session.used_words.append(player_word)
    session.last_letter = player_word[-1].lower()

    # Step 3: AI move generation (placeholder)
    ai_word = generate_ai_move(session, player_word)
    session.used_words.append(ai_word)
    session.last_letter = ai_word[-1].lower()

    return session

