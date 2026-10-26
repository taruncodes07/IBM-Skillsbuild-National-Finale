# Edge Case Hardening Plan — Grid Trace

## Top-Level Overview

The codebase is a working prototype (18/18 B2 regression passes, 63+ backend tests, 10 client tests). The underlying code, however, carries a significant debt of unguarded array accesses, unprotected division, unguarded `next()` generators, swallowed async errors, race conditions in shared mutable state, and missing input validation. None of these have broken the happy path yet, but each is a credible crash or silent-data-corruption path under slightly adversarial or unexpected inputs.

The plan groups the ~150 identified edge cases into six focused sub-tasks ordered from highest crash-risk to lowest. Each sub-task targets a single concern category so changes stay small, reviewable, and independently testable.

**Non-goals:** no feature additions, no refactors beyond what is required to fix the identified issue, no changes to the evaluation protocol or existing test fixtures.

---

## Sub-Task 1 — Guard all unprotected `next()` calls and array index accesses (crash-risk)

### Intent
Thirteen instances of `next(generator)` without a default value will raise `StopIteration` when the expected record is absent. Several direct `[0]` or `[index]` accesses assume non-empty lists. These are the most likely causes of a 500 error in production.

### Expected Outcomes
- No `StopIteration` can propagate to the API boundary.
- All array index accesses that may encounter an empty list have an explicit `None` / empty-list fallback.
- A short, clear HTTP 422 or 404 is returned instead of a 500 traceback.

### Todo List
1. `backend/main.py` line 238 — change `next(b for b in interval['balances'] if ...)` to `next((b for b in ... ), None)` and return a 404 if None.
2. `backend/main.py` line 285 — same fix.
3. `backend/main.py` line 478 — same fix.
4. `backend/workers.py` line 16 — same fix; log a warning if the balance is missing.
5. `backend/followups.py` line 42 — same fix.
6. `backend/engine.py` line 102 — add explicit `if previous is None: return` guard before unpacking `previous['alerts']`.
7. `backend/main.py` line 328 — add `if not ranked: raise HTTPException(404, ...)` before `ranked[0]`.
8. `backend/analytics.py` line 260 — add `if not rs: return ...` before `sum(...)/len(rs)`.
9. `backend/followups.py` line 79 — replace hard-coded `inv['workers'][3]` with a `.get()` or `next()` lookup by worker role.
10. `frontend/Scene.tsx` line 74 — replace `!` non-null assertion with an explicit early-return guard.
11. `frontend/App.tsx` lines 82, 85, 110 — replace `!` assertions with guarded access; render a loading/empty state instead of crashing.
12. `frontend/flight.ts` line 7 — add `if (segment + 1 >= route.length) return` before accessing `route[segment + 1]`.

### Relevant Context
- `backend/main.py` — FastAPI route handlers; all these are called from HTTP requests.
- `backend/engine.py` — interval seek and playback logic.
- `frontend/flight.ts` — drone flight path computation; used in Scene.tsx.
- `frontend/App.tsx` — top-level state; crashes here blank the whole UI.

### Status
[ ] pending

---

## Sub-Task 2 — Fix division-by-zero and numeric stability issues

### Intent
At least eight places divide by a value that can legitimately be zero (run speed, list length, vector norm, energy sum). These produce either a Python `ZeroDivisionError` crash or a JavaScript `Infinity`/`NaN` that silently corrupts display values and downstream arithmetic.

### Expected Outcomes
- No unguarded division anywhere in the call stack.
- NaN and Infinity are never serialised into an API response or rendered in the UI.
- Where a zero denominator represents a genuine data problem, an appropriate error is surfaced to the caller.

### Todo List
1. `backend/main.py` line 40 — validate `run['speed'] > 0` before `period = 15 / run['speed']`; raise 422 if zero.
2. `backend/engine.py` line 40 — same guard (speed also used here).
3. `backend/ranking.py` line 183 — if `prior[c]` is zero for all causes, log a warning and use a uniform prior fallback rather than computing entropy over a zero-sum distribution.
4. `backend/analytics.py` line 212 — clamp denominator: replace `max(input_kwh, 1e-6)` with `max(abs(input_kwh), 1e-6)` so negative near-zero values are also handled.
5. `backend/inspection.py` line 11 — guard `np.linalg.norm(right)` before dividing; if norm is zero, skip or return an empty result for that geometry.
6. `backend/inspection.py` lines 32, 46 — add `if not local` / `if not samples` early-return guards before `min(...)` / `max(...)` on potentially empty sequences.
7. `frontend/Scene.tsx` line 95 — add `if (m.waypoints_m.length === 0) return` before `center.divideScalar(m.waypoints_m.length)`.
8. `frontend/ActionsPanel.tsx` line 35 — ensure `scale` is never used as a divisor when it equals its fallback floor `0.0001`; add a `if (!isFinite(...))` display guard.

