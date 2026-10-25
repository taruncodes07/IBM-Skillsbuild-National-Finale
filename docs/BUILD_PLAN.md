Latest validation (25 October): the 18-case full adaptive run and broader local QA are complete; see docs/B2_AND_QA_REPORT.md for counts, misses, fixes and remaining validation limits. This is internal synthetic validation, not an independently blinded study.

# Grid Trace build plan

Prepared: 25 October 2026. Status: implementation plan, not an implementation or completed acceptance report.

Implementation update, 25 October: local source is now in `app/`. Replay, worker/fusion/controller foundations, provider adapters, case export linkage, conditional finance and a diagnostic baseline harness are implemented. See `app/docs/BUILD_STATUS.md` for actual checks and remaining gaps. Granite is live-verified and bounded adaptive follow-ups are implemented, with 56 backend tests passing. Gemini live fallback, the full blind B0/B1/B2 study, original source onboarding and optional vision remain pending. The prototype is maintained separately on branch grid-trace-prototype; main is unchanged.

This plan uses the local `VIDYUT_TRACE_FINAL_PRD.pdf` and the repository review at commit `8e8a59fe452bf42f1c9c96b7a853af64db9fcc73`. The user's decisions in this chat supersede conflicting PRD priorities: postpone dataset onboarding, build September 2022 replay, use Gemini after Granite failure, and defer or omit drone/CV. The repository was reviewed previously; its build and test results have not been independently rerun here.

## 1. Locked delivery decisions

- Extend the existing GridTrace implementation and retain React, TypeScript, Vite, React Three Fiber, FastAPI, SQLite, SSE and current case/evidence code.
- Use a fictional Hebbal-Sanjaynagar-inspired cell with 2 feeders, 4 DTs, 8 branches and 24 household meters: 38 measurement streams. Poles and scenery do not add measured streams.
- Replay 1-30 September 2022, in 15-minute intervals. Use the half-open IST window `[2022-09-01T00:00:00+05:30, 2022-10-01T00:00:00+05:30)`: 2,880 interval starts; final start is 30 September at 23:45 IST.
- Retain BESCOM as the real historical reference. Dataset acquisition, source verification and final onboarding happen later; they do not block development against an adapter contract.
- Four workers follow the PRD: W1 accounting, W2 physics, W3 commercial/anomaly and W4 localization/optional vision. They perform calculations and analysis; they are not four chatbots.
- One planner uses Granite through watsonx first, Gemini second, and a deterministic decision table if both providers are unavailable. The UI identifies the actual provider for each decision.
- W4 localization is required. Virtual drone, camera capture and automated CV are a final optional milestone. The core release must work without them.
- Keep independent evaluation and conditional finance. Their minimum versions are small, reproducible and evidence-linked.
- Preserve human case review, source distinctions, signed residuals, null readings and audit history throughout.

### BESCOM and replay data are separate

The PRD's BESCOM extract contains seven historical feeder records, not a month of 15-minute household telemetry. Preserve its published grain and unknown observation-window caveat. Do not interpolate it into fictional meter readings and label those readings actual BESCOM data.

Implement the replay interface now using explicitly labeled `DEV_FIXTURE` inputs. A reproducible month fixture can exercise seeking and aggregation; small numerical fixtures exercise accounting. Record their seed, generator version and hash. They are development inputs, not the PRD's frozen source or an independent evaluation set.

Later, connect the frozen 2022 replay file specified in the PRD, or separately supplied verified interval data through a distinct adapter and source contract. Until that happens, the app can be a functional fixture-backed demonstration, but the official source gate remains `PENDING`. Do not claim the frozen file's exact row count, missing-record count or hash has been verified against fixtures.

## 2. Deliverable and scope

### Core release

The user can select a September day/interval, inspect a 3D asset and its measured boundary, open an investigation, watch actual worker execution, receive an evidence-grounded recommendation from the active planner, record a human disposition, and export the complete trail.

Required screens:

1. Operations cockpit: topology, 3D cell, asset selection, balances, data quality and timeline.
2. Month replay: calendar/heatmap, interval slider, daily summaries and coverage.
3. Investigation: W1-W4 results, competing causes, planner action and actual execution trace.
4. Case review: owner, notes, assignment, disposition, reopen and export.
5. Sources and system health: input status, historical BESCOM context when available, provider health and versions.
6. Benchmark: saved B0/B1/B2 results and denominators; no invented scores before a run.
7. Impact ledger: conditional intervention assumptions, energy, invoice, cash and costs.

