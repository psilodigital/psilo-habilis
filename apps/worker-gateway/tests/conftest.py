"""Shared test fixtures for the worker-gateway test suite."""

import os
import pytest

# Point repo_root to the actual project root so resolver can find worker-packs/ and clients/
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.environ.setdefault("REPO_ROOT", _REPO_ROOT)
os.environ.setdefault("AGENTZERO_API_TOKEN", "test-token")
os.environ.setdefault("LITELLM_MASTER_KEY", "sk-test")

# Connector layer test defaults
try:
    from cryptography.fernet import Fernet
    os.environ.setdefault("CONNECTOR_ENCRYPTION_KEY", Fernet.generate_key().decode())
except ImportError:
    pass
os.environ.setdefault("GATEWAY_INTERNAL_SECRET", "test-internal-secret")


@pytest.fixture
def repo_root():
    return _REPO_ROOT


@pytest.fixture
def sample_run_request():
    """A valid WorkerRunRequest payload dict."""
    return {
        "companyId": "psilodigital",
        "workerInstanceId": "psilodigital.inbox-worker",
        "blueprintId": "inbox-worker",
        "blueprintVersion": "1.0.0",
        "taskKind": "inbound_email_triage",
        "input": {
            "message": "Subject: Inquiry about services\n\nHello, I'd like to learn more about your digital agency services.",
            "data": {"from": "client@example.com", "subject": "Inquiry about services"},
            "source": {"type": "email", "ref": "msg-001"},
        },
    }
