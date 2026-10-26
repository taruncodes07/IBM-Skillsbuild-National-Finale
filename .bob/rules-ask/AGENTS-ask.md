# Grid Trace — Ask Mode Context

Extends the root `AGENTS.md`. Use when answering questions about the codebase,
explaining behaviour, or looking up how things work.

## Key reference documents

| Question area | Where to look |
|---|---|
| Energy accounting formula | `app/README.md` § Simulation and accounting |
| Detection thresholds | `app/backend/analytics.py` `reconcile()` + `detect()` |
| Worker outputs and evidence IDs | `app/backend/workers.py` |
| LangGraph workflow graph | `app/backend/investigations.py` (graph edges at bottom) |
| Accepted planner actions | `app/backend/contracts.py` `Action` literal |
| API routes | `app/backend/main.py` or http://127.0.0.1:8000/docs |
| B2 evaluation results | `app/docs/B2_AND_QA_REPORT.md` + `adaptive-results.json` |
| B0/B1 detection results | `app/docs/independent-results.json` |
| Remaining open gates | `app/docs/BUILD_STATUS.md` § Remaining gates |
| Provider configuration | `app/docs/PROVIDERS.md` + `app/.env.example` |

## Factual boundaries — what is and is not established

When answering questions about results, always note:

- B2 scores are on **synthetic held-out realizations**, not field data.
- 18/18 rules + 18/18 Granite (October 2026 rerun) is a **regression result**,
  not evidence of model superiority or field accuracy.
- B0/B1 detection (16/20 each) covers only **six valid control branch-hours** —
  a small diagnostic, not a power study.
- `official_source_status` for readings is `'PENDING'` — no real BESCOM data
  has been ingested.
- An energy residual or image candidate **is not proof of theft**.
