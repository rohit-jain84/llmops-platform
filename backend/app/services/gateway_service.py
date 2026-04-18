import logging
import time
from decimal import Decimal

import litellm
from opentelemetry import trace as otel_trace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import PromptVersion
from app.services.cache_service import CacheService
from app.services.cost_service import CostService
from app.services.experiment_service import ExperimentService
from app.services.langfuse_service import LangFuseService
from app.services.prompt_service import PromptService
from app.services.routing_service import RoutingService
from app.telemetry.metrics import get_metrics

logger = logging.getLogger(__name__)
tracer = otel_trace.get_tracer(__name__)


class GatewayService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.experiment_svc = ExperimentService(db)
        self.prompt_svc = PromptService(db)
        self.routing_svc = RoutingService(db)
        self.cache_svc = CacheService()
        self.cost_svc = CostService(db)
        self.langfuse_svc = LangFuseService()

    async def handle_chat(self, request) -> dict:
        # 1. Experiment resolution
        variant = await self.experiment_svc.resolve_variant(request.application_id, request.user_id)

        if variant:
            prompt_version_id = variant.prompt_version_id
        else:
            # Get production version
            result = await self.db.execute(
                select(PromptVersion).where(
                    PromptVersion.template_id == request.prompt_template_id, PromptVersion.tag == "production"
                )
            )
            version = result.scalar_one_or_none()
            if not version:
                # Fallback to latest
                result = await self.db.execute(
                    select(PromptVersion)
                    .where(PromptVersion.template_id == request.prompt_template_id)
                    .order_by(PromptVersion.version_number.desc())
                    .limit(1)
                )
                version = result.scalar_one_or_none()
                if not version:
                    raise ValueError("No prompt version found")
            prompt_version_id = version.id

        # 2. Render prompt
        render_result = await self.prompt_svc.render(request.prompt_template_id, request.variables)
        rendered_input = render_result.rendered

        # 3. Semantic cache check
        with tracer.start_as_current_span("cache.lookup", attributes={"app_id": str(request.application_id)}):
            try:
                cached = await self.cache_svc.lookup(request.application_id, rendered_input)
            except Exception as e:
                logger.warning(f"Cache lookup failed, treating as miss: {e}")
                cached = None
        if cached:
            await self.cost_svc.log_request(
                application_id=request.application_id,
                model=cached.get("model", "cache"),
                input_tokens=0,
                output_tokens=0,
                cost_usd=Decimal("0"),
                latency_ms=0,
                cache_hit=True,
                prompt_version_id=prompt_version_id,
                experiment_variant_id=variant.id if variant else None,
            )
            return {
                "response": cached["response"],
                "model": cached.get("model", "cache"),
                "latency_ms": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0,
                "cache_hit": True,
                "variant_id": str(variant.id) if variant else None,
            }

        # 4. Model routing
        default_model = request.model or "gpt-4o-mini"
        target_model = await self.routing_svc.select_model(request.application_id, rendered_input, default_model)

        # 5. Create LangFuse trace
        trace = self.langfuse_svc.create_trace(
            name=str(request.application_id),
            metadata={"prompt_version_id": str(prompt_version_id)},
        )

        # 6. Call LLM via litellm
        start = time.monotonic()
        messages = [{"role": "user", "content": rendered_input}]

        kwargs = {"model": target_model, "messages": messages}
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        with tracer.start_as_current_span("llm.completion", attributes={"model": target_model}) as llm_span:
            try:
                response = await litellm.acompletion(**kwargs)
            except Exception:
                metrics = get_metrics()
                metrics["error_total"].add(1, {"model": target_model})
                llm_span.set_status(otel_trace.StatusCode.ERROR)
                raise
        latency_ms = int((time.monotonic() - start) * 1000)

        response_text = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        # Calculate cost using litellm
        cost = litellm.completion_cost(completion_response=response)

        # Record OTel metrics
        metrics = get_metrics()
        attrs = {"model": target_model}
        metrics["request_duration"].record(latency_ms, attrs)
        metrics["tokens_input"].add(input_tokens, attrs)
        metrics["tokens_output"].add(output_tokens, attrs)
        metrics["cost_total"].add(float(cost), attrs)

        # 7. Log generation to LangFuse
        trace_id = None
        if trace:
            trace_id = getattr(trace, "id", None)
            self.langfuse_svc.log_generation(
                trace=trace,
                model=target_model,
                input_text=rendered_input,
                output_text=response_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=float(cost),
            )
            self.langfuse_svc.flush()

        # 8. Store in semantic cache
        with tracer.start_as_current_span("cache.store", attributes={"model": target_model}):
            try:
                await self.cache_svc.store(
                    request.application_id,
                    rendered_input,
                    response_text,
                    target_model,
                    str(prompt_version_id),
                )
            except Exception as e:
                logger.warning(f"Cache store failed, continuing without caching: {e}")

        # 9. Log cost and usage
        await self.cost_svc.log_request(
            application_id=request.application_id,
            model=target_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=Decimal(str(round(cost, 6))),
            latency_ms=latency_ms,
            cache_hit=False,
            prompt_version_id=prompt_version_id,
            experiment_variant_id=variant.id if variant else None,
            routed_model=target_model if target_model != default_model else None,
            trace_id=trace_id,
        )

        return {
            "response": response_text,
            "model": target_model,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": float(cost),
            "cache_hit": False,
            "trace_id": trace_id,
            "variant_id": str(variant.id) if variant else None,
        }
