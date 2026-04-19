"""Tests for the connector layer: session tokens, connector store encryption, and prompt injection."""

import json
import os

import pytest

# Use the Fernet key from conftest.py (set before settings singleton is created)
_TEST_FERNET_KEY = os.environ.get("CONNECTOR_ENCRYPTION_KEY", "")


class TestSessionTokens:
    """Test JWT session token creation and validation."""

    def test_create_and_validate_token(self):
        from gateway.connectors.session import create_session_token, validate_session_token

        token = create_session_token(
            company_id="psilodigital",
            connector_id="gmail",
            scopes=["email_read"],
            ttl=60,
        )
        assert isinstance(token, str)
        assert len(token) > 0

        decoded = validate_session_token(token)
        assert decoded["company_id"] == "psilodigital"
        assert decoded["connector_id"] == "gmail"
        assert decoded["scopes"] == ["email_read"]

    def test_token_contains_expected_claims(self):
        import jwt as pyjwt
        from gateway.connectors.session import create_session_token

        token = create_session_token(
            company_id="acme",
            connector_id="slack",
            scopes=["chat_read", "chat_write"],
            ttl=300,
        )

        # Decode without verification to inspect claims
        payload = pyjwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == "acme"
        assert payload["cid"] == "slack"
        assert payload["scopes"] == ["chat_read", "chat_write"]
        assert "exp" in payload
        assert "iat" in payload
        assert payload["exp"] - payload["iat"] == 300

    def test_expired_token_raises(self):
        import jwt as pyjwt
        from gateway.connectors.session import create_session_token, validate_session_token

        # Create a token that's already expired
        token = create_session_token(
            company_id="test",
            connector_id="gmail",
            scopes=["email_read"],
            ttl=-1,  # Already expired
        )

        with pytest.raises(pyjwt.ExpiredSignatureError):
            validate_session_token(token)

    def test_invalid_token_raises(self):
        import jwt as pyjwt
        from gateway.connectors.session import validate_session_token

        with pytest.raises(pyjwt.InvalidTokenError):
            validate_session_token("not-a-valid-token")


class TestConnectorStoreEncryption:
    """Test Fernet encryption/decryption in ConnectorStore (no DB required)."""

    def _make_store(self):
        """Create a ConnectorStore without connecting to DB."""
        from gateway.store.connector_store import ConnectorStore

        store = ConnectorStore.__new__(ConnectorStore)
        from cryptography.fernet import Fernet
        store._fernet = Fernet(_TEST_FERNET_KEY.encode())
        store._pool = None
        store._database_url = ""
        return store

    def test_encrypt_decrypt_roundtrip(self):
        store = self._make_store()
        original = {
            "access_token": "ya29.test-access-token",
            "refresh_token": "1//test-refresh-token",
            "client_id": "123.apps.googleusercontent.com",
            "client_secret": "GOCSPX-secret",
        }
        encrypted = store._encrypt(original)
        assert isinstance(encrypted, bytes)
        assert encrypted != json.dumps(original).encode()  # Not plaintext

        decrypted = store._decrypt(encrypted)
        assert decrypted == original

    def test_encrypted_data_is_not_readable(self):
        store = self._make_store()
        data = {"secret_key": "super-sensitive-value"}
        encrypted = store._encrypt(data)
        # Encrypted bytes should not contain the plaintext
        assert b"super-sensitive-value" not in encrypted

    def test_different_encryptions_produce_different_ciphertext(self):
        store = self._make_store()
        data = {"token": "test"}
        enc1 = store._encrypt(data)
        enc2 = store._encrypt(data)
        # Fernet uses random IV, so same plaintext produces different ciphertext
        assert enc1 != enc2


class TestPromptConnectorInjection:
    """Test that connector auth tokens are injected into assembled prompts."""

    def test_format_connector_instructions(self):
        from gateway.prompt import PromptAssembler

        assembler = PromptAssembler()
        connectors = [
            {
                "connector_id": "gmail",
                "auth_token": "eyJ.test.token",
                "scopes": ["email_read"],
            }
        ]

        text = assembler._format_connector_instructions(connectors)
        assert "## Available Connectors" in text
        assert "Gmail" in text
        assert "eyJ.test.token" in text
        assert "email_read" in text
        assert "gmail_list_messages" in text
        assert "gmail_get_message" in text
        assert "gmail_search" in text

    def test_no_connectors_returns_empty(self):
        from gateway.prompt import PromptAssembler

        assembler = PromptAssembler()
        assert assembler._format_connector_instructions([]) == ""
        assert assembler._format_connector_instructions(None) == ""

    def test_assemble_includes_connectors_in_system_prompt(self):
        from gateway.prompt import PromptAssembler

        assembler = PromptAssembler()
        connectors = [
            {
                "connector_id": "gmail",
                "auth_token": "test-token-123",
                "scopes": ["email_read"],
            }
        ]

        result = assembler.assemble(
            task_kind="inbound_email_triage",
            input_message="Test email",
            input_data=None,
            blueprint={"id": "inbox-worker"},
            persona="You are an inbox worker.",
            playbook="",
            policies={},
            output_schema=None,
            client_context={},
            merged_config={"model": "test"},
            connectors=connectors,
        )

        assert "test-token-123" in result.system_prompt
        assert "Gmail" in result.system_prompt
        assert "connectors" in result.metadata["sources"]

    def test_assemble_without_connectors_has_no_connector_section(self):
        from gateway.prompt import PromptAssembler

        assembler = PromptAssembler()

        result = assembler.assemble(
            task_kind="inbound_email_triage",
            input_message="Test email",
            input_data=None,
            blueprint={"id": "inbox-worker"},
            persona="You are an inbox worker.",
            playbook="",
            policies={},
            output_schema=None,
            client_context={},
            merged_config={"model": "test"},
        )

        assert "Available Connectors" not in result.system_prompt
        assert "connectors" not in result.metadata.get("sources", [])
