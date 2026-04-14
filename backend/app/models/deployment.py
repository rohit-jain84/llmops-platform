import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin
from app.models.enums import DeploymentStatus


class Deployment(UUIDMixin, Base):
    __tablename__ = "deployments"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False
    )
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DeploymentStatus.PENDING_EVAL
    )
    canary_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=True
    )
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=True
    )
    deployed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    prompt_version = relationship("PromptVersion", foreign_keys=[prompt_version_id])
    previous_version = relationship("PromptVersion", foreign_keys=[previous_version_id])
    eval_run = relationship("EvalRun")
    deployer = relationship("User")
