"""Tests for the response parser."""

import json
import pytest
from gateway.response_parser import ResponseParser


@pytest.fixture
def parser():
    return ResponseParser()


class TestResponseParser:
    def test_parse_json_code_block(self, parser):
        response = '''Here is the result:

```json
{
    "classification": {"intent": "inquiry", "urgency": "medium", "sentiment": "positive", "language": "en"},
    "artifacts": [{"type": "draft_reply", "content": "Thank you for reaching out.", "approvalStatus": "pending"}]
}
```
'''
        result = parser.parse(response)
        assert result.parse_method == "code_block"
        assert result.classification is not None
        assert result.classification.intent == "inquiry"
        assert len(result.artifacts) > 0

    def test_parse_raw_json(self, parser):
        response = json.dumps({
            "classification": {"intent": "spam", "urgency": "low", "sentiment": "neutral", "language": "en"},
        })
        result = parser.parse(response)
        assert result.parse_method == "raw_json"
        assert result.classification is not None
        assert result.classification.intent == "spam"

    def test_fallback_on_plain_text(self, parser):
        response = "I analyzed the email and it appears to be a general inquiry."
        result = parser.parse(response)
        assert result.parse_method == "fallback"
        assert len(result.artifacts) == 1
        assert result.artifacts[0].type == "raw_response"

    def test_empty_response(self, parser):
        result = parser.parse("")
        assert result.parse_method == "empty"
        assert len(result.artifacts) == 0

    def test_draft_reply_extraction(self, parser):
        response = json.dumps({
            "classification": {"intent": "inquiry", "urgency": "medium", "sentiment": "neutral", "language": "en"},
            "draft_reply": {"body": "Thank you for your inquiry.", "subject": "Re: Inquiry", "approvalStatus": "pending"},
        })
        result = parser.parse(response)
        draft_artifacts = [a for a in result.artifacts if a.type == "draft_reply"]
        assert len(draft_artifacts) == 1
        assert "Thank you" in draft_artifacts[0].content

    def test_invalid_json_code_block(self, parser):
        response = '```json\n{invalid json}\n```'
        result = parser.parse(response)
        # Should fall through to fallback
        assert result.parse_method == "fallback"
