# Open-source tools for the local AI assistant

This is the first repository-scoped adoption step for the nine requested tools. The current application already talks to Ollama. The concrete code change in this branch checks whether the selected model is ready for tool-agent mode before reading knowledge-library metadata. The accompanying skills and catalog make the other tools discoverable without adding unused dependencies.

## What is included

- Project skills for Codex-compatible discovery at `.agents/skills/local-ai-tooling/SKILL.md` and Claude Code discovery at `.claude/skills/local-ai-tooling/SKILL.md`.
- [Pinned upstream inventory](upstreams.json): canonical repositories, source commits, release tags where available, licenses and focused runtime/security notes.
- Offline tests for the Ollama preflight and existing per-run web-search permissions.

Checkout of the branch makes the project files available to clients that support those skill paths. No account-wide Claude/ChatGPT skill, MCP connection, provider account, software binary or model was installed by these files.

## Use each tool where it fits

| Item | Role here | Adoption state |
| --- | --- | --- |
| Ollama | Existing local chat and tool-agent model runtime | Agent-mode readiness check added; Windows runtime acceptance still pending |
| OpenHands | Optional coding workspace for an isolated checkout | Reference only; do not give unrestricted host access |
| Langflow | Optional visual flow prototyping in a separate environment | Reference only; no replacement for existing retrieval backend |
| Awesome LLM Apps | Source examples for a specific later feature | Reference only; inspect individual examples and licenses |
| Scrapling | Optional public-web extraction when a defined task needs it | Reference only; no scraping or MCP server enabled |
| free-for-dev | Discovery of hosting/developer service options | Links only; no account or subscription created |
| Open Design | Optional design workspace for a separate design task | Reference only; no provider or MCP configuration |
| Awesome MCP Servers | Discover individual MCP implementations | Reference only; each server needs its own access review |
| Public APIs | Discover an API for a specific use case | Reference only; no API credentials or data sharing |

## Ollama acceptance

Run `python -m unittest discover -s frontend/tests -v` for offline regression tests. These use mocked transport and synthetic model responses; they do not establish a working runtime.

On the intended computer, after the existing Windows setup gates:

1. Confirm Ollama listens only on loopback and record its actual version. The inventory version is an inspected upstream release, not a claim that the computer runs it.
2. Select an already installed local model with tool support and try Agent mode. Confirm unsupported or missing models return a clear error before library metadata is requested.
3. Check ordinary Chat separately, including a model without tool support; ordinary Chat is unchanged.
4. Exercise a permitted synthetic library and verify citations. Keep web search off unless explicitly needed.
5. Record restart, privacy and backup/restore results in a local report, outside this public repository.

Ollama can serve cloud-backed models even through a loopback API. Explicit remote model metadata is refused in the local tool-agent preflight. Also use Ollama's documented local-only setting, `OLLAMA_NO_CLOUD=1`, when configuring the runtime. This code check is not a whole-system network audit.

## Pin and license boundaries

The catalog pins source snapshots. It is not a dependency lockfile, binary checksum list or vulnerability audit. No upstream source is vendored. Recheck release notes and advisories before executing or upgrading any runtime; model licenses are separate from the Ollama code license.

At review time, free-for-dev had no root LICENSE and GitHub's license metadata was null. Keep it as a link, not content to redistribute under an assumed license. Catalog licenses do not grant rights to every listed service, server or template.

OpenHands' current repository describes Agent Canvas; old installation tutorials may no longer apply. Open Design is specifically `nexu-io/open-design`, matching the supplied source. These tools run agents or flows and should remain isolated from private libraries until their data paths and permissions are explicitly configured.

## بالعربية

أُضيفت مهارة على مستوى هذا المشروع لـ Claude Code وCodex، مع سجل روابط وإصدارات مرجعية للأدوات التسع. التغيير البرمجي يراجع جاهزية نموذج Ollama لوضع الوكيل قبل قراءة بيانات مكتبات المستندات. هذا لا يعني تثبيت البرامج على جهازك أو إنشاء اتصالات خارجية؛ تلك خطوات منفصلة تحتاج جهاز التشغيل واختباراً فعلياً.
