"""
Stub runtime adapter.

Returns deterministic simulated results for local development and testing.
This adapter does NOT call any external service.

TODO: Replace with real Agent Zero adapter once A0 project-scoped execution
      and structured output are confirmed working.
"""

from typing import Any, Dict

from ..logging import logger
from ..models import Artifact, Classification
from .base import RuntimeAdapter, RuntimeResult


class StubRuntimeAdapter(RuntimeAdapter):
    """Deterministic stub that simulates worker execution."""

    @property
    def name(self) -> str:
        return "stub"

    async def execute(
        self,
        *,
        task_kind: str,
        input_message: str,
        input_data: Dict[str, Any] | None,
        merged_config: Dict[str, Any],
        blueprint: Dict[str, Any],
        client_context: Dict[str, str],
    ) -> RuntimeResult:
        logger.info(
            "STUB ADAPTER: Simulating execution for task_kind=%s", task_kind
        )

        if task_kind == "inbound_email_triage":
            return self._simulate_email_triage(input_message, merged_config)

        # Generic fallback for unknown task kinds
        return RuntimeResult(
            artifacts=[
                Artifact(
                    type="generic_result",
                    content=f"Stub execution completed for task kind '{task_kind}'. "
                    f"Input: {input_message[:100]}",
                    approvalStatus="not_required",
                )
            ],
            tokens_used=0,
            model_used=merged_config.get("model", "stub/none"),
        )

    def _simulate_email_triage(
        self, input_message: str, config: Dict[str, Any]
    ) -> RuntimeResult:
        """Simulate the inbox worker email triage flow."""
        # Deterministic classification based on input
        message_lower = input_message.lower()

        if any(w in message_lower for w in ["buy", "price", "quote", "pricing"]):
            intent = "sales_lead"
            urgency = "medium"
        elif any(w in message_lower for w in ["help", "broken", "error", "bug", "issue"]):
            intent = "support"
            urgency = "high"
        elif any(w in message_lower for w in ["spam", "unsubscribe", "winner", "lottery"]):
            intent = "spam"
            urgency = "low"
        else:
            intent = "inquiry"
            urgency = "low"

        classification = Classification(
            intent=intent,
            urgency=urgency,
            sentiment="neutral",
            language="en",
        )

        artifacts = []

        # Spam gets no reply
        if intent != "spam":
            approval_required = config.get("approvalRequired", True)
            approval_status = "pending" if approval_required else "approved"

            artifacts.append(
                Artifact(
                    type="draft_reply",
                    content=(
                        f"Thank you for reaching out. We have received your message "
                        f"and classified it as a '{intent}' with '{urgency}' urgency. "
                        f"A team member will follow up shortly.\n\n"
                        f"Best regards,\nThe Psilodigital Team"
                    ),
                    approvalStatus=approval_status,
                    metadata={"replySubject": "Re: Your inquiry", "tone": "friendly"},
                )
            )

        artifacts.append(
            Artifact(
                type="classification_report",
                content=(
                    f"Classification: intent={intent}, urgency={urgency}, "
                    f"sentiment=neutral, language=en"
                ),
                approvalStatus="not_required",
            )
        )

        status_override = None
        if intent != "spam" and config.get("approvalRequired", True):
            status_override = "awaiting_approval"

        result = RuntimeResult(
            classification=classification,
            artifacts=artifacts,
            tokens_used=0,
            model_used="stub/deterministic",
        )
        # Attach status hint for the route handler
        result._status_override = status_override  # type: ignore[attr-defined]
        return result
