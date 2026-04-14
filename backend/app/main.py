import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import v1_router
from app.config import settings
from app.middleware.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — initialize OpenTelemetry tracing and metrics
    try:
        from app.telemetry.setup import setup_telemetry
        setup_telemetry(app)
        logger.info("OpenTelemetry tracing initialized")
    except Exception as e:
        logger.warning(f"OpenTelemetry tracing setup failed (non-fatal): {e}")

    try:
        from app.telemetry.metrics import get_metrics
        get_metrics()  # Eagerly create metrics so exporters start immediately
        logger.info("OpenTelemetry metrics initialized")
    except Exception as e:
        logger.warning(f"OpenTelemetry metrics setup failed (non-fatal): {e}")

    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLMOps Platform",
        description="LLMOps Platform for AI Application Lifecycle Management",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RateLimitMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()
