import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LangFuseService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            if settings.langfuse_secret_key and settings.langfuse_public_key:
                from langfuse import Langfuse
                self._client = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host,
                )
        return self._client

    def create_trace(self, name: str, metadata: dict | None = None) -> object | None:
        client = self._get_client()
        if not client:
            return None
        try:
            return client.trace(name=name, metadata=metadata or {})
        except Exception as e:
            logger.warning(f"LangFuse trace creation failed: {e}")
            return None

    def log_generation(
        self,
        trace: object | None,
        model: str,
        input_text: str,
        output_text: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        cost_usd: float = 0,
        metadata: dict | None = None,
    ):
        if not trace:
            return
        try:
            trace.generation(
                name="llm-call",
                model=model,
                input=input_text,
                output=output_text,
                usage={
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                },
                metadata={
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                    **(metadata or {}),
                },
            )
        except Exception as e:
            logger.warning(f"LangFuse generation logging failed: {e}")

    def flush(self):
        client = self._get_client()
        if client:
            try:
                client.flush()
            except Exception:
                pass
