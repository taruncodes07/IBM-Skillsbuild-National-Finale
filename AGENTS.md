# Grid Trace — Agent Instructions

> **Scope:** This file documents the architecture, commands, conventions, and
> hard boundaries for AI-assisted work on the Grid Trace repository.
> Configuration work recorded in this file was performed in the current
> session; it does not backdate or attribute any earlier development work to
> an AI agent.

---

## Repository layout

```
Grid trace/              ← workspace root (this file lives here)
├── app/                 ← all runnable source
│   ├── backend/         ← Python FastAPI + analytics + LangGraph workflow
│   ├── frontend/        ← React 19 + TypeScript + Three.js
│   ├── tests/           ← pytest backend suite + Node client tests
│   ├── docs/            ← build status, evaluation results, QA reports
│   ├── data/            ← runtime SQLite + evidence PNGs (gitignored, keep .gitkeep)
│   ├── scenarios.json   ← scenario calibration seeds
│   ├── requirements.txt / requirements.lock.txt
│   └── package.json
├── AGENTS.md            ← this file
├── edge-case-hardening-plan.md
├── GRID_TRACE_BUILD_PLAN.md
├── VIDYUT_TRACE_FINAL_PRD.pdf
└── README.md
```

---

## Setup and build

All commands run from `app/` unless noted.

### First-time setup (Windows PowerShell)

```powershell
# From workspace root — creates venv, installs deps, builds frontend, starts server
.\start.ps1

# Or step-by-step from app/
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm ci --no-audit --no-fund
npm run build
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Interactive API docs at `/docs`.

### Frontend development mode

```powershell
# Keep uvicorn running in one terminal, then:
npm run dev    # Vite dev server with /api proxy; open the printed Vite URL
```

### Docker

```powershell
docker compose up --build -d   # port 8080, named SQLite+evidence volume
```

---

## Test commands

```powershell
# From app/ — use the project virtual environment
$env:TEMP = "$PWD\.test-tmp"; $env:TMP = $env:TEMP

# Full backend suite (101 tests as of October 2026)
.\.venv\Scripts\python.exe -m pytest -q

# Client tests (13 Node tests — flight interpolation + recovery)
npm run test:client

# TypeScript type-check + production build
npm run build

# Independent diagnostic evaluator (B0/B1 detection)
.\.venv\Scripts\python.exe tests\benchmark_independent.py

