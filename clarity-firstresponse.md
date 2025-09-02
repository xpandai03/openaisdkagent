nice---this is super actionable. i'll give you a **single, streamlined mega-prompt** for Claude Code that bakes in all of Claude's notes:

-   exact Computer Use integration (stub first, live later)

-   auto-create Vector Store on startup (no chicken-egg)

-   MCP optional with safe fallback if npm missing

-   Airtable tool actually wired to the agent (gated by env)

-   error handling + sane defaults so it runs immediately

-   one FastAPI endpoint /run + healthz

-   30-min build flow (Phase 1→4) inside one prompt

copy--paste this into Claude Code as-is.

* * * * *

**CLAUDE CODE MEGA PROMPT --- "operator-style agent MVP (Python)"**
=================================================================

You are my build copilot. Create a working Python repo I can run **immediately** with no manual pre-steps. It must compile and run in one shot.

**Goals**
---------

-   OpenAI **Agents SDK** (Python) using **Responses API**.

-   Tools: **WebSearch**, **FileSearch (RAG via Vector Stores)**, **Computer Use**.

-   **Single agent** first (WebSearch only), then **incrementally enable FileSearch + Computer Use**.

-   **Airtable** function tool (optional; wire it if env present).

-   **MCP** filesystem server (optional; skip cleanly if npm missing).

-   **Auto vector store creation** on first run with small inline test docs.

-   **Computer Use stub** (mock screenshots + action log) first; switchable to "live" later.

-   **FastAPI** API: POST /run + /healthz.

-   **Errors handled**: missing env, failed tool connections, npm missing.

-   **Render/Docker** files included but secondary; local run must succeed without them.

**Project layout**
------------------

```
operator_agent/
  app/
    __init__.py
    settings.py
    agents.py
    main.py
    tools/
      airtable_tool.py
    runtimes/
      computer_stub.py
      computer_live_bridge.py   # (scaffold only; clear TODOs)
    startup/
      vectorstore_bootstrap.py
  tests/
    test_smoke.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  Makefile
  render.yaml
  Dockerfile
```

**Dependencies**
----------------

requirements.txt:

```
openai>=1.40.0
openai-agents>=0.1.0
fastapi
uvicorn[standard]
pydantic
python-dotenv
httpx
Pillow
```

