# Testing Patterns

**Analysis Date:** 2026-04-19

## Test Framework

**Runner:**
- Python: pytest (configured in `apps/worker-gateway/pyproject.toml`)
- TypeScript: Not configured (no test framework detected in packages)

**Assertion Library:**
- Python: pytest's built-in assertions (`assert`)

**Run Commands:**
```bash
pytest                           # Run all tests (excludes integration tests by default)
pytest -m integration            # Run integration tests only
pytest tests/test_routes.py      # Run specific test file
pytest -v                        # Verbose output
```

## Test File Organization

**Location:**
- Python: Co-located in `apps/worker-gateway/tests/` directory (separate from source)
- Structure mirrors source: `gateway/adapters/agentzero.py` → `tests/test_agentzero_integration.py`

**Naming:**
- Test files: `test_*.py` (e.g., `test_routes.py`, `test_connectors.py`, `test_prompt.py`)
- Test classes: `Test*` (e.g., `class TestRoutes`)
- Test methods: `test_*` (e.g., `test_root`, `test_run_worker_success`)

**Structure:**
```
apps/worker-gateway/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── test_routes.py        # API endpoint tests
│   ├── test_adapters.py      # Adapter unit tests
│   ├── test_connectors.py    # Connector integration tests
│   └── test_*.py             # Additional test modules
└── gateway/                  # Source code
```

## Test Structure

**Suite Organization:**
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app import app

@pytest.fixture
async def client():
    # Setup
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Teardown (implicit in async context manager)

class TestRoutes:
    @pytest.mark.asyncio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "worker-gateway"
```

**Patterns:**
- Async test methods decorated with `@pytest.mark.asyncio`
- Fixtures for shared setup (e.g., `client`, `sample_run_request`)
- Test classes group related tests (e.g., `class TestRoutes` for all route handlers)
- Arrange-Act-Assert pattern (setup → call → verify)

## Mocking

**Framework:**
- Python: pytest fixtures for dependency injection (no explicit mocking library detected)
- Manual mocking via module-level globals (e.g., `app_module.http_client = httpx.AsyncClient()`)

**Patterns:**
```python
@pytest.fixture
async def client():
    # Manually inject test dependencies
    app_module.http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    app_module.runtime_adapter = StubRuntimeAdapter()
    app_module.config_store = FileConfigStore()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await app_module.http_client.aclose()
```

**What to Mock:**
- External HTTP clients (e.g., `httpx.AsyncClient`)
- Runtime adapters (e.g., use `StubRuntimeAdapter` instead of `AgentZeroAdapter`)
- Config stores (e.g., `FileConfigStore` for tests)

**What NOT to Mock:**
- Application logic under test
- Pydantic models (use real instances)
- Internal utilities

## Fixtures and Factories

**Test Data:**
```python
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
            "message": "Subject: Inquiry...",
            "data": {"from": "client@example.com"},
            "source": {"type": "email", "ref": "msg-001"},
        },
    }
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Test-specific fixtures: Within test files using `@pytest.fixture`

**Fixture Scope:**
- Default: Function scope (created per test)
- Async fixtures: Use `async def` and `yield` for setup/teardown

## Coverage

**Requirements:** Not enforced (no coverage target in config)

**View Coverage:**
```bash
pytest --cov=gateway --cov-report=html
# (requires pytest-cov to be installed)
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and classes in isolation
- Location: `tests/test_adapters.py`, `tests/test_resolver.py`, `tests/test_prompt.py`
- Dependencies: Minimal external dependencies, use stubs/mocks

**Integration Tests:**
- Scope: Multiple components working together (e.g., API → adapter → external service)
- Marker: `@pytest.mark.integration`
- Location: `tests/test_agentzero_integration.py`, `tests/test_connectors.py`
- Configuration: Excluded by default (`addopts = "-m 'not integration'"` in `pyproject.toml`)
- Run explicitly: `pytest -m integration`
- Requirements: Running downstream services (Agent Zero, LiteLLM)

**E2E Tests:**
- Framework: Not implemented
- Future consideration for full stack validation

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_run_worker_success(self, client, sample_run_request):
    resp = await client.post("/v1/workers/run", json=sample_run_request)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("completed", "awaiting_approval")
```

**Error Testing:**
```python
@pytest.mark.asyncio
async def test_run_worker_blueprint_not_found(self, client, sample_run_request):
    sample_run_request["blueprintId"] = "nonexistent"
    resp = await client.post("/v1/workers/run", json=sample_run_request)
    assert resp.status_code == 200  # API returns 200 with error payload
    data = resp.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "BLUEPRINT_NOT_FOUND"
```

**Environment Setup:**
```python
# In conftest.py
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.environ.setdefault("REPO_ROOT", _REPO_ROOT)
os.environ.setdefault("AGENTZERO_API_TOKEN", "test-token")
os.environ.setdefault("LITELLM_MASTER_KEY", "sk-test")
```

**Test Configuration:**
- `pyproject.toml` settings:
  - `asyncio_mode = "auto"` — automatic async support
  - `testpaths = ["tests"]` — test discovery path
  - `pythonpath = ["."]` — import resolution
  - `markers = ["integration: ..."]` — custom test markers

---

*Testing analysis: 2026-04-19*
