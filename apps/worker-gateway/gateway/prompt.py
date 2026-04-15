"""
Prompt assembler for worker execution.

Constructs structured prompts from blueprint assets (persona, playbook, policies)
and client context, producing a system prompt + user prompt pair suitable for
any runtime adapter.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .logging import logger


@dataclass
class AssembledPrompt:
    """Result of prompt assembly — ready to send to a runtime adapter."""

    system_prompt: str
    user_prompt: str
    output_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptAssembler:
    """
    Assembles prompts from blueprint assets and client context.

    System prompt structure:
      1. Persona (from persona.md)
      2. Policy constraints (from policies/*.yaml)
      3. Output format instructions (from run-result.schema.json)

    User prompt structure:
      1. Playbook steps for the task kind (from playbook.md)
      2. Client context sections (from clients/<id>/context/*.md)
      3. Task input (message + structured data)
    """

    def assemble(
        self,
        *,
        task_kind: str,
        input_message: str,
        input_data: Optional[Dict[str, Any]],
        blueprint: Dict[str, Any],
        persona: str,
        playbook: str,
        policies: Dict[str, Dict[str, Any]],
        output_schema: Optional[Dict[str, Any]],
        client_context: Dict[str, str],
        merged_config: Dict[str, Any],
    ) -> AssembledPrompt:
        """Assemble a full prompt from all available sources."""
        system_parts: List[str] = []
        user_parts: List[str] = []
        metadata: Dict[str, Any] = {"sources": []}

        # --- System prompt ---

        # 1. Persona
        if persona:
            system_parts.append(persona.strip())
            metadata["sources"].append("persona")

        # 2. Policy constraints
        policy_text = self._format_policies(policies, merged_config)
        if policy_text:
            system_parts.append(policy_text)
            metadata["sources"].append("policies")

        # 3. Output format instructions
        if output_schema:
            schema_text = self._format_output_instructions(output_schema)
            system_parts.append(schema_text)
            metadata["sources"].append("output_schema")

        # --- User prompt ---

        # 1. Playbook steps for this task kind
        playbook_section = self._extract_task_playbook(playbook, task_kind)
        if playbook_section:
            user_parts.append(f"## Playbook\n\n{playbook_section}")
            metadata["sources"].append("playbook")

        # 2. Client context
        for ctx_name, ctx_content in sorted(client_context.items()):
            user_parts.append(
                f"## Company Context: {ctx_name}\n\n{ctx_content.strip()}"
            )
        if client_context:
            metadata["sources"].append("client_context")
            metadata["context_files"] = list(client_context.keys())

        # 3. Task input
        task_section = self._format_task_input(task_kind, input_message, input_data)
        user_parts.append(task_section)
        metadata["sources"].append("task_input")

        # Track config
        metadata["task_kind"] = task_kind
        metadata["model"] = merged_config.get("model", "unknown")
        metadata["blueprint_id"] = blueprint.get("id", "unknown")

        system_prompt = "\n\n---\n\n".join(system_parts)
        user_prompt = "\n\n---\n\n".join(user_parts)

        logger.info(
            "Assembled prompt: %d system chars, %d user chars, sources=%s",
            len(system_prompt),
            len(user_prompt),
            metadata["sources"],
        )

        return AssembledPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=output_schema,
            metadata=metadata,
        )

    def _format_policies(
        self,
        policies: Dict[str, Dict[str, Any]],
        merged_config: Dict[str, Any],
    ) -> str:
        """Format policy constraints into a system prompt section."""
        parts: List[str] = []

        parts.append("## Operational Constraints\n")

        # Approval policy
        if "approval" in policies:
            ap = policies["approval"]
            default_rule = ap.get("rules", {}).get("default", "require_approval")
            parts.append(f"- Default approval policy: **{default_rule}**")
            overrides = ap.get("rules", {}).get("overrides", {})
            if overrides:
                for category, rule in overrides.items():
                    action = rule.get("action", "unknown")
                    approval = rule.get("approval", "require_approval")
                    parts.append(
                        f"  - {category}: action={action}, approval={approval}"
                    )

        # Tool policy
        if "tools" in policies:
            tp = policies["tools"]
            allowed = tp.get("allowed", [])
            denied = tp.get("denied", [])
            if allowed:
                tool_names = [t.get("id", "?") for t in allowed]
                parts.append(f"- Allowed tools: {', '.join(tool_names)}")
            if denied:
                tool_names = [t.get("id", "?") for t in denied]
                parts.append(f"- Denied tools (never use): {', '.join(tool_names)}")

        # Config constraints
        if merged_config.get("approvalRequired"):
            parts.append(
                "- All outputs that take external action MUST be held for human approval."
            )

        return "\n".join(parts)

    def _format_output_instructions(
        self, output_schema: Dict[str, Any]
    ) -> str:
        """Format output schema as instructions in the system prompt."""
        schema_json = json.dumps(output_schema, indent=2)
        return (
            "## Output Format\n\n"
            "You MUST respond with valid JSON matching this schema. "
            "Do not include any text before or after the JSON.\n\n"
            f"```json\n{schema_json}\n```"
        )

    def _extract_task_playbook(self, playbook: str, task_kind: str) -> str:
        """Extract the relevant task section from the playbook markdown."""
        if not playbook:
            return ""

        # Look for a heading matching the task kind
        # e.g. "## Task: inbound_email_triage"
        pattern = rf"##\s+Task:\s*{re.escape(task_kind)}\b"
        match = re.search(pattern, playbook, re.IGNORECASE)
        if not match:
            logger.warning(
                "No playbook section found for task_kind '%s'", task_kind
            )
            return playbook.strip()

        # Extract from this heading to the next ## heading or end of file
        start = match.start()
        next_heading = re.search(r"\n##\s+Task:", playbook[match.end() :])
        if next_heading:
            end = match.end() + next_heading.start()
        else:
            end = len(playbook)

        return playbook[start:end].strip()

    def _format_task_input(
        self,
        task_kind: str,
        input_message: str,
        input_data: Optional[Dict[str, Any]],
    ) -> str:
        """Format the task input as a user prompt section."""
        parts = [f"## Task Input\n\n**Task kind:** {task_kind}\n"]

        parts.append(f"**Message:**\n{input_message}")

        if input_data:
            data_json = json.dumps(input_data, indent=2, default=str)
            parts.append(f"\n**Structured data:**\n```json\n{data_json}\n```")

        return "\n".join(parts)
