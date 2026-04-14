from abc import ABC, abstractmethod


class BaseEvaluator(ABC):
    name: str
    description: str

    @abstractmethod
    async def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: str | None,
        context: dict,
    ) -> float:
        """Return a score for this evaluation metric."""
        ...
