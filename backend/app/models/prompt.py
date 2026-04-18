import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PromptTemplate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (UniqueConstraint("application_id", "name", name="uq_prompt_template_app_name"),)

    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    application = relationship("Application", back_populates="prompt_templates")
    versions = relationship(
        "PromptVersion",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="PromptVersion.version_number.desc()",
    )


class PromptVersion(UUIDMixin, Base):
    __tablename__ = "prompt_versions"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_templates.id"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    model_config_json: Mapped[dict | None] = mapped_column("model_config", JSONB, nullable=True, default=dict)
    tag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    template = relationship("PromptTemplate", back_populates="versions")

    __table_args__ = (UniqueConstraint("template_id", "version_number", name="uq_prompt_version_template_num"),)
