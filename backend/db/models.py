from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    BigInteger,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime


Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    status = Column(String, nullable=False)
    total_score = Column(Integer, nullable=False, default=0)
    rounds_played = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class PlayerStats(Base):
    __tablename__ = "player_stats"

    username = Column(String, primary_key=True)
    games_played = Column(Integer, nullable=False, default=0)
    total_score = Column(Integer, nullable=False, default=0)
    best_score = Column(Integer, nullable=False, default=0)
    avg_score = Column(Numeric, nullable=False, default=0)


class Trace(Base):
    __tablename__ = "traces"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    turn = Column(Integer, nullable=False)
    step_name = Column(String, nullable=False)
    model = Column(String, nullable=True)
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    usd_cost = Column(Numeric, nullable=True)
    outcome = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
