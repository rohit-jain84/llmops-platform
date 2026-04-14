import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.enums import HumanEvalAssignmentStatus
from app.models.evaluation import (
    EvalDataset,
    EvalDatasetItem,
    EvalResult,
    EvalRun,
    HumanEvalAssignment,
    HumanEvalCampaign,
)
from app.models.user import User
from app.models.prompt import PromptVersion
from app.schemas.evaluation import (
    EvalDatasetCreate,
    EvalDatasetItemBulkCreate,
    EvalDatasetItemResponse,
    EvalDatasetResponse,
    EvalResultResponse,
    EvalRunCreate,
    EvalRunResponse,
    HumanEvalAssignmentResponse,
    HumanEvalCampaignCreate,
    HumanEvalCampaignResponse,
    HumanEvalRatingSubmit,
    RegressionCheckResponse,
)
from app.services.evaluation_service import EvaluationService

router = APIRouter()


# --- Datasets ---
@router.get("/datasets", response_model=list[EvalDatasetResponse])
async def list_datasets(
    application_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(EvalDataset)
    if application_id:
        query = query.where(EvalDataset.application_id == application_id)
    result = await db.execute(query.order_by(EvalDataset.created_at.desc()))
    datasets = result.scalars().all()
    response = []
    for ds in datasets:
        count_result = await db.execute(
            select(func.count()).where(EvalDatasetItem.dataset_id == ds.id)
        )
        item_count = count_result.scalar() or 0
        resp = EvalDatasetResponse.model_validate(ds)
        resp.item_count = item_count
        response.append(resp)
    return response


@router.post("/datasets", response_model=EvalDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    data: EvalDatasetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dataset = EvalDataset(
        application_id=data.application_id,
        name=data.name,
        dataset_type=data.dataset_type,
        description=data.description,
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)
    return EvalDatasetResponse.model_validate(dataset)


@router.post("/datasets/{dataset_id}/items", response_model=list[EvalDatasetItemResponse], status_code=status.HTTP_201_CREATED)
async def add_items(
    dataset_id: uuid.UUID,
    data: EvalDatasetItemBulkCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = []
    for item_data in data.items:
        item = EvalDatasetItem(
            dataset_id=dataset_id,
            input_vars=item_data.input_vars,
            expected_output=item_data.expected_output,
            metadata_json=item_data.metadata,
        )
        db.add(item)
        items.append(item)
    await db.flush()
    for item in items:
        await db.refresh(item)
    return items


# --- Eval Runs ---
@router.post("/runs", response_model=EvalRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_eval_run(
    data: EvalRunCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = EvaluationService(db)
    return await svc.trigger_eval_run(data, user.id)


@router.get("/runs/{run_id}", response_model=EvalRunResponse)
async def get_eval_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(EvalRun).where(EvalRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return run


@router.get("/runs/{run_id}/results", response_model=list[EvalResultResponse])
async def get_eval_results(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvalResult).where(EvalResult.eval_run_id == run_id).order_by(EvalResult.created_at)
    )
    return result.scalars().all()


# --- Human Eval ---
@router.post("/campaigns", response_model=HumanEvalCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: HumanEvalCampaignCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = EvaluationService(db)
    return await svc.create_human_eval_campaign(data, user.id)


@router.get("/campaigns/{campaign_id}", response_model=HumanEvalCampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(HumanEvalCampaign).where(HumanEvalCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    total = await db.execute(
        select(func.count()).where(HumanEvalAssignment.campaign_id == campaign_id)
    )
    completed = await db.execute(
        select(func.count()).where(
            HumanEvalAssignment.campaign_id == campaign_id,
            HumanEvalAssignment.status == HumanEvalAssignmentStatus.COMPLETED,
        )
    )
    resp = HumanEvalCampaignResponse.model_validate(campaign)
    resp.total_assignments = total.scalar() or 0
    resp.completed_assignments = completed.scalar() or 0
    return resp


@router.get("/campaigns/{campaign_id}/assignments", response_model=list[HumanEvalAssignmentResponse])
async def get_assignments(
    campaign_id: uuid.UUID,
    evaluator_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(HumanEvalAssignment).where(HumanEvalAssignment.campaign_id == campaign_id)
    if evaluator_id:
        query = query.where(HumanEvalAssignment.evaluator_id == evaluator_id)
    result = await db.execute(query.order_by(HumanEvalAssignment.created_at))
    return result.scalars().all()


# --- Regression Detection ---
@router.get("/regression/{template_id}", response_model=RegressionCheckResponse)
async def check_regression(
    template_id: uuid.UUID,
    v1: int | None = None,
    v2: int | None = None,
    threshold_pct: float = 5.0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compare eval scores between two prompt versions and detect regressions.

    If v1/v2 are not provided, compares the two most recent versions that have
    completed eval runs.
    """
    if v1 is not None and v2 is not None:
        # Fetch specific versions
        r1 = await db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == v1,
            )
        )
        r2 = await db.execute(
            select(PromptVersion).where(
                PromptVersion.template_id == template_id,
                PromptVersion.version_number == v2,
            )
        )
        ver1 = r1.scalar_one_or_none()
        ver2 = r2.scalar_one_or_none()
        if not ver1 or not ver2:
            raise HTTPException(status_code=404, detail="One or both versions not found")
    else:
        # Find two most recent versions with completed eval runs
        result = await db.execute(
            select(PromptVersion)
            .join(EvalRun, EvalRun.prompt_version_id == PromptVersion.id)
            .where(
                PromptVersion.template_id == template_id,
                EvalRun.status == "completed",
                EvalRun.aggregate_scores.isnot(None),
            )
            .order_by(PromptVersion.version_number.desc())
            .distinct()
            .limit(2)
        )
        versions = result.scalars().all()
        if len(versions) < 2:
            raise HTTPException(
                status_code=404,
                detail="Need at least 2 versions with completed eval runs for regression check",
            )
        ver2, ver1 = versions[0], versions[1]  # ver2 = newer, ver1 = older

    # Get the latest completed eval run for each version
    run1_result = await db.execute(
        select(EvalRun)
        .where(
            EvalRun.prompt_version_id == ver1.id,
            EvalRun.status == "completed",
            EvalRun.aggregate_scores.isnot(None),
        )
        .order_by(EvalRun.created_at.desc())
        .limit(1)
    )
    run2_result = await db.execute(
        select(EvalRun)
        .where(
            EvalRun.prompt_version_id == ver2.id,
            EvalRun.status == "completed",
            EvalRun.aggregate_scores.isnot(None),
        )
        .order_by(EvalRun.created_at.desc())
        .limit(1)
    )
    run1 = run1_result.scalar_one_or_none()
    run2 = run2_result.scalar_one_or_none()

    if not run1 or not run2:
        raise HTTPException(
            status_code=404,
            detail="Both versions need completed eval runs with scores",
        )

    prev_scores = run1.aggregate_scores
    curr_scores = run2.aggregate_scores

    regressions = []
    improvements = []

    all_metrics = set(prev_scores.keys()) | set(curr_scores.keys())
    for metric in sorted(all_metrics):
        prev_val = prev_scores.get(metric)
        curr_val = curr_scores.get(metric)
        if prev_val is None or curr_val is None:
            continue

        delta = curr_val - prev_val
        pct_change = (delta / prev_val * 100) if prev_val != 0 else 0.0

        entry = {
            "metric": metric,
            "current": round(curr_val, 3),
            "previous": round(prev_val, 3),
            "delta": round(delta, 3),
            "pct_change": round(pct_change, 2),
        }

        if pct_change < -threshold_pct:
            regressions.append(entry)
        elif pct_change > threshold_pct:
            improvements.append(entry)

    return RegressionCheckResponse(
        has_regression=len(regressions) > 0,
        current_version=ver2.version_number,
        previous_version=ver1.version_number,
        current_scores={k: round(v, 3) for k, v in curr_scores.items()},
        previous_scores={k: round(v, 3) for k, v in prev_scores.items()},
        regressions=regressions,
        improvements=improvements,
        threshold_pct=threshold_pct,
    )


@router.post("/assignments/{assignment_id}/rate", response_model=HumanEvalAssignmentResponse)
async def submit_rating(
    assignment_id: uuid.UUID,
    data: HumanEvalRatingSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = EvaluationService(db)
    return await svc.submit_rating(assignment_id, data, user.id)
