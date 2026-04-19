# Contributing to Habilis

Thanks for taking the time to contribute. Habilis is still early, so focused pull requests, clear context, and good docs help a lot.

## Ways to contribute

- Report reproducible bugs
- Improve setup and troubleshooting docs
- Add tests around existing behavior
- Propose small, incremental product or infrastructure improvements
- Fix typos, naming issues, and developer experience rough edges

## Before you start

- Search existing issues and pull requests before opening a new one
- Open an issue before starting larger features, architecture shifts, or breaking changes
- Keep each pull request scoped to a single problem when possible
- Follow the existing architecture docs so changes stay aligned with the project direction

Start with:

- [`README.md`](README.md)
- [`docs/mission.md`](docs/mission.md)
- [`docs/decisions.md`](docs/decisions.md)
- [`docs/local-dev.md`](docs/local-dev.md)

## Local setup

1. Fork the repository and clone your fork.
2. Install JavaScript dependencies:

   ```sh
   pnpm install
   ```

3. Generate local environment variables:

   ```sh
   make setup
   ```

4. Add at least one provider API key to `.env`.
5. Install Python test dependencies for the gateway:

   ```sh
   python -m pip install -r apps/worker-gateway/requirements-dev.txt
   ```

6. Start the local stack when your change needs running services:

   ```sh
   make build
   make status
   ```

## Development workflow

- Branch from `main`
- Use a descriptive branch name such as `fix/gateway-timeout`, `feat/gmail-sync`, or `docs/quickstart`
- Prefer small, reviewable commits with clear messages
- Avoid unrelated refactors in the same pull request
- Update docs when behavior, configuration, or setup changes
- Add or update tests when changing logic
- For material architecture decisions, add a new ADR entry to `docs/decisions.md`

## Validation

Run the checks that match your change. At minimum, run the relevant subset below before opening a pull request:

```sh
make validate
make test-gateway
make test-types
pnpm turbo run typecheck
pnpm --dir apps/dashboard lint
```

If your change affects Docker, multi-service flows, or environment wiring, also run:

```sh
make test
```

## Pull request expectations

Please include:

- A short explanation of what changed and why
- A linked issue when one exists
- Testing notes describing what you ran
- Screenshots or request/response examples for UI or API changes
- Any follow-up work that remains out of scope

Use the pull request template and keep the checklist honest. If a box does not apply, say why.

## Review process

- Maintainer approval is required before merge
- Maintainers may ask for scope reduction if a pull request mixes too many concerns
- Priority goes to changes that improve reliability, observability, safety, developer experience, and documentation

## Licensing

By submitting a contribution, you agree that your work will be licensed under the repository's Apache-2.0 license.

## Security

Please do not open public issues for vulnerabilities. Follow [`SECURITY.md`](SECURITY.md).
