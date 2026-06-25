from fastapi import FastAPI, HTTPException
from uuid import uuid4
from datetime import datetime

from backend.db.session import supabase
from backend.agent.session import ChainSession, Difficulty
from backend.agent.steps import play_turn as agent_play_turn


app = FastAPI(title="AI Word Chain Game Backend")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/game/start")
async def start_game(username: str, difficulty: Difficulty):
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
            "used_words": [],
            "last_letter": None,
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


@app.post("/game/{game_id}/turn")
async def play_turn(game_id: str, player_word: str):
    # Load game state from Supabase
    game_resp = (
        supabase
        .table("games")
        .select("*")
        .eq("id", game_id)
        .single()
        .execute()
    )

    if getattr(game_resp, "error", None):
        raise HTTPException(status_code=404, detail="Game not found")

    game = game_resp.data
    session = ChainSession(
        game_id=game_id,
        username=game["username"],
        difficulty=Difficulty(game["difficulty"]),
        current_round=game.get("rounds_played", 0),
        total_score=game.get("total_score", 0),
        used_words=game.get("used_words", []) or [],
        last_letter=game.get("last_letter"),
        cascade_streak=0,
        game_status=game.get("status", "active"),
    )

    session, turn_result = agent_play_turn(session, player_word)

    # Persist updated game state
    update_resp = (
        supabase
        .table("games")
        .update({
            "total_score": session.total_score,
            "rounds_played": session.current_round,
            "status": session.game_status,
            "used_words": session.used_words,
            "last_letter": session.last_letter,
        })
        .eq("id", game_id)
        .execute()
    )

    if getattr(update_resp, "error", None):
        raise HTTPException(status_code=500, detail=f"Failed to update game: {update_resp.error}")

    # Persist simple traces for each step
    for step in session.step_traces:
        supabase.table("traces").insert({
            "game_id": game_id,
            "turn": session.current_round,
            "step_name": step["step_name"],
            "model": None,
            "tokens_in": step.get("tokens_in"),
            "tokens_out": step.get("tokens_out"),
            "latency_ms": step.get("latency_ms"),
            "usd_cost": step.get("usd_cost"),
            "outcome": step.get("outcome"),
            "payload": step,
        }).execute()

    return {
        "game_id": game_id,
        "session": session,
        "turn_result": turn_result,
    }


@app.get("/game/{game_id}/trace")
async def get_game_trace(game_id: str):
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