(Do **not** include Playwright; we'll keep "live" computer mode scaffolded only.)

**Settings & Defaults**
-----------------------

-   .env.example keys (all optional with sane defaults):

    -   OPENAI_API_KEY=

    -   OPENAI_VECTOR_STORE_ID= # if empty, auto-create on first run and persist to .state

    -   AIRTABLE_API_KEY=

    -   AIRTABLE_BASE_ID=

    -   AIRTABLE_TABLE_NAME=TestTable

    -   COMPUTER_MODE=MOCK # MOCK | LIVE

    -   COMPUTER_BRIDGE_URL=http://127.0.0.1:34115 # used in LIVE mode only

-   app/settings.py: load env via dotenv; expose a Settings object; create a local .state/operator_agent.json file to persist the created vector store id if not set.

**Phase 1 --- Core scaffold & health**
------------------------------------

-   main.py: FastAPI app with:

    -   POST /run -> JSON {task: str} → returns {result, steps, mode_flags}.

    -   GET /healthz -> {"ok": true} and includes flags {websearch:bool, filesearch:bool, computer:"MOCK"|"LIVE"}.

    -   GET /docs enabled.

-   Implement **WebSearch only** at first so POST /run always returns something.

-   Add tests/test_smoke.py that hits /healthz then /run with a trivial query.

**Phase 2 --- Vector Store (auto)**
---------------------------------

-   startup/vectorstore_bootstrap.py:

    -   On import (safely), if OPENAI_VECTOR_STORE_ID is empty and OPENAI_API_KEY present, auto-create a Vector Store and upload **two tiny in-memory docs** (strings), e.g.:

        -   patagonia_notes.md → 8--10 bullet lines

        -   tokyo_shops.md → 5 short entries

    -   Persist the new store id in .state/operator_agent.json; use it thereafter.

    -   If API key missing or creation fails, **gracefully disable FileSearch**, but app still runs.

-   agents.py should read the persisted id at startup if env var is blank.

**Phase 3 --- Agent & Tools**
---------------------------

-   agents.py:

    -   Build **one Agent** with:

        -   instructions: short; "Use WebSearch/FileSearch. If the task mentions 'open', 'click', 'type', or 'add to cart', use Computer."

        -   tools:

            -   WebSearchTool() (always on)

            -   FileSearchTool(vector_store_ids=[resolved_id]) (only if id available)

            -   ComputerTool(config) (always present, but it will internally no-op in MOCK mode)

        -   **Airtable tool** (function tool) registered **only if** AIRTABLE_* present. Give it a clear name: upsert_airtable_record(payload: object).

    -   Provide async def run_agent(task_text: str) -> dict returning:

        -   final_text

        -   tool_calls (compact list of {name, ok|error, summary})

        -   used_file_search: bool

        -   computer_mode: "MOCK"|"LIVE"

-   **MCP filesystem server (stdio)**:

    -   Try to start npx -y @modelcontextprotocol/server-filesystem ./sandbox at startup.

    -   If Node/npm not found or start fails, **skip** MCP with a warning; do not crash.

    -   Allowlist only read_file and write_file.

    -   MCP is optional and not used in the main happy path; just demonstrate registration.

**Phase 4 --- Computer Use Integration (clear contract)**
-------------------------------------------------------

-   We'll implement **MOCK first**:

    -   runtimes/computer_stub.py exposes a tiny executor the ComputerTool will call via an **internal Python adapter** (no HTTP). Given an action (click, type, navigate, etc.), it:

        -   logs the action to stdout,

        -   returns a fake "screenshot" PNG generated with Pillow (simple 1024×640 image with text overlay of the action),

        -   and a small JSON state ({"url":"mock://...","notes":["..."]}).

    -   This ensures ComputerTool actions **always succeed** in MOCK mode without Playwright/Chrome.

-   **LIVE scaffold**:

    -   runtimes/computer_live_bridge.py: implement a **FastAPI HTTP bridge** with endpoints:

        -   POST /action {type, selector?, text?, url?} -> executes against a headful browser (TODO); for now, return 501 "not implemented".

        -   GET /screenshot -> returns a stub PNG (same as MOCK) until you wire a real browser.

    -   In agents.py, when COMPUTER_MODE=LIVE, the ComputerTool should **post** actions to COMPUTER_BRIDGE_URL and fetch /screenshot each step; on any failure, degrade gracefully and log a tool error.

**Airtable tool (actually wired)**
----------------------------------

-   tools/airtable_tool.py:

    -   Implement upsert_airtable_record(payload: dict) using Airtable REST.

    -   Register it on the agent **only when** all three env vars present.

    -   On error (network, 4xx), return a **friendly message** and mark the tool call as error but **do not** crash the run.

**Error handling (explicit)**
-----------------------------

-   If OPENAI_API_KEY missing → WebSearch and FileSearch are disabled; /run still returns a deterministic local answer explaining tools are in "demo disabled" mode.

-   If Vector Store creation fails → log and continue with WebSearch only.

-   If MCP fails to start → log and continue.

-   If Computer in LIVE mode can't reach bridge → log, mark tool error, continue answering with WebSearch/RAG.

**FastAPI**
-----------

-   POST /run accepts {"task": "..."}, calls run_agent, returns {result, steps, mode_flags}.

-   GET /healthz returns:

```
{
  "ok": true,
  "websearch": true|false,
  "filesearch": true|false,
  "computer": "MOCK"|"LIVE",
  "airtable": true|false,
  "mcp": true|false
}
```

**Makefile**
------------

Targets:

-   setup: create venv, install deps

-   run: start API (uvicorn app.main:app --reload)

-   smoke: curl /healthz and a sample /run

-   mcp: attempt to run the MCP filesystem server (if needed later)

-   (no Playwright targets)

**README.md**
-------------

Short, step-by-step:

1.  make setup

2.  copy .env.example → .env, set OPENAI_API_KEY if you have one; otherwise the app runs with tools limited.

3.  make run

4.  test:

```
curl -s -X POST http://127.0.0.1:8000/run\
  -H "content-type: application/json"\
  -d '{"task":"Summarize our jacket notes and suggest 2 Tokyo areas to shop."}' | jq

curl -s -X POST http://127.0.0.1:8000/run\
  -H "content-type: application/json"\
  -d '{"task":"Open a jacket site and add to cart (stop before purchase)."}' | jq
```

-   explain MOCK vs LIVE and how to flip COMPUTER_MODE.

-   note that LIVE bridge is scaffolded only (returns 501) and can be wired later.

-   optional section: set Airtable env vars to enable the tool.

-   optional: MCP may be skipped if npm missing.

**Render + Docker (secondary)**
-------------------------------

-   include render.yaml + Dockerfile:

    -   Dockerfile: python:3.11-slim, install deps, expose $PORT, run uvicorn

    -   render.yaml: basic web service using the Dockerfile; health check /healthz

-   but **do not** require these to run locally.

**Implementation details & quality bars**
-----------------------------------------

-   Keep code tight; type hints where helpful.

-   Log each tool call into a compact steps array (name, ok/error, message).

-   For FileSearch: show how vector_store_ids=[id] is threaded; if id missing, disable the tool.

-   For ComputerTool: implement a thin adapter object that, when in MOCK, calls computer_stub; when in LIVE, posts to the bridge. Give the tool a conservative max_actions_per_run=30.

-   Unit test test_smoke.py should assert /healthz keys exist and /run returns result and steps.

Create all files now with **working code**. Return a short "HOW TO RUN" checklist at the end.

* * * * *

**Quick confirmations for you (answer only if you want to tweak defaults)**
---------------------------------------------------------------------------

-   Keep **COMPUTER_MODE=MOCK** default? (I set it to MOCK.)

-   Ok with storing the created Vector Store id in .state/operator_agent.json?

-   Airtable table name default "TestTable" fine?

if you want me to also generate a follow-up **"LIVE bridge" prompt** (Playwright + Chromium + selectors + allowlist + screenshot loop), say the word and I'll drop that next.