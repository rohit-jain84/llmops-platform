import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    database_url: str = "postgresql+asyncpg://llmops:llmops_dev@localhost:5432/llmops"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # LLM Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # LangFuse
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "http://localhost:3001"

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "llmops-backend"

    # Evaluator
    evaluator_model: str = "gpt-4o-mini"

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # Semantic Cache
    cache_similarity_threshold: float = 0.95
    cache_ttl_seconds: int = 3600

    model_config = {"env_file": ".env", "extra": "ignore"}

    def validate_secrets(self) -> None:
        """Raise on startup if default secrets are used in production."""
        env = os.getenv("APP_ENV", "development").lower()
        if env not in ("development", "dev", "test"):
            insecure_defaults = {
                "jwt_secret_key": "dev-secret-key-change-in-production",
            }
            for field, default_val in insecure_defaults.items():
                if getattr(self, field, None) == default_val:
                    raise ValueError(
                        f"Insecure default detected for {field}. "
                        f"Set a unique value via environment variable before running in {env} mode."
                    )


settings = Settings()
settings.validate_secrets()
