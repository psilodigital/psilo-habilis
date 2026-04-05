#!/usr/bin/env bash
# ===========================================================================
# Psilodigital Worker Platform — v1 Smoke Test
#
# Tests the blueprint-driven worker execution pipeline end-to-end.
#
# Usage:
#   bash infra/scripts/smoke-v1.sh              # default: localhost:8080
#   bash infra/scripts/smoke-v1.sh localhost:8090  # custom host:port
# ===========================================================================

set -euo pipefail

BASE="${1:-localhost:8080}"
URL="http://${BASE}"
PASS=0
FAIL=0

green()  { printf "\033[32m✓ %s\033[0m\n" "$1"; }
red()    { printf "\033[31m✗ %s\033[0m\n" "$1"; }
header() { printf "\n\033[1m--- %s ---\033[0m\n" "$1"; }

check() {
  local desc="$1" expected="$2" actual="$3"
  if echo "$actual" | grep -q "$expected"; then
    green "$desc"
    PASS=$((PASS + 1))
  else
    red "$desc (expected '$expected', got '$actual')"
    FAIL=$((FAIL + 1))
  fi
}

# -------------------------------------------------------------------
header "1. Health & Info"

ROOT=$(curl -sf "${URL}/")
check "GET / returns status ok" '"status":"ok"' "$ROOT"

HEALTH=$(curl -sf "${URL}/health")
check "GET /health returns status" '"status"' "$HEALTH"

INFO=$(curl -sf "${URL}/info")
check "GET /info returns version 1.0.0" '"version":"1.0.0"' "$INFO"
check "GET /info shows stub adapter" '"runtimeAdapter":"stub"' "$INFO"

# -------------------------------------------------------------------
header "2. Sales Inquiry (→ sales_lead, awaiting_approval)"

SALES=$(curl -sf -X POST "${URL}/v1/workers/run" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "psilodigital",
    "workerInstanceId": "psilodigital.inbox-worker",
    "blueprintId": "inbox-worker",
    "blueprintVersion": "1.0.0",
    "taskKind": "inbound_email_triage",
    "input": {
      "message": "Hi, I would like to know your pricing for the AI worker platform.",
      "source": {"type": "email", "ref": "msg-001", "timestamp": "2025-04-05T10:30:00Z"}
    }
  }')

check "Sales: status is awaiting_approval" '"status":"awaiting_approval"' "$SALES"
check "Sales: intent is sales_lead" '"intent":"sales_lead"' "$SALES"
check "Sales: has draft_reply artifact" '"type":"draft_reply"' "$SALES"
check "Sales: blueprint resolved" '"name":"Inbox Worker"' "$SALES"
check "Sales: client resolved" '"name":"Psilodigital"' "$SALES"
check "Sales: config merged (timeoutSeconds=90)" '"timeoutSeconds":90' "$SALES"

# -------------------------------------------------------------------
header "3. Support Request (→ support, high urgency)"

SUPPORT=$(curl -sf -X POST "${URL}/v1/workers/run" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "psilodigital",
    "workerInstanceId": "psilodigital.inbox-worker",
    "blueprintId": "inbox-worker",
    "blueprintVersion": "1.0.0",
    "taskKind": "inbound_email_triage",
    "input": {
      "message": "Help! Our integration is broken and we keep getting error 500."
    }
  }')

check "Support: intent is support" '"intent":"support"' "$SUPPORT"
check "Support: urgency is high" '"urgency":"high"' "$SUPPORT"

# -------------------------------------------------------------------
header "4. Spam Detection (→ spam, completed, no reply)"

SPAM=$(curl -sf -X POST "${URL}/v1/workers/run" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "psilodigital",
    "workerInstanceId": "psilodigital.inbox-worker",
    "blueprintId": "inbox-worker",
    "blueprintVersion": "1.0.0",
    "taskKind": "inbound_email_triage",
    "input": {
      "message": "Congratulations! You are the winner of our lottery!"
    }
  }')

check "Spam: status is completed (auto-archived)" '"status":"completed"' "$SPAM"
check "Spam: intent is spam" '"intent":"spam"' "$SPAM"
# Spam should NOT have a draft_reply
if echo "$SPAM" | grep -q '"type":"draft_reply"'; then
  red "Spam: should NOT have draft_reply"
  FAIL=$((FAIL + 1))
else
  green "Spam: correctly has no draft_reply"
  PASS=$((PASS + 1))
fi

# -------------------------------------------------------------------
header "5. Error Cases"

ERR_CLIENT=$(curl -sf -X POST "${URL}/v1/workers/run" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "nonexistent",
    "workerInstanceId": "nonexistent.inbox-worker",
    "blueprintId": "inbox-worker",
    "blueprintVersion": "1.0.0",
    "taskKind": "inbound_email_triage",
    "input": {"message": "test"}
  }')

check "Error: unknown client returns CLIENT_NOT_FOUND" '"code":"CLIENT_NOT_FOUND"' "$ERR_CLIENT"

ERR_TASK=$(curl -sf -X POST "${URL}/v1/workers/run" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "psilodigital",
    "workerInstanceId": "psilodigital.inbox-worker",
    "blueprintId": "inbox-worker",
    "blueprintVersion": "1.0.0",
    "taskKind": "nonexistent_task",
    "input": {"message": "test"}
  }')

check "Error: bad task kind returns UNSUPPORTED_TASK_KIND" '"code":"UNSUPPORTED_TASK_KIND"' "$ERR_TASK"

# -------------------------------------------------------------------
header "Results"

TOTAL=$((PASS + FAIL))
echo ""
echo "  ${PASS}/${TOTAL} checks passed"

if [ "$FAIL" -gt 0 ]; then
  echo "  ${FAIL} checks FAILED"
  exit 1
else
  echo "  All checks passed!"
  exit 0
fi
