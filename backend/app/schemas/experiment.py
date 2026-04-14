import uuid
from datetime import datetime

from pydantic import BaseModel


class ExperimentVariantCreate(BaseModel):
    prompt_version_id: uuid.UUID
    traffic_pct: int
    label: str


class ExperimentCreate(BaseModel):
    application_id: uuid.UUID
    name: str
    variants: list[ExperimentVariantCreate]


class ExperimentVariantResponse(BaseModel):
    id: uuid.UUID
    prompt_version_id: uuid.UUID
    traffic_pct: int
    label: str

    model_config = {"from_attributes": True}


class ExperimentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    variants: list[ExperimentVariantResponse] = []

    model_config = {"from_attributes": True}


class ExperimentResultResponse(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    request_count: int
    metrics: dict | None
    p_value: float | None
    is_winner: bool | None
    updated_at: datetime

    model_config = {"from_attributes": True}
