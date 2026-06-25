import json
import os
from datetime import datetime

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LLM_LOG_PATH = os.path.join(LOG_DIR, "llm_calls.jsonl")


def log_llm_call(record: dict) -> None:
    """Append a single LLM call record as JSONL.

    Expected keys include (but are not limited to):
    - game_id, turn, step_name
    - model, tokens_in, tokens_out, latency_ms, usd_cost
    - timestamp, prompt_summary
    """
    record = dict(record)
    record.setdefault("timestamp", datetime.utcnow().isoformat())
    with open(LLM_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
