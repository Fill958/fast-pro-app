"""Общий доступ к Claude для всех агентов."""
import json

import anthropic

from bot import config


def ask(prompt: str, schema: dict | None = None, max_tokens: int = 2000):
    """Задаёт вопрос Claude. Со schema возвращает dict, без неё — текст. None при отказе."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    output_config = {"effort": "low"}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    response = client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        output_config=output_config,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        return None
    text = "".join(b.text for b in response.content if b.type == "text")
    return json.loads(text) if schema else text
