import uuid

import pytest
from httpx import AsyncClient

from app.models.application import Application


@pytest.mark.asyncio
async def test_budget_alerts(client: AsyncClient, db_session, test_user, auth_headers):
    app_obj = Application(name="Cost App", description="Test", created_by=test_user.id)
    db_session.add(app_obj)
    await db_session.commit()
    await db_session.refresh(app_obj)

    # Create budget alert
    response = await client.post(
        "/api/v1/cost/budget-alerts",
        json={
            "application_id": str(app_obj.id),
            "budget_usd": 100.00,
            "period": "monthly",
            "alert_pct": [80, 100],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    alert = response.json()
    assert alert["budget_usd"] == "100.00"

    # List budget alerts
    response = await client.get("/api/v1/cost/budget-alerts", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_cost_analytics(client: AsyncClient, db_session, test_user, auth_headers):
    response = await client.get("/api/v1/cost/analytics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_cost_usd" in data
    assert "total_requests" in data
