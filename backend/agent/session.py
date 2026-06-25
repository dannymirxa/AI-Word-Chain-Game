from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class StepTrace(BaseModel):
    step_name: str
    start_ts: float
    end_ts: float
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    usd_cost: float = 0.0
    outcome: str = "ok"
    error: Optional[str] = None


class ChainSession(BaseModel):
    game_id: str
    username: str
    difficulty: Difficulty
    current_round: int = 0
    total_score: int = 0
    used_words: list[str] = Field(default_factory=list)
    last_letter: Optional[str] = None
    cascade_streak: int = 0
    game_status: str = "active"  # active | ended | error | quit
    step_traces: list[StepTrace] = Field(default_factory=list)
    validation_retries: int = 0
    creativity_retries: int = 0
    ai_move_retries: int = 0
