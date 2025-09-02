perfect --- I've got enough to feed Claude Code. Below are ready-to-paste prompts (short, surgical) that will make Claude scaffold the repo, wire the OpenAI Agents SDK (Python), add **WebSearch + FileSearch + Computer Use**, stub **Airtable** integration, and set you up to deploy the agent API on **Render** (computer-use runtime local for now; you can move it to a hardened VM later).

Use them in order. Don't edit---just paste each into Claude Code and let it do the work.

* * * * *

**Prompt 1 --- Project scaffold (repo, deps, files, env)**
========================================================

**Paste to Claude Code:**

```
You are my build copilot. Create a Python project called `operator_agent`.
Goals:
- OpenAI Agents SDK (responses API) with WebSearch, FileSearch (Vector Stores), and Computer Use.
- Minimal FastAPI wrapper so I can `POST /run` with a task and get result.
- Local dev uses .env for secrets. Render deploy uses environment variables.

Tasks:
1) Project structure:
operator_agent/
  app/main.py
  app/agents.py
  app/tools/airtable_tool.py
  app/vectorstore_setup.py
  app/settings.py
  requirements.txt
  README.md
  .env.example
  render.yaml
  Makefile
  .gitignore

2) requirements.txt:
openai>=1.40.0
openai-agents>=0.1.0
fastapi
uvicorn[standard]
pydantic
python-dotenv
httpx
playwright
Pillow

3) .gitignore standard Python, venv, .env

4) .env.example with:
OPENAI_API_KEY=
OPENAI_VECTOR_STORE_ID=   # optional, can be filled after create
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
AIRTABLE_TABLE_NAME=TestTable

5) app/settings.py:
- load env vars via dotenv if present
- dataclass/settings object exposing the above vars

6) app/agents.py:
- build two Agents SDK agents:
  a) TriageAgent: instructions = "Decide whether to answer via search/RAG or hand off to BrowserAgent for on-screen work." tools=[WebSearchTool(), FileSearchTool(vector_store_ids from env)]
  b) BrowserAgent: instructions = "You can use the computer to operate the browser. Explain plan briefly, then act." tools=[ComputerTool(), WebSearchTool(), FileSearchTool(...)]
- add basic guardrail: ComputerTool configured with max_actions_per_run=40 and high_risk_operations_enabled=False
- add MCP filesystem server (stdio) pointing to `./sandbox` and allowlist only read_file/write_file
- wire a simple handoff from TriageAgent → BrowserAgent
- export an async function `run_agent(task_text: str)` that runs TriageAgent with the input and returns the final output text (plus a simple dict of tool_calls made)

7) app/main.py:
- FastAPI app with POST /run { "task": "..." }
- calls run_agent and returns JSON { result, steps_summary }

8) app/tools/airtable_tool.py:
- Provide a simple *function tool* (not MCP yet): `upsert_airtable_record(payload: dict)` using Airtable REST API (Authorization: Bearer, base, table)
- Make it optional: if env vars missing, the tool no-ops with a clear message.
- Expose a helper to register this tool on a given Agent when the env is set.

9) app/vectorstore_setup.py:
- Script `python -m app.vectorstore_setup` that:
  - Creates a Vector Store using OpenAI Vector Stores API
  - Uploads a couple tiny test docs from a new `./sandbox/docs/` folder (create and write 2 small .md files)
  - Prints the created Vector Store ID to console
- Don't hardcode private keys; read from env.

10) render.yaml:
- Define a single web service:
  name: operator-agent-api
  type: web
  env: docker
  plan: starter
  autoDeploy: true
  dockerCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  envVars: OPENAI_API_KEY, OPENAI_VECTOR_STORE_ID, AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME (as FromService or plain)
- We'll keep the Computer Use runtime local for now (safer). Render hosts only the API.

11) Dockerfile (at repo root):
- Python 3.11 slim
- install system deps for Playwright (even if local runtime elsewhere), then `pip install -r requirements.txt`
- default CMD same as render.yaml

12) Makefile:
- targets:
  - setup: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
  - run: uvicorn app.main:app --reload
  - vectorstore: python -m app.vectorstore_setup

13) README.md (concise):
- local dev steps: `make setup`, create `.env`, `make run`
- how to create vector store: `make vectorstore` then put id into OPENAI_VECTOR_STORE_ID
- how to try: curl POST /run with a task
- note: computer-use runtime is separate (see next prompt); for now the BrowserAgent will attempt to use it when configured.

Create all files with clean, working code. Keep docstrings and comments minimal and practical.
```

* * * * *

**Prompt 2 --- Computer Use runtime (local) + dev test**
======================================================

**Paste to Claude Code:**

