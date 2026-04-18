import pytest
from httpx import AsyncClient

from app.models.application import Application
from app.models.prompt import PromptTemplate, PromptVersion


@pytest.mark.asyncio
async def test_create_experiment(client: AsyncClient, db_session, test_user, auth_headers):
    # Setup: create app with prompt versions
    app_obj = Application(name="Exp App", description="Test", created_by=test_user.id)
    db_session.add(app_obj)
    await db_session.flush()

    template = PromptTemplate(application_id=app_obj.id, name="Exp Prompt")
    db_session.add(template)
    await db_session.flush()

    v1 = PromptVersion(
        template_id=template.id,
        version_number=1,
        content="Control: {{input}}",
        created_by=test_user.id,
    )
    v2 = PromptVersion(
        template_id=template.id,
        version_number=2,
        content="Variant: {{input}}",
        created_by=test_user.id,
    )
    db_session.add_all([v1, v2])
    await db_session.commit()

    # Create experiment
    response = await client.post(
        "/api/v1/experiments",
        json={
            "application_id": str(app_obj.id),
            "name": "A/B Test 1",
            "variants": [
                {"prompt_version_id": str(v1.id), "traffic_pct": 50, "label": "control"},
                {"prompt_version_id": str(v2.id), "traffic_pct": 50, "label": "variant_a"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    exp = response.json()
    assert exp["name"] == "A/B Test 1"
    assert len(exp["variants"]) == 2

    # Start experiment
    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/start",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "running"

    # Stop experiment
    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/stop",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# Statistical significance tests
# ---------------------------------------------------------------------------


async def _create_running_experiment(client, db_session, test_user, auth_headers):
    """Helper: creates an app, prompt versions, and a running experiment with two variants."""
    app_obj = Application(name="Sig App", description="Test", created_by=test_user.id)
    db_session.add(app_obj)
    await db_session.flush()

    template = PromptTemplate(application_id=app_obj.id, name="Sig Prompt")
    db_session.add(template)
    await db_session.flush()

    v1 = PromptVersion(
        template_id=template.id,
        version_number=1,
        content="Control: {{input}}",
        created_by=test_user.id,
    )
    v2 = PromptVersion(
        template_id=template.id,
        version_number=2,
        content="Variant: {{input}}",
        created_by=test_user.id,
    )
    db_session.add_all([v1, v2])
    await db_session.commit()

    response = await client.post(
        "/api/v1/experiments",
        json={
            "application_id": str(app_obj.id),
            "name": "Significance Test",
            "variants": [
                {"prompt_version_id": str(v1.id), "traffic_pct": 50, "label": "control"},
                {"prompt_version_id": str(v2.id), "traffic_pct": 50, "label": "variant_a"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    exp = response.json()

    # Start it
    await client.post(f"/api/v1/experiments/{exp['id']}/start", headers=auth_headers)

    return exp


@pytest.mark.asyncio
async def test_record_eval_score(client: AsyncClient, db_session, test_user, auth_headers):
    """Scores can be recorded against a variant and accumulate in metrics."""
    exp = await _create_running_experiment(client, db_session, test_user, auth_headers)
    variant_id = exp["variants"][0]["id"]

    for score in [0.8, 0.9, 0.85]:
        response = await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{variant_id}/scores",
            params={"score": score},
            headers=auth_headers,
        )
        assert response.status_code == 200

    result = response.json()
    assert result["request_count"] == 3
    assert len(result["metrics"]["scores"]) == 3
    assert result["metrics"]["scores"] == pytest.approx([0.8, 0.9, 0.85])


@pytest.mark.asyncio
async def test_significance_clear_winner(client: AsyncClient, db_session, test_user, auth_headers):
    """When one variant is clearly better, it should be marked as winner."""
    exp = await _create_running_experiment(client, db_session, test_user, auth_headers)
    v_control = exp["variants"][0]["id"]
    v_variant = exp["variants"][1]["id"]

    # Control: low scores
    for score in [0.3, 0.35, 0.28, 0.32, 0.31, 0.29, 0.33, 0.30]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_control}/scores",
            params={"score": score},
            headers=auth_headers,
        )

    # Variant: clearly higher scores
    for score in [0.9, 0.88, 0.92, 0.87, 0.91, 0.89, 0.93, 0.90]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_variant}/scores",
            params={"score": score},
            headers=auth_headers,
        )

    # Compute significance
    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/significance",
        headers=auth_headers,
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2

    winner = [r for r in results if r["is_winner"]]
    assert len(winner) == 1
    assert winner[0]["variant_id"] == v_variant
    assert winner[0]["p_value"] < 0.05


@pytest.mark.asyncio
async def test_significance_no_winner_similar_scores(client: AsyncClient, db_session, test_user, auth_headers):
    """When scores are similar, no winner should be declared."""
    exp = await _create_running_experiment(client, db_session, test_user, auth_headers)
    v_control = exp["variants"][0]["id"]
    v_variant = exp["variants"][1]["id"]

    # Both variants have nearly identical scores
    for score in [0.80, 0.82, 0.79, 0.81, 0.80]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_control}/scores",
            params={"score": score},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_variant}/scores",
            params={"score": score + 0.005},
            headers=auth_headers,
        )

    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/significance",
        headers=auth_headers,
    )
    results = response.json()
    winners = [r for r in results if r["is_winner"]]
    assert len(winners) == 0


