"""
Blueprint + Client + Instance resolver.

Loads YAML config files from disk and merges them into a resolved
configuration for a worker run.

Resolution order (later wins):
  1. Blueprint defaults (from pack.yaml)
  2. Client instance overrides (from *.instance.yaml)
  3. Per-request run overrides (from the API request body)
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from .config import settings
from .logging import logger


class ResolutionError(Exception):
    """Raised when blueprint, client, or instance cannot be resolved."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_blueprint(blueprint_id: str, version: str) -> Dict[str, Any]:
    """Load a worker pack blueprint from worker-packs/<id>/pack.yaml."""
    pack_dir = Path(settings.repo_root) / "worker-packs" / blueprint_id
    pack_file = pack_dir / "pack.yaml"

    if not pack_file.exists():
        raise ResolutionError(
            code="BLUEPRINT_NOT_FOUND",
            message=f"Blueprint '{blueprint_id}' not found at {pack_file}",
        )

    blueprint = _load_yaml(pack_file)

    if blueprint.get("version") != version:
        raise ResolutionError(
            code="BLUEPRINT_VERSION_MISMATCH",
            message=(
                f"Requested version '{version}' but blueprint "
                f"'{blueprint_id}' is at version '{blueprint.get('version')}'"
            ),
        )

    logger.info(
        "Resolved blueprint: %s@%s (%s)",
        blueprint_id,
        version,
        blueprint.get("name", "unnamed"),
    )
    return blueprint


def resolve_client(client_id: str) -> Dict[str, Any]:
    """Load client company config from clients/<id>/company.yaml."""
    company_file = Path(settings.repo_root) / "clients" / client_id / "company.yaml"

    if not company_file.exists():
        raise ResolutionError(
            code="CLIENT_NOT_FOUND",
            message=f"Client '{client_id}' not found at {company_file}",
        )

    client = _load_yaml(company_file)
    logger.info("Resolved client: %s (%s)", client_id, client.get("name", "unnamed"))
    return client


def resolve_worker_instance(
    client_id: str, instance_id: str
) -> Dict[str, Any]:
    """Load worker instance config from clients/<client>/workers/<worker>.instance.yaml."""
    # Instance ID format: "clientId.workerName" → file: workerName.instance.yaml
    parts = instance_id.split(".", 1)
    if len(parts) != 2 or parts[0] != client_id:
        raise ResolutionError(
            code="INVALID_INSTANCE_ID",
            message=(
                f"Instance ID '{instance_id}' must be formatted as "
                f"'{client_id}.<worker-name>'"
            ),
        )

    worker_name = parts[1]
    instance_file = (
        Path(settings.repo_root)
        / "clients"
        / client_id
        / "workers"
        / f"{worker_name}.instance.yaml"
    )

    if not instance_file.exists():
        raise ResolutionError(
            code="INSTANCE_NOT_FOUND",
            message=f"Worker instance '{instance_id}' not found at {instance_file}",
        )

    instance = _load_yaml(instance_file)

    if not instance.get("enabled", True):
        raise ResolutionError(
            code="INSTANCE_DISABLED",
            message=f"Worker instance '{instance_id}' is disabled.",
        )

    logger.info("Resolved worker instance: %s", instance_id)
    return instance


def load_client_context(client_id: str) -> Dict[str, str]:
    """Load client context files (company-profile.md, brand-voice.md, etc.)."""
    context_dir = Path(settings.repo_root) / "clients" / client_id / "context"
    context: Dict[str, str] = {}

    if not context_dir.exists():
        return context

    for md_file in sorted(context_dir.glob("*.md")):
        context[md_file.stem] = md_file.read_text(encoding="utf-8")

    if context:
        logger.info("Loaded %d context files for client %s", len(context), client_id)

    return context


def merge_config(
    blueprint: Dict[str, Any],
    instance: Dict[str, Any],
    run_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Merge configuration from blueprint defaults → instance overrides → run overrides.

    Returns a flat resolved config dict.
    """
    # Start with blueprint defaults
    defaults = blueprint.get("defaults", {})
    merged = {
        "model": defaults.get("model", "openai/gpt-4o-mini"),
        "maxTokens": defaults.get("maxTokens", 4096),
        "temperature": defaults.get("temperature", 0.3),
        "approvalRequired": defaults.get("approvalRequired", True),
        "timeoutSeconds": defaults.get("timeoutSeconds", 120),
    }

    # Apply instance overrides
    overrides = instance.get("overrides", {})
    for key in merged:
        if key in overrides:
            merged[key] = overrides[key]

    # Apply per-request run overrides
    if run_overrides:
        for key in merged:
            if key in run_overrides and run_overrides[key] is not None:
                merged[key] = run_overrides[key]

    logger.info("Merged config: %s", merged)
    return merged


def resolve_all(
    client_id: str,
    worker_instance_id: str,
    blueprint_id: str,
    blueprint_version: str,
    run_overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, str]]:
    """
    Full resolution pipeline. Returns:
      (blueprint, client, instance, merged_config, client_context)
    """
    blueprint = resolve_blueprint(blueprint_id, blueprint_version)
    client = resolve_client(client_id)
    instance = resolve_worker_instance(client_id, worker_instance_id)
    client_context = load_client_context(client_id)
    merged_config = merge_config(blueprint, instance, run_overrides)

    return blueprint, client, instance, merged_config, client_context
