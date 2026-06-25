# AI Word Chain Game

Backend, eval harness, and (later) frontend implementation for the AI Word Chain Game.

## Branches

- `main`: Stable backend implementation (FastAPI, Supabase persistence, basic agent logic).
- `agent`: In-progress work integrating Google ADK and MCP-style tools.

## MCP-style tools (agent branch)

On the `agent` branch, MCP-style tool wrappers live under `backend/mcp_tools/`.

- `score_word_tool(word, is_creative, cascade_streak)` wraps `backend.game.core.score_word` and returns a serializable dict.
- `word_lookup_tool(word)` queries the Supabase `word_list` table for existence and an optional `freq_rank` field.

These functions are designed to be exposed as MCP tools for a Google ADK agent, so the agent can:

- Validate player words against a real dictionary / frequency list.
- Compute scoring deterministically via a shared game core.

Supabase expected schema for `word_list`:

```sql
create table if not exists public.word_list (
  word text primary key,
  freq_rank int
);
```

The ADK agent will call these tools via MCP, while FastAPI continues to provide the public HTTP API.