Keep the existing 3D scene operational. Limit scenic work to readability, coherent selection and performance. Defer photorealistic reconstruction, real GIS, production authentication, utility AMI integration, advanced power flow and physical aircraft.

### Optional final release increment

Reviewer-approved virtual mission, actual rendered RGB frames, side-by-side image review and bounded OpenCV results. If omitted, mark visual inspection `NOT_IMPLEMENTED` or `DISABLED` and route cases to human/field checks. Do not display simulated findings or completed visual missions.

## 3. Runtime architecture

The runtime consists of a source/replay service, deterministic workers, evidence fusion, a bounded LangGraph workflow, provider adapters, a policy gateway, case storage and the existing UI.

Execution sequence:

1. Verify the selected source contract and assemble a coherent observation window.
2. W1 validates the meter cut and computes raw accounting.
3. Invalid measurements take the missing-data/human-review branch. Valid accounting enables W2 and W3, which may execute concurrently.
4. W2 computes bounded technical losses; W3 assesses available consumption/commercial signals.
5. W4 determines the smallest defensible measured area and available inspection methods.
6. Deterministic fusion assembles observations, alternative causes, contradictions and admissible actions.
7. The active planner proposes a typed next action using only this evidence bundle.
8. The policy gateway validates the proposal before any tool executes.
9. A permitted extra tool produces new evidence and returns to fusion, within a bounded loop.
10. Human review records the case outcome; finance evaluates explicitly hypothetical intervention assumptions.

No model directly edits readings, computes authoritative finance, launches a mission or resolves a case. The planner receives neither challenge truth nor renderer-only injected geometry. Do not forward the complete current scene snapshot to a model: it includes physical geometry used to draw synthetic scenarios.

LangGraph tracks orchestration state and conditional routes. SQLite remains the durable application store; resume work from persisted execution records rather than relying on graph memory alone. Use one local backend process initially.

## 4. Worker specifications

### W1 - metering and accounting

Extract and preserve the useful logic in `backend/analytics.py`.

- Validate exact immediate downstream cuts; reject duplicates, nested meters and unknown topology versions.
- Align interval starts/ends and energy units. Preserve duplicates, revisions and rollover errors as diagnostics until reconciled.
- Return input, downstream sum, authorized unmetered energy, raw gap, completeness and source lineage.
- Missing required readings produce `DATA_INCOMPLETE`; never replace them with zero.
- Keep negative gaps/residuals for consistency review.
- Aggregate only disjoint boundaries. A feeder total must not add its DT and branch totals again.

Acceptance: the golden example gives `12.5 - 10.5 - 0 - 0.4 = 1.6 kWh`, or 12.8%; missing-data, nested-cut, duplicate and negative-value controls behave correctly.

### W2 - electrical physics

- Reuse the current reduced-order loss equation as an explicitly assumed model.
- Move coefficients into a versioned parameter configuration, separate from challenge generation.
- Return low/central/high technical-loss estimates and corresponding residual bounds.
- Record assumptions about voltage, conductor characteristics, transformer losses and uncertainty.
- Classify significant unexplained residual only where the uncertainty treatment supports it.
- With energy-only data, return insufficient information for claims about actual overheating, current, resistance identification or calibrated power flow.

Acceptance: increasing assumed technical loss changes residual bounds predictably; missing parameters cause explicit limitations; measurements are never modified to fit the model.

### W3 - commercial and consumption anomaly

- Calculate consumption shifts against a declared historical baseline with time-of-day controls.
- For chronological replay, use only earlier observations; do not use later September readings to diagnose earlier intervals.
- Treat early-month baseline warmup as `INSUFFICIENT_HISTORY` unless an independently declared prior period exists.
- Return consumption-change reasons without assigning guilt to households.
- Compute billing/payment comparisons only when matching-period records exist. Otherwise return `NOT_AVAILABLE` and `COLLECTION_UNKNOWN`.
- Legitimate demand changes alone must not create an unexplained-loss verdict.

