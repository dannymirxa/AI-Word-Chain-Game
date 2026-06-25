from backend.game.core import score_word
from backend.db.session import supabase


def score_word_tool(word: str, is_creative: bool, cascade_streak: int) -> dict:
    """MCP-style scoring tool wrapper around backend.game.core.score_word.

    Returns a plain dict so it can be serialized easily by an MCP server or ADK tool.
    """
    breakdown = score_word(word, is_creative, cascade_streak)
    return {
        "base": breakdown.base,
        "creative_bonus": breakdown.creative_bonus,
        "length_bonus": breakdown.length_bonus,
        "cascade_multiplier": breakdown.cascade_multiplier,
        "total": breakdown.total,
    }


def word_lookup_tool(word: str) -> dict:
    """Lookup a word in the Supabase-backed word_list table.

    Expected schema for word_list:
      - word text primary key
      - freq_rank int (optional)
    """
    w = (word or "").strip().lower()
    if not w:
        return {"valid": False, "reason": "empty"}

    resp = (
        supabase
        .table("word_list")
        .select("word,freq_rank")
        .eq("word", w)
        .limit(1)
        .execute()
    )

    if getattr(resp, "error", None):
        return {"valid": False, "reason": f"tool_error:{resp.error}"}

    data = resp.data or []
    if not data:
        return {"valid": False, "reason": "not_in_dictionary"}

    row = data[0]
    return {
        "valid": True,
        "freq_rank": row.get("freq_rank"),
    }
