# Local AI Assistant: setup and acceptance guide

[Back to the README](../README.md)

Setup review baseline: `df4e30cf74617410cc4d707f0de9c36e25bb9f24`. This revision adds a server-side web-search guard and offline regression tests. Commands below are checked against the repository; Windows setup, model downloads and live application acceptance tests were not run.

## Choose the real local path

The real product consists of Ollama, Open WebUI and the Python-served React frontend on the same computer. Use the current default branch, `claude/local-ai-windows-setup-yv2ekh`; do not assume an unrelated `main` branch is the installation source.

Requirements reflected in the scripts:

- Windows 11 and PowerShell, with resources assessed before selecting a model.
- Python 3.11 or 3.12 for the current installer check; the Open WebUI launch command specifically selects Python 3.12.
- Ollama and the selected model downloaded before a fully local inference session.
- Open WebUI configured with a local account and knowledge collection.
- Node.js/npm only when rebuilding the React source. The committed bundle can otherwise run under Python.

Package/model installation needs network access and disk space. “Local inference” does not mean a first installation works without downloads.

## Staged setup, not one blind command

Run each step from the repository root only after reviewing the preceding gate and the script itself:

```powershell
.\scripts\00-audit.ps1
.\scripts\02-install-ollama.ps1
ollama pull qwen3:4b
.\scripts\03-benchmark.ps1 -Model qwen3:4b
.\scripts\04-install-openwebui.ps1
```

`qwen3:4b` is the existing kit's starting example, not a measured recommendation for every computer. See [model strategy](02-model-strategy.md). The Open WebUI installer starts a new PowerShell process and uses `open-webui@latest`; confirm a compatible version before relying on repeatable setup. The script's launch message does not prove account creation, security settings or ingestion have completed.

Follow the existing [Open WebUI setup checklist](03-openwebui-deployment.md): create the local administrator account, review registration settings, verify model availability and persistence, then configure the embedding model before importing documents. Do not import confidential libraries merely to test that a page loads.

## Launch and operate

```powershell
.\scripts\start-ai.ps1
.\scripts\status.ps1
.\scripts\start-frontend.ps1
```

Expected local endpoints are Ollama on `127.0.0.1:11434`, Open WebUI on `127.0.0.1:8080`, and the custom frontend on `127.0.0.1:8090`. A red service status means the UI is not connected; it is not a reason to substitute sample results.

The frontend proxies `/owui/*`, `/ollama/*`, `/agent/run` and `/sys/stats` through [server.py](../frontend/server.py). Keep both backend URL overrides pointed to trusted loopback services. System statistics use Windows PowerShell; another OS may show unavailable values even if the HTML loads.

For normal shutdown and backup, review and use the existing operating scripts:

```powershell
.\scripts\stop-ai.ps1
.\scripts\backup.ps1
```

Follow [backup/update guidance](11-backup-updates.md) for sequencing. A completed archive is not a proven restore: test restoration into an isolated location before relying on it.

## Privacy boundaries that need verification

- Loopback binding avoids ordinary remote network exposure; it is not a substitute for account security or trust in local applications/browser extensions.
- Open WebUI authentication remains necessary. The frontend stores an API key in localStorage; avoid shared browser profiles and never publish or screenshot it.
- Do not override local backend URLs with cloud destinations or add a public tunnel as an installation workaround.
- [agent.py](../frontend/agent.py) enforces web-search permission in the execution dispatch map, not only the prompt/schema. With web search disabled, even a model-returned `web_search` call is rejected without invoking its handler. Unknown tools are rejected too. The trace records `blocked: true` and `network: false` for rejected calls.
- `/agent/run` accepts `allowWeb` only as a JSON boolean; omitted means `false`, while strings, numbers, arrays, objects and `null` return HTTP 400. Direct Python callers must pass exactly `True` to enable web search. Permission is rebuilt separately for every run.
- Optional web search uses an external search service. A model-generated query may contain private context; enabled use needs a deliberate data-sharing decision. The guard does not audit other applications, service configuration or every possible network route.
- Source-grounding prompts are instructions, not a proof that every answer or citation is correct. Test unsupported and multilingual questions with known reference answers.

These boundaries take precedence over broader “private by design” or “opt-in only” claims in older design prose.

## Check the tool-permission boundary offline

From the repository root with Python 3.11 or 3.12:

```powershell
python -m unittest discover -s frontend/tests -v
```

The standard-library suite in [test_agent_permissions.py](../frontend/tests/test_agent_permissions.py) mocks model/Open WebUI traffic and the web-search handler, blocks real HTTP requests, and needs no installed frontend packages or live services. It verifies disabled search never invokes the handler, an enabled invocation calls a stub exactly once, malformed opt-ins cannot enable search, unknown tools are denied and knowledge-base search/document reading retain the selected scope.

These are focused unit tests, not live retrieval validation or a Windows installer/backup test. No CI workflow is committed. After setup gates pass, verify the actual Agent checkbox and trace on the intended computer using only permitted test material; offline mocks do not certify model or provider compatibility.

## Public preview is not the local product

The existing [demo builder](../frontend/build/build-demo.mjs) replaces the API layer with canned data and creates `frontend/demo-dist/`. It retains a visible sample-data banner. It does not expose or connect a visitor to the local Python server.

From `frontend/`, after installing build dependencies:

```powershell
node build/build-demo.mjs
```

For a static host, the existing preview workflow uses `frontend/` as its root, that command as its build, and `demo-dist` as output. Preserve the banner and keep private files out of the build. Do not relabel it as a full working cloud edition. The normal `npm run build` remains the real local bundle and writes `dist/` instead.

## Acceptance before a real-data rollout

- [ ] A tested Open WebUI/model combination is recorded and repeatable; `latest` drift is addressed.
- [ ] All services remain on loopback, with approved local account/registration settings.
- [ ] One permitted document is indexed and retrieved with traceable sources.
- [ ] Unsupported questions are handled honestly in Arabic and English.
- [ ] Model latency and memory use are measured on the intended computer.
- [x] Server-side tool permissions reject model-requested disallowed tools in offline regression tests.
- [ ] The Agent checkbox and trace are verified against the intended local model/services with permitted test material.
- [ ] Browser credentials, documents, reports and backups are protected and excluded from publication.
- [ ] A shutdown/restart and isolated backup restore preserve the intended libraries and history.

Keep the existing source, committed real bundle and staged documentation intact while closing these acceptance gaps.
