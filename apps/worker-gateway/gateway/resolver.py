"""
Blueprint + Company + Instance resolver.

Loads YAML config files from disk and merges them into a resolved
configuration for a worker run.

Merge precedence (later wins):
  1. Blueprint defaults    — from worker-packs/<id>/pack.yaml → defaults
  2. Instance overrides    — from clients/<company>/workers/<w>.instance.yaml → overrides
  3. Per-request overrides — from the API request body → runOverrides
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import yaml

from .config import settings
from .logging import logger

if TYPE_CHECKING:
    from .store.base import ConfigStore


class ResolutionError(Exception):
    """Raised when blueprint, company, or instance cannot be resolved."""

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


def resolve_company(company_id: str) -> Dict[str, Any]:
    """Load company config from clients/<id>/company.yaml."""
    company_file = Path(settings.repo_root) / "clients" / company_id / "company.yaml"

    if not company_file.exists():
        raise ResolutionError(
            code="COMPANY_NOT_FOUND",
            message=f"Company '{company_id}' not found at {company_file}",
        )

    company = _load_yaml(company_file)
    logger.info("Resolved company: %s (%s)", company_id, company.get("name", "unnamed"))
    return company


def resolve_worker_instance(
    company_id: str, instance_id: str
) -> Dict[str, Any]:
    """Load worker instance config from clients/<company>/workers/<worker>.instance.yaml."""
    # Instance ID format: "companyId.workerName" → file: workerName.instance.yaml
    parts = instance_id.split(".", 1)
    if len(parts) != 2 or parts[0] != company_id:
        raise ResolutionError(
            code="INVALID_INSTANCE_ID",
            message=(
                f"Instance ID '{instance_id}' must be formatted as "
                f"'{company_id}.<worker-name>'"
            ),
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


def load_company_context(company_id: str) -> Dict[str, str]:
    """Load company context files (company-profile.md, brand-voice.md, etc.)."""
    context_dir = Path(settings.repo_root) / "clients" / company_id / "context"
    context: Dict[str, str] = {}

    if not context_dir.exists():
        return context

    for md_file in sorted(context_dir.glob("*.md")):
        context[md_file.stem] = md_file.read_text(encoding="utf-8")

    if context:
        logger.info("Loaded %d context files for company %s", len(context), company_id)

    return context


# ---------------------------------------------------------------------------
# Blueprint asset loaders
# ---------------------------------------------------------------------------


def load_persona(blueprint_id: str) -> str:
    """Load the persona markdown for a blueprint."""
    persona_file = Path(settings.repo_root) / "worker-packs" / blueprint_id / "persona.md"
    if not persona_file.exists():
        logger.warning("No persona file for blueprint '%s'", blueprint_id)
        return ""
    content = persona_file.read_text(encoding="utf-8")
    logger.info("Loaded persona for blueprint '%s' (%d chars)", blueprint_id, len(content))
    return content


def load_playbook(blueprint_id: str) -> str:
    """Load the playbook markdown for a blueprint."""
    playbook_file = Path(settings.repo_root) / "worker-packs" / blueprint_id / "playbook.md"
    if not playbook_file.exists():
        logger.warning("No playbook file for blueprint '%s'", blueprint_id)
        return ""
    content = playbook_file.read_text(encoding="utf-8")
    logger.info("Loaded playbook for blueprint '%s' (%d chars)", blueprint_id, len(content))
    return content


def load_policies(blueprint_id: str) -> Dict[str, Dict[str, Any]]:
    """Load all policy YAML files for a blueprint."""
    policies_dir = Path(settings.repo_root) / "worker-packs" / blueprint_id / "policies"
    policies: Dict[str, Dict[str, Any]] = {}

    if not policies_dir.exists():
        logger.warning("No policies directory for blueprint '%s'", blueprint_id)
        return policies

    for yaml_file in sorted(policies_dir.glob("*.yaml")):
        # e.g. "approval-policy.yaml" → key "approval"
        key = yaml_file.stem.replace("-policy", "")
        policies[key] = _load_yaml(yaml_file)

    logger.info(
        "Loaded %d policies for blueprint '%s': %s",
        len(policies),
        blueprint_id,
        list(policies.keys()),
    )
    return policies


def load_output_schema(blueprint_id: str) -> Optional[Dict[str, Any]]:
    """Load the run-result JSON schema for a blueprint."""
    # Check both possible locations: outputs/ and root
    for subpath in ("outputs/run-result.schema.json", "run-result.schema.json"):
        schema_file = Path(settings.repo_root) / "worker-packs" / blueprint_id / subpath
        if schema_file.exists():
            content = schema_file.read_text(encoding="utf-8")
            schema = json.loads(content)
            logger.info("Loaded output schema for blueprint '%s'", blueprint_id)
            return schema

    logger.warning("No output schema for blueprint '%s'", blueprint_id)
    return None


def load_agent_configs(blueprint_id: str) -> Dict[str, Dict[str, Any]]:
    """Load all agent YAML configs for a blueprint."""
    agents_dir = Path(settings.repo_root) / "worker-packs" / blueprint_id / "agents"
    agents: Dict[str, Dict[str, Any]] = {}

    if not agents_dir.exists():
        return agents

    for yaml_file in sorted(agents_dir.glob("*.yaml")):
        agents[yaml_file.stem] = _load_yaml(yaml_file)

    logger.info(
        "Loaded %d agent configs for blueprint '%s': %s",
        len(agents),
        blueprint_id,
        list(agents.keys()),
    )
    return agents


def load_blueprint_assets(blueprint_id: str) -> Dict[str, Any]:
    """
    Load all assets for a blueprint at once.

    Returns a dict with keys: persona, playbook, policies, output_schema, agents
    """
    return {
        "persona": load_persona(blueprint_id),
        "playbook": load_playbook(blueprint_id),
        "policies": load_policies(blueprint_id),
        "output_schema": load_output_schema(blueprint_id),
        "agents": load_agent_configs(blueprint_id),
    }


# ---------------------------------------------------------------------------
# Config merging
# ---------------------------------------------------------------------------


def merge_config(
    blueprint: Dict[str, Any],
    instance: Dict[str, Any],
    run_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Merge configuration with explicit precedence (later wins):

      1. Blueprint defaults    — pack.yaml → defaults
      2. Instance overrides    — *.instance.yaml → overrides
      3. Per-request overrides — request body → runOverrides

    Returns a flat resolved config dict with these keys:
      model, maxTokens, temperature, approvalRequired, timeoutSeconds
    """
    # Layer 1: blueprint defaults
    defaults = blueprint.get("defaults", {})
    merged = {
        "model": defaults.get("model", "openai/gpt-4o-mini"),
        "maxTokens": defaults.get("maxTokens", 4096),
        "temperature": defaults.get("temperature", 0.3),
        "approvalRequired": defaults.get("approvalRequired", True),
        "timeoutSeconds": defaults.get("timeoutSeconds", 120),
    }

    # Layer 2: instance overrides
    overrides = instance.get("overrides", {})
    for key in merged:
        if key in overrides:
            merged[key] = overrides[key]

    # Layer 3: per-request run overrides
    if run_overrides:
        for key in merged:
            if key in run_overrides and run_overrides[key] is not None:
                merged[key] = run_overrides[key]

    logger.info("Merged config: %s", merged)
    return merged


