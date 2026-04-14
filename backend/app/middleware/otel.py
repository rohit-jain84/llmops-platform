from app.telemetry.setup import setup_telemetry


def init_otel_middleware(app):
    setup_telemetry(app)
