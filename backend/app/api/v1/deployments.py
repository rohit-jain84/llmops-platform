import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.deployment import Deployment
from app.models.user import User
from app.schemas.deployment import DeploymentCreate, DeploymentResponse
from app.services.deployment_service import DeploymentService

router = APIRouter()


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    data: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = DeploymentService(db)
    return await svc.create_deployment(data, user.id)


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.get("", response_model=list[DeploymentResponse])
async def list_deployments(
    application_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Deployment)
    if application_id:
        query = query.where(Deployment.application_id == application_id)
    result = await db.execute(query.order_by(Deployment.created_at.desc()))
    return result.scalars().all()


@router.post("/{deployment_id}/promote", response_model=DeploymentResponse)
async def promote_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = DeploymentService(db)
    return await svc.promote(deployment_id)


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = DeploymentService(db)
    return await svc.rollback(deployment_id)
