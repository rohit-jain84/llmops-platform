import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.experiment import Experiment
from app.models.user import User
from app.schemas.experiment import ExperimentCreate, ExperimentResponse, ExperimentResultResponse
from app.services.experiment_service import ExperimentService

router = APIRouter()


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    application_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Experiment).options(selectinload(Experiment.variants))
    if application_id:
        query = query.where(Experiment.application_id == application_id)
    result = await db.execute(query.order_by(Experiment.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.create_experiment(data, user.id)


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Experiment).options(selectinload(Experiment.variants)).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
async def start_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.start_experiment(experiment_id)


@router.post("/{experiment_id}/stop", response_model=ExperimentResponse)
async def stop_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.stop_experiment(experiment_id)


@router.get("/{experiment_id}/results", response_model=list[ExperimentResultResponse])
async def get_results(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.get_results(experiment_id)


@router.post("/{experiment_id}/significance", response_model=list[ExperimentResultResponse])
async def compute_significance(
    experiment_id: uuid.UUID,
    significance_level: float = 0.05,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.compute_significance(experiment_id, significance_level)


@router.post("/{experiment_id}/variants/{variant_id}/scores", response_model=ExperimentResultResponse)
async def record_eval_score(
    experiment_id: uuid.UUID,
    variant_id: uuid.UUID,
    score: float,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.record_eval_score(experiment_id, variant_id, score)


@router.post("/{experiment_id}/promote-winner", response_model=ExperimentResponse)
async def promote_winner(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ExperimentService(db)
    return await svc.promote_winner(experiment_id)
