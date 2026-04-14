import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.prompt import PromptTemplate, PromptVersion
from app.models.user import User
from app.schemas.prompt import (
    PromptDiffDetailedResponse,
    PromptDiffResponse,
    PromptRenderRequest,
    PromptRenderResponse,
    PromptTagRequest,
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateWithVersions,
    PromptVersionCreate,
    PromptVersionResponse,
)
from app.services.prompt_service import PromptService

router = APIRouter()


@router.get("/applications/{app_id}/prompts", response_model=list[PromptTemplateResponse])
async def list_prompts(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.application_id == app_id)
        .order_by(PromptTemplate.created_at.desc())
    )
    return result.scalars().all()


@router.post("/applications/{app_id}/prompts", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    app_id: uuid.UUID,
    data: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = PromptTemplate(application_id=app_id, name=data.name, description=data.description)
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


@router.get("/prompts/{template_id}", response_model=PromptTemplateWithVersions)
async def get_prompt(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PromptTemplate)
        .options(selectinload(PromptTemplate.versions))
        .where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return template


@router.get("/prompts/{template_id}/versions", response_model=list[PromptVersionResponse])
async def list_versions(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.template_id == template_id)
        .order_by(PromptVersion.version_number.desc())
    )
    return result.scalars().all()


@router.post("/prompts/{template_id}/versions", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    template_id: uuid.UUID,
    data: PromptVersionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = PromptService(db)
    return await svc.create_version(template_id, data, user.id)


@router.get("/prompts/{template_id}/versions/{num}", response_model=PromptVersionResponse)
async def get_version(
    template_id: uuid.UUID,
    num: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.template_id == template_id, PromptVersion.version_number == num)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/prompts/{template_id}/versions/{num}/tag", response_model=PromptVersionResponse)
async def tag_version(
    template_id: uuid.UUID,
    num: int,
    data: PromptTagRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = PromptService(db)
    return await svc.tag_version(template_id, num, data.tag)


@router.post("/prompts/{template_id}/versions/{num}/rollback", response_model=PromptVersionResponse)
async def rollback_version(
    template_id: uuid.UUID,
    num: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = PromptService(db)
    return await svc.rollback_to_version(template_id, num, user.id)


@router.get("/prompts/{template_id}/diff", response_model=PromptDiffResponse)
async def diff_versions(
    template_id: uuid.UUID,
    v1: int,
    v2: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = PromptService(db)
    return await svc.diff_versions(template_id, v1, v2)


@router.get("/prompts/{template_id}/diff/detailed", response_model=PromptDiffDetailedResponse)
async def diff_versions_detailed(
    template_id: uuid.UUID,
    v1: int,
    v2: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = PromptService(db)
    return await svc.diff_versions_detailed(template_id, v1, v2)


@router.post("/prompts/{template_id}/render", response_model=PromptRenderResponse)
async def render_prompt(
    template_id: uuid.UUID,
    data: PromptRenderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = PromptService(db)
    return await svc.render(template_id, data.variables, data.version_number)
