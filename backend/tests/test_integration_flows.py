"""
Integration tests: end-to-end flows across multiple services.

These tests exercise realistic user journeys through the API:
1. Prompt lifecycle: create app → prompt → versions → tag → diff → regression check
2. Experiment lifecycle: create experiment → start → record results → stop → promote
3. Cost tracking: request logs → analytics → budget alerts
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.cost import LLMRequestLog
from app.models.enums import EvalRunStatus, ExperimentStatus
from app.models.evaluation import EvalDataset, EvalDatasetItem, EvalResult, EvalRun
from app.models.experiment import Experiment, ExperimentResult, ExperimentVariant
from app.models.prompt import PromptTemplate, PromptVersion


# ---- Helpers ----

async def create_app_with_prompt(
    db: AsyncSession, user_id: uuid.UUID, app_name: str = "Integration App"
) -> tuple[Application, PromptTemplate]:
    """Create an application and prompt template directly in the database."""
    app = Application(id=uuid.uuid4(), name=app_name, description="Integration test", created_by=user_id)
    db.add(app)
    await db.flush()

    template = PromptTemplate(
        id=uuid.uuid4(),
        application_id=app.id,
        name=f"{app_name} Prompt",
        description="Integration test prompt",
    )
    db.add(template)
    await db.flush()
    await db.refresh(app)
    await db.refresh(template)
    return app, template


# ---- Test: Full Prompt Lifecycle ----

@pytest.mark.asyncio
async def test_prompt_lifecycle_with_diff_and_regression(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Create app → prompt → multiple versions → tag → detailed diff → regression check."""

    # Step 1: Create application via API
    resp = await client.post(
        "/api/v1/applications",
        json={"name": "Lifecycle App", "description": "Full lifecycle test"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    app_id = resp.json()["id"]

    # Step 2: Create prompt template
    resp = await client.post(
        f"/api/v1/applications/{app_id}/prompts",
        json={"name": "Lifecycle Prompt", "description": "Testing lifecycle"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    template_id = resp.json()["id"]

    # Step 3: Create version 1
    resp = await client.post(
        f"/api/v1/prompts/{template_id}/versions",
        json={
            "content": "Hello {{name}}! Welcome.",
            "commit_message": "Initial version",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    v1 = resp.json()
    assert v1["version_number"] == 1
    assert "name" in v1["variables"]
    v1_id = v1["id"]

    # Step 4: Create version 2 with more variables
    resp = await client.post(
        f"/api/v1/prompts/{template_id}/versions",
        json={
            "content": "Hello {{name}}! Welcome to {{company}}.\nYour role: {{role}}",
            "commit_message": "Added company and role variables",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    v2 = resp.json()
    assert v2["version_number"] == 2
    v2_id = v2["id"]

    # Step 5: Tag version 2 as production
    resp = await client.post(
        f"/api/v1/prompts/{template_id}/versions/2/tag",
        json={"tag": "production"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["tag"] == "production"

    # Step 6: Basic diff
    resp = await client.get(
        f"/api/v1/prompts/{template_id}/diff?v1=1&v2=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    diff = resp.json()
    assert diff["v1_content"] == "Hello {{name}}! Welcome."
    assert "{{company}}" in diff["v2_content"]

    # Step 7: Detailed diff
    resp = await client.get(
        f"/api/v1/prompts/{template_id}/diff/detailed?v1=1&v2=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    detailed = resp.json()
    assert detailed["lines_added"] > 0
    assert "company" in detailed["variables_added"]
    assert "role" in detailed["variables_added"]
    assert detailed["v2_tag"] == "production"
    assert detailed["v2_commit_message"] == "Added company and role variables"
    # v1 should have fewer variables
    assert len(detailed["v1_variables"]) < len(detailed["v2_variables"])

    # Step 8: Render production version
    resp = await client.post(
        f"/api/v1/prompts/{template_id}/render",
        json={"variables": {"name": "Alice", "company": "Acme", "role": "Engineer"}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "Alice" in resp.json()["rendered"]
    assert "Acme" in resp.json()["rendered"]

    # Step 9: Create eval dataset and eval runs for regression detection
    resp = await client.post(
        "/api/v1/eval/datasets",
        json={
            "application_id": app_id,
            "name": "Lifecycle Golden Set",
            "dataset_type": "golden",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    dataset_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/eval/datasets/{dataset_id}/items",
        json={
            "items": [
                {"input_vars": {"name": "Test"}, "expected_output": "Hello Test!"},
            ]
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    # Create completed eval runs directly in DB (since Celery isn't running in tests)
    run1 = EvalRun(
        id=uuid.uuid4(),
        prompt_version_id=uuid.UUID(v1_id),
        dataset_id=uuid.UUID(dataset_id),
        status=EvalRunStatus.COMPLETED,
        trigger="manual",
        aggregate_scores={"relevance": 3.5, "coherence": 4.0, "safety": 4.5},
        created_by=test_user.id,
        completed_at=datetime.now(timezone.utc),
    )
    run2 = EvalRun(
        id=uuid.uuid4(),
        prompt_version_id=uuid.UUID(v2_id),
        dataset_id=uuid.UUID(dataset_id),
        status=EvalRunStatus.COMPLETED,
        trigger="manual",
        aggregate_scores={"relevance": 4.2, "coherence": 3.2, "safety": 4.8},
        created_by=test_user.id,
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(run1)
    db_session.add(run2)
    await db_session.commit()

    # Step 10: Regression check
    resp = await client.get(
        f"/api/v1/eval/regression/{template_id}?v1=1&v2=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    reg = resp.json()
    assert reg["current_version"] == 2
    assert reg["previous_version"] == 1
    # coherence dropped from 4.0 to 3.2 = -20%, should be a regression
    assert reg["has_regression"] is True
    regression_metrics = [r["metric"] for r in reg["regressions"]]
    assert "coherence" in regression_metrics
    # relevance improved from 3.5 to 4.2 = +20%, should be an improvement
    improvement_metrics = [r["metric"] for r in reg["improvements"]]
    assert "relevance" in improvement_metrics

    # Step 11: Rollback to v1
    resp = await client.post(
        f"/api/v1/prompts/{template_id}/versions/1/rollback",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    v3 = resp.json()
    assert v3["version_number"] == 3
    assert v3["content"] == "Hello {{name}}! Welcome."
    assert "Rollback" in v3["commit_message"]


# ---- Test: Experiment Lifecycle ----

@pytest.mark.asyncio
async def test_experiment_lifecycle(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Create experiment → start → stop → verify results."""
    app, template = await create_app_with_prompt(db_session, test_user.id, "Experiment App")

    # Create two prompt versions
    v1 = PromptVersion(
        id=uuid.uuid4(), template_id=template.id, version_number=1,
        content="V1: Answer {{question}}", variables={"question": ""},
        created_by=test_user.id,
    )
    v2 = PromptVersion(
        id=uuid.uuid4(), template_id=template.id, version_number=2,
        content="V2: Please answer {{question}} thoughtfully", variables={"question": ""},
        created_by=test_user.id,
    )
    db_session.add(v1)
    db_session.add(v2)
    await db_session.commit()

    # Create experiment via API
    resp = await client.post(
        "/api/v1/experiments",
        json={
            "application_id": str(app.id),
            "name": "V1 vs V2 Test",
            "variants": [
                {"prompt_version_id": str(v1.id), "traffic_pct": 50, "label": "Control"},
                {"prompt_version_id": str(v2.id), "traffic_pct": 50, "label": "Challenger"},
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    exp = resp.json()
    exp_id = exp["id"]
    assert exp["status"] == "draft"
    assert len(exp["variants"]) == 2

    # Start experiment
    resp = await client.post(
        f"/api/v1/experiments/{exp_id}/start",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"

    # Get experiment
    resp = await client.get(
        f"/api/v1/experiments/{exp_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"

    # Stop experiment
    resp = await client.post(
        f"/api/v1/experiments/{exp_id}/stop",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    # Get results
    resp = await client.get(
        f"/api/v1/experiments/{exp_id}/results",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2


# ---- Test: Cost Tracking Flow ----

@pytest.mark.asyncio
async def test_cost_tracking_flow(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Create request logs → query analytics → create budget alert."""
    app, template = await create_app_with_prompt(db_session, test_user.id, "Cost App")

    # Insert request logs directly
    models = ["gpt-4o-mini", "gpt-4o", "claude-sonnet-4-20250514"]
    for i in range(20):
        log = LLMRequestLog(
            id=uuid.uuid4(),
            application_id=app.id,
            model=models[i % len(models)],
            input_tokens=100 + i * 10,
            output_tokens=50 + i * 5,
            cost_usd=Decimal(str(round(0.001 * (i + 1), 6))),
            latency_ms=200 + i * 50,
            cache_hit=i % 4 == 0,
        )
        db_session.add(log)
    await db_session.commit()

    # Query analytics
    resp = await client.get(
        "/api/v1/cost/analytics",
        params={"application_id": str(app.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    analytics = resp.json()
    assert analytics["total_requests"] == 20
    assert float(analytics["total_cost_usd"]) > 0
    assert analytics["total_input_tokens"] > 0
    assert analytics["total_output_tokens"] > 0
    assert 0 <= analytics["cache_hit_rate"] <= 1

    # Create budget alert
    resp = await client.post(
        "/api/v1/cost/budget-alerts",
        json={
            "application_id": str(app.id),
            "budget_usd": 100.00,
            "period": "monthly",
            "alert_pct": [80, 100],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    alert = resp.json()
    assert float(alert["budget_usd"]) == 100.00
    assert alert["is_active"] is True

    # List budget alerts
    resp = await client.get(
        "/api/v1/cost/budget-alerts",
        params={"application_id": str(app.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ---- Test: Eval Dataset and Run Flow ----

@pytest.mark.asyncio
async def test_eval_dataset_and_run_flow(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Create dataset → add items → verify counts → list datasets."""
    app, template = await create_app_with_prompt(db_session, test_user.id, "Eval App")

    # Create dataset
    resp = await client.post(
        "/api/v1/eval/datasets",
        json={
            "application_id": str(app.id),
            "name": "Golden Dataset",
            "dataset_type": "golden",
            "description": "Integration test dataset",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    dataset = resp.json()
    dataset_id = dataset["id"]

    # Add items
    resp = await client.post(
        f"/api/v1/eval/datasets/{dataset_id}/items",
        json={
            "items": [
                {"input_vars": {"query": "Hello"}, "expected_output": "Hi there!"},
                {"input_vars": {"query": "Help me"}, "expected_output": "Sure!"},
                {"input_vars": {"query": "Bye"}, "expected_output": "Goodbye!"},
            ]
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    items = resp.json()
    assert len(items) == 3

    # List datasets — should show item count
    resp = await client.get(
        "/api/v1/eval/datasets",
        params={"application_id": str(app.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) >= 1
    ds = next(d for d in datasets if d["id"] == dataset_id)
    assert ds["item_count"] == 3


# ---- Test: Deployment Flow ----

@pytest.mark.asyncio
async def test_deployment_create_and_list(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Create deployment → list → verify status."""
    app, template = await create_app_with_prompt(db_session, test_user.id, "Deploy App")

    v1 = PromptVersion(
        id=uuid.uuid4(), template_id=template.id, version_number=1,
        content="Deploy test", variables={}, created_by=test_user.id,
    )
    db_session.add(v1)
    await db_session.commit()

    # List deployments (initially empty)
    resp = await client.get(
        "/api/v1/deployments",
        params={"application_id": str(app.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    # Create deployment
    resp = await client.post(
        "/api/v1/deployments",
        json={"prompt_version_id": str(v1.id), "canary_pct": 10},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    dep = resp.json()
    assert dep["canary_pct"] == 10
    dep_id = dep["id"]

    # Get deployment
    resp = await client.get(
        f"/api/v1/deployments/{dep_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["prompt_version_id"] == str(v1.id)


# ---- Test: Regression Check Without Eval Runs ----

@pytest.mark.asyncio
async def test_regression_check_requires_eval_runs(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Regression check returns 404 when no eval runs exist."""
    app, template = await create_app_with_prompt(db_session, test_user.id, "NoEval App")

    v1 = PromptVersion(
        id=uuid.uuid4(), template_id=template.id, version_number=1,
        content="No eval", variables={}, created_by=test_user.id,
    )
    db_session.add(v1)
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/eval/regression/{template.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ---- Test: Application CRUD ----

@pytest.mark.asyncio
async def test_application_crud(
    client: AsyncClient, db_session: AsyncSession, test_user, auth_headers
):
    """Create → list → get application."""
    resp = await client.post(
        "/api/v1/applications",
        json={"name": "CRUD App", "description": "Integration test"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    app_id = resp.json()["id"]

    resp = await client.get("/api/v1/applications", headers=auth_headers)
    assert resp.status_code == 200
    assert any(a["id"] == app_id for a in resp.json())

    resp = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "CRUD App"
