# test/test_backend_smoke.py

import os
from uuid import uuid4
from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")


def test_supabase_connection():
    """Simple Supabase connectivity + schema sanity check."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Try a cheap select against games (limit 1)
    resp = client.table("games").select("*").limit(1).execute()
    assert getattr(resp, "error", None) is None, f"Supabase error: {resp.error}"
    # resp.data is a list; we don't care about contents here
    print("Supabase games table reachable, rows:", len(resp.data))


def test_health_endpoint():
    """Check FastAPI /health endpoint."""
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ok", data
    print("/health OK")


def test_start_game_and_trace():
    """Hit /game/start then /game/{id}/trace."""
    # Start a game
    params = {"username": f"tester_{uuid4().hex[:6]}", "difficulty": "easy"}
    r = requests.post(f"{BASE_URL}/game/start", params=params)
    assert r.status_code == 200, r.text
    body = r.json()
    game_id = body["game_id"]
    print("Started game:", game_id)

    # Fetch trace (will be empty for now)
    r2 = requests.get(f"{BASE_URL}/game/{game_id}/trace")
    assert r2.status_code == 200, r2.text
    trace = r2.json()
    assert isinstance(trace, list)
    print("Trace length:", len(trace))


if __name__ == "__main__":
    # Run all tests in a simple way
    test_supabase_connection()
    test_health_endpoint()
    test_start_game_and_trace()
    print("All smoke tests passed.")