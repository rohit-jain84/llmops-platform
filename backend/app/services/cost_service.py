import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import LLMRequestLog
from app.schemas.cost import CostAnalyticsResponse, CostForecastResponse


class CostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_request(
        self,
        application_id: uuid.UUID,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        latency_ms: int,
        cache_hit: bool = False,
        prompt_version_id: uuid.UUID | None = None,
        experiment_variant_id: uuid.UUID | None = None,
        routed_model: str | None = None,
        trace_id: str | None = None,
    ) -> LLMRequestLog:
        log = LLMRequestLog(
            application_id=application_id,
            prompt_version_id=prompt_version_id,
            experiment_variant_id=experiment_variant_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            routed_model=routed_model,
            trace_id=trace_id,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_analytics(
        self,
        application_id: uuid.UUID | None,
        date_from: str | None,
        date_to: str | None,
        group_by: str,
    ) -> CostAnalyticsResponse:
        query = select(
            func.sum(LLMRequestLog.cost_usd).label("total_cost"),
            func.count().label("total_requests"),
            func.sum(LLMRequestLog.input_tokens).label("total_input_tokens"),
            func.sum(LLMRequestLog.output_tokens).label("total_output_tokens"),
            func.avg(LLMRequestLog.cache_hit.cast(int)).label("cache_hit_rate"),
        )

        if application_id:
            query = query.where(LLMRequestLog.application_id == application_id)
        if date_from:
            query = query.where(LLMRequestLog.created_at >= date_from)
        if date_to:
            query = query.where(LLMRequestLog.created_at <= date_to)

        result = await self.db.execute(query)
        row = result.one()

        # Build breakdown
        breakdown_query = select(
            func.date_trunc(group_by, LLMRequestLog.created_at).label("period"),
            func.sum(LLMRequestLog.cost_usd).label("cost"),
            func.count().label("requests"),
        )
        if application_id:
            breakdown_query = breakdown_query.where(LLMRequestLog.application_id == application_id)
        if date_from:
            breakdown_query = breakdown_query.where(LLMRequestLog.created_at >= date_from)
        if date_to:
            breakdown_query = breakdown_query.where(LLMRequestLog.created_at <= date_to)

        breakdown_query = breakdown_query.group_by("period").order_by("period")
        breakdown_result = await self.db.execute(breakdown_query)
        breakdown = [
            {"period": str(r.period), "cost": float(r.cost or 0), "requests": r.requests}
            for r in breakdown_result.all()
        ]

        return CostAnalyticsResponse(
            total_cost_usd=row.total_cost or Decimal("0"),
            total_requests=row.total_requests or 0,
            total_input_tokens=row.total_input_tokens or 0,
            total_output_tokens=row.total_output_tokens or 0,
            cache_hit_rate=float(row.cache_hit_rate or 0),
            breakdown=breakdown,
        )

    async def get_forecast(self, app_id: uuid.UUID) -> CostForecastResponse:
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        result = await self.db.execute(
            select(
                func.sum(LLMRequestLog.cost_usd).label("total"),
                func.count().label("days"),
            )
            .where(
                LLMRequestLog.application_id == app_id,
                LLMRequestLog.created_at >= seven_days_ago,
            )
        )
        row = result.one()
        total_cost = float(row.total or 0)
        daily_avg = total_cost / 7 if total_cost > 0 else 0

        # Project 30 days
        projected = daily_avg * 30
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        current_result = await self.db.execute(
            select(func.sum(LLMRequestLog.cost_usd))
            .where(
                LLMRequestLog.application_id == app_id,
                LLMRequestLog.created_at >= current_month_start,
            )
        )
        current_cost = float(current_result.scalar() or 0)

        trend_pct = ((daily_avg * 30 - current_cost) / max(current_cost, 0.01)) * 100

        daily_projections = []
        for i in range(30):
            day = now + timedelta(days=i)
            daily_projections.append({
                "date": day.strftime("%Y-%m-%d"),
                "projected_cost": round(daily_avg, 4),
            })

        return CostForecastResponse(
            application_id=app_id,
            current_period_cost=Decimal(str(round(current_cost, 6))),
            projected_cost=Decimal(str(round(projected, 6))),
            trend_pct=round(trend_pct, 2),
            forecast_days=30,
            daily_projections=daily_projections,
        )
