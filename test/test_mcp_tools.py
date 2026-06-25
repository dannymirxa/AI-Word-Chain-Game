# test/test_mcp_tools.py

"""
Smoke tests for MCP-style tools in backend/mcp_tools/game_tools.py.

These tests assume:
- SUPABASE_URL and SUPABASE_KEY are set in the environment.
- A 'word_list' table exists in Supabase with at least some rows:
    create table if not exists public.word_list (
      word text primary key,
      freq_rank int
    );
"""

import os
from uuid import uuid4

from supabase import create_client
from backend.mcp_tools.game_tools import score_word_tool, word_lookup_tool


def _get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


def test_score_word_tool_basic():
    """Score a simple non-creative word and a creative one; just prints results."""
    # Non-creative: short word, no cascade
    r1 = score_word_tool("apple", is_creative=False, cascade_streak=0)
    print("score_word_tool non-creative:", r1)

    # Creative: longer word, cascade streak >= 3
    r2 = score_word_tool("elephant", is_creative=True, cascade_streak=3)
    print("score_word_tool creative with cascade:", r2)

    assert r1["base"] == 10
    assert r2["base"] == 10
    assert r2["cascade_multiplier"] in (1, 2)  # depends on current cascade rule


def test_word_lookup_tool_known_and_unknown():
    """
    Lookup a word that should exist in word_list and one that should not.

    You may need to insert a known test word into word_list manually, e.g.:
      insert into word_list (word, freq_rank) values ('testword', 1000);
    """
    client = _get_supabase_client()

    # Ensure a known test word exists
    test_word = f"testword_{uuid4().hex[:6]}"
    client.table("word_list").insert(
        {"word": test_word, "freq_rank": 1000}
    ).execute()

    # Known word
    known = word_lookup_tool(test_word)
    print("word_lookup_tool known:", known)
    assert known["valid"] is True
    assert known["freq_rank"] == 1000

    # Unknown word (very unlikely to exist)
    unknown = word_lookup_tool("zzzqzzqzzq" + uuid4().hex[:4])
    print("word_lookup_tool unknown:", unknown)
    assert unknown["valid"] is False


if __name__ == "__main__":
    # Simple runner if you don't want pytest yet
    test_score_word_tool_basic()
    test_word_lookup_tool_known_and_unknown()
    print("All MCP tool smoke tests passed.")