@pytest.mark.asyncio
async def test_significance_insufficient_data(client: AsyncClient, db_session, test_user, auth_headers):
    """With only 1 score per variant, p-value should be 1.0 and no winner declared."""
    exp = await _create_running_experiment(client, db_session, test_user, auth_headers)
    v_control = exp["variants"][0]["id"]
    v_variant = exp["variants"][1]["id"]

    await client.post(
        f"/api/v1/experiments/{exp['id']}/variants/{v_control}/scores",
        params={"score": 0.5},
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/experiments/{exp['id']}/variants/{v_variant}/scores",
        params={"score": 0.9},
        headers=auth_headers,
    )

    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/significance",
        headers=auth_headers,
    )
    results = response.json()
    for r in results:
        assert r["is_winner"] is False
    # At least one result should have p_value = 1.0
    p_values = [r["p_value"] for r in results if r["p_value"] is not None]
    assert any(p == 1.0 for p in p_values)


@pytest.mark.asyncio
async def test_significance_one_tailed_directionality(client: AsyncClient, db_session, test_user, auth_headers):
    """The test must be one-tailed: higher-mean variant wins, not just 'different'."""

    exp = await _create_running_experiment(client, db_session, test_user, auth_headers)
    v_control = exp["variants"][0]["id"]
    v_variant = exp["variants"][1]["id"]

    # Control is clearly HIGHER than variant
    for score in [0.9, 0.88, 0.92, 0.87, 0.91, 0.89, 0.93, 0.90]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_control}/scores",
            params={"score": score},
            headers=auth_headers,
        )
    for score in [0.3, 0.35, 0.28, 0.32, 0.31, 0.29, 0.33, 0.30]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_variant}/scores",
            params={"score": score},
            headers=auth_headers,
        )

    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/significance",
        headers=auth_headers,
    )
    results = response.json()
    winner = [r for r in results if r["is_winner"]]
    assert len(winner) == 1
    # The CONTROL (higher scores) must win, not the variant
    assert winner[0]["variant_id"] == v_control


@pytest.mark.asyncio
async def test_significance_custom_level(client: AsyncClient, db_session, test_user, auth_headers):
    """A stricter significance level (0.001) should reject borderline cases."""
    exp = await _create_running_experiment(client, db_session, test_user, auth_headers)
    v_control = exp["variants"][0]["id"]
    v_variant = exp["variants"][1]["id"]

    # Moderately different scores -- pass alpha=0.05 but fail alpha=0.001.
    # Means 0.5125 vs 0.5725, t ≈ -3.24, two-sample p ≈ 0.018
    # (verified via scipy.stats.ttest_ind): well below 0.05, well above 0.001.
    for score in [0.5, 0.55, 0.48, 0.52]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_control}/scores",
            params={"score": score},
            headers=auth_headers,
        )
    for score in [0.55, 0.60, 0.56, 0.58]:
        await client.post(
            f"/api/v1/experiments/{exp['id']}/variants/{v_variant}/scores",
            params={"score": score},
            headers=auth_headers,
        )

    response = await client.post(
        f"/api/v1/experiments/{exp['id']}/significance",
        params={"significance_level": 0.001},
        headers=auth_headers,
    )
    results = response.json()
    # With very strict alpha, borderline differences should not produce a winner
    winners = [r for r in results if r["is_winner"]]
    assert len(winners) == 0
