import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Application(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    creator = relationship("User", back_populates="applications")
    prompt_templates = relationship("PromptTemplate", back_populates="application", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="application", cascade="all, delete-orphan")
    eval_datasets = relationship("EvalDataset", back_populates="application", cascade="all, delete-orphan")