async def resolve_all(
    company_id: str,
    worker_instance_id: str,
    blueprint_id: str,
    blueprint_version: str,
    run_overrides: Optional[Dict[str, Any]] = None,
    store: Optional["ConfigStore"] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, str]]:
    """
    Full resolution pipeline. Returns:
      (blueprint, company, instance, merged_config, company_context)

    Blueprint is always resolved from YAML on disk.
    Company/instance resolution is delegated to the ConfigStore if provided,
    otherwise falls back to the legacy file-based functions.
    """
    # Blueprint always from disk (versioned product definition)
    blueprint = resolve_blueprint(blueprint_id, blueprint_version)

    if store:
        # Delegate company/instance to the config store
        try:
            company = await store.get_company(company_id)
        except KeyError as exc:
            raise ResolutionError(code="COMPANY_NOT_FOUND", message=str(exc)) from exc

        try:
            instance = await store.get_worker_instance(company_id, worker_instance_id)
        except KeyError as exc:
            raise ResolutionError(code="INSTANCE_NOT_FOUND", message=str(exc)) from exc
        except ValueError as exc:
            raise ResolutionError(code="INSTANCE_DISABLED", message=str(exc)) from exc

        company_context = await store.get_company_context(company_id)
    else:
        # Legacy: direct file-based resolution
        company = resolve_company(company_id)
        instance = resolve_worker_instance(company_id, worker_instance_id)
        company_context = load_company_context(company_id)

    merged_config = merge_config(blueprint, instance, run_overrides)

    return blueprint, company, instance, merged_config, company_context
