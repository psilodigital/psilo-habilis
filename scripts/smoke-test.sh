#!/usr/bin/env bash
# Smoke tests for the Habilis stack.
# Run after `docker compose up` with all services healthy.
set -euo pipefail

PASS=0
FAIL=0
WARN=0

ok()   { PASS=$((PASS+1)); echo "  [PASS] $1"; }
fail() { FAIL=$((FAIL+1)); echo "  [FAIL] $1"; }
warn() { WARN=$((WARN+1)); echo "  [WARN] $1"; }

echo ""
echo "=== Habilis Stack Smoke Tests ==="
echo ""

# 1. docker compose config
echo "--- Compose validation ---"
if docker compose config --quiet 2>/dev/null; then
  ok "docker compose config is valid"
else
  fail "docker compose config has errors"
fi

# 2. All services running
echo ""
echo "--- Service status ---"
for svc in postgres redis litellm paperclip agentzero worker-gateway; do
  state=$(docker compose ps --format '{{.State}}' "$svc" 2>/dev/null || echo "missing")
  if echo "$state" | grep -qi "running"; then
    ok "$svc is running"
  else
    fail "$svc state: $state"
  fi
done

# 3. Health endpoints
echo ""
echo "--- Health endpoints ---"

# Worker gateway
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/healthz 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  ok "worker-gateway /healthz -> $HTTP_CODE"
else
  fail "worker-gateway /healthz -> $HTTP_CODE"
fi

# LiteLLM health (use /health/liveliness — no auth required)
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:4000/health/liveliness 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  ok "litellm /health/liveliness -> $HTTP_CODE"
else
  fail "litellm /health/liveliness -> $HTTP_CODE"
fi

# Paperclip health
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3100/api/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  ok "paperclip /api/health -> $HTTP_CODE"
else
  fail "paperclip /api/health -> $HTTP_CODE"
fi

# Agent Zero reachability
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:50080/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 500 ] 2>/dev/null; then
  ok "agentzero / -> $HTTP_CODE"
else
  fail "agentzero / -> $HTTP_CODE"
fi

# 4. Wake endpoint test
echo ""
echo "--- Wake endpoint ---"
WAKE_CODE=$(curl -s -o /tmp/habilis-wake-resp.json -w '%{http_code}' -X POST http://localhost:8080/paperclip/wake \
  -H 'Content-Type: application/json' \
  -d '{"runId":"smoke-test-001","agentId":"test-agent","companyId":"test-co","input":"ping"}' \
  2>/dev/null || echo "000")
WAKE_BODY=$(cat /tmp/habilis-wake-resp.json 2>/dev/null || echo "")

if [ "$WAKE_CODE" = "202" ]; then
  ok "POST /paperclip/wake -> 202"
elif [ "$WAKE_CODE" = "200" ]; then
  ok "POST /paperclip/wake -> 200"
else
  fail "POST /paperclip/wake -> $WAKE_CODE"
fi

# Check response body contains accepted
if echo "$WAKE_BODY" | grep -q '"accepted":true'; then
  ok "Wake response contains accepted:true"
elif echo "$WAKE_BODY" | grep -q '"accepted": true'; then
  ok "Wake response contains accepted: true"
else
  warn "Wake response body unexpected: $WAKE_BODY"
fi

# 5. Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed, $WARN warnings ==="
echo ""

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
