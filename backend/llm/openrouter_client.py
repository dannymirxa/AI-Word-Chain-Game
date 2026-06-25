import os
import time
import requests
from typing import Optional, Tuple

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


class LLMCallResult(Tuple[str, int, int, float, int]):
    """(text, tokens_in, tokens_out, usd_cost, latency_ms)."""


def call_openrouter(prompt: str, system_prompt: Optional[str] = None) -> tuple[str, int, int, float, int]:
    """Call OpenRouter with a simple text prompt.

    Returns (text, tokens_in, tokens_out, usd_cost, latency_ms).
    On error, raises RuntimeError.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
    }

    t0 = time.time()
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    t1 = time.time()

    latency_ms = int((t1 - t0) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text}")

    data = resp.json()
    text = data["choices"][0]["message"]["content"]

    usage = data.get("usage", {})
    tokens_in = usage.get("prompt_tokens", 0)
    tokens_out = usage.get("completion_tokens", 0)
    # Approximate cost: if OpenRouter returns 'total_cost' use it, else 0
    usd_cost = float(usage.get("total_cost", 0.0))

    return text, tokens_in, tokens_out, usd_cost, latency_ms
