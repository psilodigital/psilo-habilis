"""Tests for the blueprint + company + instance resolver."""

import pytest
from gateway.resolver import (
    ResolutionError,
    load_blueprint_assets,
    load_company_context,
    load_persona,
    load_playbook,
    load_policies,
    load_output_schema,
    merge_config,
    resolve_all,
    resolve_blueprint,
    resolve_company,
    resolve_worker_instance,
)


class TestResolveBlueprint:
    def test_resolve_inbox_worker(self):
        bp = resolve_blueprint("inbox-worker", "1.0.0")
        assert bp["id"] == "inbox-worker"
        assert bp["version"] == "1.0.0"
        assert "inbound_email_triage" in bp["taskKinds"]

    def test_blueprint_not_found(self):
        with pytest.raises(ResolutionError) as exc_info:
            resolve_blueprint("nonexistent", "1.0.0")
        assert exc_info.value.code == "BLUEPRINT_NOT_FOUND"

    def test_version_mismatch(self):
        with pytest.raises(ResolutionError) as exc_info:
            resolve_blueprint("inbox-worker", "9.9.9")
        assert exc_info.value.code == "BLUEPRINT_VERSION_MISMATCH"


class TestResolveCompany:
    def test_resolve_psilodigital(self):
        company = resolve_company("psilodigital")
        assert company["id"] == "psilodigital"
        assert company["name"] == "Psilodigital"

    def test_company_not_found(self):
        with pytest.raises(ResolutionError) as exc_info:
            resolve_company("nonexistent")
        assert exc_info.value.code == "COMPANY_NOT_FOUND"


class TestResolveWorkerInstance:
    def test_resolve_inbox_worker_instance(self):
        instance = resolve_worker_instance("psilodigital", "psilodigital.inbox-worker")
        assert instance["instanceId"] == "psilodigital.inbox-worker"
        assert instance["blueprintId"] == "inbox-worker"

    def test_invalid_instance_id_format(self):
        with pytest.raises(ResolutionError) as exc_info:
            resolve_worker_instance("psilodigital", "bad-format")
        assert exc_info.value.code == "INVALID_INSTANCE_ID"

    def test_instance_not_found(self):
        with pytest.raises(ResolutionError) as exc_info:
            resolve_worker_instance("psilodigital", "psilodigital.nonexistent")
        assert exc_info.value.code == "INSTANCE_NOT_FOUND"


class TestMergeConfig:
    def test_blueprint_defaults(self):
        bp = {"defaults": {"model": "test-model", "maxTokens": 2048, "temperature": 0.5, "approvalRequired": False, "timeoutSeconds": 60}}
        instance = {}
        merged = merge_config(bp, instance)
        assert merged["model"] == "test-model"
        assert merged["maxTokens"] == 2048

    def test_instance_overrides(self):
        bp = {"defaults": {"model": "default", "maxTokens": 4096, "temperature": 0.3, "approvalRequired": True, "timeoutSeconds": 120}}
        instance = {"overrides": {"model": "override-model", "temperature": 0.7}}
        merged = merge_config(bp, instance)
        assert merged["model"] == "override-model"
        assert merged["temperature"] == 0.7
        assert merged["maxTokens"] == 4096  # unchanged

    def test_run_overrides(self):
        bp = {"defaults": {"model": "default", "maxTokens": 4096, "temperature": 0.3, "approvalRequired": True, "timeoutSeconds": 120}}
        instance = {"overrides": {"model": "instance-model"}}
        run = {"model": "run-model"}
        merged = merge_config(bp, instance, run)
        assert merged["model"] == "run-model"


class TestAssetLoaders:
    def test_load_persona(self):
        persona = load_persona("inbox-worker")
        assert "Inbox Worker" in persona
        assert len(persona) > 100

    def test_load_playbook(self):
        playbook = load_playbook("inbox-worker")
        assert "inbound_email_triage" in playbook

    def test_load_policies(self):
        policies = load_policies("inbox-worker")
        assert "approval" in policies
        assert "model" in policies
        assert "memory" in policies
        assert "tool" in policies

    def test_load_output_schema(self):
        schema = load_output_schema("inbox-worker")
        # May or may not exist depending on file location
        # Just verify it doesn't crash
        assert schema is None or isinstance(schema, dict)

    def test_load_blueprint_assets(self):
        assets = load_blueprint_assets("inbox-worker")
        assert "persona" in assets
        assert "playbook" in assets
        assert "policies" in assets
        assert len(assets["persona"]) > 0

    def test_load_company_context(self):
        ctx = load_company_context("psilodigital")
        assert "company-profile" in ctx or "brand-voice" in ctx


class TestResolveAll:
    @pytest.mark.asyncio
    async def test_full_resolution(self):
        bp, company, instance, config, ctx = await resolve_all(
            company_id="psilodigital",
            worker_instance_id="psilodigital.inbox-worker",
            blueprint_id="inbox-worker",
            blueprint_version="1.0.0",
        )
        assert bp["id"] == "inbox-worker"
        assert company["id"] == "psilodigital"
        assert instance["instanceId"] == "psilodigital.inbox-worker"
        assert "model" in config
        assert isinstance(ctx, dict)
