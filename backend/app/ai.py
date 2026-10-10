"""Groq (Llama 3.3 70B) helper.

The AI only *suggests* a category and flags unusual claims. If the call fails
for any reason (no key, timeout, network error, invalid JSON) we return a safe
"unavailable" result, so the rest of the app keeps working with a manual
category and rule-based flags.
"""
import json
import logging

import httpx

from .config import AI_TIMEOUT_SECONDS, CATEGORIES, GROQ_API_KEY, GROQ_MODEL, GROQ_URL

logger = logging.getLogger("spendflow.ai")

SYSTEM_PROMPT = (
    "You review company expense claims for a small team. "
    "Reply with JSON only, in this exact shape: "
    '{"category": "<one of: ' + ", ".join(CATEGORIES) + '>", '
    '"is_unusual": true or false, "reason": "<one short sentence>"}. '
    "Set is_unusual to true when the description is vague, the amount looks "
    "too high for the item, or the item looks personal rather than business. "
    "Keep the reason under 20 words."
)


def unavailable() -> dict:
    return {"category": None, "is_unusual": False, "reason": "", "ai_available": False}


def analyze_expense(description: str, amount: float) -> dict:
    """Return {category, is_unusual, reason, ai_available}. Never raises."""
    if not GROQ_API_KEY:
        return unavailable()
    try:
        response = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                "temperature": 0.1,
                "max_tokens": 200,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Amount (INR): {amount}\nDescription: {description}",
                    },
                ],
            },
            timeout=AI_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        category = data.get("category")
        if category not in CATEGORIES:
            category = "Other"
        return {
            "category": category,
            "is_unusual": bool(data.get("is_unusual", False)),
            "reason": str(data.get("reason", ""))[:300],
            "ai_available": True,
        }
    except Exception as exc:  # timeout, network, HTTP error, bad JSON, ...
        logger.warning("AI call failed, using fallback: %s", exc)
        return unavailable()