### Relevant Context
- `backend/ranking.py` — Bayesian cause-ranking; incorrect entropy leads to silent misordering.
- `backend/inspection.py` — uses OpenCV/NumPy geometry; crashes are non-obvious.
- `frontend/Scene.tsx` — Three.js scene graph; NaN positions freeze the renderer.

### Status
[ ] pending

---

## Sub-Task 3 — Add missing input validation on API endpoints

### Intent
Pydantic models catch type errors at the boundary, but several downstream code paths assume structural invariants (non-empty lists, valid asset IDs, valid date strings) that Pydantic does not enforce. These must be validated before the first piece of business logic runs.

### Expected Outcomes
- All API endpoints return a clear 422 with a descriptive message when required invariants are violated.
- No HTTP 500 can be triggered by malformed but Pydantic-valid input.

### Todo List
1. `backend/finance.py` line 5 — wrap `date.fromisoformat(...)` in a try/except ValueError and re-raise as HTTPException 422 with message "invalid date format".
2. `backend/main.py` line 394 — validate that every ID in `body.observed_asset_ids` exists in `BY_ID` and return a 422 listing the unknown IDs.
3. `backend/main.py` line 420 — validate that `c['boundary_asset_id']` resolves to an asset with a 3-element `position_m` before unpacking.
4. `backend/main.py` line 452 — add `if len(raw) < 24: raise HTTPException(422, "PNG too short")` before byte-slice IHDR validation.
5. `backend/sources.py` line 46 — validate `0 <= sequence < MONTH_INTERVALS` and raise HTTPException 422 with "sequence out of range".
6. `backend/simulation.py` line 75 — validate that `e['target_asset_id']` is a key in `CHILDREN` before access; raise 422 if missing.
7. `backend/main.py` line 309 — validate `revision` is a positive integer before string-formatting it into balance IDs.

### Relevant Context
- `backend/main.py` — central API surface; widest blast radius.
- `backend/finance.py` — date arithmetic; invalid ISO dates raise unhandled ValueError.
- `backend/sources.py` — sequence bounds used in interval retrieval.

### Status
[ ] pending

---

## Sub-Task 4 — Fix async error swallowing and race conditions

### Intent
Several async paths silently discard errors (empty `.catch(() => {})` handlers) and two concurrent-write races are present: case creation and reading-revision can both fire simultaneously. Silent errors prevent operators from diagnosing failures; races can corrupt persisted investigation state.

### Expected Outcomes
- No `.catch()` silently discards an error; at minimum the error is logged to the console.
- Case creation is idempotent or guarded against double-submission.
- Reading-revision writes are serialised or guarded against concurrent modification.

### Todo List
1. `frontend/App.tsx` line 70 — replace empty `.catch(() => {})` with `.catch(err => console.error('[App] load error', err))` and set a visible error state.
2. `frontend/InvestigationPanel.tsx` line 25 — cap the polling retry: track a consecutive-failure counter, apply exponential back-off after 3 failures, and stop after 10 failures (show an error banner).
3. `frontend/App.tsx` line 95 — add a boolean `creating` ref; set it before and clear it after `createCaseFor()` to prevent double-submit on rapid clicks.
4. `backend/investigations.py` line 130 / 146 — ensure `inv.update()` is called only once per state transition; consolidate the two calls into a single update at the end of the function.
5. `backend/main.py` lines 459–463 — in the broad `except Exception as exc` handler, log `traceback.format_exc()` before raising HTTPException so the full stack trace is not silently lost.
6. `backend/store.py` line 24 — wrap `json.loads(r[0])` in try/except and raise a descriptive RuntimeError on corrupt JSON rather than letting it propagate as an uncontextualised ValueError.

### Relevant Context
- `frontend/InvestigationPanel.tsx` — polls every 750 ms; infinite loop on persistent API failure.
- `backend/investigations.py` — LangGraph state machine; double-write risks partial state.
- `backend/store.py` — SQLite backing store; corrupt JSON is rare but catastrophic.

### Status
[ ] pending

---

## Sub-Task 5 — Harden frontend undefined-dereference and stale closure patterns

### Intent
The frontend uses TypeScript non-null assertions (`!`) in more than 20 places and has several stale-closure patterns around React refs. Under empty-state or loading-state conditions, these produce white-screen crashes or silently stale values.

