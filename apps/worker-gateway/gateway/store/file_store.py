"""
File-based config store.

Loads company and worker instance configs from YAML files on disk.
This is the default store — no database required.
"""

from pathlib import Path
from typing import Any, Dict

import yaml

from ..config import settings
from ..logging import logger
from .base import ConfigStore


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class FileConfigStore(ConfigStore):
    """Config store backed by YAML files in clients/."""

    @property
    def name(self) -> str:
        return "file"

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        company_file = Path(settings.repo_root) / "clients" / company_id / "company.yaml"
        if not company_file.exists():
            raise KeyError(f"Company '{company_id}' not found at {company_file}")
        company = _load_yaml(company_file)
        logger.info("Resolved company: %s (%s)", company_id, company.get("name", "unnamed"))
        return company

    async def get_worker_instance(
        self, company_id: str, instance_id: str
    ) -> Dict[str, Any]:
        # Instance ID format: "companyId.workerName" → file: workerName.instance.yaml
        parts = instance_id.split(".", 1)
        if len(parts) != 2 or parts[0] != company_id:
            raise KeyError(
                f"Instance ID '{instance_id}' must be formatted as '{company_id}.<worker-name>'"
            )

        worker_name = parts[1]
        instance_file = (
            Path(settings.repo_root)
            / "clients"
            / company_id
            / "workers"
            / f"{worker_name}.instance.yaml"
        )

        if not instance_file.exists():
            raise KeyError(f"Worker instance '{instance_id}' not found at {instance_file}")

        instance = _load_yaml(instance_file)

        if not instance.get("enabled", True):
            raise ValueError(f"Worker instance '{instance_id}' is disabled.")

        logger.info("Resolved worker instance: %s", instance_id)
        return instance

    async def get_company_context(self, company_id: str) -> Dict[str, str]:
        context_dir = Path(settings.repo_root) / "clients" / company_id / "context"
        context: Dict[str, str] = {}

        if not context_dir.exists():
            return context

        for md_file in sorted(context_dir.glob("*.md")):
            context[md_file.stem] = md_file.read_text(encoding="utf-8")

        if context:
            logger.info("Loaded %d context files for company %s", len(context), company_id)

        return context
