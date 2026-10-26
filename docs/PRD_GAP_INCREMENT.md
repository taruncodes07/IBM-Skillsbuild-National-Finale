# PRD v4.0 gap increment

26 October 2026. Built on branch `grid-trace-prototype` at commit `05cd764`.

Closes four PRD v4.0 requirements that had no implementation: the quantitative half of
FR-06 (AC-14), coverage-aware localization (AC-13) including Scenario H, Scenario G
(AC-05), and ground-first inspection (FR-07, AC-08, Demo-A3).

**Verification status.** Verified on the reference Windows host, 26 October 2026:
`pytest -q` reported **89 passed, 0 failed**, and `npm run build` completed `tsc --noEmit`
plus a clean Vite production bundle (2,157 modules; the large-chunk warning for the 3D scene
is pre-existing). `verify_prd_gaps.py` passes every check. Browser QA, FPS and live-provider
runs for this increment remain unmeasured.

---

## New files

| File | Purpose |
| --- | --- |
| `backend/ranking.py` | Deterministic next-check ranking: information gain, S(a) scoring, eligibility gates, sensitivity analysis, abstention. |
| `backend/coverage.py` | Metering-inventory profiles and cut observability, parameterised from published CEA counts. |
| `tests/test_prd_gaps.py` | 22 tests across AC-14, AC-13, AC-05 and FR-07. |
| `verify_prd_gaps.py` | Standalone stdlib-only check; runs before the virtual environment exists. |
| `docs/PRD_GAP_INCREMENT.md` | This document. |

## Changed files

| File | Change |
| --- | --- |
| `backend/analytics.py` | `reconcile()` takes `installed`; un-instrumented cuts return `insufficient_observability` with `residual=None`. `detect()` separates observability events from data-quality events. |
| `backend/engine.py` | `create_run()` takes `coverage_profile`; new `set_coverage()` and `installed_for()`; Scenario G incident wiring; baseline sigma skips null residuals. |
| `backend/simulation.py` | `MATCHED_RESIDUAL` family and `matched_residual_incidents()`; four new scenario ids. |
| `backend/main.py` | `ground_review` case state; 6 new endpoints; aerial approval gated on an open ground question; case detail returns ground observations. |
| `frontend/types.ts` | `Ground`, `RankedAction`, `Actions`, `CoverageSummary`; extended `Snapshot`, `Detail`, `Balance`, `Mission`. |
| `frontend/App.tsx` | Ground-review panel and `recordGround()`; `approve()` precondition; coverage selector; observability disclosure. |
| `frontend/style.css` | Styles for ground review, coverage chip, observability note. |
| `tests/test_acceptance.py` | `ground()` helper; three mission tests now record a ground observation first. |

---

## 1. FR-06 quantitative ranking (AC-14)

`S(a) = IG(a) x R x A - 0.35 x Cn - 0.15 x Tn`, with `Cn = min(C/2000, 1)` and
`Tn = min(T/120, 1)`, exactly as PRD section 5 specifies.

Information gain is computed properly as `H(prior) - sum_o P(o|a) H(H|o,a)` in bits, over
five candidate causes, using a versioned authored outcome table (`OUTCOME_TABLE_VERSION`).
An action whose likelihoods are not authored (`REQUEST_BILLING_AUDIT`) returns an IG
**range**, never a fabricated point value.

Nine actions are catalogued, each with its question, reliability, access, itemised cost
(travel / staff / equipment / processing, in INR) and expected minutes.

**Eligibility is decided before scoring**, so infeasible actions are rejected rather than
ranked low:

- normal or non-persistent measurements permit only abstention or a summary;
- incomplete data permits only the repair that matches the defect;
- an unavailable billing record blocks a billing audit;
- **an aerial viewpoint is rejected until ground review records an unanswered question.**

Sensitivity varies IG, cost, time, reliability and access by ±20% over 16 combinations.
Actions within 0.05 are reported as tied, and an unstable winner sets
`human_choice_required`. A best score at or below 0.05 abstains.

PRD Table 4 reproduces from logged components:

| Action | Published | Computed | Delta |
| --- | --- | --- | --- |
| Meter record cross-check | 0.493 | 0.4925 | 0.0005 |
| Ground observation | 0.557 | 0.5573 | 0.0003 |
| Drone before ground review | Ineligible | rejected before scoring | — |
| Drone after specified ground gap | 0.517 | 0.5173 | 0.0003 |

Endpoint: `GET /api/balances/{bid}/actions?run_id=...&case_id=...`

Every ranked entry logs action id, prerequisite status, question, IG and range, likelihood
confidence, reliability, access, cost components with currency, expected minutes,
normalisation constants, score, sensitivity bounds, rank and policy version. Rejected
actions carry their rejection reason.

**Honest limitation.** All costs, reliabilities, access probabilities and likelihoods are
authored assumptions, not measured Indian inspection economics. The 0.35 and 0.15 weights
are a policy dial, not a discovered constant — present them that way.

## 2. Coverage-aware localization (AC-13) and Scenario H

Five profiles. The four named ones are parameterised from the Central Electricity
Authority's *Status of Metering in the Country*, reference date 31 March 2025, and from
PGVCL's BEE energy audit FY2023-24:

| Profile | Published basis |
| --- | --- |
| `full_sectional` | Synthetic best case; not a utility profile. |
| `tpddl_like` | 1,286 HV + 16,929 LT feeders metered; 4,342 of 4,986 DTs communicable (87%). |
| `bescom_like` | 6,389 of 6,389 feeders metered; DTs 25.10% overall, **65.18% urban** (this district is urban, so the urban figure is used); 11,745,006 consumers metered. |
| `tgspdcl_like` | 8,713 of 8,713 feeders metered, 1,616 on NFMS (18.55%); 197,266 of 614,590 DTs (32.10%). **This is Scenario H.** |
| `pgvcl_like` | 4,860 of 9,920 feeders communicable; **0 of 1,126,220 DTs** — that report states DT-wise loss computation is not possible. |

