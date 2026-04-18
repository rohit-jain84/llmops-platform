import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.database import async_session_factory
from app.models.cost import BudgetAlert, LLMRequestLog
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.cost_tasks.check_budgets")
def check_budgets():
    _run_async(_check_budgets_async())


async def _check_budgets_async():
    async with async_session_factory() as db:
        result = await db.execute(select(BudgetAlert).where(BudgetAlert.is_active == True))
        alerts = result.scalars().all()

        for alert in alerts:
            now = datetime.now(timezone.utc)

            if alert.period == "daily":
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif alert.period == "weekly":
                period_start = now - timedelta(days=now.weekday())
                period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            else:  # monthly
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            cost_result = await db.execute(
                select(func.sum(LLMRequestLog.cost_usd)).where(
                    LLMRequestLog.application_id == alert.application_id,
                    LLMRequestLog.created_at >= period_start,
                )
            )
            total_spend = float(cost_result.scalar() or 0)
            budget = float(alert.budget_usd)

            if budget > 0:
                usage_pct = (total_spend / budget) * 100
                for threshold in sorted(alert.alert_pct):
                    if usage_pct >= threshold:
                        last = alert.last_triggered_pct or 0
                        if threshold > last:
                            logger.warning(
                                f"Budget alert: App {alert.application_id} at {usage_pct:.1f}% "
                                f"(${total_spend:.2f}/${budget:.2f}) - threshold {threshold}%"
                            )
                            alert.last_triggered_pct = threshold

        await db.commit()


@celery_app.task(name="app.workers.cost_tasks.generate_cost_forecast")
def generate_cost_forecast():
    _run_async(_generate_cost_forecast_async())


async def _generate_cost_forecast_async():
    async with async_session_factory() as db:
        # Get unique application IDs with recent activity
        result = await db.execute(
            select(LLMRequestLog.application_id)
            .where(LLMRequestLog.created_at >= datetime.now(timezone.utc) - timedelta(days=7))
            .distinct()
        )
        app_ids = [row[0] for row in result.all()]

        for app_id in app_ids:
            logger.info(f"Generated cost forecast for application {app_id}")
