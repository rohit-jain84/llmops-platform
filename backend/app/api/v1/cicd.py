import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.enums import EvalRunStatus
from app.models.evaluation import EvalRun
from app.models.user import User

router = APIRouter()


class TriggerEvalRequest(BaseModel):
    prompt_version_id: str
    dataset_id: str


class TriggerEvalResponse(BaseModel):
    eval_run_id: str


class EvalStatusResponse(BaseModel):
    status: str
    aggregate_scores: dict | None = None
    quality_gate_passed: bool = False


@router.post("/trigger-eval", response_model=TriggerEvalResponse)
async def trigger_eval(
    data: TriggerEvalRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.schemas.evaluation import EvalRunCreate
    from app.services.evaluation_service import EvaluationService

    svc = EvaluationService(db)
    run = await svc.trigger_eval_run(
        EvalRunCreate(
            prompt_version_id=uuid.UUID(data.prompt_version_id),
            dataset_id=uuid.UUID(data.dataset_id),
            trigger="ci_cd",
        ),
        user.id,
    )
    return TriggerEvalResponse(eval_run_id=str(run.id))


@router.get("/eval-status/{run_id}", response_model=EvalStatusResponse)
async def eval_status(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(EvalRun).where(EvalRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")

    quality_gate_passed = False
    if run.status == EvalRunStatus.COMPLETED and run.aggregate_scores:
        # Quality gate: all LLM-judge scores must be >= 3.5
        scores = run.aggregate_scores
        llm_scores = {k: v for k, v in scores.items() if k not in ("latency", "format_compliance")}
        if llm_scores:
            quality_gate_passed = all(v >= 3.5 for v in llm_scores.values())

    return EvalStatusResponse(
        status=run.status,
        aggregate_scores=run.aggregate_scores,
        quality_gate_passed=quality_gate_passed,
    )
