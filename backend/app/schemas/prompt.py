import uuid
from datetime import datetime

from pydantic import BaseModel


class PromptTemplateCreate(BaseModel):
    name: str
    description: str | None = None


class PromptTemplateResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptTemplateWithVersions(PromptTemplateResponse):
    versions: list["PromptVersionResponse"] = []


class PromptVersionCreate(BaseModel):
    content: str
    variables: dict | None = None
    model_config_data: dict | None = None
    tag: str | None = None
    commit_message: str | None = None


class PromptVersionResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    version_number: int
    content: str
    variables: dict | None
    model_config_json: dict | None
    tag: str | None
    commit_message: str | None
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptTagRequest(BaseModel):
    tag: str


class PromptRenderRequest(BaseModel):
    version_number: int | None = None
    variables: dict


class PromptRenderResponse(BaseModel):
    rendered: str
    version_number: int


class PromptDiffResponse(BaseModel):
    v1: int
    v2: int
    v1_content: str
    v2_content: str


class PromptDiffDetailedResponse(PromptDiffResponse):
    """Extended diff response with version metadata and change stats."""
    v1_tag: str | None = None
    v2_tag: str | None = None
    v1_commit_message: str | None = None
    v2_commit_message: str | None = None
    v1_created_at: datetime | None = None
    v2_created_at: datetime | None = None
    v1_variables: list[str] = []
    v2_variables: list[str] = []
    variables_added: list[str] = []
    variables_removed: list[str] = []
    lines_added: int = 0
    lines_removed: int = 0
    lines_changed: int = 0
