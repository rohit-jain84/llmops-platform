"""Initial schema

Revision ID: 001
Revises: None
Create Date: 2026-04-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="engineer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Applications
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Prompt Templates
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("application_id", "name", name="uq_prompt_template_app_name"),
    )

    # Prompt Versions
    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_templates.id"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("variables", postgresql.JSONB, nullable=True),
        sa.Column("model_config", postgresql.JSONB, nullable=True),
        sa.Column("tag", sa.String(50), nullable=True),
        sa.Column("commit_message", sa.Text, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("template_id", "version_number", name="uq_prompt_version_template_num"),
    )
    op.create_index("ix_prompt_versions_template_tag", "prompt_versions", ["template_id", "tag"])

    # Experiments
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_experiments_app_status", "experiments", ["application_id", "status"])

    # Experiment Variants
    op.create_table(
        "experiment_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column(
            "prompt_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=False
        ),
        sa.Column("traffic_pct", sa.Integer, nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
    )

    # Experiment Results
    op.create_table(
        "experiment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiment_variants.id"), nullable=False),
        sa.Column("request_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metrics", postgresql.JSONB, nullable=True),
        sa.Column("p_value", sa.Float, nullable=True),
        sa.Column("is_winner", sa.Boolean, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Eval Datasets
    op.create_table(
        "eval_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dataset_type", sa.String(50), nullable=False, server_default="golden"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Eval Dataset Items
    op.create_table(
        "eval_dataset_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_datasets.id"), nullable=False),
        sa.Column("input_vars", postgresql.JSONB, nullable=False),
        sa.Column("expected_output", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Eval Runs
    op.create_table(
        "eval_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "prompt_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=False
        ),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_datasets.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("trigger", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("aggregate_scores", postgresql.JSONB, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_eval_runs_prompt_version", "eval_runs", ["prompt_version_id"])

    # Eval Results
    op.create_table(
        "eval_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("eval_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_runs.id"), nullable=False),
        sa.Column(
            "dataset_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_dataset_items.id"), nullable=False
        ),
        sa.Column("llm_response", sa.Text, nullable=True),
        sa.Column("scores", postgresql.JSONB, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("token_usage", postgresql.JSONB, nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Human Eval Campaigns
    op.create_table(
        "human_eval_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("eval_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_runs.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dimensions", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Human Eval Assignments
    op.create_table(
        "human_eval_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("human_eval_campaigns.id"), nullable=False
        ),
        sa.Column("evaluator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("eval_result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_results.id"), nullable=False),
        sa.Column("ratings", postgresql.JSONB, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # LLM Request Log
    op.create_table(
        "llm_request_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column(
            "prompt_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=True
        ),
        sa.Column(
            "experiment_variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("experiment_variants.id"),
            nullable=True,
        ),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cache_hit", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("routed_model", sa.String(100), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    op.create_index("ix_llm_request_log_app_created", "llm_request_log", ["application_id", "created_at"])

    # Budget Alerts
    op.create_table(
        "budget_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("budget_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("period", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("alert_pct", postgresql.ARRAY(sa.Integer), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_triggered_pct", sa.Integer, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Routing Rules
    op.create_table(
        "routing_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("condition", postgresql.JSONB, nullable=False),
        sa.Column("target_model", sa.String(100), nullable=False),
        sa.Column("fallback_model", sa.String(100), nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Deployments
    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column(
            "prompt_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=False
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending_eval"),
        sa.Column("canary_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column("eval_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_runs.id"), nullable=True),
        sa.Column(
            "previous_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=True
        ),
        sa.Column("deployed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("deployments")
    op.drop_table("routing_rules")
    op.drop_table("budget_alerts")
    op.drop_index("ix_llm_request_log_app_created")
    op.drop_table("llm_request_log")
    op.drop_table("human_eval_assignments")
    op.drop_table("human_eval_campaigns")
    op.drop_table("eval_results")
    op.drop_index("ix_eval_runs_prompt_version")
    op.drop_table("eval_runs")
    op.drop_table("eval_dataset_items")
    op.drop_table("eval_datasets")
    op.drop_table("experiment_results")
    op.drop_table("experiment_variants")
    op.drop_index("ix_experiments_app_status")
    op.drop_table("experiments")
    op.drop_index("ix_prompt_versions_template_tag")
    op.drop_table("prompt_versions")
    op.drop_table("prompt_templates")
    op.drop_table("applications")
    op.drop_table("users")
