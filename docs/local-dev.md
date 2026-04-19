# Local Development Guide

## Prerequisites

- Docker and Docker Compose v2
- At least one LLM provider API key (OpenAI, Anthropic, Google, Groq, or OpenRouter)
- ~4 GB free RAM

## First-Time Setup

```sh
# 1. Generate .env with random secrets
make setup

# 2. Edit .env and add at least one provider API key
#    e.g. OPENAI_API_KEY=sk-...

# 3. Build and start
make build

# 4. Verify all services are healthy
make status

# 5. Run smoke tests (13 checks)
make test
```

## Service Map

| Service | Internal URL | Host URL | Purpose |
|---|---|---|---|
| Postgres | `postgres:5432` | not exposed | System of record |
| Redis | `redis:6379` | not exposed | Reserved for future queue/cache/coordination use |
| Dashboard | `http://dashboard:3000` | `http://localhost:3000` | Customer-facing product surface |
| LiteLLM | `http://litellm:4000` | `http://localhost:4000` | Model gateway |
| Paperclip | `http://paperclip:3100` | `http://localhost:3100` | Control plane |
| Agent Zero | `http://agentzero:80` | `http://localhost:50080` | Worker runtime |
| Worker Gateway | `http://worker-gateway:8080` | `http://localhost:8080` | Orchestration bridge |

## Post-Boot Configuration

### Step 1: Get Agent Zero API Token

1. Open http://localhost:50080
2. Log in: `admin` / (password from `AGENTZERO_AUTH_PASSWORD` in `.env`)
3. Go to **Settings > External Services**
4. Copy the API token
5. Set `AGENTZERO_API_TOKEN=<token>` in `.env`
6. Run `make restart-worker-gateway`

### Step 2: Configure Agent Zero to Use LiteLLM

In the Agent Zero UI (http://localhost:50080), configure the chat model:

- **Provider**: OpenAI Compatible
- **Base URL**: `http://litellm:4000`
- **API Key**: your `LITELLM_MASTER_KEY` value from `.env`
- **Model**: `gpt-4.1-mini` (or any model from `services/litellm/config.yaml`)

This routes all Agent Zero model requests through LiteLLM instead of direct provider calls.

### Step 3: Configure Paperclip HTTP Adapter

1. Open http://localhost:3100
2. Log in (Paperclip creates default credentials on first boot — check container logs if needed)
3. Create an agent with adapter type **HTTP**
4. Set the webhook URL:
   ```
   http://worker-gateway:8080/paperclip/wake
   ```
5. Send a test task
6. Verify in logs: `make logs-worker-gateway`

## Available Model Aliases

Workers should use these LiteLLM model aliases (defined in `services/litellm/config.yaml`):

| Alias | Underlying Model | Use Case |
|---|---|---|
| `worker-default` | `openai/gpt-4.1-mini` | Standard worker tasks |
| `worker-strong` | `anthropic/claude-sonnet-4-5` | Complex reasoning |
| `gpt-4.1-mini` | `openai/gpt-4.1-mini` | Direct OpenAI |
| `gpt-4.1` | `openai/gpt-4.1` | High-capability OpenAI |
| `claude-sonnet-4-5` | `anthropic/claude-sonnet-4-5` | Direct Anthropic |
| `gemini-2.5-flash` | `gemini/gemini-2.5-flash` | Google fast |
| `groq-llama-3.3-70b` | `groq/llama-3.3-70b-versatile` | Groq fast inference |
| `openrouter-auto` | `openrouter/auto` | OpenRouter fallback |

To call a model through LiteLLM from any service on the Docker network:

```sh
curl http://litellm:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "worker-default", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Worker Gateway Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET /` | Root check | `{"service":"worker-gateway","status":"ok"}` |
| `GET /healthz` | Health with downstream status | Checks agentzero + litellm reachability |
| `GET /info` | Service metadata | Endpoints, downstream URLs, token status |
| `POST /paperclip/wake` | Wake endpoint | Accepts Paperclip task, executes via runtime adapter, returns 2xx |

## Wake Payload Contract

```json
{
  "runId": "run-abc123",
  "agentId": "inbox-worker",
  "input": "Process the latest emails",
  "context": {}
}
```

The gateway:
1. Accepts the payload
2. Sends `input` to Agent Zero via `POST /api_message`
3. Returns a 2xx response to Paperclip when the wake flow completes

## Useful Commands

```sh
make logs                    # All service logs
make logs-worker-gateway     # Single service logs
make restart-worker-gateway  # Restart one service
make status                  # Container health overview
make test                    # 13-check smoke test
make clean                   # Stop + remove volumes (full reset)
make shell-paperclip         # Shell into container
```

## Troubleshooting

**LiteLLM boots but model calls fail**: No provider API keys in `.env`. Add at least one.

**Worker gateway shows "degraded"**: One or more downstream services unreachable. Check `make status`.

**Agent Zero returns 401/403**: API token mismatch. Re-copy from Agent Zero UI and restart gateway.

**Paperclip wake fails**: Verify the HTTP adapter points to `http://worker-gateway:8080/paperclip/wake` and that gateway auth settings match your Paperclip setup.

**Postgres init scripts not running**: Init scripts only run on first boot with empty data volume. Run `make clean` then `make build` for a full reset.
