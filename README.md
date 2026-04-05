# Psilodigital Worker Stack (Hetzner / Coolify)

This stack gives you a practical base for:

- Paperclip as the control plane
- LiteLLM as the model gateway
- Agent Zero as a separate worker runtime
- a small `worker-gateway` service as the webhook target for Paperclip's HTTP adapter
- shared Postgres + Redis infrastructure

## Important caveat

This stack is **deployable**, but the `worker-gateway` is intentionally a **thin stub**, not a finished Paperclip-to-Agent-Zero bridge.

That is the correct place to add your custom logic for:

1. receiving Paperclip HTTP adapter wake events
2. deciding which worker to run
3. waking Agent Zero or your own worker orchestration
4. pushing status/results back into Paperclip

## Why the bridge exists

Paperclip's HTTP adapter is meant to POST to an external agent service. It sends execution context to that external runtime, which then processes the job and calls back to Paperclip. Agent Zero is a separate runtime/UI and is not, by itself, a documented drop-in Paperclip webhook target.

## Paperclip first boot

The Paperclip service in this compose file tries to bootstrap itself with:

```sh
paperclipai onboard --yes
```

on first start if no config exists under `/paperclip/instances/default/config.json`.

After the first successful boot, you should still review and harden the server configuration, especially for internet-facing deployment.

## Suggested production hardening steps

1. Keep `paperclip`, `litellm`, and your eventual dashboard on public domains.
2. Keep `postgres`, `redis`, and ideally `agentzero` internal-only.
3. In Coolify, attach domains only to:
   - Paperclip
   - LiteLLM
   - your branded dashboard (later)
4. After Paperclip starts, open a shell in the Paperclip container and run:

```sh
paperclipai configure --section server
```

Then move the instance to the proper authenticated/public configuration.

## Suggested Coolify domains

- `paperclip.yourdomain.com` -> Paperclip service, port 3100
- `llm.yourdomain.com` -> LiteLLM service, port 4000
- `workers.yourdomain.com` -> your dashboard later
- No public domain for Postgres / Redis / Agent Zero unless you specifically want one

## Paperclip HTTP adapter target

Inside Paperclip, configure an agent with adapter type `http` and point it to:

```txt
http://worker-gateway:8080/paperclip/wake
```

If you need to test from outside the Docker network, publish the worker-gateway port and use your host/domain.

## Copy to .env

```sh
cp .env.example .env
```

Then fill in your real secrets.

## Run locally

```sh
docker compose up --build
```

## Coolify notes

- Use Docker Compose build pack.
- Point Coolify to this compose file.
- Set all required environment variables in Coolify.
- Prefer pinning LiteLLM to an exact stable tag after your first successful test.
