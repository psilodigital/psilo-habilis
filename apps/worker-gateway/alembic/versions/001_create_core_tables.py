"""Create core tables: companies, worker_instances, run_history

Revision ID: 001
Revises: None
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- companies ---
    op.create_table(
        "companies",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text()),
        sa.Column("industry", sa.Text()),
        sa.Column("tier", sa.Text(), server_default="starter"),
        sa.Column("contact_email", sa.Text()),
        sa.Column("contact_owner", sa.Text()),
        sa.Column("paperclip_company_id", sa.Text()),
        sa.Column("agentzero_project_id", sa.Text()),
        sa.Column("litellm_team", sa.Text()),
        sa.Column("settings", JSONB, server_default="{}"),
        sa.Column("context_files", JSONB, server_default="{}"),
        sa.Column("active_workers", JSONB, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- worker_instances ---
    op.create_table(
        "worker_instances",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Text(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("blueprint_id", sa.Text(), nullable=False),
        sa.Column("blueprint_version", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("overrides", JSONB, server_default="{}"),
        sa.Column("context_refs", JSONB, server_default="[]"),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_worker_instances_company_id", "worker_instances", ["company_id"])

    # --- run_history ---
    op.create_table(
        "run_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", sa.Text(), unique=True, nullable=False),
        sa.Column(
            "company_id",
            sa.Text(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
        ),
        sa.Column("worker_instance_id", sa.Text()),
        sa.Column("blueprint_id", sa.Text(), nullable=False),
        sa.Column("blueprint_version", sa.Text(), nullable=False),
        sa.Column("task_kind", sa.Text(), nullable=False),
        sa.Column("input_message", sa.Text()),
        sa.Column("input_data", JSONB),
        sa.Column("run_overrides", JSONB),
        sa.Column("resolved_config", JSONB),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("classification", JSONB),
        sa.Column("artifacts", JSONB, server_default="[]"),
        sa.Column("runtime_adapter", sa.Text()),
        sa.Column("model_used", sa.Text()),
        sa.Column("tokens_used", sa.Integer(), server_default="0"),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_run_history_company_id", "run_history", ["company_id"])
    op.create_index("ix_run_history_worker_instance_id", "run_history", ["worker_instance_id"])
    op.create_index("ix_run_history_status", "run_history", ["status"])
    op.create_index("ix_run_history_started_at", "run_history", ["started_at"])


def downgrade() -> None:
    op.drop_table("run_history")
    op.drop_table("worker_instances")
    op.drop_table("companies")
