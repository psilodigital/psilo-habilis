# Third-Party Notices

Habilis integrates with and depends on several third-party projects and
services. This file is provided for attribution and operational clarity. It does
not replace or modify the terms of any upstream license.

Habilis itself is licensed under Apache-2.0. Third-party components retain
their own licenses and terms.

Last reviewed: 2026-04-19

## Foundational Open Source Components

### Paperclip

- Role in Habilis: control plane for orchestration, companies, tasks, budgets,
  and approvals
- Upstream project: <https://github.com/paperclipai/paperclip>
- Upstream license: MIT
- Upstream license file: <https://github.com/paperclipai/paperclip/blob/master/LICENSE>

### Agent Zero

- Role in Habilis: worker runtime and execution environment
- Upstream project: <https://github.com/agent0ai/agent-zero>
- Upstream license: MIT
- Upstream license file: <https://github.com/agent0ai/agent-zero/blob/main/LICENSE>

### LiteLLM

- Role in Habilis: unified model gateway and provider-agnostic routing layer
- Upstream project: <https://github.com/BerriAI/litellm>
- Upstream license: MIT for the open-source portions of the repository
- Upstream license file: <https://github.com/BerriAI/litellm/blob/main/LICENSE>
- Important note: LiteLLM's license states that content under `enterprise/`, if
  present, is licensed separately. Habilis should only assume MIT coverage for
  the open-source portions of LiteLLM.

## External Provider And Service Terms

Some Habilis workflows may call third-party hosted APIs and services that are
not covered by the open-source licenses above. Their use is governed by each
provider's own terms, policies, and acceptable use rules.

Examples include:

- OpenAI
- Anthropic
- Google AI / Gmail / Google APIs
- Groq
- OpenRouter

Using Habilis with any of these services does not transfer or replace those
providers' terms.

## Redistribution Guidance

At present, Habilis integrates these systems primarily as separate services and
upstream images rather than by vendoring large portions of their source code
into this repository.

If Habilis later vendors, copies, or redistributes modified upstream code, keep
the relevant upstream copyright and license notices with those copied portions
and review any additional obligations before release.

## Trademark Note

Project names such as Paperclip, Agent Zero, LiteLLM, OpenAI, Anthropic, Google,
Groq, and OpenRouter are trademarks or product names of their respective owners.
This file uses those names only to describe compatibility and integration.
