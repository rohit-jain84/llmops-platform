from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from app.config import settings


def setup_metrics():
    resource = Resource.create({"service.name": settings.otel_service_name})

    exporter = OTLPMetricExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=15000)
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)

    return metrics.get_meter("llmops")


meter = None


def get_meter():
    global meter
    if meter is None:
        try:
            meter = setup_metrics()
        except Exception:
            meter = metrics.get_meter("llmops")
    return meter


# Custom metrics
def create_custom_metrics():
    m = get_meter()

    request_duration = m.create_histogram(
        name="llmops_request_duration_ms",
        description="LLM request duration in milliseconds",
        unit="ms",
    )

    tokens_input = m.create_counter(
        name="llmops_tokens_input_total",
        description="Total input tokens",
    )

    tokens_output = m.create_counter(
        name="llmops_tokens_output_total",
        description="Total output tokens",
    )

    cost_total = m.create_counter(
        name="llmops_cost_usd_total",
        description="Total cost in USD",
    )

    cache_hits = m.create_up_down_counter(
        name="llmops_cache_hits",
        description="Cache hit counter",
    )

    eval_score = m.create_histogram(
        name="llmops_eval_score",
        description="Evaluation scores",
    )

    error_total = m.create_counter(
        name="llmops_error_total",
        description="Total errors",
    )

    return {
        "request_duration": request_duration,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "cost_total": cost_total,
        "cache_hits": cache_hits,
        "eval_score": eval_score,
        "error_total": error_total,
    }


_metrics = None


def get_metrics() -> dict:
    """Return the singleton metrics dict, creating it on first call."""
    global _metrics
    if _metrics is None:
        _metrics = create_custom_metrics()
    return _metrics