# Full adaptive B2 evaluation — spends provider quota; preserve artifact first
.\.venv\Scripts\python.exe tests\adaptive_evaluation.py --provider rules   # dry run
.\.venv\Scripts\python.exe tests\adaptive_evaluation.py --provider watsonx # live
```

Set `TEMP`/`TMP` to `.test-tmp` before running pytest on Windows to avoid
permission errors with SQLite in the system temp directory.

---

## Architecture overview

### Frontend (`app/frontend/`)

| File | Role |
|---|---|
| `App.tsx` | Top-level state, SSE stream, run/case/actor lifecycle |
| `Scene.tsx` | Three.js / React Three Fiber 3D network scene + drone |
| `InvestigationPanel.tsx` | Worker results, planner decisions, adaptive follow-ups |
| `ActionsPanel.tsx` | Ranked next-check affordances (FR-06) |
| `MonthReplay.tsx` | September 2022 replay calendar |
| `ProvenancePanel.tsx` | Recomputation and analysis-revision history |
| `flight.ts` | Drone waypoint interpolation (pure function, unit-tested) |
| `recovery.ts` | Browser-storage resilience and investigation deduplication |
| `api.ts` | Typed fetch wrapper with `ApiError` |
| `types.ts` | Shared TypeScript types (Snapshot, Asset, Balance, …) |

### Backend (`app/backend/`)

| Module | Role |
|---|---|
| `main.py` | FastAPI app, all HTTP routes, clock loop |
| `engine.py` | Run lifecycle: create, step, seek, snapshot, revise |
| `simulation.py` | **Private** physical truth — never imported by analytics |
| `analytics.py` | Reconciliation and alert detection — reads only observations |
| `topology.py` | Static asset graph: `BY_ID`, `CHILDREN`, `SECTIONS` |
| `sources.py` | September 2022 development fixture, CSV ingestion |
| `workers.py` | W1–W4 pure analytical workers |
| `followups.py` | Registered read-only follow-up checks (electrical, topology, localization) |
| `investigations.py` | LangGraph stateful investigation workflow |
| `providers.py` | Granite (watsonx) and Gemini transport adapters |
| `ranking.py` | Next-check scoring: information gain × reliability × access − cost |
| `contracts.py` | Pydantic models shared across the analytical boundary |
| `coverage.py` | Metering coverage profiles and installed-meter inventories |
| `store.py` | SQLite key-value and interval stores |
| `finance.py` | Conditional impact calculator |
| `inspection.py` | OpenCV Canny+Hough detector — pixels only, no truth |
| `benchmark.py` | Read-only access to evaluation result artifacts |
| `settings.py` | `.env` loader (data only, never exec) |

### Investigation workflow (LangGraph)

```
START → workers → planner → policy → [followup → planner →]* complete → END
```

- `workers`: W1–W4 run synchronously; observations are frozen at investigation creation.
- `planner`: Granite → Gemini → deterministic rules (first successful provider pins).
- `policy`: `validate_policy()` in `workers.py` — independent of the planner; blocks
  disallowed actions before execution.
- `followup`: registered read-only checks only; no network, no simulator, no truth.
- Limits: 3 extra checks, 6 provider calls, 60-second shared deadline.

### Storage

- `store.py` uses a single WAL-mode SQLite at `data/gridtrace.sqlite3`
  (overridable via `GRIDTRACE_DATA`).
- `objects` table: key-value UPSERT for runs, cases, investigations, evidence, …
- `intervals` / `private_truth` tables: immutable append-only per (run_id, seq).
- Audit table has database-level triggers preventing UPDATE and DELETE.
- Evidence PNGs live under `data/evidence/` as immutable files; SHA-256 is stored.

---

## Coding conventions

### Python backend

- Formatting: compact, no unnecessary blank lines inside functions (matches
  existing style).
- Types: Pydantic models for all API bodies and inter-module contracts; use
  `ConfigDict(extra='forbid')` on public-boundary models.
- Errors: return `HTTPException` with a specific status code and plain-text
  detail from route handlers. Log full tracebacks before raising 500s.
- Null safety: use `next((...), None)` with an explicit None check; never rely
  on `StopIteration` propagating.
- Division: guard every denominator that can be zero before the operation.
- No f-string SQL; use parameterised queries through `store.DB.execute`.

### TypeScript / React frontend

- Strict null-safety: no `!` non-null assertions unless the type system
  guarantees non-null at that point. Use optional chaining and explicit guards.
- Error handling: never use an empty `.catch(() => {})`. Log to `console.error`
  at minimum; set visible error state for user-facing failures.
- Polling: always cap retry loops — use exponential back-off and a maximum
  failure count before surfacing an error to the user.
- State: prefer React state and refs over module-level mutable variables.

### General

- Minimal change principle: make the smallest edit that solves the problem.
  Do not refactor unrelated code, add unrequested features, or change test
  fixtures.
- Tests: every new backend route or analytics change needs a corresponding
  test. Client-side logic with clear inputs/outputs should have a Node test.
- Do not commit or push. Changes are local-only unless the user explicitly
  requests otherwise.

---

## Boundaries — what must never cross

| Boundary | Rule |
|---|---|
| `simulation.py` → `analytics.py` | `analytics.py` **never** imports `simulation.py` or `store.private_truth`. It receives only `readings` (observations). |
| Private truth → workers | W1–W4 receive only `snapshot['readings']`, `snapshot['balances']`, `snapshot['alerts']`. No truth, no simulator state. |
| Planner → direct execution | Model proposals are **validated by `policy`** before any action is executed. A model output is never directly applied. |
| Image detector → truth | `inspection.py` receives RGB pixels, camera pose, and the target asset ID from approved topology. No incident type, truth mask, or injected ground truth. |
| Analytics → authorization claim | Energy residuals and image candidates are **signals for human investigation**, not proof of theft, authorization failure, or guilt. |

---

## Scenario and evaluation files

- `scenarios.json` — calibration seeds and scenario descriptions; do not edit
  without updating the corresponding evaluator.
- `docs/adaptive-results.json` — sealed B2 evaluation artifact; do not edit
  manually. Rerun `tests/adaptive_evaluation.py` to refresh.
- `docs/independent-results.json` — B0/B1 detection diagnostic artifact.
- The code fingerprint in benchmark results becomes STALE automatically when
  any `backend/*.py` or evaluator file changes.

---

## Provider credentials

Credentials live only in `app/.env` (gitignored). Copy `app/.env.example` and
fill in values. The backend reads them via `settings.load_environment()` at
startup. Never hardcode credentials in source or tests.

```
WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://eu-de.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-4-h-small
GEMINI_API_KEY=
GEMINI_MODEL_ID=
```

Tests mock providers; they do not require live credentials.

---

## Remaining open gates (as of 26 October 2026 session)

- Gemini live verification (503/timeout in previous session).
- Real BESCOM / frozen replay source onboarding (official source gate PENDING).
- Independently owned blinded B0/B1/B2 study with equal budgets.
- Broader device/accessibility coverage and reference-laptop performance
  measurements.
- Optional drone/CV in real field imagery (deferred).
