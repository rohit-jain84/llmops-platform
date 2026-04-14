import uuid

import pytest
from httpx import AsyncClient

from app.models.application import Application


@pytest.mark.asyncio
async def test_create_dataset_and_items(client: AsyncClient, db_session, test_user, auth_headers):
    app_obj = Application(name="Eval App", description="Test", created_by=test_user.id)
    db_session.add(app_obj)
    await db_session.commit()
    await db_session.refresh(app_obj)

    # Create dataset
    response = await client.post(
        "/api/v1/eval/datasets",
        json={
            "application_id": str(app_obj.id),
            "name": "Golden Dataset",
            "dataset_type": "golden",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    dataset = response.json()
    dataset_id = dataset["id"]

    # Add items
    response = await client.post(
        f"/api/v1/eval/datasets/{dataset_id}/items",
        json={
            "items": [
                {
                    "input_vars": {"question": "What is 2+2?"},
                    "expected_output": "4",
                },
                {
                    "input_vars": {"question": "What is the capital of France?"},
                    "expected_output": "Paris",
                },
            ]
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert len(response.json()) == 2

    # List datasets
    response = await client.get("/api/v1/eval/datasets", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
