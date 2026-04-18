import pytest
from httpx import AsyncClient

from app.models.application import Application


@pytest.mark.asyncio
async def test_create_and_list_prompts(client: AsyncClient, db_session, test_user, auth_headers):
    # Create an application first
    app_obj = Application(name="Test App", description="Test", created_by=test_user.id)
    db_session.add(app_obj)
    await db_session.commit()
    await db_session.refresh(app_obj)

    # Create prompt template
    response = await client.post(
        f"/api/v1/applications/{app_obj.id}/prompts",
        json={"name": "Test Prompt", "description": "A test prompt"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    template = response.json()
    assert template["name"] == "Test Prompt"
    template_id = template["id"]

    # Create a version
    response = await client.post(
        f"/api/v1/prompts/{template_id}/versions",
        json={
            "content": "Hello {{name}}, welcome to {{place}}!",
            "commit_message": "Initial version",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    version = response.json()
    assert version["version_number"] == 1
    assert "name" in version["variables"]
    assert "place" in version["variables"]

    # List versions
    response = await client.get(
        f"/api/v1/prompts/{template_id}/versions",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Render
    response = await client.post(
        f"/api/v1/prompts/{template_id}/render",
        json={"variables": {"name": "Alice", "place": "Wonderland"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["rendered"] == "Hello Alice, welcome to Wonderland!"


@pytest.mark.asyncio
async def test_tag_and_diff(client: AsyncClient, db_session, test_user, auth_headers):
    app_obj = Application(name="Tag App", description="Test", created_by=test_user.id)
    db_session.add(app_obj)
    await db_session.commit()
    await db_session.refresh(app_obj)

    resp = await client.post(
        f"/api/v1/applications/{app_obj.id}/prompts",
        json={"name": "Tag Prompt"},
        headers=auth_headers,
    )
    template_id = resp.json()["id"]

    # Create two versions
    await client.post(
        f"/api/v1/prompts/{template_id}/versions",
        json={"content": "Version 1 content"},
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/prompts/{template_id}/versions",
        json={"content": "Version 2 content"},
        headers=auth_headers,
    )

    # Tag version 1
    resp = await client.post(
        f"/api/v1/prompts/{template_id}/versions/1/tag",
        json={"tag": "production"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["tag"] == "production"

    # Diff
    resp = await client.get(
        f"/api/v1/prompts/{template_id}/diff?v1=1&v2=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    diff = resp.json()
    assert diff["v1_content"] == "Version 1 content"
    assert diff["v2_content"] == "Version 2 content"
