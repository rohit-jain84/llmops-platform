import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import RoutingRule


class RoutingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def select_model(
        self,
        app_id: uuid.UUID,
        input_text: str,
        default_model: str = "gpt-4o-mini",
    ) -> str:
        result = await self.db.execute(
            select(RoutingRule)
            .where(RoutingRule.application_id == app_id, RoutingRule.is_active == True)
            .order_by(RoutingRule.priority.asc())
        )
        rules = result.scalars().all()

        for rule in rules:
            if self._evaluate_condition(rule.condition, input_text):
                return rule.target_model

        return default_model

    def _evaluate_condition(self, condition: dict, input_text: str) -> bool:
        cond_type = condition.get("type")

        if cond_type == "complexity":
            # Simple heuristic: token count proxy
            threshold = condition.get("threshold", 500)
            word_count = len(input_text.split())
            return word_count > threshold

        elif cond_type == "keyword":
            keywords = condition.get("keywords", [])
            text_lower = input_text.lower()
            return any(kw.lower() in text_lower for kw in keywords)

        elif cond_type == "length":
            max_length = condition.get("max_length", 1000)
            return len(input_text) > max_length

        return False
