import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.application import Application
from app.models.user import User

router = APIRouter()


class ApplicationCreate(BaseModel):
    name: str
    description: str | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Application).order_by(Application.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Application).where(Application.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application name already exists")

    app = Application(name=data.name, description=data.description, created_by=user.id)
    db.add(app)
    await db.flush()
    await db.refresh(app)
    return app


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app
