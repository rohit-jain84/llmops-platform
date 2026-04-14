import uuid
from datetime import datetime

from pydantic import BaseModel


class DeploymentCreate(BaseModel):
    prompt_version_id: uuid.UUID
    canary_pct: int = 10


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    prompt_version_id: uuid.UUID
    status: str
    canary_pct: int
    eval_run_id: uuid.UUID | None
    previous_version_id: uuid.UUID | None
    deployed_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
