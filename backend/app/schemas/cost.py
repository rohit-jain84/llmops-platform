import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CostAnalyticsQuery(BaseModel):
    application_id: uuid.UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    group_by: str = "day"  # day, week, month, model, application


class CostAnalyticsResponse(BaseModel):
    total_cost_usd: Decimal
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    cache_hit_rate: float
    breakdown: list[dict]


class CostForecastResponse(BaseModel):
    application_id: uuid.UUID
    current_period_cost: Decimal
    projected_cost: Decimal
    trend_pct: float
    forecast_days: int
    daily_projections: list[dict]


class BudgetAlertCreate(BaseModel):
    application_id: uuid.UUID
    budget_usd: Decimal
    period: str = "monthly"
    alert_pct: list[int] = [80, 100]


class BudgetAlertResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    budget_usd: Decimal
    period: str
    alert_pct: list[int]
    is_active: bool
    last_triggered_pct: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