`coverage_mode` (what is installed) is reported separately from `completeness` (what
arrived). An absent meter yields `validity='insufficient_observability'`, `residual=None`,
`qualifies=False` and the list of un-instrumented assets. It is never zero-filled and never
counted as a repairable data fault.

Changing coverage creates a new `inventory_version` and **clears persistence streaks**,
because a streak earned under a different cut cannot carry over.

Verified result — the same 1.2 kWh event on `branch-03`:

| Profile | branch-03 | Localizes to |
| --- | --- | --- |
| `full_sectional` | valid, residual 1.214 kWh | BRANCH |
| `tpddl_like` | valid | BRANCH |
| `bescom_like` | insufficient observability | none |
| `tgspdcl_like` | insufficient observability | none |
| `pgvcl_like` | insufficient observability | none |

**The strongest demo line, and it is physics rather than rhetoric.** Under `bescom_like`
the feeder-to-DT cut still reconciles cleanly — residual −0.003 kWh against a 0.269 kWh
threshold. The theft sits *below* the DT meter, which already counts it, so no
feeder-level accounting can ever see it. That is an observability limit, not a detector
failure, and the system says so instead of guessing. A naive residual baseline would
produce a confident branch alert under every profile.

Endpoints: `GET /api/coverage/profiles`, `GET /api/runs/{rid}/coverage`,
`POST /api/runs/{rid}/coverage` (presenter only; refused while a mission is active).

## 3. Scenario G (AC-05)

Four variants hold the apparent excess comparable while varying evidence quality:

| Variant | Apparent excess | Evidence | Recommended |
| --- | --- | --- | --- |
| `matched_residual_complete` | 1.214 kWh | valid | topology check |
| `matched_residual_incomplete` | null | missing reading | restore missing data |
| `matched_residual_stale_mapping` | 1.214 kWh | stale topology | topology check |
| `matched_residual_model_shift` | 1.000 kWh | valid | topology check |

`model_shift` carries **no unmetered load at all** — an elevated technical loss alone
produces a comparable apparent excess from an entirely different cause, which is the point
of the test.

**Partial result, stated honestly.** The incomplete case diverges cleanly. Three variants
currently converge on the same first check because, at a uniform prior, the topology check
has the highest information gain — checking the model before suspecting consumption is
defensible, but it is not four distinct answers. Sharpening this needs a non-uniform
prior, which is the billing-efficiency prior proposed as FR-15 and not in this increment.
The full ranked list and the rejection reasons already differ across all four.

## 4. Ground-first inspection (FR-07, AC-08, Demo-A3)

Case states now follow PRD section 8: `triaged -> ground_review -> inspection_requested`,
with `triaged -> under_review` retained as the no-drone path.

`POST /api/cases/{cid}/ground-observations` records access, observed asset ids, visibility,
and either `resolved_from_ground` or **the exact outstanding question**. Validation rejects
a resolution that also carries a question, a non-resolution with no question, a resolution
without obtained access, and unknown asset ids. It is idempotent and reviewer-only.

Aerial approval now requires a ground observation that leaves a question open, and is
refused when the ground view was `clear`. The approved mission stores
`ground_observation_id`, `answering_question` and `ground_visibility`, which is Demo-A3.

**This is a breaking change.** Three tests in `test_acceptance.py` approved missions
directly from `triaged`; they now record a ground observation first, via a new `ground()`
helper. The frontend `approve()` is gated the same way and a ground-review panel was added,
so the existing drone flow keeps working.

---

## How to verify

```powershell
cd "C:\Users\HP\Desktop\IBM Final\gridtrace-updated"

# 1. Arithmetic only - no virtual environment needed
python verify_prd_gaps.py

# 2. Full suite (expect 65 existing + 22 new)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pytest -q

# 3. Frontend typecheck and build
npm ci --no-audit --no-fund
npm run build

# 4. Run it
.\start.ps1
```

All four steps have been run on the reference host: `verify_prd_gaps.py` passes, `pytest -q`
reports 89 passed, and `npm run build` is clean. Browser interaction QA is not claimed.

## Demo path

1. Simulation laboratory → scenario `Visible unmetered load`, coverage `Full sectional`, seed 42. Step three times; `branch-03` alerts.
2. Open `GET /api/balances/branch-03/actions?run_id=...` — ranked checks with costs, sensitivity and a surfaced tie.
3. New run, same scenario and seed, coverage `Sparse DT coverage (TGSPDCL-like)`. No alert; an observability event appears instead, and the actions endpoint abstains.
4. Open a case → triage → record a ground observation with an obstructed view and a specific question → the flight is now approvable. Mark it resolved from ground instead and the flight is refused.
5. Scenario G: run `matched_residual_complete` and `matched_residual_incomplete` and show the same apparent excess producing a different next check.

## What this increment does not do

- No IBM Bob evidence (AC-12, Bob-A1 to A3) — still zero artifacts, still 10 of 25 marks.
- No challenge mode (FR-12, FR-13, AC-17).
- No paired drone A/B (AC-16).
- No `EvaluationAdapter` restructure or B2 baseline (AC-15).
- No billing-efficiency prior (proposed FR-15), which is what would fully separate Scenario G.
- Official source gate remains `PENDING`; the fixture is still `DEV_FIXTURE`.
