"""Production config — 12-Factor: all values from environment variables."""
import os
import uuid
from dataclasses import dataclass, field


def _resolve_redis_url() -> str:
    """Resolve Redis URL from env (Render Blueprint or manual Dashboard link)."""
    env = os.getenv("ENVIRONMENT", "production")
    for key in ("REDIS_URL", "REDIS_CONNECTION_STRING", "KEY_VALUE_URL"):
        value = os.getenv(key, "").strip()
        if not value:
            continue
        # Ignore compose/local URLs accidentally set on cloud
        if env == "production" and (
            "localhost" in value
            or "127.0.0.1" in value
            or "://redis:" in value
        ):
            continue
        return value
    return ""


@dataclass
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    instance_id: str = field(
        default_factory=lambda: os.getenv("INSTANCE_ID", f"instance-{uuid.uuid4().hex[:6]}")
    )

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "mock-agent"))

    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "secret"))
    allowed_origins: list = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )

    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "10"))
    )
    cost_per_request_usd: float = field(
        default_factory=lambda: float(os.getenv("COST_PER_REQUEST_USD", "0.001"))
    )

    redis_url: str = field(default_factory=_resolve_redis_url)
    redis_connect_retries: int = field(
        default_factory=lambda: int(os.getenv("REDIS_CONNECT_RETRIES", "30"))
    )
    redis_connect_retry_delay: float = field(
        default_factory=lambda: float(os.getenv("REDIS_CONNECT_RETRY_DELAY", "2"))
    )

    def validate(self) -> "Settings":
        if self.environment == "production" and self.agent_api_key in ("", "dev-key-change-me"):
            raise ValueError("AGENT_API_KEY must be set in production!")
        return self


settings = Settings().validate()
