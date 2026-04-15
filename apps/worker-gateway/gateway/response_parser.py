"""
Response parser for runtime adapter output.

Extracts structured data (Classification + Artifacts) from free-text
runtime responses, with fallback handling for non-JSON output.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .logging import logger
from .models import Artifact, Classification


class ParseResult:
    """Result of parsing a runtime response."""

    def __init__(
        self,
        *,
        classification: Optional[Classification] = None,
        artifacts: Optional[List[Artifact]] = None,
        raw_response: str = "",
        parse_method: str = "none",
    ):
        self.classification = classification
        self.artifacts = artifacts or []
        self.raw_response = raw_response
        self.parse_method = parse_method


class ResponseParser:
    """
    Parses free-text runtime responses into structured Classification + Artifacts.

    Extraction strategy (in order):
      1. JSON code block (```json ... ```)
      2. Raw JSON object (starts with {)
      3. Fallback: treat entire response as a single raw artifact
    """

    def parse(
        self,
        response_text: str,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> ParseResult:
        """Parse a runtime response into structured data."""
        if not response_text or not response_text.strip():
            return ParseResult(
                raw_response=response_text,
                parse_method="empty",
            )

        # Try JSON code block extraction
        json_data = self._extract_json_code_block(response_text)
        if json_data is not None:
            return self._build_result(json_data, response_text, "code_block")

        # Try raw JSON extraction
        json_data = self._extract_raw_json(response_text)
        if json_data is not None:
            return self._build_result(json_data, response_text, "raw_json")

        # Fallback: raw text as artifact
        logger.info("No JSON found in response, using fallback")
        return ParseResult(
            artifacts=[
                Artifact(
                    type="raw_response",
                    content=response_text.strip(),
                    approvalStatus="pending",
                )
            ],
            raw_response=response_text,
            parse_method="fallback",
        )

    def _extract_json_code_block(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from a ```json ... ``` code block."""
        pattern = r"```json\s*\n(.*?)\n\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            logger.warning("JSON code block found but invalid: %s", e)
            return None

    def _extract_raw_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a JSON object from text that starts with {."""
        stripped = text.strip()
        if not stripped.startswith("{"):
            return None

        # Find matching closing brace
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            # Try to find the first complete JSON object
            depth = 0
            for i, char in enumerate(stripped):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(stripped[: i + 1])
                        except json.JSONDecodeError:
                            return None
            return None

    def _build_result(
        self,
        data: Dict[str, Any],
        raw_response: str,
        parse_method: str,
    ) -> ParseResult:
        """Build a ParseResult from extracted JSON data."""
        classification = self._extract_classification(data)
        artifacts = self._extract_artifacts(data)

        return ParseResult(
            classification=classification,
            artifacts=artifacts,
            raw_response=raw_response,
            parse_method=parse_method,
        )

    def _extract_classification(
        self, data: Dict[str, Any]
    ) -> Optional[Classification]:
        """Extract classification from parsed JSON."""
        cls_data = data.get("classification")
        if not cls_data or not isinstance(cls_data, dict):
            return None

        try:
            return Classification(
                intent=cls_data.get("intent", "other"),
                urgency=cls_data.get("urgency", "medium"),
                sentiment=cls_data.get("sentiment", "neutral"),
                language=cls_data.get("language", "en"),
            )
        except Exception as e:
            logger.warning("Failed to parse classification: %s", e)
            return None

    def _extract_artifacts(self, data: Dict[str, Any]) -> List[Artifact]:
        """Extract artifacts from parsed JSON."""
        artifacts: List[Artifact] = []

        # Check for artifacts array
        raw_artifacts = data.get("artifacts", [])
        if isinstance(raw_artifacts, list):
            for item in raw_artifacts:
                if isinstance(item, dict):
                    artifacts.append(
                        Artifact(
                            type=item.get("type", "unknown"),
                            content=item.get("content", ""),
                            approvalStatus=item.get(
                                "approvalStatus", "pending"
                            ),
                            metadata=item.get("metadata"),
                        )
                    )

        # Check for draft_reply at top level
        if "draft_reply" in data and isinstance(data["draft_reply"], dict):
            reply = data["draft_reply"]
            artifacts.append(
                Artifact(
                    type="draft_reply",
                    content=reply.get("body", reply.get("content", "")),
                    approvalStatus=reply.get("approvalStatus", "pending"),
                    metadata={
                        k: v
                        for k, v in reply.items()
                        if k not in ("body", "content", "approvalStatus")
                    }
                    or None,
                )
            )

        # Check for classification_report at top level
        if "classification" in data:
            artifacts.append(
                Artifact(
                    type="classification_report",
                    content=json.dumps(data["classification"], indent=2),
                    approvalStatus="not_required",
                )
            )

        return artifacts
