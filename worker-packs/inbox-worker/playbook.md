# Inbox Worker — Playbook

Step-by-step operational guide for processing inbound email.

## Task: inbound_email_triage

### Step 1 — Receive

Accept the inbound email payload. Extract:
- sender address
- subject line
- body text (plain or HTML → plain)
- attachments metadata (names, sizes — do not process content in v1)
- timestamp

### Step 2 — Classify

Run the classifier agent to determine:
- **intent**: inquiry | support | sales_lead | spam | internal | other
- **urgency**: low | medium | high | critical
- **sentiment**: positive | neutral | negative
- **language**: ISO 639-1 code (e.g., "en", "pt")

### Step 3 — Route

Based on classification:
- **spam** → log and archive, no reply
- **critical urgency** → flag for immediate human review
- **sales_lead** → draft reply + notify sales channel
- **support** → draft reply using support templates
- **inquiry** → draft reply using general templates
- **internal** → forward to appropriate internal contact
- **other** → flag for human review

### Step 4 — Draft Reply

If a reply is warranted:
- Use the reply-drafter agent
- Apply company brand voice from client context
- Keep reply under 200 words unless the inquiry is complex
- Include a clear call to action where appropriate

### Step 5 — Approval Gate

If approval is required (per approval policy):
- Hold the draft and include it in the run result as a pending artifact
- Mark the run status as `awaiting_approval`

If auto-send is allowed for this category:
- Mark the draft as `approved` and include send instructions

### Step 6 — Output

Produce a structured run result containing:
- classification details
- draft reply (if any)
- approval status
- artifacts list
- execution metadata (timing, model used, token count)
