# Technology Stack

**Analysis Date:** 2026-04-19

## Languages

**Primary:**
- Python 3.12 - Worker gateway (`apps/worker-gateway/`), Gmail MCP connector (`services/gmail-mcp/`)
- TypeScript 5.7.0/5.9.3 - Dashboard (`apps/dashboard/`), shared packages (`packages/`)

**Secondary:**
- JavaScript (Node.js 20/22) - Paperclip service runtime, build tooling

## Runtime

**Environment:**
- Python 3.12 (slim base image)
- Node.js 20-alpine (Paperclip service)
- Node.js 22-alpine (Dashboard build/production)

**Package Manager:**
- pnpm 9.15.4 (JavaScript/TypeScript monorepo)
- pip (Python services)
- Lockfile: `pnpm-lock.yaml` present for JS/TS

## Frameworks

**Core:**
- FastAPI 0.116.1 - Worker gateway (`apps/worker-gateway/app.py`)
- Next.js 16.2.4 - Dashboard application (`apps/dashboard/`)
- React 19.2.4 - Dashboard UI library
- Uvicorn 0.35.0 - ASGI server for Python services

**Testing:**
- pytest - Worker gateway unit tests (`apps/worker-gateway/tests/`)
- Jest/Vitest - TypeScript packages (via turbo)

**Build/Dev:**
- Turbo 2.3.0 - Monorepo build orchestration (`turbo.json`)
- Tailwind CSS 4 - Dashboard styling
- ESLint 9 - JavaScript/TypeScript linting
- Drizzle ORM 0.45.2 - Database migrations and queries

## Key Dependencies

**Critical:**
- httpx 0.28+ - HTTP client for worker-gateway, Gmail MCP connector
- better-auth 1.6.5 - Dashboard authentication framework
- pydantic-settings 2.7+ - Configuration management in Python services
- drizzle-orm 0.45.2 - TypeScript database layer
- SQLAlchemy 2.0+ - Python database layer with asyncpg driver
- Alembic 1.14+ - Database migrations for worker-gateway

**Infrastructure:**
- asyncpg 0.30+ - PostgreSQL async driver for Python
- pg 8.20.0 - PostgreSQL driver for Node.js/TypeScript
- cryptography 44.0+ - Connector credential encryption
- pyjwt 2.10+ - JWT handling in Python services

**External Services:**
- paperclipai (npm global) - Control plane CLI/runtime (`services/paperclip/Dockerfile`)
- litellm (docker.litellm.ai/berriai/litellm:main-stable) - Model gateway proxy
- agent0ai/agent-zero - Worker runtime container
- mcp 1.9+ - Model Context Protocol SDK for connectors

**Google Integration:**
- google-api-python-client 2.160+ - Gmail API access
- google-auth 2.38+ - Google authentication
- google-auth-oauthlib 1.2+ - OAuth flow handling

## Configuration

**Environment:**
- `.env` file for local development (generated from `.env.example` via `make setup`)
- Docker Compose environment variable injection
- Pydantic Settings for Python config validation
- Environment variables for all services (see `.env.example`)

**Build:**
- `turbo.json` - Monorepo task orchestration
- `docker-compose.yml` - Service definitions and dependencies
- `next.config.ts` - Next.js configuration
- `drizzle.config.ts` - Database schema management
- `tsconfig.json` - TypeScript compiler options (per package)
- `eslint.config.mjs` - Linting rules
- `services/litellm/config.yaml` - Model routing and proxy settings
- `alembic.ini` - Database migration configuration

## Platform Requirements

**Development:**
- Docker with Docker Compose support
- Make (for workflow shortcuts in `Makefile`)
- pnpm 9.15.4 (managed via corepack)
- Python 3.12+ (for local worker-gateway development)

**Production:**
- Docker Compose runtime (Hetzner via Coolify)
- PostgreSQL 17-alpine (shared database)
- Redis 7-alpine (future dashboard caching)
- 6 containerized services: postgres, redis, litellm, paperclip, agentzero, worker-gateway, dashboard, gmail-mcp

---

*Stack analysis: 2026-04-19*
