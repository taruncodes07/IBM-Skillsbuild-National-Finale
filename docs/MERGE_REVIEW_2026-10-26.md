# Combined branch review — 26 October 2026

Inputs: `grid-trace-prototype` at `ff6fe5ecb2a21230bf98d1634044a8d73f892ec6` and
`dev_1` at `f26cd80a011b678aff3a1bb56bf2bae8a6022ef2`. Previous main:
`8e8a59fe452bf42f1c9c96b7a853af64db9fcc73`.

## Resolution and fixes

- Merged both histories. Resolved the accounting conflict by retaining installed-meter
  inventories and supporting Dev 1's legacy named coverage modes as an additional gate.
  Explicit inventories cannot be overridden by a legacy full-coverage argument.
- Retained both scoring interfaces. `backend/ranking.py` remains the operational engine
  used by the API/UI, including persistence and ground-review prerequisites.
  `analytics.rank_next_checks` is a compatibility/calibration helper, not an execution
  authority. Its empty action catalog now abstains and sensitivity overlap is surfaced.
- Retained Dev 1's CSV ingestion, sample readings, topology slice and supplied evidence
  documents. Hardened CSV text/path handling for Windows, finite-value validation,
  explicit timezone parsing and duplicate detection across equivalent UTC offsets.
  Duplicate records no longer count as valid readings.
- Kept invalid balances null. Updated the Scenario G regression to explicitly require
  null residuals for both missing readings and stale mapping, instead of expecting a
  numeric stale-mapping residual.
- Fixed the mission panel's launch eligibility for the new `ground_review` state.
  Updated the main walkthrough to include the required ground observation.
- Updated Vite from 6.2.6 to 6.4.5 within the same major version. The dependency audit
  reported zero vulnerabilities after this update.
- Preserved supplied Bob reports as supplied; their authenticity was not independently
  established by this merge review. The structured session ledger remains separate.

## Executed verification

- Full backend suite: **101 passed**, including four new cross-branch/CSV regressions.
- Client recovery and flight tests: **13 passed**.
- TypeScript and Vite production build: **passed**.
- `verify_prd_gaps.py`: all checks passed.
- Refreshed independent deterministic evaluation: B0 and B1 each match 16/20 eligible
  synthetic events, zero false alerts across six valid control branch-hours. These are
  small synthetic diagnostics, not field accuracy. Report hash:
  `82b6ef0b75f9d6973578793a2bc189d7a7104386bec10f988d6cd6692dcefe1f`.
- Chromium browser walkthrough: start visible-unmetered-load scenario, step three
  intervals, open case, triage, switch reviewer, record an obstructed ground view with
  an unanswered overhead question, approve flight, complete route and two captures.
  Stored mission is `completed`, both frame keys exist, and both evidence records declare
  `webgl_scene`. Browser console: zero errors/warnings in this walkthrough.

Environment: Windows, Python 3.14, local virtual environment installed from
`requirements.txt`, Node 24.19, locked frontend dependencies. The full Python transitive
`requirements.lock.txt` environment and Docker image were not rebuilt in this review.
Python emits the existing LangChain/Pydantic V1 compatibility warning on 3.14; the tests
pass. Vite still reports the existing large scene-bundle warning.

Original frozen CSV onboarding remains pending. The new generic CSV parser does not
automatically replace the active development replay adapter. Live Granite/Gemini calls
were not repeated; prior live-model results remain historical and fingerprint checks
correctly mark them stale for changed backend code. No model credentials were required.

## Publication

The previous main is preserved as `backup/main-before-integration-2026-10-26`.
Both development branches are retained. Main can advance to the combined merge commit
without rewriting or discarding repository history.