Acceptance: missing commercial fields produce unavailable states; a legitimate surge with matching upstream energy does not become a theft finding.

### W4 - localization and optional vision

Core mode `CHECK_INSPECTABLE_LOCATION`:

- Identify the smallest significant, fully measured section.
- Return localization level, candidate region, supporting evidence, missing measurements and inspectability reasons.
- Visualize a branch/DT coverage region; do not invent a particular pole or household from branch accounting alone.
- When visual inspection is disabled, mark it unavailable and recommend a meter, mapping or human field check where appropriate.

Optional mode `ANALYZE_VISUAL_EVIDENCE` wraps existing OpenCV code. It accepts actual pixels, camera pose and approved geometry, with results `CANDIDATE_FOUND`, `NO_VISIBLE_CANDIDATE` or `INCONCLUSIVE`.

Acceptance: removing downstream coverage prevents unjustified finer localization; disabling vision does not break W4 or case completion.

## 5. Shared contracts and evidence fusion

Use Pydantic models and corresponding TypeScript types for:

- `SourceManifest`, `ReplayRun`, `ObservationWindow` and `MetricProvenance`.
- `WorkerRequest`, `WorkerResult`, `EvidenceItem` and `FusionResult`.
- `PlannerContext`, `PlannerProposal`, `PolicyDecision` and `ExecutionEvent`.
- `CaseRevision`, `BenchmarkConfig`, `BenchmarkResult` and `FinanceScenario`.

Every worker request carries run/investigation IDs, area, time window, source kind/hash, topology version, input evidence IDs, requested-by identity and runtime budget. Every result carries status, findings, evidence IDs, missing inputs, uncertainty, algorithm version, input hashes, elapsed time and retryability.

Evidence items carry a stable ID, claim, scope, time window, source, hash, assumptions and permitted inference. Fusion maintains nonexclusive hypotheses such as missing telemetry, topology mismatch, meter fault, technical-model error, authorized unmetered load and unexplained unmetered consumption.

Rules must prevent double-counting correlated evidence, treat missing readings as a quality failure, avoid converting consumption drops into bypass proof, and preserve unresolved competing causes. Show `SUPPORTS`, `WEAKENS` and `UNKNOWN` relationships; calibrated cause probabilities are outside the initial build.

## 6. Granite primary and Gemini fallback

### Provider interface

Implement adapters with `healthcheck()`, `propose(context, allowed_tools, budget)` and normalized usage/error reporting. Both return the same validated `PlannerProposal`; provider-specific response objects stay inside adapters.

Server-only configuration:

