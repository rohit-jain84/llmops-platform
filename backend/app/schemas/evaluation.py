import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


# Datasets
class EvalDatasetCreate(BaseModel):
    application_id: uuid.UUID
    name: str
    dataset_type: str = "golden"
    description: str | None = None


class EvalDatasetResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    dataset_type: str
    description: str | None
    created_at: datetime
    item_count: int = 0

    model_config = {"from_attributes": True}


class EvalDatasetItemCreate(BaseModel):
    input_vars: dict
    expected_output: str | None = None
    metadata: dict | None = None


class EvalDatasetItemBulkCreate(BaseModel):
    items: list[EvalDatasetItemCreate]


class EvalDatasetItemResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    input_vars: dict
    expected_output: str | None
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Eval Runs
class EvalRunCreate(BaseModel):
    prompt_version_id: uuid.UUID
    dataset_id: uuid.UUID
    trigger: str = "manual"


class EvalRunResponse(BaseModel):
    id: uuid.UUID
    prompt_version_id: uuid.UUID
    dataset_id: uuid.UUID
    status: str
    trigger: str
    aggregate_scores: dict | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class EvalResultResponse(BaseModel):
    id: uuid.UUID
    eval_run_id: uuid.UUID
    dataset_item_id: uuid.UUID
    llm_response: str | None
    scores: dict | None
    latency_ms: int | None
    token_usage: dict | None
    cost_usd: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


# Human Eval
class HumanEvalCampaignCreate(BaseModel):
    eval_run_id: uuid.UUID
    name: str
    dimensions: list[dict]
    evaluator_ids: list[uuid.UUID]


class HumanEvalCampaignResponse(BaseModel):
    id: uuid.UUID
    eval_run_id: uuid.UUID
    name: str
    dimensions: dict
    status: str
    created_at: datetime
    total_assignments: int = 0
    completed_assignments: int = 0

    model_config = {"from_attributes": True}


class HumanEvalAssignmentResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    evaluator_id: uuid.UUID
    eval_result_id: uuid.UUID
    ratings: dict | None
    notes: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HumanEvalRatingSubmit(BaseModel):
    ratings: dict
    notes: str | None = None


# Regression Detection
class RegressionCheckResponse(BaseModel):
    has_regression: bool
    current_version: int
    previous_version: int
    current_scores: dict[str, float]
    previous_scores: dict[str, float]
    regressions: list[dict]  # [{metric, current, previous, delta, pct_change}]
    improvements: list[dict]
    threshold_pct: float
