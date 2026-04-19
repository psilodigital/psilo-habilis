# Security Policy

Security matters a lot in Habilis because the platform touches authentication,
tenant isolation, connector credentials, worker execution, and external tool
access.

## Supported Versions

At this stage, security fixes are applied to the latest code on `main`.

| Version | Supported |
| --- | --- |
| `main` | Yes |
| Older branches and unpublished snapshots | No |

## Reporting a Vulnerability

Please do not open a public GitHub issue for security problems.

Use one of these private paths instead:

1. GitHub private vulnerability reporting, if it is enabled for the repository.
2. The private contact method listed on the repository owner's GitHub profile.

Please include:

- A clear description of the issue
- Reproduction steps or a proof of concept
- Affected components or paths
- Impact assessment
- Any suggested mitigation, if you have one

## What to Expect

- We aim to acknowledge reports within 5 business days
- We will triage the report, reproduce it if possible, and decide on severity
- We may ask follow-up questions to validate the issue safely
- We will try to coordinate disclosure with a fix when appropriate

## Scope Examples

Examples of in-scope issues include:

- Authentication or authorization bypasses
- Tenant isolation failures
- Exposure of secrets, tokens, or connector credentials
- Remote code execution paths in gateway, dashboard, or service integrations
- SSRF, command injection, or privilege escalation
- Sensitive data leaks in logs, callbacks, or APIs

Out-of-scope examples usually include:

- Requests for general security advice
- Reports that require unrealistic local compromise assumptions
- Missing best-practice headers without an exploitable impact
- Vulnerabilities only present in unsupported forks or outdated branches
