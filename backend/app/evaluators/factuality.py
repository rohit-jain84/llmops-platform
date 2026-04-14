import logging

import litellm

from app.config import settings
from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import register

logger = logging.getLogger(__name__)

FACTUALITY_PROMPT = """You are an evaluation judge. Rate how factually grounded the response is based on the provided context/expected output.

Input: {input_text}
Response: {output_text}
Expected Output: {expected_output}

Rate on a scale of 1-5:
1 = Completely fabricated or contradicts the context
2 = Mostly inaccurate with some correct elements
3 = Mix of accurate and inaccurate information
4 = Mostly accurate with minor issues
5 = Fully grounded and factually correct

Respond with ONLY a single number (1-5)."""


@register
class FactualityEvaluator(BaseEvaluator):
    name = "factuality"
    description = "LLM-as-judge: rates how grounded the response is in the provided context"

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: str | None,
        context: dict,
    ) -> float:
        try:
            prompt = FACTUALITY_PROMPT.format(
                input_text=input_text,
                output_text=output_text,
                expected_output=expected_output or "N/A",
            )
            response = await litellm.acompletion(
                model=settings.evaluator_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=5,
            )
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(1.0, min(5.0, score))
        except Exception as e:
            logger.warning(f"Factuality evaluation failed: {e}")
            return 3.0
