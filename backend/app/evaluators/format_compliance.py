import json
import logging

from app.evaluators.base import BaseEvaluator
from app.evaluators.registry import register

logger = logging.getLogger(__name__)


@register
class FormatComplianceEvaluator(BaseEvaluator):
    name = "format_compliance"
    description = "Programmatic: validate response against expected format constraints"

    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: str | None,
        context: dict,
    ) -> float:
        checks_passed = 0
        total_checks = 0

        # Check: non-empty response
        total_checks += 1
        if output_text and output_text.strip():
            checks_passed += 1

        # Check: reasonable length (not too short or too long)
        total_checks += 1
        if 10 < len(output_text) < 50000:
            checks_passed += 1

        # Check: if expected_output looks like JSON, check response is valid JSON
        if expected_output:
            try:
                json.loads(expected_output)
                total_checks += 1
                try:
                    json.loads(output_text)
                    checks_passed += 1
                except (json.JSONDecodeError, ValueError):
                    pass
            except (json.JSONDecodeError, ValueError):
                pass

        return 1.0 if total_checks > 0 and checks_passed == total_checks else 0.0
