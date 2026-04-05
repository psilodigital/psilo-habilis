#!/usr/bin/env bash
# Generate a local .env from .env.example with random secrets.
# Safe to re-run — will not overwrite an existing .env unless --force is passed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_EXAMPLE="$PROJECT_DIR/.env.example"
ENV_FILE="$PROJECT_DIR/.env"

if [ ! -f "$ENV_EXAMPLE" ]; then
  echo "ERROR: $ENV_EXAMPLE not found" >&2
  exit 1
fi

if [ -f "$ENV_FILE" ] && [ "${1:-}" != "--force" ]; then
  echo ".env already exists. Use --force to overwrite."
  exit 0
fi

# --- Generate random values ---
rand_alphanum() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$1" || true; }
rand_hex()      { LC_ALL=C tr -dc 'a-f0-9'    </dev/urandom | head -c "$1" || true; }

POSTGRES_PW="$(rand_alphanum 32)"
LITELLM_KEY="sk-$(rand_alphanum 48)"
PAPERCLIP_JWT="$(rand_hex 64)"
A0_PASSWORD="$(rand_alphanum 32)"

# --- Copy template and replace placeholder values ---
cp "$ENV_EXAMPLE" "$ENV_FILE"

# macOS-compatible sed -i (BSD vs GNU)
_sed_i() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"            # GNU
  else
    sed -i '' "$@"         # BSD / macOS
  fi
}

_sed_i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PW}|"                   "$ENV_FILE"
_sed_i "s|^LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=${LITELLM_KEY}|"                "$ENV_FILE"
_sed_i "s|^PAPERCLIP_AGENT_JWT_SECRET=.*|PAPERCLIP_AGENT_JWT_SECRET=${PAPERCLIP_JWT}|" "$ENV_FILE"
_sed_i "s|^AGENTZERO_AUTH_PASSWORD=.*|AGENTZERO_AUTH_PASSWORD=${A0_PASSWORD}|"        "$ENV_FILE"

echo ""
echo "=== .env generated ==="
echo ""
echo "  POSTGRES_PASSWORD    = ${POSTGRES_PW:0:4}... (generated)"
echo "  LITELLM_MASTER_KEY   = ${LITELLM_KEY:0:8}... (generated)"
echo "  PAPERCLIP_JWT_SECRET = ${PAPERCLIP_JWT:0:8}... (generated)"
echo "  AGENTZERO_PASSWORD   = ${A0_PASSWORD:0:4}... (generated)"
echo ""
echo "Still needs manual input:"
echo "  - At least one LLM provider API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)"
echo "  - AGENTZERO_API_TOKEN (from Agent Zero UI after first boot: Settings > External Services)"
echo ""
echo "Edit $ENV_FILE to fill these in, then run: make build"
