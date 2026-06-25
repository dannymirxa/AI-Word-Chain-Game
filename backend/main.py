from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from backend.db.session import get_db
from backend.db import models
from backend.agent.session import ChainSession, Difficulty


app = FastAPI(title="AI Word Chain Game Backend")


@app.on_event("startup")
def startup_check_db():
    # Simple connectivity check on startup
    from backend.db.session import engine

    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Database connectivity check failed: {exc}") from exc


@app.post("/game/start")
def start_game(username: str, difficulty: Difficulty, db: Session = Depends(get_db)):
    game_id = uuid4()
    game = models.Game(
        id=game_id,
        username=username,
        difficulty=difficulty.value,
        status="active",
        total_score=0,
        rounds_played=0,
        created_at=datetime.utcnow(),
    )
    db.add(game)
    db.commit()

    session = ChainSession(
        game_id=str(game_id),
        username=username,
        difficulty=difficulty,
        current_round=0,
        total_score=0,
        used_words=[],
        last_letter=None,
        cascade_streak=0,
        game_status="active",
    )

    return {"game_id": str(game_id), "session": session}


@app.get("/game/{game_id}/trace")
def get_game_trace(game_id: str, db: Session = Depends(get_db)):
    traces = (
        db.query(models.Trace)
        .filter(models.Trace.game_id == game_id)
        .order_by(models.Trace.turn, models.Trace.id)
        .all()
    )
    return [
        {
            "id": t.id,
            "turn": t.turn,
            "step_name": t.step_name,
            "model": t.model,
            "tokens_in": t.tokens_in,
            "tokens_out": t.tokens_out,
            "latency_ms": t.latency_ms,
            "usd_cost": float(t.usd_cost) if t.usd_cost is not None else None,
            "outcome": t.outcome,
            "payload": t.payload,
            "created_at": t.created_at.isoformat(),
        }
        for t in traces
    ]
