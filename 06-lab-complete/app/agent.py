"""Agent logic: mock/OpenAI responses and Redis-backed conversation history."""
from datetime import datetime, timezone

from app.config import settings
from app.redis_client import redis_client
from utils.mock_llm import ask as mock_ask

CONVERSATION_TTL_SECONDS = 60 * 60 * 24 * 7


def _conversation_key(user_id: str) -> str:
    return f"conversation:{user_id}"


def load_conversation(user_id: str) -> list[dict]:
    history = redis_client.get_json(_conversation_key(user_id))
    return history if isinstance(history, list) else []


def save_conversation(user_id: str, history: list[dict]) -> None:
    redis_client.set_json(
        _conversation_key(user_id),
        history[-40:],
        ttl_seconds=CONVERSATION_TTL_SECONDS,
    )


def generate_answer(question: str) -> str:
    if settings.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.model_name,
                messages=[{"role": "user", "content": question}],
            )
            return response.choices[0].message.content or ""
        except Exception:
            pass
    return mock_ask(question, delay=0.05)


def ask_user(user_id: str, question: str) -> tuple[str, int]:
    history = load_conversation(user_id)
    answer = generate_answer(question)
    now = datetime.now(timezone.utc).isoformat()

    history.extend(
        [
            {"role": "user", "content": question, "timestamp": now},
            {"role": "assistant", "content": answer, "timestamp": now},
        ]
    )
    save_conversation(user_id, history)

    conversation_length = sum(1 for item in history if item.get("role") == "user")
    return answer, conversation_length
