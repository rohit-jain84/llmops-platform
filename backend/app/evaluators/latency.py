from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import register


@register
class LatencyEvaluator(BaseEvaluator):
    name = "latency"
    description = "Measured: actual LLM response time in milliseconds"

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: str | None,
        context: dict,
    ) -> float:
        return float(context.get("latency_ms", 0))
