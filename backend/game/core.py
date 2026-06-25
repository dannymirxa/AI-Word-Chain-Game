from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TurnScoreBreakdown(BaseModel):
    base: int = 0
    creative_bonus: int = 0
    length_bonus: int = 0
    cascade_multiplier: int = 1

    @property
    def total(self) -> int:
        return (self.base + self.creative_bonus + self.length_bonus) * self.cascade_multiplier


def score_word(word: str, is_creative: bool, cascade_streak: int) -> TurnScoreBreakdown:
    """Score a single word according to game rules.

    - +10 base
    - +5 if creative
    - +1 per letter beyond 5
    - If cascade_streak >= 3, apply x2 multiplier to this turn's subtotal.
    """
    word = (word or "").strip()
    base = 10
    creative_bonus = 5 if is_creative else 0
    length_bonus = max(0, len(word) - 5)
    cascade_multiplier = 2 if cascade_streak >= 3 else 1

    return TurnScoreBreakdown(
        base=base,
        creative_bonus=creative_bonus,
        length_bonus=length_bonus,
        cascade_multiplier=cascade_multiplier,
    )


class ChainSession(BaseModel):
    game_id: str
    username: str
    difficulty: Difficulty
    current_round: int = 0
    total_score: int = 0
    used_words: list[str] = []
    last_letter: Optional[str] = None
    cascade_streak: int = 0
    game_status: str = "active"

