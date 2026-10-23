# Agent Orchestration Layer

A tool-using agent built on top of the existing Ollama + Open WebUI stack —
the local, self-hosted equivalent of what Voiceflow/Botpress-style
"agent + RAG" builders do, without sending documents to a third-party cloud
platform (see `docs/01-system-readiness.md`'s validation of that Instagram
post: the pattern is legitimate, but those platforms are cloud SaaS).

This is a **post-Gate-10 enhancement**, per the master plan's Section 27/39
rule to only add capability once the base gates pass and a real need
justifies it — it does not replace or gate the base RAG assistant in
`docs/06-assistants.md`.

## Why "tool-using agent" over the alternatives

Two other shapes were considered and rejected for now:

- **Fixed multi-step prompt chains** — more predictable, but the model can't
  decide its own steps; doesn't fit "agent" in the sense the reference post
  used it.
- **Visual flow builder (Voiceflow/Botpress-style canvas)** — closest to the
  reference post, but a large build (canvas UI + flow engine + node
  library) that the project's own "do not overengineer" rule (Section 39)
  argues against building speculatively.

Tool-calling — the model decides when to call a small, fixed set of local
tools — gives real agentic behavior with a modest, auditable implementation:
one Python module (`frontend/agent.py`, ~250 lines, stdlib only) plus one
React screen.

## Architecture

```
Browser (Agent screen)
   │  POST /agent/run  {model, kbIds, allowWeb, messages}
   ▼
frontend/server.py (loopback proxy, unchanged transport)
   │  forwards the browser's Open WebUI API key
   ▼
frontend/agent.py  run_agent()
   │
   ├── POST {ollama}/api/chat  { model, messages, tools, stream:false }
   │     Ollama's native tool-calling (verified against ollama/ollama
   │     docs/api.md) — NOT Open WebUI's chat/completions endpoint, so the
   │     tool-call loop is fully under this module's control.
   │
   ├── search_knowledge_base → POST {owui}/api/v1/retrieval/query/collection
   │     body: {collection_names: kbIds, query, k}
   │     (verified: open-webui/open-webui backend/open_webui/routers/
   │      retrieval.py, QueryCollectionsForm)
   │
   ├── read_document → GET {owui}/api/v1/files/{id}/data/content → {content}
   │     (verified: backend/open_webui/routers/files.py)
   │
   ├── get_current_datetime, calculate → local, deterministic, no network
   │
   └── web_search → DuckDuckGo HTML endpoint, OPT-IN ONLY (see below)
```

No new vector database, no new embedding model, no new LLM server — the
tools call back into Open WebUI's own REST API, reusing the single existing
backend of truth (docs/00 Section "Do not over-engineer").

## The loop

`run_agent()` in `frontend/agent.py`:

1. Build a system prompt listing the available tools and the filenames in
   the selected knowledge base(s) (fetched once via `/api/v1/knowledge/`).
2. Call Ollama with the running message list + tool schema.
3. If the response has no `tool_calls`, that's the final answer — stop.
4. Otherwise check each requested tool against the run's dispatch allowlist,
   execute only permitted handlers, append a `{"role":"tool",
   "tool_name", "content"}` message per Ollama's documented format, and
   loop.
5. Hard cap: **6 steps.** If exceeded, the last content is returned with
   `truncated: true` — never a silent infinite loop, never a fabricated
   "done" (matches the project's "no silent caps" principle).

The full trace (every tool call, its arguments, and its result) is returned
to the browser and rendered as a step-by-step card list before the final
answer — more transparent than a black-box chat reply, and the closest
analogue to Voiceflow/Botpress's visible flow execution without building an
actual flow canvas.

## Tools

| Tool | What it does | Network |
|---|---|---|
| `search_knowledge_base` | RAG retrieval over the knowledge base(s) selected in the UI (the model cannot expand scope beyond what the user picked) | Local (Open WebUI) |
| `read_document` | Full extracted text of one named file, resolved by fuzzy filename match against the selected knowledge base(s) | Local (Open WebUI) |
| `get_current_datetime` | Current local date/time | None |
| `calculate` | Arithmetic via a restricted `ast`-based evaluator (`+ - * / // % **`, parentheses only — no names, no calls, so it cannot execute code) | None |
| `web_search` | DuckDuckGo HTML endpoint, no API key | **External — opt-in only** |

## `web_search` — the one tool that leaves the machine

This directly implements the **hybrid boundary** described in
`docs/08-security-privacy.md` and Section 38 of the master plan: private
work stays local by default, and any external route is a deliberate,
user-controlled exception — never automatic.

- **Off by default**, every session — the checkbox in the Agent screen is
  never remembered as "on".
- The system prompt tells the model explicitly whether `web_search` exists
  for this run; when it's off, the tool schema omits it. Model output is
  still untrusted: the dispatcher also omits the web-search handler unless
  `allow_web is True`, so a returned disallowed call cannot invoke it.
- `/agent/run` requires a JSON boolean for `allowWeb` (omitted means
  `false`); non-boolean values return HTTP 400. Direct Python callers also
  need exactly `True`, not a truthy string or integer. The permission is
  specific to each run and cannot carry over from an earlier run.
- Rejected web-search and unknown-tool calls produce a clear error in the
  trace and tool response, with `blocked: true` and `network: false`.
- Every permitted web-search invocation is tagged `network: true` and rendered with a
  visible amber "leaves this machine" badge in the trace — never blended
  in with local tool calls.
- Best-effort scrape of DuckDuckGo's dependency-free HTML endpoint
  (`class="result__a"` / `class="result__snippet"`, long-stable markup, no
  API key). If DuckDuckGo changes its markup this degrades to a clear "no
  results parsed" message returned to the model — never a crash, never a
  silently empty success presented as a real answer.
- Never send a confidential/private-collection query through this tool —
  the same judgment call as any other cloud escape hatch in this project.

## Security notes

- `search_knowledge_base` and `read_document` are hard-scoped to the
  `kbIds` the browser sent — the tool implementation filters by that list
  server-side, so a prompt-injected instruction inside a retrieved document
  cannot make the agent reach into a knowledge base the user didn't select.
- The Open WebUI API key is forwarded per-request from the browser's
  existing Settings-stored key (`frontend/README.md`) — `agent.py` never
  stores or logs it.
- `calculate`'s evaluator is AST-based and only permits numeric literals,
  the arithmetic operators, and parentheses — no `Name`, `Call`, or
  `Attribute` nodes are accepted, so it cannot be used to execute code
  regardless of what a malicious document or prompt injection asks for.
- All local tool traffic stays on `127.0.0.1` between `server.py`,
  Ollama, and Open WebUI, consistent with `docs/08-security-privacy.md`.

## Using it

Workspace → **Agent** in the frontend (`frontend/README.md`). Pick a
tool-capable model (qwen3 is confirmed to support tool calling), select the
knowledge base(s) it may search, leave "Allow web search" off unless you
explicitly need it, and ask a question. Each tool call appears as its own
card before the final answer.

## Offline permission regression tests

Run `python -m unittest discover -s frontend/tests -v` from the repository
root with Python 3.11 or 3.12. The standard-library tests use synthetic model
responses and mock every service/search call; real HTTP requests are blocked
and asserted absent. They cover disabled/enabled/unknown tool dispatch,
strict request booleans, per-run isolation and selected knowledge-base scope.
They do not validate live Ollama/Open WebUI APIs, Windows installation,
document retrieval quality or backup restoration.
