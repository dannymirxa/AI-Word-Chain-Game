from fastapi import FastAPI, HTTPException
from uuid import uuid4
from datetime import datetime

from backend.db.session import supabase
from backend.agent.session import ChainSession, Difficulty


app = FastAPI(title="AI Word Chain Game Backend")


@app.get("/health")
def health_check():
    """Basic health check to verify the service is up."""
    return {"status": "ok"}


@app.post("/game/start")
async def start_game(username: str, difficulty: Difficulty):
    """Start a new game and persist it via Supabase HTTP API.

    For now, parameters are accepted as query params:
    /game/start?username=danial&difficulty=easy
    """
    game_id = str(uuid4())

    response = (
        supabase
        .table("games")
        .insert({
            "id": game_id,
            "username": username,
            "difficulty": difficulty.value,
            "status": "active",
            "total_score": 0,
            "rounds_played": 0,
            "created_at": datetime.utcnow().isoformat(),
        })
        .execute()
    )

    if getattr(response, "error", None):
        raise HTTPException(status_code=500, detail=f"Failed to create game: {response.error}")

    session = ChainSession(
        game_id=game_id,
        username=username,
        difficulty=difficulty,
        current_round=0,
        total_score=0,
        used_words=[],
        last_letter=None,
        cascade_streak=0,
        game_status="active",
    )

    return {"game_id": game_id, "session": session}


@app.get("/game/{game_id}/trace")
async def get_game_trace(game_id: str):
    """Return full ordered trace for a game from Supabase traces table."""
    response = (
        supabase
        .table("traces")
        .select("*")
        .eq("game_id", game_id)
        .order("turn", asc=True)
        .order("id", asc=True)
        .execute()
    )

    if getattr(response, "error", None):
        raise HTTPException(status_code=500, detail=f"Failed to fetch trace: {response.error}")

    return response.data or []
