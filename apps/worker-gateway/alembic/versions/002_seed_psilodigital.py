"""Seed psilodigital company and inbox-worker instance

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO companies (id, name, display_name, industry, tier,
                contact_email, contact_owner,
                paperclip_company_id, agentzero_project_id,
                settings, context_files, active_workers)
            VALUES (
                'psilodigital',
                'Psilodigital',
                'Psilodigital Digital Agency',
                'technology',
                'internal',
                'team@psilodigital.com',
                'André Esteves',
                'psilodigital',
                'psilodigital',
                :settings,
                :context_files,
                :active_workers
            )
            ON CONFLICT (id) DO NOTHING
            """
        ).bindparams(
            settings=json.dumps({
                "timezone": "America/Sao_Paulo",
                "locale": "pt-BR",
                "defaultModel": "openai/gpt-4o-mini",
            }),
            context_files=json.dumps({}),
            active_workers=json.dumps([
                {"instanceRef": "workers/inbox-worker.instance.yaml"}
            ]),
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO worker_instances (id, company_id, blueprint_id, blueprint_version,
                enabled, overrides, context_refs, notes)
            VALUES (
                'psilodigital.inbox-worker',
                'psilodigital',
                'inbox-worker',
                '1.0.0',
                true,
                :overrides,
                :context_refs,
                'First worker instance for internal dogfooding. All replies require human approval in v1.'
            )
            ON CONFLICT (id) DO NOTHING
            """
        ).bindparams(
            overrides=json.dumps({
                "model": "openai/gpt-4o-mini",
                "temperature": 0.3,
                "approvalRequired": True,
                "maxConcurrentRuns": 2,
                "timeoutSeconds": 90,
            }),
            context_refs=json.dumps([
                "../context/company-profile.md",
                "../context/brand-voice.md",
            ]),
        )
    )


def downgrade() -> None:
    op.execute("DELETE FROM worker_instances WHERE id = 'psilodigital.inbox-worker'")
    op.execute("DELETE FROM companies WHERE id = 'psilodigital'")
