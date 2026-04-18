import logging
import time

import redis.asyncio as redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

logger = logging.getLogger(__name__)

SKIP_PATHS = {"/health", "/health/"}

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
        )
    return _redis_client


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in SKIP_PATHS:
            return await call_next(request)
        if not settings.rate_limit_enabled:
            return await call_next(request)

        limit = settings.rate_limit_requests
        window = settings.rate_limit_window_seconds
        ip = _client_ip(request)
        now = int(time.time())
        window_key = now // window
        key = f"ratelimit:{ip}:{window_key}"

        try:
            r = _get_redis()
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, window)

            remaining = max(0, limit - current)

            if current > limit:
                retry_after = window - (now % window)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        except redis.RedisError:
            logger.warning("Redis unavailable for rate limiting — allowing request")
            return await call_next(request)
