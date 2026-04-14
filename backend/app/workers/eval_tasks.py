import asyncio
import logging
import time
import uuid
from decimal import Decimal

import litellm
from opentelemetry import trace
from sqlalchemy import select

from app.database import async_session_factory
from app.evaluators.registry import EVALUATORS
from app.models.enums import EvalRunStatus
from app.models.evaluation import EvalDatasetItem, EvalResult, EvalRun
from app.models.prompt import PromptVersion
from app.services.prompt_service import PromptService
from app.telemetry.metrics import get_metrics
from app.workers.celery_app import celery_app

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.eval_tasks.run_eval_suite")
def run_eval_suite(self, eval_run_id: str):
    with tracer.start_as_current_span("eval.run_suite", attributes={"eval_run_id": eval_run_id}):
        _run_async(_run_eval_suite_async(eval_run_id))


async def _run_eval_suite_async(eval_run_id: str):
    async with async_session_factory() as db:
        # Get eval run
        result = await db.execute(
            select(EvalRun).where(EvalRun.id == uuid.UUID(eval_run_id))
        )
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"Eval run {eval_run_id} not found")
            return

        run.status = EvalRunStatus.RUNNING
        await db.commit()

        try:
            # Get prompt version
            pv_result = await db.execute(
                select(PromptVersion).where(PromptVersion.id == run.prompt_version_id)
            )
            prompt_version = pv_result.scalar_one()

            # Get dataset items
            items_result = await db.execute(
                select(EvalDatasetItem).where(EvalDatasetItem.dataset_id == run.dataset_id)
            )
            items = items_result.scalars().all()

            model_config = prompt_version.model_config_json or {}
            model = model_config.get("model", "gpt-4o-mini")

            all_scores = {}
            evaluators = {name: cls() for name, cls in EVALUATORS.items()}

            for item in items:
                # Render prompt
                import jinja2
                env = jinja2.Environment(undefined=jinja2.StrictUndefined)
                template = env.from_string(prompt_version.content)
                rendered = template.render(**item.input_vars)

                # Call LLM
                start = time.monotonic()
                try:
                    response = await litellm.acompletion(
                        model=model,
                        messages=[{"role": "user", "content": rendered}],
                        temperature=model_config.get("temperature", 0.7),
                        max_tokens=model_config.get("max_tokens", 1024),
                    )
                    latency_ms = int((time.monotonic() - start) * 1000)
                    output = response.choices[0].message.content or ""
                    input_tokens = response.usage.prompt_tokens if response.usage else 0
                    output_tokens = response.usage.completion_tokens if response.usage else 0
                    cost = litellm.completion_cost(completion_response=response)
                except Exception as e:
                    logger.error(f"LLM call failed for item {item.id}: {e}")
                    latency_ms = int((time.monotonic() - start) * 1000)
                    output = f"Error: {e}"
                    input_tokens = 0
                    output_tokens = 0
                    cost = 0

                # Run evaluators
                scores = {}
                metrics = get_metrics()
                for name, evaluator in evaluators.items():
                    try:
                        score = await evaluator.evaluate(
                            input_text=rendered,
                            output_text=output,
                            expected_output=item.expected_output,
                            context={"model": model, "latency_ms": latency_ms},
                        )
                        scores[name] = score
                    except Exception as e:
                        logger.warning(f"Evaluator {name} failed: {e}")
                        scores[name] = 0.0
                    metrics["eval_score"].record(
                        scores[name], {"evaluator": name, "model": model}
                    )

                # Add latency as a score
                scores["latency"] = float(latency_ms)

                # Store result
                eval_result = EvalResult(
                    eval_run_id=run.id,
                    dataset_item_id=item.id,
                    llm_response=output,
                    scores=scores,
                    latency_ms=latency_ms,
                    token_usage={"input": input_tokens, "output": output_tokens},
                    cost_usd=Decimal(str(round(cost, 6))),
                )
                db.add(eval_result)

                # Accumulate scores
                for key, value in scores.items():
                    if key not in all_scores:
                        all_scores[key] = []
                    all_scores[key].append(value)

            # Aggregate scores
            aggregate = {}
            for key, values in all_scores.items():
                if values:
                    aggregate[key] = round(sum(values) / len(values), 4)

            run.aggregate_scores = aggregate
            run.status = EvalRunStatus.COMPLETED
            from datetime import datetime, timezone
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"Eval run {eval_run_id} completed. Scores: {aggregate}")

        except Exception as e:
            logger.error(f"Eval run {eval_run_id} failed: {e}")
            run.status = EvalRunStatus.FAILED
            await db.commit()
            raise