```
Now add the local Computer Use runtime.

Goal:
- Use OpenAI Computer Use sample runtime pattern (Playwright + screenshots) but keep it embedded here as a lightweight dev runner.
- Provide a simple CLI `python -m app.computer_runtime` that:
  - Launches a Chromium instance via Playwright
  - Exposes a small loop that listens for actions from the Agents SDK tool (if SDK offers a local connector) OR provides a minimal "action executor" that the ComputerTool can call. If the SDK expects us to run a sidecar, create a small HTTP bridge on localhost:34115 that accepts JSON {action,...}, runs it in the browser, takes a screenshot, returns next state.
  - Safety: disallow navigation to domains outside a small allowlist we keep in code: ["patagonia.com","google.com","duckduckgo.com","amazon.co.jp","amazon.com"] and block form submits by default.

Changes:
1) Create `app/computer_runtime.py` with the HTTP bridge described above (FastAPI is fine).
2) In `app/agents.py`, configure ComputerTool to target this local bridge (http://127.0.0.1:34115) and document where to tweak the allowlist.
3) Add a Makefile target `computer`: `python -m app.computer_runtime`
4) Update README with a "Computer Use Dev" section:
   - Run terminal 1: `make computer` (starts headful browser + executor)
   - Run terminal 2: `make run`
   - Test: POST /run with: "Find a black Patagonia jacket in Tokyo I'd like, show options, then use the computer to open the best page and add to cart (stop before purchase)."

Implement defensively: timeouts, max steps, and log each action to stdout. Keep code compact and clear.
```

* * * * *

**Prompt 3 --- Vector Store seed + Airtable tool smoke test**
===========================================================

**Paste to Claude Code:**

```
Wire up two small test docs and a smoke test for FileSearch + Airtable.

Tasks:
1) Under `sandbox/docs/`, create:
   - `patagonia_notes.md` with 10 short lines of jacket notes
   - `tokyo_shops.md` with 5 dummy shop entries (Shibuya/Harajuku/Shinjuku)

2) Ensure `app/vectorstore_setup.py` uploads those and prints the vector store ID.

3) Add a small dev script `python -m app.smoke` that:
   - Ensures OPENAI_VECTOR_STORE_ID is set
   - Calls run_agent("Summarize key jacket preferences from our docs, and list three Tokyo neighborhoods to shop.")
   - If AIRTABLE_* envs are present, call `upsert_airtable_record({"run":"smoke","status":"ok","ts":...})` and print the Airtable response; otherwise print "(Airtable disabled)".

4) README: add a "Smoke Test" section:
   - `make vectorstore` → copy printed ID to .env as OPENAI_VECTOR_STORE_ID
   - `python -m app.smoke`
```

* * * * *

**Prompt 4 --- Render deploy**
============================

**Paste to Claude Code:**

```
Prepare for Render deploy.

Tasks:
1) Confirm Dockerfile works on Render: use PORT env; ensure Playwright install isn't required for the API container (we only need API on Render).
   - If Playwright add-ons slow the image, gate them behind a build ARG `INSTALL_PLAYWRIGHT=false` and default false.
2) Ensure `render.yaml` points to this Dockerfile and command. Include health check: GET /docs should return 200.
3) Add a `/healthz` route in FastAPI returning {"ok":true}.
4) README: "Deploy to Render" steps: push to GitHub → connect → set env vars → deploy. Note: computer-use runtime remains local or in a separate hardened VM for now.
```

* * * * *

**Prompt 5 --- "Run check" & test task**
======================================

**Paste to Claude Code:**

```
Do a final run check.

1) Validate imports and types across the codebase.
2) Generate a short list of curl commands:
   - curl -X POST http://127.0.0.1:8000/run -H "content-type: application/json" -d '{"task":"Find a black Patagonia jacket in Tokyo I'd like, show options, then open the best page and stop before purchase."}'
   - curl -X POST http://127.0.0.1:8000/run -H "content-type: application/json" -d '{"task":"Summarize our local docs and log a smoke record to Airtable if configured."}'
3) Print instructions for starting both processes:
   - Terminal A: `make computer`
   - Terminal B: `make run`
4) Ensure the result JSON includes a simple steps summary (tool calls performed + any handoff) and a final answer.
Return only the final checklist and the curl examples.
```

* * * * *

**Notes & next steps (from me)**
--------------------------------

-   **Airtable via MCP**: once you've proven the flow, we can swap the function tool for an **MCP server** that exposes get_table, insert_record, update_record using Airtable's REST. For the MVP, the function tool is simpler and unblocks you.

-   **Render + Computer Use**: keep the **computer runtime** local (or a separate VM) until you're happy with allowlists and auditing. When ready, we'll containerize it and lock it down (no credentials, DNS allowlist, record sessions).

-   **HIPAA** later: add PHI redaction on any web/file search, rotate logs to a secure sink, and move to BAA-covered infra.

If you want, I can also give you a **single mega-prompt** that tells Claude to execute Prompts 1--5 sequentially; but running them step-by-step makes it easier to catch issues fast.