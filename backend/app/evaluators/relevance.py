import logging

import litellm

from app.config import settings
from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import register

logger = logging.getLogger(__name__)

RELEVANCE_PROMPT = """You are an evaluation judge. Rate how relevant the response is to the question asked.

Question: {input_text}
Response: {output_text}

Rate on a scale of 1-5:
1 = Completely irrelevant, does not address the question at all
2 = Mostly irrelevant with slight connection to the topic
3 = Partially relevant, addresses some aspects of the question
4 = Mostly relevant, addresses the main question with minor tangents
5 = Perfectly relevant, directly and completely answers the question

Respond with ONLY a single number (1-5)."""


@register
class RelevanceEvaluator(BaseEvaluator):
    name = "relevance"
    description = "LLM-as-judge: does the response actually answer the question asked?"

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: str | None,
        context: dict,
    ) -> float:
        try:
            prompt = RELEVANCE_PROMPT.format(input_text=input_text, output_text=output_text)
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
            logger.warning(f"Relevance evaluation failed: {e}")
            return 3.0
