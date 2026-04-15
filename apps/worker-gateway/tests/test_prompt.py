"""Tests for the prompt assembler."""

import pytest
from gateway.prompt import PromptAssembler


@pytest.fixture
def assembler():
    return PromptAssembler()


@pytest.fixture
def base_args():
    return {
        "task_kind": "inbound_email_triage",
        "input_message": "Subject: Hello\n\nI want to learn more about your services.",
        "input_data": {"from": "client@example.com"},
        "blueprint": {"id": "inbox-worker", "version": "1.0.0"},
        "persona": "# Inbox Worker Persona\n\nYou are a reliable email assistant.",
        "playbook": "# Playbook\n\n## Task: inbound_email_triage\n\n### Step 1\nClassify the email.",
        "policies": {
            "approval": {
                "rules": {
                    "default": "require_approval",
                    "overrides": {
                        "spam": {"action": "auto_archive", "approval": "none"},
                    },
                }
            },
            "tools": {
                "allowed": [{"id": "email_read"}],
                "denied": [{"id": "email_send"}],
            },
        },
        "output_schema": {"type": "object", "properties": {"classification": {"type": "object"}}},
        "client_context": {"company-profile": "We are a digital agency."},
        "merged_config": {"model": "openai/gpt-4o-mini", "approvalRequired": True},
    }


class TestPromptAssembly:
    def test_system_prompt_includes_persona(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "Inbox Worker Persona" in result.system_prompt

    def test_system_prompt_includes_policies(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "require_approval" in result.system_prompt
        assert "email_read" in result.system_prompt

    def test_system_prompt_includes_output_schema(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "You MUST respond with valid JSON" in result.system_prompt

    def test_user_prompt_includes_playbook(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "Classify the email" in result.user_prompt

    def test_user_prompt_includes_context(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "digital agency" in result.user_prompt

    def test_user_prompt_includes_task_input(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "Hello" in result.user_prompt
        assert "inbound_email_triage" in result.user_prompt

    def test_metadata_tracks_sources(self, assembler, base_args):
        result = assembler.assemble(**base_args)
        assert "persona" in result.metadata["sources"]
        assert "policies" in result.metadata["sources"]
        assert "output_schema" in result.metadata["sources"]
        assert "playbook" in result.metadata["sources"]
        assert "task_input" in result.metadata["sources"]

    def test_empty_persona_excluded(self, assembler, base_args):
        base_args["persona"] = ""
        result = assembler.assemble(**base_args)
        assert "persona" not in result.metadata["sources"]

    def test_no_output_schema(self, assembler, base_args):
        base_args["output_schema"] = None
        result = assembler.assemble(**base_args)
        assert "output_schema" not in result.metadata["sources"]
        assert "JSON" not in result.system_prompt