- `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `WATSONX_MODEL_ID`.
- `GEMINI_API_KEY`, `GEMINI_MODEL_ID`, and an explicit Google Gemini endpoint configuration where needed.
- `PLANNER_PRIMARY=watsonx`, `PLANNER_FALLBACK=gemini`.
- `MAX_EXTRA_TOOL_STEPS=3`, `MAX_PROVIDER_CALLS_PER_CASE=6`, `PLANNER_OUTPUT_TOKEN_LIMIT=500`, `PLANNER_REQUEST_TIMEOUT_SECONDS=15`, `PLANNER_CASE_TIMEOUT_SECONDS=60` as initial configurable limits.

The PRD's provisional Granite model is `ibm/granite-4-h-small`; verify chat/tool support in the configured region. Select and pin an available tool-capable Gemini model at implementation time; do not hardcode an unverified model name into the plan.

### Failover rules

1. Run a small capability healthcheck for configured providers, outside replay accounting.
2. Attempt Granite while healthy. Missing credentials, unsupported model/tool capability, authentication failure or exhausted service retries make it unavailable for that planning step.
3. For timeout, throttling and temporary server failures, allow at most one bounded retry when the case deadline and call budget permit. All attempts count toward the global budget.
4. Fall back to Gemini with the same permitted tools, sanitized evidence and remaining case budget. Do not rerun already completed worker actions.
5. If both fail, use the deterministic decision table and show `RULE_FALLBACK`.
6. Persist provider, model, attempt, fallback reason, latency and available token usage for each decision. A Gemini result is labeled Gemini, even if Granite was attempted first.
7. Pin the working provider for the rest of an active investigation to avoid oscillation. Recheck primary health for new cases after a cooldown.

Malformed responses are rejected. Allow at most one repair attempt within the same limits. A policy-denied action is not a provider outage: do not switch models to bypass the denial. Never resend a side-effecting tool because a provider request timed out; execution IDs and idempotency protect against duplicates.

### Allowed actions and execution controls

Start with the PRD actions: electrical recheck, meter review, billing audit, topology check, localization, missing-data request, case summary and abstain. Register `PROPOSE_VIRTUAL_DRONE` only when the optional capability is enabled.

Policy validates action enum, evidence ownership, source/time alignment, asset existence, localization, permissions, tool availability, repeat requests and remaining budget. Reject invented evidence IDs and unsupported locations. External review requests become case tasks; they do not imply an integrated utility service has completed them.

Tool outputs and case notes are untrusted data. Expose only registered application functions, without arbitrary web browsing, code execution, shell or file access. Persist concise decision justifications and actual tool events; do not store or display private chain-of-thought.

## 7. Month replay implementation

Refactor `backend/engine.py` to accept an observation source instead of unconditionally calling `simulation.generate()`.

Source adapter operations: describe source, list interval starts, read an interval/window and calculate coverage-aware aggregates. Implement a fixture adapter first, the frozen gzip CSV adapter next when data is provided, and a separate historical BESCOM adapter.

Required behavior:

- Convert canonical timestamps to UTC for joins and show IST in the interface. Do not use the machine date to define replay.
- Replace fixed 0-95 bounds across backend schemas, history queries, frontend controls and tests with source-derived interval counts.
- Support play, pause, step, speed and seek. Playback speed changes wall-clock pacing, not the 0.25-hour accounting interval.
- Seeking selects an existing interval; it does not generate new readings or mutate source history.
- Separate observed-through progression from selected-view interval. Seeking must not advance persistence streaks twice or introduce future data into historical baselines.
- Compute W1/W2 and bounded deterministic summaries across the month; invoke the LLM on investigation creation or explicit replan, never automatically 2,880 times per run.
- Precompute/cache accounting and daily rollups. Cache by source hash, topology, cut signature, algorithm and parameter versions.
- Mark partial days and excluded readings visibly. A sum over valid readings is not presented as a complete daily total.
- Tag requests with run ID, selected interval and view-generation ID; discard late responses after a seek or run switch. Persisted case evidence remains attached to its original interval.
- Keep developer incident injection in a separate laboratory/challenge mode; disable injection and source mutation for frozen replay.

Acceptance: first/last interval, midnight boundaries, random seek, repeat load, coverage rollup, identical replay, stale UI response and case timestamp tests pass.

## 8. Backend, storage and API changes

Keep existing endpoints working where practical; add versioned fields and adapters rather than rewriting the case API solely to match names in the PDF.

Add or extend:

- `GET /api/sources`, `GET /api/health` and `GET /api/bescom/feeders`.
- `POST /api/runs` with source mode, source ID/hash and topology version.
- Replay control with seek and expected revision; snapshot/window and month-summary queries.
- `POST /api/investigations`, `POST /api/investigations/{id}/plan`, and paginated execution trace.
- Saved benchmark execution/results and finance-scenario endpoints.

Suggested modules under `backend/`: `schemas.py`, `sources/`, `replay.py`, `workers/`, `fusion.py`, `orchestration/graph.py`, `orchestration/providers/`, `policy.py`, `finance.py` and `benchmark/`. These are proposed future paths, not files already created.

Retain SQLite and existing evidence directories. Introduce schema migrations and persistent source, worker-execution, evidence, planner-attempt, trace-event, benchmark and finance records. The initial implementation can retain existing case/object storage while giving new records explicit schemas.

Use transactions for state change plus audit append. Add expected revisions and idempotency to new mutations. Use a serialized database write path with the initial single-process backend; do not let concurrently finishing workers independently commit interleaved case transitions. Persist job state so a restart marks interrupted jobs accurately and resumes or safely retries idempotent work.

SSE communicates monotonic event IDs and correlation IDs. Replay/view state and investigation execution have separate revisions. Long provider requests must not block FastAPI's event loop or freeze replay.

## 9. Frontend work

Split `frontend/App.tsx` incrementally into cockpit, timeline, investigation, case review, sources/health, benchmark and finance components. Retain existing scene controls and shared asset IDs.

Required UI details:

- Persistent source and simulation-time badge; distinct labels for development fixtures, synthetic replay and historical extract.
- September calendar, 2,880-position timeline, selected time, play/pause/seek and daily coverage.
- Selected boundary waterfall: input, downstream, authorized allocation, technical range and signed residual.
- W1-W4 worker cards showing actual status, findings, limitations and evidence links.
- Planner badge showing Granite, Gemini or rules; fallback reason and readable next action.
- Evidence-to-hypothesis list/graph and spatial coverage highlight; a simple evidence list is sufficient initially.
- Case ownership, notes, human disposition and JSON/Markdown export with linked source/worker/provider versions.
- Retry/cancel states, keyboard asset selection and recovery after refresh.

Do not animate fake agent conversations. Distinguish model decision justification from measured observations. Test narrow and laptop layouts; minimal browser testing of core workflows remains mandatory even when the optional drone/CV verification is deferred.

## 10. Independent evaluation

Keep the existing tests as regression coverage. Do not report their synthetic results as an independent benchmark of the new system.

Build an evaluator separate from worker/inference code. Freeze the candidate commit and thresholds before generating held-out cases. Use independent physical parameters or human-authored golden fixtures; do not import detector loss coefficients into the challenge generator.

Vary branch, timing, severity, noise and mixed mechanisms. Include normal demand, legitimate demand shifts, missing/stale telemetry, topology mismatch, under-registration, authorized unmetered load, elevated technical loss and multiple plausible causes. Use a declared initial suite, for example 24-40 cases spanning these strata; report per-stratum counts and treat small samples as limited evidence.

Compare:

- B0: fixed threshold and ranked areas.
- B1: mandatory workers plus deterministic next-action rules.
- B2: identical workers and evidence plus the adaptive planner.

Use equal observed inputs, available tools and inspection budgets. Record planner provider on every B2 case. A controlled Granite comparison pins Granite; a controlled Gemini comparison pins Gemini. Label production-style failover as a separate mixed-provider run so it cannot be attributed entirely to Granite.

Score detection recall, false alerts per valid clean branch-hours, smallest-observable-boundary accuracy, simulation delay, correct next action, action cost, planner latency and trace completeness. Publish denominator definitions and utility weights before execution. Reveal sealed truth only to the scorer after the inference run. Report all failures and abstentions.

Without drone/CV, restrict action/CV claims to available capabilities; do not treat skipped vision as a successful negative observation. A basic benchmark is a release requirement; larger challenge sets and ablations can follow later.

## 11. Finance and impact ledger

Implement a deterministic function over an explicit hypothetical intervention, date window, affected area, effectiveness range, tariff/supply-cost assumptions, collection fraction and investigation/repair/API costs.

Keep separate outputs:

- Physical avoided supply kWh, only for a justified physical intervention baseline.
- Newly billable kWh and invoice value.
- Modeled collected cash, explicitly conditional on collection assumptions.
- Avoided supply expense, investigation/repair/API costs and modeled net benefit.

Use `net = modeled cash + avoided supply expense - total cost`; do not add invoice value again. An under-registration correction does not automatically reduce delivered energy. An alert alone creates no realized recovery. Missing payment data means actual collection is unknown even when a user explores assumed collection fractions.

Provide conservative/base/optimistic assumption sets and at least one negative-net scenario. Show source, units, scope and assumptions beside every KPI. Actual BESCOM realized savings remain unknown. Financial outputs never feed challenge truth or force a favorable planner score.

## 12. Implementation sequence and checkpoints

### M0 - restore and baseline the existing application

Bring the repository into the workspace, inspect applicable repository instructions, install locked dependencies and reproduce the current frontend build and backend tests. Record the actual baseline commit and failures. Preserve existing useful tests and case behavior. Add the final PRD and this scope update to project documentation.

Exit: existing app starts, the current baseline is measured, and core versus optional work is explicit.

### M1 - contracts and September replay

Implement source/time contracts, fixture adapter, configurable interval count, timeline/seek, quality-aware rollups and source badges. Extract observation ingestion from the generator.

Exit: all 2,880 interval positions are addressable against a labeled development month, with reproducible daily totals. Official dataset verification remains pending until onboarding.

### M2 - W1-W4 and fusion

Wrap accounting, add bounded physics, chronological W3 baselines, W4 localization and typed evidence fusion. Persist executions and support deterministic case recommendations first.

Exit: missing-data, legitimate-load and unexplained-residual cases show correct worker findings, alternative causes and smallest justified area.

### M3 - Granite, Gemini and policy

Implement provider healthchecks/adapters, actual tool-calling loop, bounded LangGraph routes, fallback, policy validation and trace events. Use mocked provider responses for failure tests and live credentials for separate capability checks.

Exit: one live provider produces a valid evidence-grounded action; forced Granite failure reaches Gemini when configured; both failures reach rules without duplicate actions. If credentials are unavailable, mark live integration pending rather than treating mocked responses as proof.

### M4 - complete the operator workflow

Connect timeline, workers, hypotheses, provider identity, next-action tasks, case revision/history and export. Preserve replay timestamps through seeking, refresh and restart. Add system health and useful error recovery.

Exit: one complete investigation finishes through human disposition without a drone dependency.

### M5 - benchmark and finance

Freeze candidate settings, execute the independent baseline comparison, persist results and add the conditional ledger with accounting tests. Surface actual measured outcomes and limitations.

Exit: B0/B1/B2 results are reproducible and attributed to the correct providers; finance includes unknown actual collection and a negative-net example.

### M6 - source onboarding, when the files are ready

Connect the BESCOM historical extract and the frozen month adapter, verify original bytes/hashes, validate counts and IDs, and repeat replay/aggregation/quality checks. Inspect the historical source's period caveat. Re-evaluate thresholds against the replay's scale using declared development calibration, without opening held-out truth. Changing thresholds requires a new version and fresh benchmark disclosure.

This milestone can start as soon as files arrive. It is independent of provider/UI implementation but required before declaring the PRD's official source gate complete.

### M7 - optional drone/CV, last

Enable proposals only after localization and feature checks. Reuse reviewer gates and mission/capture code. Verify actual scene frames, hashes, positive/negative/occluded views and failure recovery before exposing automated findings. If skipped, ship the core release with a visible capability status and human field-check path.

## 13. Four-person ownership and 48-hour integration target

Assumption: four developers; existing app baseline is usable; provider accounts are prepared; dataset onboarding is deliberately deferred. This is an aggressive integration target, not a guarantee. An individual developer should follow the same milestones sequentially and re-estimate after baseline reproduction.

- Developer A: source adapters, replay, W1/W2, time handling and numerical tests.
- Developer B: schemas, orchestration, provider adapters, fusion/policy, persistence and failure recovery.
- Developer C: month controls, cockpit integration, worker trace, case UX and browser verification.
- Developer D: W3/W4 integration support, independent challenge ownership, benchmark, finance and demo evidence. A freezes detector/threshold settings before D creates the sealed challenge; D must not tune the detector against held-out truth.

Keep shared contracts agreed before parallel changes. One owner controls schema migrations and integration. These are team assignments for implementation, not instructions to create coding subagents during this planning task.

Suggested integration windows:

- H0-4: baseline reproduction, schemas, feature flags and provider capability spikes.
- H4-12: month replay plus W1/W2; UI timeline and provider adapters proceed in parallel.
- H12-20: W3/W4, fusion, policy, bounded planner/fallback and persisted trace.
- H20-28: complete case workflow, uncertainty views, export and core browser checks.
- H28-36: frozen independent benchmark, finance and provider failure tests.
- H36-42: repair integration issues, measure performance, finish source/health labels and demo flow.
- H42-48: feature freeze, three core workflow rehearsals, restart/recovery checks and package handoff.

Drone/CV is outside this core 48-hour commitment. Start it only after core gates pass and there is an explicit time budget. Dataset delivery/verification is also not assumed complete merely because the integration window ends.

## 14. Test and release gates

Required automated coverage:

- Accounting arithmetic, signed residuals, exact cuts, missing/invalid/duplicate readings and unit validation.
- September boundaries, 2,880 intervals, UTC/IST conversion, coverage-aware aggregation and replay determinism.
- W3 warmup and prevention of future-data leakage.
- Fusion contradictions, correlation handling, localization limits and unavailable commercial fields.
- Provider parsing, timeouts, authentication/rate errors, failover, budgets and provider attribution.
- Invalid evidence/tool/asset rejection; denied actions cannot bypass policy through fallback.
- Idempotent tool execution, revision conflicts, atomic audit appends and restart recovery.
- Benchmark truth isolation, independently constructed fixtures and fair comparison budgets.
- Finance category separation, unknown payments, no double-counted invoice/cash and negative net outcomes.

Core browser scenarios: normal interval; incomplete cut; unexplained residual; Granite or Gemini action; forced provider fallback; human disposition; seek/refresh/reopen/export. Run at least three consecutive end-to-end rehearsals with no unrecovered crash. This core QA is retained; only drone/CV QA is optional.

Initial performance targets: at least 30 FPS on a declared laptop; local deterministic interval processing p95 below 500 ms over at least 100 intervals; responsive UI during provider requests. Report actual provider latency and usage rather than assuming either provider is faster or cheaper.

Release gates:

1. Replay and source labels are truthful; official source status is either verified or explicitly pending.
2. W1-W4 core modes, fusion and policy pass their meaningful numerical/behavioral tests.
3. At least one live planner provider is verified for an agent-enabled release. Rules-only operation is labeled a deterministic preview.
4. Failover and action idempotency work; export names the provider that actually decided each step.
5. A complete human-reviewed case survives refresh/restart.
6. Independent results and conditional finance are displayed without fabricated wins.
7. Core browser rehearsals pass. Optional vision has a separate enabled/verified gate.

These gates define the revised scope. They do not claim the original PRD's Granite-specific or drone-specific gates passed when Gemini is used or vision is omitted.

## 15. Handoff and five-minute demonstration

Handoff: working source, lockfiles, migration/startup scripts, final PRD plus scope decisions, environment-variable template without credentials, test commands, source status/manifest, benchmark configuration/results, sample evidence-linked case export and known limitations.

Demo sequence:

1. Show BESCOM historical context when onboarded, or its pending source status without placeholder values.
2. Show September replay and a selected area's measured cut and coverage.
3. Open an investigation and show actual W1-W4 findings and alternative causes.
4. Show the active Granite/Gemini planner, permitted next action and policy decision.
5. Record a human outcome and open its export/audit history.
6. Show independent comparison and conditional impact, including failures or negative net results.

Use a separately labeled challenge case for a positive demonstration if the replay has no supported anomaly. Do not edit historical/source readings to ensure a dramatic result. If optional vision is completed, add it between planning and human review; otherwise show the field-check task.

## 16. Implementation references

- Local governing source: `VIDYUT_TRACE_FINAL_PRD.pdf`, especially sections 3, 6-7 and 10-14. User decisions in this plan override its provider fallback and optional-vision priority.
- Reviewed repository: https://github.com/taruncodes07/IBM-Skillsbuild-National-Finale/tree/8e8a59fe452bf42f1c9c96b7a853af64db9fcc73
- Existing acceptance limitations: https://github.com/taruncodes07/IBM-Skillsbuild-National-Finale/blob/8e8a59fe452bf42f1c9c96b7a853af64db9fcc73/docs/ACCEPTANCE.md
- IBM tool-calling workflow: https://www.ibm.com/watsonx/developer/capabilities/tool-calling/
- Google Gemini function calling: https://docs.x.ai/developers/tools/function-calling
- Google Gemini structured outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs

Provider documentation was consulted on 25 October 2026. It supports the adapter approach, not authenticated account availability. Pin actual SDK versions and model IDs after real capability checks.


Implementation update: added and live-ran a nine-case pinned Granite first-action pilot, separate from full adaptive B2. Six Granite proposals matched the predeclared triage rubric; rules matched nine. All nine proposals passed policy. Failures and mismatches remain visible, and no action-cost or field accuracy claim is made. See app/docs/BUILD_STATUS.md.

Policy update: normal and nonpersistent states now block diagnostic escalation independently of model or operator choice. The same nine-case Granite pilot matched the conservative rubric on 9/9 after this guard, with the earlier 6/9 report preserved. This is regression verification rather than a new independent benchmark.
