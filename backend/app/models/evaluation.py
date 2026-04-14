import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import EvalRunStatus, HumanEvalAssignmentStatus, HumanEvalCampaignStatus


class EvalDataset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "eval_datasets"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False, default="golden")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="eval_datasets")
    items = relationship("EvalDatasetItem", back_populates="dataset", cascade="all, delete-orphan")


class EvalDatasetItem(UUIDMixin, Base):
    __tablename__ = "eval_dataset_items"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_datasets.id"), nullable=False
    )
    input_vars: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    dataset = relationship("EvalDataset", back_populates="items")


class EvalRun(UUIDMixin, Base):
    __tablename__ = "eval_runs"

    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_datasets.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=EvalRunStatus.PENDING)
    trigger: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    aggregate_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prompt_version = relationship("PromptVersion")
    dataset = relationship("EvalDataset")
    results = relationship("EvalResult", back_populates="eval_run", cascade="all, delete-orphan")


class EvalResult(UUIDMixin, Base):
    __tablename__ = "eval_results"

    eval_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=False
    )
    dataset_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_dataset_items.id"), nullable=False
    )
    llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    eval_run = relationship("EvalRun", back_populates="results")
    dataset_item = relationship("EvalDatasetItem")


class HumanEvalCampaign(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "human_eval_campaigns"

    eval_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dimensions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=HumanEvalCampaignStatus.ACTIVE)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    eval_run = relationship("EvalRun")
    assignments = relationship("HumanEvalAssignment", back_populates="campaign", cascade="all, delete-orphan")


class HumanEvalAssignment(UUIDMixin, Base):
    __tablename__ = "human_eval_assignments"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("human_eval_campaigns.id"), nullable=False
    )
    evaluator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    eval_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eval_results.id"), nullable=False
    )
    ratings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=HumanEvalAssignmentStatus.PENDING)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    campaign = relationship("HumanEvalCampaign", back_populates="assignments")
    evaluator = relationship("User")
    eval_result = relationship("EvalResult")
