from app.evaluators.base import BaseEvaluator

EVALUATORS: dict[str, type[BaseEvaluator]] = {}


def register(cls: type[BaseEvaluator]) -> type[BaseEvaluator]:
    EVALUATORS[cls.name] = cls
    return cls