### Expected Outcomes
- No TypeScript non-null assertion that cannot be statically guaranteed.
- All array `.find()` results are checked before use.
- `activeRun.current` and `pinnedSequence.current` refs are always updated in the same effect that reads them.
- Empty/loading/error states are rendered instead of crashing.

### Todo List
1. Enable `"strictNullChecks": true` in `app/tsconfig.json` if not already set — this will surface all remaining `!` assertions as compile errors.
2. `frontend/App.tsx` line 23 — replace `h!.input_kwh` with `h?.input_kwh ?? 0`.
3. `frontend/App.tsx` line 62 — add null guard before accessing `saved.assetId`.
4. `frontend/App.tsx` line 119 — replace `.slice().reverse().find(...)` on `detail?.ground` with optional chaining `detail?.ground?.slice().reverse().find(...)`.
5. `frontend/MonthReplay.tsx` line 11 — add `if (day >= (month?.days.length ?? 0)) return null` before rendering the selected day.
6. `frontend/recovery.ts` line 21 — re-examine the `!>=` operator precedence; rewrite as `v.sequence != null && v.sequence >= 0 && v.sequence < 2880`.
7. `frontend/InvestigationPanel.tsx` line 42 — add `if (!inv.workers) return` before `.map()`.
8. `frontend/ProvenancePanel.tsx` line 32 — use `history?.recomputations ?? []` consistently.
9. `frontend/Scene.tsx` line 23 — add a runtime length check `if (a.position_m.length < 3) return null` before unpacking the tuple.
10. `frontend/workers.py` / `frontend/types.ts` — add a UI guard in any numeric display that checks `isFinite(value)` before rendering; replace non-finite values with `"—"`.

### Relevant Context
- `frontend/recovery.ts` — operator precedence bug is a logic error, not just style.
- `frontend/types.ts` — `input_kwh: number | null` flows throughout the UI; guards must be consistent.
- `app/tsconfig.json` — enabling strictNullChecks surfaces all remaining gaps at compile time.

### Status
[ ] pending

---

## Sub-Task 6 — Minor hardening: settings parsing, coverage arithmetic, PNG byte-slice

### Intent
A small cluster of lower-severity issues involves defensive arithmetic (floating-point fudge factors, off-by-one in coverage), fragile string parsing (settings.py), and hard-coded magic bytes (PNG IHDR). While individually low-risk, they are easy to fix and reduce long-term fragility.

### Expected Outcomes
- `settings.py` never crashes on a 2-character quoted string.
- `coverage.py` fraction arithmetic is documented and the fudge-factor intent is a named constant.
- PNG IHDR validation has an explicit length guard.
- `MonthReplay.tsx` regex does not hard-code the 2022-09 date period.

### Todo List
1. `backend/settings.py` line 18 — check `len(value) >= 2` before slicing `value[1:-1]`; if the condition fails, return `value` unchanged.
2. `backend/coverage.py` line 78 — replace the bare `1e-9` fudge factor with a named constant `FLOAT_EPSILON = 1e-9` and add a comment explaining it prevents floating-point rounding from cutting the last ID from a group.
3. `backend/main.py` line 452 — add `if len(raw) < 24: raise HTTPException(422, "image data too short for PNG IHDR")` before the `raw[16:20]` slice.
4. `frontend/MonthReplay.tsx` line 15 — derive the date regex from the scenario's `period_start` field rather than hardcoding `2022-09`.
5. `backend/benchmark.py` line 18 — wrap the JSON parse in a try/except and log the error explicitly rather than silently returning `{'status': 'STALE'}`.
6. `backend/sources.py` line 110 — replace implicit `readings[k]['energy_import_kwh'] or 0` with `readings[k].get('energy_import_kwh') or 0` to be explicit about the missing-key case.

### Relevant Context
- `backend/settings.py` — reads environment/config values; edge case only on malformed input.
- `frontend/MonthReplay.tsx` — hardcoded date is a latent bug for any scenario outside the 2022-09 period.

### Status
[ ] pending

---

## Open Questions for Review

1. **StopIteration vs 404**: For missing balances in `main.py`, should the API return 404 (record not found) or 422 (input refers to non-existent asset)? The distinction matters for client error handling.
2. **Strict null checks scope**: Enabling `strictNullChecks` may introduce a large number of compile errors at once. Should sub-task 5 apply it immediately (fixing all resulting errors) or only fix the individually identified issues first?
3. **Investigation double-write**: The two `inv.update()` calls in `investigations.py` — is the second call intentional (revision after policy routing) or a copy-paste bug? Needs owner confirmation before consolidating.
4. **MonthReplay date regex**: What field carries the scenario period? If it is `scenario_settings.period_start`, confirm the format so the regex can be derived correctly.
