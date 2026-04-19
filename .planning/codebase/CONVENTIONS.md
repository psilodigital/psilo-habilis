# Coding Conventions

**Analysis Date:** 2026-04-19

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `response_parser.py`, `agentzero_integration.py`)
- Python tests: `test_*.py` (e.g., `test_routes.py`, `test_connectors.py`)
- TypeScript source: `kebab-case.ts` (e.g., `worker-run-request.ts`, `worker-instance.ts`)
- Config files: lowercase with extensions (e.g., `tsconfig.json`, `pyproject.toml`)

**Functions:**
- Python: `snake_case` for all functions and methods
- TypeScript: `camelCase` for functions and methods
- Private/internal Python functions: prefix with `_` (e.g., `_find_repo_root()`, `_extract_classification()`)
- Async functions: no special prefix, use `async def` keyword

**Variables:**
- Python: `snake_case` for all variables (e.g., `run_id`, `merged_config`, `http_client`)
- TypeScript: `camelCase` for variables (e.g., `companyId`, `workerInstanceId`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `_TOOL_CONNECTOR_MAP`, `_REPO_ROOT`)
- Global module-level vars: `lowercase_snake_case` (e.g., `http_client`, `runtime_adapter`)

**Types:**
- Python classes: `PascalCase` (e.g., `WorkerRunRequest`, `StubRuntimeAdapter`, `ConfigStore`)
- TypeScript types/interfaces: `PascalCase` (e.g., `WorkerBlueprint`, `BlueprintDefaults`, `RunStatus`)
- Python exceptions: `PascalCase` with `Error` suffix (e.g., `ResolutionError`, `PaperclipClientError`)

## Code Style

**Formatting:**
- Python: Ruff (configured in `apps/worker-gateway/pyproject.toml`)
  - Line length: 100 characters
  - Target version: Python 3.12
- TypeScript: No explicit formatter detected in project root (relies on IDE/editor defaults)
- Indentation: 4 spaces for Python, 2 spaces for TypeScript (standard convention)

**Linting:**
- Python: Ruff (linter + formatter combined)
- TypeScript: No ESLint config in project root (monorepo uses Turbo for builds)
- Line length enforced at 100 characters for Python

## Import Organization

**Python Order:**
1. Standard library imports (e.g., `import asyncio`, `import uuid`, `import json`)
2. Third-party imports (e.g., `import httpx`, `from fastapi import FastAPI`, `from pydantic import BaseModel`)
3. Local application imports (e.g., `from gateway.config import settings`, `from gateway.models import ...`)

**Path Aliases:**
- TypeScript: Package aliases via `@habilis/` namespace (e.g., `@habilis/shared-types`)
- Python: Relative imports within `gateway/` package (e.g., `from gateway.logging import logger`)

**Import Style:**
- Python: Absolute imports preferred (`from gateway.config import settings`)
- Group imports by source (stdlib → third-party → local)
- No wildcard imports (`from module import *`)

## Error Handling

**Patterns:**
- Custom exception classes for domain errors (e.g., `ResolutionError`, `PaperclipClientError`)
- Exceptions carry structured data via class attributes (e.g., `ResolutionError.code`, `ResolutionError.message`)
- HTTP endpoints return 200 with error payload rather than HTTP error codes for business logic failures
- Try/except with specific logging:
  ```python
  try:
      # operation
  except Exception as exc:
      logger.error("Context: %s", exc)
      return error_response(...)
  ```
- Error responses use dedicated builder functions (e.g., `_error_response()` in `apps/worker-gateway/app.py`)

## Logging

**Framework:** Python `logging` module with custom JSON formatter

**Implementation:**
- Structured JSON logging via `gateway.logging.JSONFormatter`
- Log fields: `ts`, `level`, `logger`, `msg`, `exc` (for exceptions)
- Logger name: `"worker-gateway"`
- Log level: Configurable via `settings.log_level` (default: `INFO`)

**Patterns:**
- Use parameterized logging: `logger.info("Run completed: runId=%s status=%s", run_id, status)`
- Include context in log messages (runId, companyId, blueprintId, etc.)
- Log at entry/exit of major operations (route handlers, adapter methods)
- Log errors with `logger.error()`, warnings with `logger.warning()`

## Comments

**When to Comment:**
- Module docstrings at file top explaining purpose (e.g., `"""Psilodigital Worker Gateway — v1"""`)
- Function docstrings for public APIs and complex logic
- Inline comments for non-obvious implementation details
- TODO comments for planned improvements (e.g., `# TODO: extract from A0 response if available`)

**Docstring Style:**
- Python: Triple-quoted strings at module/function level
- Format: Plain text descriptions, no strict format (not Google/NumPy style)
- TypeScript: JSDoc-style comments for type exports (e.g., `/** Possible run statuses */`)

## Function Design

**Size:**
- Keep functions focused on single responsibility
- Extract helpers for reusable logic (e.g., `_resolve_connectors()`, `_error_response()`)
- Async functions for I/O operations (HTTP calls, database queries)

**Parameters:**
- Use keyword-only arguments for clarity in Python (e.g., `def _resolve_connectors(*, company_id: str, ...)`)
- Type hints on all parameters and return values
- Pydantic models for structured input/output

**Return Values:**
- Python: Explicit type hints (e.g., `-> Dict[str, Any]`, `-> WorkerRunResponse`)
- TypeScript: Explicit return types on exported functions
- Return structured objects, not tuples

## Module Design

**Exports:**
- Python: Direct imports from module (e.g., `from gateway.models import WorkerRunRequest`)
- TypeScript: Barrel exports via `index.ts` files (e.g., `packages/shared-types/src/index.ts`)

**Package Structure:**
- Python: Package-based organization (`gateway/` as package with `__init__.py`)
- TypeScript: Monorepo packages under `packages/` (e.g., `@habilis/shared-types`, `@habilis/config`)
- Separation of concerns: models, config, adapters, stores as separate modules

**Barrel Files:**
- TypeScript: Used in all packages (e.g., `src/index.ts` re-exports all types)
- Python: Not used (direct imports preferred)

---

*Convention analysis: 2026-04-19*
