import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.cost import BudgetAlert
from app.models.user import User
from app.schemas.cost import (
    BudgetAlertCreate,
    BudgetAlertResponse,
    CostAnalyticsQuery,
    CostAnalyticsResponse,
    CostForecastResponse,
)
from app.services.cost_service import CostService

router = APIRouter()


@router.get("/analytics", response_model=CostAnalyticsResponse)
async def get_analytics(
    application_id: uuid.UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    group_by: str = "day",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CostService(db)
    return await svc.get_analytics(application_id, date_from, date_to, group_by)


@router.get("/forecast/{app_id}", response_model=CostForecastResponse)
async def get_forecast(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = CostService(db)
    return await svc.get_forecast(app_id)


@router.post("/budget-alerts", response_model=BudgetAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_alert(
    data: BudgetAlertCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    alert = BudgetAlert(
        application_id=data.application_id,
        budget_usd=data.budget_usd,
        period=data.period,
        alert_pct=data.alert_pct,
        created_by=user.id,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


@router.get("/budget-alerts", response_model=list[BudgetAlertResponse])
async def list_budget_alerts(
    application_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(BudgetAlert)
    if application_id:
        query = query.where(BudgetAlert.application_id == application_id)
    result = await db.execute(query.order_by(BudgetAlert.created_at.desc()))
    return result.scalars().all()
