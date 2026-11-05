---
name: local-ai-tooling
description: Work on this repository's Ollama agent integration or evaluate the nine referenced open-source tools for a specific local AI workflow.
---

# Local AI tooling

This repository already uses Ollama and Open WebUI. Keep the existing local knowledge-library backend; a new catalog entry is not a reason to replace it.

- For the nine requested tools, read `docs/tooling/README.md` and the matching entry in `docs/tooling/upstreams.json`. Pins identify inspected upstream source, not installed or tested binaries.
- For agent-mode model readiness, inspect `frontend/agent.py` and `frontend/tests/`. Run `python -m unittest discover -s frontend/tests -v` from the repository root. Ordinary chat remains separate from tool-agent mode.
- Resource catalogs are references. Select and review one concrete example, service or MCP server only when a task needs it. Do not bulk-install catalog entries.
- OpenHands, Langflow, Scrapling and Open Design are optional separate runtimes, not dependencies of this application. Check fit, license, exact version, data destination and resource needs before proposing an integration.
- Keep local documents, credentials and operational reports out of Git. Use a separate branch for changes. Installing a runtime, downloading a model, configuring credentials or an MCP connection, merging and deploying remain distinct actions.
- Describe results precisely: reference recorded, code tested offline, runtime installed, service connected and real-machine acceptance verified are different states.

The same entrypoint is mirrored in `.agents/skills/local-ai-tooling/` and `.claude/skills/local-ai-tooling/` for project-level discovery. It is not an account-wide skill installation.
