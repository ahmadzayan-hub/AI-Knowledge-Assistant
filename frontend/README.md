# Local AI Assistant — Custom Frontend (React)

The mockup UI, live: a React single-page app in the project's design language
(dark `#0B0D14` ground, violet accent), pre-compiled to plain JS/CSS and wired
to the real local stack. **No Node.js is required on the Windows laptop** —
only to rebuild the bundle after an edit. Running it needs Python only.

```
Browser ── http://127.0.0.1:8090
             │  frontend/server.py  (Python stdlib, loopback-only)
             ├── static files: index.html, dist/bundle.js, dist/bundle.css
             ├── /owui/*    → Open WebUI  127.0.0.1:8080   (models, knowledge, RAG chat)
             ├── /ollama/*  → Ollama      127.0.0.1:11434  (version, loaded models)
             ├── /agent/run → agent.py — tool-using agent loop (see docs/15)
             └── /sys/stats → live RAM/CPU via PowerShell CIM
```

## Source layout

```
frontend/
  src/
    main.jsx                 entry point (createRoot)
    App.jsx                  top-level state: active view, API key, loaded data
    api.js                   fetch helpers — talks only to the loopback proxy
    useStatus.js              polls Ollama / Open WebUI / RAM+CPU every 7s
    styles.css                design tokens + component styles
    components/
      Sidebar.jsx             nav + live system-status card
      MobileNav.jsx           bottom tab bar on screens under 760px
      Home.jsx                stat cards, top knowledge bases, quick actions
      Chat.jsx                streaming chat, model + knowledge-base selectors
      Agent.jsx               tool-using agent + step-by-step trace (docs/15)
      KnowledgeBases.jsx      collections + per-collection file table
      Assistants.jsx          models/assistants published by Open WebUI
      Settings.jsx            API-key setup + live system info
  build/
    build.mjs                 esbuild config — bundles + minifies src/ → dist/
    build-demo.mjs             builds a SAMPLE-DATA bundle for public hosting (see below)
    mock-api.js                demo-only data layer (swapped in for src/api.js)
  dist/                       COMPILED OUTPUT — committed; this is what ships
    bundle.js, bundle.css
  index.html                  thin shell: <div id="root"> + <script src="/dist/bundle.js">
  server.py                   loopback proxy + static file server + /agent/run route
  agent.py                    tool-using agent loop (stdlib only) — see docs/15
  package.json                react, react-dom, esbuild (devDependency)
```

`dist/` is deliberately committed to the repo — the Windows laptop only runs
`server.py` and never needs Node. `node_modules/` is gitignored.

## Rebuilding after an edit

Requires Node.js (only on whichever machine you edit `src/` on — not required
to *run* the app):

```powershell
cd frontend
npm install     # first time only
npm run build   # writes dist/bundle.js + dist/bundle.css
```

## Features (live data, not samples)

- **Home** — knowledge base count, installed models, loaded-in-RAM models,
  free RAM; top knowledge bases; quick actions.
- **Chat** — streaming answers from any Open WebUI model; select a knowledge
  base to get RAG-grounded, citation-instructed answers (`files:[{type:
  "collection"}]`); Arabic/English with correct RTL (`dir="auto"` bubbles).
- **Knowledge Bases** — collections with document counts and per-collection
  file lists (name, date, size).
- **Agent** — a tool-using agent (search a knowledge base, read one named
  document, check the date, do math, and — opt-in only — search the web)
  that shows every tool call it makes before its final answer. Full design
  and security notes in `docs/15-agent-orchestration.md`.
- **Assistants** — every model/custom assistant published by Open WebUI.
- **Settings** — API key setup + connection test, live system info.
- **Sidebar status card** — Ollama/Open WebUI up-down dots, active model,
  RAM and CPU bars, refreshed every 7 s.

Document upload and knowledge-base administration deliberately stay in Open
WebUI (one backend of truth) — the "Open WebUI" quick action jumps there.

## Run (Gates 1–4 must already pass)

```powershell
# Stack up first:  .\scripts\start-ai.ps1
.\scripts\start-frontend.ps1        # starts server.py + opens the browser
```

First use: in Open WebUI go to **Settings → Account → API keys**, create a
key, paste it into the frontend's **Settings** view, Save & test. The key is
stored only in this browser's localStorage on this machine.

## Public demo build (sample data — never the real app)

The real app cannot be meaningfully hosted on Vercel/any public host: its API
calls (`/owui`, `/ollama`, `/agent/run`, `/sys/stats`) only resolve on
`127.0.0.1` of whichever machine runs `server.py` — that's the privacy
guarantee working as designed, not a gap to route around.

For a shareable preview instead, `build/build-demo.mjs` builds the *same*
components against `build/mock-api.js` (canned data, no network calls) into
`demo-dist/` — a plain static site with an unmissable amber "Demo — sample
data only" banner. Unlike `dist/`, `demo-dist/` is gitignored, not committed
— its only consumer is a static host that builds it fresh from source on
every deploy, so a checked-in copy would just be dead weight.

```powershell
cd frontend
node build/build-demo.mjs        # writes demo-dist/{index.html,bundle.js,bundle.css}
```

To deploy it (e.g. to Vercel): point the host at this repo's `frontend/`
directory with `installCommand: npm install`, `buildCommand: node
build/build-demo.mjs`, `outputDirectory: demo-dist`, framework auto-detection
off. No environment variables or secrets needed — it's fully static.

## Security posture

- `server.py` binds **127.0.0.1 only**; the proxy targets are loopback too.
- No external origins, no CDNs, no telemetry; React itself is bundled into
  `dist/bundle.js` at build time — nothing is fetched from a CDN at runtime.
- The API key never leaves the machine (browser → loopback proxy → Open WebUI).
- The Agent's `web_search` tool is the one deliberate exception — off by
  default, opt-in per session, clearly badged in the trace. See docs/15.
- Same rules as the rest of the kit (docs/08): no port forwarding, no tunnels.
