# Grid Trace — Electricity Distribution Digital Twin

> Historical specification for the original scenario laboratory. The governing local specification is `../VIDYUT_TRACE_FINAL_PRD.pdf`; current implementation priorities and branding follow `../GRID_TRACE_BUILD_PLAN.md` and `docs/BUILD_STATUS.md`.

## Product requirements document

**Version:** 1.0 · **Prepared:** 24 October 2026 · **Status:** Build-ready hackathon specification  
**Team:** Four people · **Build window:** 24–48 hours  
**Primary deliverable:** A working browser application with a functional 3D distribution simulation, explainable loss detection, targeted simulated drone inspection, and an auditable human review workflow.

> **Product promise:** Find the smallest observable network section with persistent unexplained energy loss, gather visual evidence where useful, and help a person decide the next investigation step.
>
> **Demo disclosure:** All network assets, meter readings, incidents, drone flights, and inspection images in the MVP are synthetic. The system demonstrates an investigation workflow; it does not establish real-world theft, field accuracy, or recovered revenue.

## Contents

1. [Executive summary](#1-executive-summary)
2. [Problem, evidence, and factual boundaries](#2-problem-evidence-and-factual-boundaries)
3. [Users, outcomes, and user stories](#3-users-outcomes-and-user-stories)
4. [MVP scope and priorities](#4-mvp-scope-and-priorities)
5. [Product experience and functional requirements](#5-product-experience-and-functional-requirements)
6. [Simulation and energy reconciliation](#6-simulation-and-energy-reconciliation)
7. [Anomaly detection and investigation ranking](#7-anomaly-detection-and-investigation-ranking)
8. [Simulated drone inspection and computer vision](#8-simulated-drone-inspection-and-computer-vision)
9. [Case management and accountability](#9-case-management-and-accountability)
10. [Architecture and interfaces](#10-architecture-and-interfaces)
11. [Data contracts and schemas](#11-data-contracts-and-schemas)
12. [Nonfunctional requirements](#12-nonfunctional-requirements)
13. [Demo scenarios and presentation](#13-demo-scenarios-and-presentation)
14. [Acceptance criteria and verification](#14-acceptance-criteria-and-verification)
15. [Success metrics and evaluation](#15-success-metrics-and-evaluation)
16. [Four-person delivery plan](#16-four-person-delivery-plan)
17. [Risks, tradeoffs, and mitigations](#17-risks-tradeoffs-and-mitigations)
18. [Post-hackathon path and references](#18-post-hackathon-path-and-references)

## 1. Executive summary

GridTrace is a simulation-backed investigation workspace for electricity distribution losses. A live 3D neighborhood represents feeders, transformers, sectional monitoring points, household meters, poles, and service connections. The scene and analytical panels share the same topology, clock, readings, and incident state.

The operator observes an unexplained energy imbalance, narrows it from feeder to transformer to monitored branch, and reviews possible causes. If overhead connections are visible, the operator approves a simulated drone inspection. A virtual RGB camera captures the scene; a small image-processing pipeline highlights candidate extra wire segments. The resulting evidence joins the meter analysis in a case that a human can assign, investigate, dismiss, or resolve with a recorded reason.

The central demonstration is the complete loop:

**Simulate → reconcile → localize → inspect → review → record → replay.**

The 3D view must be operational: clicking an asset changes the investigation context, injecting an incident changes upstream measurements, and a drone inspection produces images from that scene. A cinematic animation disconnected from the data does not satisfy the product.

### 1.1 Refined problem statement

Build an explainable electricity-loss investigation system that combines sectional energy accounting with a functional 3D digital twin and targeted simulated drone RGB inspection to prioritize suspected unmetered consumption, distinguish alternative explanations, and maintain an accountable human review trail.

### 1.2 Assumptions and conversation continuity

The earlier discussion confirms the electricity-theft/accountability problem, a requirement to show 3D simulation, interest in drones for validation, and the decision to use a digital twin. Retrieved assistant messages contained reference placeholders rather than their full responses. Consequently, no unavailable earlier statistics or implementation promises are treated as established facts. The detailed network size, architecture, thresholds, and milestones below are explicit design decisions for this specification.

An India-oriented distribution-utility setting is assumed for context; the demonstration uses a fictional neighborhood. No utility partnership, real AMI connection, real drone, proprietary theft dataset, or GPU is assumed. Four teammates with basic web/backend skills and one ordinary development laptop must be sufficient.

## 2. Problem, evidence, and factual boundaries

### 2.1 Is the problem real, and how large is it?

Distribution losses are a material operational problem. India's Ministry of Power reported aggregate technical and commercial (AT&C) losses of **15.04% for FY2024–25** in a January 2026 release. That figure describes aggregate distribution performance; it is **not a national electricity-theft rate**. [S1]

Published research treats nontechnical losses as including theft, faulty meters, and billing errors. These categories require different remedies; a detector must not collapse them into one accusation. [S2]

The practical relevance of energy accounting is supported by India's Bureau of Energy Efficiency framework for annual distribution energy audits and periodic energy accounting. RDSS also includes consumer, distribution-transformer, and feeder smart metering. Neither source implies that complete, synchronized telemetry is available in every neighborhood. [S3, S4]

**Extent caveat:** This PRD does not estimate theft-only national kWh or monetary losses. Those require a defined geography, time period, verified theft attribution, and an appropriate financial methodology. Multiplying the national AT&C percentage by electricity sales or tariffs would not provide a defensible theft estimate.

### 2.2 Causes and alternative explanations

The investigation must account for:

- Unmetered connections, bypassed consumption, or meter under-registration.
- Legitimate technical dissipation in conductors and transformers.
- Meter faults, calibration errors, counter resets, or meter replacement.
- Missing, delayed, duplicated, or misaligned readings.
- Incorrect consumer-to-transformer mapping or changed switch configuration.
- Authorized unmetered loads, including public lighting where applicable.
- Legitimate changes in occupancy or consumption patterns.
- Distributed generation or storage flows in a future deployment.
- Billing and collection problems, which are outside the MVP's physical-energy reconciliation model.

Low consumption alone is insufficient evidence of wrongdoing. A positive residual is an investigation signal, not a legal finding.

### 2.3 Why combine these capabilities?

Meter analytics identify where an imbalance is observable. A topology-aware view makes its boundaries understandable. Targeted imagery may reveal a physical connection that warrants inspection. Case management makes ownership, uncertainty, decisions, and follow-up visible.

Drones are already used for visual and sensor-based overhead infrastructure inspection. This supports the inspection concept, not a claim that RGB imagery can establish theft. [S5] The product-specific inference is that imagery can supplement energy-accounting investigations when relevant overhead assets are visible.

### 2.4 Claims the MVP must avoid

- AT&C loss, technical loss, unexplained energy, and confirmed theft are not interchangeable.
- RGB images cannot measure current, see internal meter tampering, prove a cable is energized, or determine billing authorization.
- Thermal hot spots, if explored later, can indicate faults or loading and do not prove theft.
- A digital twin backed only by simulated telemetry is a **simulation-backed prototype**, not a continuously synchronized operational twin of a real utility.
- Household attribution is unavailable when instrumentation only supports branch-level localization.
- No automatic penalties, disconnections, public accusation, or enforcement action are permitted.

## 3. Users, outcomes, and user stories

### 3.1 Primary users

**Distribution analyst:** Needs to identify persistent unexplained losses, see data quality, and prioritize limited inspection resources.

**Inspection reviewer:** Needs a bounded task, contextual imagery, uncertainty, and a place to record observations.

**Supervisor/auditor:** Needs ownership, decision reasons, timestamps, evidence provenance, and visibility into unresolved cases.

**Hackathon presenter:** Needs deterministic scenarios, an understandable 3D scene, and a reliable five-minute demonstration.

### 3.2 User stories

- **US-01:** As an analyst, I can click a feeder, transformer, branch, or meter and see its parent, downstream assets, readings, and quality state.
- **US-02:** As an analyst, I can compare input energy, downstream energy, expected technical losses, and the unexplained residual for the same interval.
- **US-03:** As an analyst, I can identify the smallest instrumented section with persistent excess residual without treating every home in it as suspicious.
- **US-04:** As an analyst, I can inspect the reasons behind a household watchlist signal and see legitimate alternative causes.
- **US-05:** As a reviewer, I can approve a targeted simulated RGB mission and inspect original and annotated frames.
- **US-06:** As a reviewer, I can mark imagery inconclusive and request a meter/field inspection instead of forcing a theft decision.
- **US-07:** As a supervisor, I can assign a case, review its event history, and require a reason for resolution or dismissal.
- **US-08:** As an auditor, I can export a case containing the exact readings, model versions, image hashes, actors, and decisions used.
- **US-09:** As a presenter, I can inject and reset scenarios and replay the same seed with the same results.
- **US-10:** As a reviewer, I can distinguish synthetic ground truth from observations available to the detection system.

## 4. MVP scope and priorities

### 4.1 P0 — required within 24 hours

- One fictional 3D neighborhood: **2 feeders, 4 transformers, 8 monitored branches, and 24 household meters**.
- Each feeder supplies two transformers; each transformer supplies two branches; each branch supplies three households.
- Metered boundaries at two feeder outputs, four transformer secondaries, eight branch entrances, and 24 households: **38 measurement streams**.
- Seeded consumption profiles, technical-loss model, interval telemetry, play/pause/speed/reset, and scenario injection.
- Feeder/transformer/branch reconciliation with missing-data handling and persistent anomaly alerts.
- Asset selection, simple history charts, an alert queue, and readable localization in the scene.
- One targeted simulated drone workflow with scene-derived RGB capture and functional image-based candidate detection.
- Persistent cases, assignments, evidence, review decisions, and append-only application audit events.
- A working positive scenario, clean negative scenario, and missing-meter negative control.
- Visible synthetic-data labels and a downloadable case report.

### 4.2 P1 — complete during hours 24–48

- Meter-fault, legitimate load-change, hidden-bypass, topology-error, and occlusion scenarios.
- More camera viewpoints, parameter variation, and a held-out synthetic evaluation suite.
- Reviewer/supervisor permissions enforced by the backend and better audit export.
- Persistent replay snapshots and robust browser refresh recovery.
- Performance polish, accessibility checks, and a recorded backup demonstration.

### 4.3 P2 — optional only after P0/P1 pass

- An independent statistical anomaly detector for comparison with the rule baseline.
- Licensed real inspection-image examples shown separately from simulated captures.
- Basic simulated voltage/phase overlays, richer scenery, or an alternative route planner.

### 4.4 Explicitly outside hackathon scope

Physical drone flight, drone autopilot integration, live AMI/SCADA ingestion, full AC power flow, protection coordination, real GIS reconstruction, satellite theft detection, production IAM, utility billing, legal evidence certification, a newly trained general-purpose theft vision model, and autonomous enforcement.

The project is a hackathon application specification; it does not include building a real distribution network or obtaining field permissions.

## 5. Product experience and functional requirements

### 5.1 Main workspace

The center contains the 3D neighborhood. A left panel provides asset navigation and alerts. A right panel shows the selected asset's energy balance, history, and investigation controls. A bottom timeline controls simulation time and replay. A persistent banner says **Synthetic demonstration**.

**FR-01 — Scene interaction:** Orbit, pan, zoom, select assets, focus a selected branch, and reset the camera. Provide a parallel text asset list so navigation does not depend solely on 3D picking.

**FR-02 — Live state:** Display labels for normal, unexplained loss, data incomplete, and under review. Use icons/text as well as color. Flow animation is illustrative; its speed must not be presented as measured electrical current.

**FR-03 — Shared state:** Every object has the same stable asset ID in the scene, topology, meter data, alert, mission, and case. No hard-coded alert highlighting disconnected from the analysis output.

**FR-04 — Simulation control:** Play, pause, single-step, and select 1×/10×/60× playback. One simulated 15-minute interval takes 15 seconds at 1×, 1.5 seconds at 10×, and 0.25 seconds at 60×. Both simulated time and wall time remain visible. Batch updates at high speed without losing interval calculations.

**FR-05 — Incident control:** A presenter-only drawer can select incident type, location, start/end interval, and severity. Hide incident ground truth from the ordinary analyst view until explicitly revealed.

### 5.2 Analysis and inspection flow

**FR-06 — Reconciliation:** Show an expandable balance with boundary meter IDs, interval, raw measurements, expected technical loss, uncertainty threshold, residual, and missing inputs.

**FR-07 — Alerts:** Create one active alert per section and rule family, update its interval history, and avoid duplicate cases on every replay tick. Explain which rule fired and how long it persisted.

**FR-08 — Localization:** Highlight the smallest valid measured boundary. Display “branch-level localization; household unresolved” when finer attribution is unsupported.

**FR-09 — Inspection approval:** Require an explicit reviewer action before starting a simulated mission. Show target section, included poles, observation limits, and synthetic status.

**FR-10 — Evidence review:** Present original RGB frame beside annotated output, capture time, camera pose, detector version, candidate regions, and a conclusion of candidate visible feature, no visible candidate, or inconclusive.

**FR-11 — Failure recovery:** A failed image-processing job leaves energy analysis intact and offers retry or “continue without visual evidence.” No CV output may silently become a negative finding.

### 5.3 Case and reporting flow

**FR-12 — Case lifecycle:** Support creation from an alert, assignment, mission/evidence linkage, reviewer notes, resolution/dismissal reasons, reopening, and a chronological activity trail.

**FR-13 — Export:** Download a self-contained JSON case report and a readable Markdown summary. Include image filenames/hashes and provide the associated original/annotated PNG downloads; clearly state when images are separate files rather than embedded in the report.

**FR-14 — Reset semantics:** Resetting simulation starts a new run ID. Existing cases remain attached to their original run and do not silently change with the new scene.

## 6. Simulation and energy reconciliation

### 6.1 Network and clock

Use a radial directed graph with explicit metering boundaries. Households connect to their branch, branches to transformer secondaries, and transformers to feeders. Pole geometry supports inspection but does not create additional measurements. Store local 3D coordinates in meters; do not label them GPS coordinates.

Generate seven clean baseline days and one scenario day with **15-minute UTC intervals**. The interface may display Asia/Kolkata time, with the zone named. Each run stores its seed, topology version, scenario settings, and rule version. Replay uses the simulation clock, never the browser's current wall clock for analytical windows.

### 6.2 Consumption and measurement generation

Create varied household daily profiles with morning/evening peaks, random noise, and household-specific magnitude. Select these as illustrative synthetic distributions, not representative Indian household statistics.

Maintain two separate layers:

1. **Private simulator truth:** Actual household demand, added unmetered load, injected faults, actual technical losses, and object identity.
2. **Observed telemetry:** Meter readings after noise, under-registration, missingness, delay, or faults.

Build upstream true energy from the sum of physical downstream demand and modeled segment losses. An unmetered load must increase energy recorded at its upstream boundaries even when absent from household readings. Meter under-registration changes the reported reading without reducing physical demand. Missing telemetry is null, never zero.

Expected technical losses used by the detector are estimated from clean baseline observations and configuration; they must not read incident truth. A lightweight model such as `a × duration_hours + b × aggregate_load_kW² × duration_hours` is sufficient. Fit or set coefficients per boundary and document their units and assumed uncertainty. This is an accounting approximation, not a solved electrical load-flow model.

### 6.3 Section balance

For interval `t` and boundary `s`:

```text
R(s,t) = E_in(s,t)
         - SUM(E_out(k,t) for k in the downstream metered cut)
         - E_authorized_unmetered(s,t)
         - L_expected(s,t)

residual_ratio = R(s,t) / max(E_in(s,t), epsilon_kWh)
```

All terms are **interval kWh**, not instantaneous kW or raw cumulative counters. The downstream cut must be disjoint and cover the intended boundary exactly once:

- Feeder: compare feeder output with its two transformer-secondary meters. Expected loss includes intervening feeder conductors and transformer losses.
- Transformer secondary: compare its secondary meter with the two branch-entrance meters. Expected loss covers only the wiring between these boundaries.
- Branch: compare branch-entrance energy with its three household meters and any declared authorized unmetered load. Expected loss covers branch and service wiring.

Do not subtract transformer meters and their household descendants in the same balance. Do not sum feeder, transformer, and branch residuals into a total: their regions overlap. Aggregate only disjoint regions, with the boundary selection recorded.

**Worked synthetic example:** Branch input is 12.5 kWh, household sum is 10.5 kWh, authorized unmetered load is 0, and expected technical loss is 0.4 kWh. The residual is 1.6 kWh, or 12.8% of input. That is unexplained energy for that boundary and interval; it is not yet confirmed stolen energy.

### 6.4 Data validity gates

- Align all required measurements to the same interval and topology version.
- Require complete boundary coverage for loss classification in P0. Show completeness even when incomplete.
- Reject duplicates by meter/interval/revision; accept a later revision through an explicit recomputation event.
- Detect cumulative-counter reset or rollover before converting counters to interval energy. Generated P0 inputs may use interval energy directly.
- Missing meter, stale data, timestamp mismatch, invalid negative interval energy, and unknown topology produce `data_incomplete` or `invalid`, not theft alerts.
- Unexpected negative residuals produce a mapping, export, or data-quality review signal. Never silently clamp them out of the stored balance.
- Authorized unmetered load is a declared estimate with uncertainty. Do not derive it from hidden event labels.

## 7. Anomaly detection and investigation ranking

### 7.1 Explainable baseline

**Section rule:** On valid intervals, flag excess residual when:

```text
R > max(absolute_floor_kWh, ratio_floor × E_in, 3 × sigma_residual_kWh)
```

Start with a demo absolute floor of **0.25 kWh**, a ratio floor of **8%**, and persistence of **3 consecutive valid intervals**. These are initial synthetic-demo settings, not field-validated thresholds. Calibrate on clean calibration runs and freeze before evaluation. `sigma_residual_kWh` is the clean-baseline residual variability, with a positive floor to avoid zero-noise artifacts.

Three complete affected intervals imply a nominal 45-minute persistence window. For events beginning within an interval, report actual detection delay from event onset; do not promise an exact 45-minute field response.

**Meter watchlist rule:** Compare a meter with its own seven-day same-time baseline. A drop below 50% of expected usage for three valid intervals may add a “consumption change” reason only when the containing branch already has excess residual. Require a minimum baseline demand floor. Label small-sample baseline uncertainty. Do not create a theft case solely from this rule.

**Data-quality rule:** Missing data and inconsistent counters create quality events routed separately from unexplained-loss cases.

### 7.2 Localization and prioritization

Evaluate from feeder down to branch. A feeder anomaly does not imply that every transformer is abnormal. Prefer the smallest valid monitored boundary with excess residual. If downstream measurements are unavailable, retain the coarser location and say why.

Prioritize actionable sections by persistent unexplained kWh, persistence, and data quality. Within a section, show meter reasons separately; ties remain unresolved. A hidden direct tap can affect no household meter pattern at all, so the system must still localize the branch without inventing a suspect household.

Display an **investigation priority**, not a probability of theft. Show component reasons instead of a fabricated calibrated confidence percentage. The vision detector's match score is also distinct from theft likelihood.

### 7.3 Separation from ground truth

The analysis module receives only observed readings, approved topology, baseline parameters, and declared authorized loads. It cannot query scenario truth, injected object labels, or true consumption. Evaluation joins predictions with truth after inference. Camera detection follows the same rule: pixels and approved asset geometry are allowed; incident labels and injected-object bounding boxes are not.

## 8. Simulated drone inspection and computer vision

### 8.1 Targeted mission behavior

After a reviewer approves a mission for a flagged branch, animate a drone along three to five predefined local waypoints around its poles and service connections. Mission states are `queued`, `approved`, `flying`, `capturing`, `processing`, `completed`, `failed`, and `cancelled`. Wall-time flight animation lasts about 10–20 seconds and is independent of paused telemetry replay.

Draw the camera frustum, show the target asset IDs, and capture two or three 640×480 RGB frames from the actual scene. During capture hide selection outlines, alert colors, presenter labels, and debug objects. These overlays would leak the answer to the detector. Simulated waypoints and clearances are visual design choices, not a real-world safe-flight plan.

### 8.2 Minimum functional CV implementation

Use a deliberately constrained pixel-based detector for stylized overhead-wire geometry:

1. Render the current RGB camera frame with fixed camera calibration.
2. Crop the overhead inspection region; run grayscale conversion, edge detection, and line-segment/Hough detection with OpenCV.
3. Compare detected line segments with projected **approved** service-wire paths, using a documented pixel tolerance and minimum length.
4. Group unmatched segments into candidate extra-connection regions, preserving the original frame.
5. Return boxes/line overlays, a geometric match score, detector parameters/version, and an observation-limit note.

This is a functional CV pipeline operating on pixels. It is intentionally limited to controlled synthetic views and must be described that way. It is not a general trained model for real theft detection. An added wire must use the same material family as approved wires so a unique color does not encode the incident label. A decorative line is a negative control.

For P0, use two fixed unobstructed views and test both candidate-present and candidate-absent frames. For P1, vary camera pose, wire contrast, clutter, and partial occlusion. If geometry, lighting, or registration prevents a usable observation, return `inconclusive`.

### 8.3 Evidence interpretation

The evidence card may state **“Candidate extra overhead connection visible; authorization and energization unverified.”** It must not say “theft confirmed by drone.”

An RGB-negative result does not clear a persistent energy imbalance. Indoor bypasses, underground connections, thin wires, and occlusion may be invisible. Route these cases to meter/field inspection. A visible extra line may be authorized or unrelated; the reviewer must consider this before deciding next steps.

### 8.4 Fallback disclosure

If functional image processing is not completed, retain captured frames and allow manual annotation. Label the build **manual visual review; CV incomplete** and mark FR-10/AC-06 partially unmet. Pre-scripted boxes, object-ID masks, or scene truth must never be presented as CV inference. Pre-recorded imagery may serve as an explicitly labeled backup, but does not pass the live-capture acceptance criterion.

## 9. Case management and accountability

### 9.1 Lifecycle

```text
open → triaged → inspection_requested → evidence_ready → under_review
under_review → field_check_required | resolved | dismissed
field_check_required → under_review
resolved | dismissed → reopened → triaged
```

Cases can move from triaged directly to under_review when imagery is irrelevant. Failure or cancellation of a mission leaves the case open and records the reason.

Allowed dispositions include data-quality issue, authorized load, technical-loss/model issue, meter fault, suspected unmetered consumption requiring field verification, and inconclusive. A simulator-revealed truth label may appear in an evaluation panel, but is not a reviewer finding from field evidence.

### 9.2 Required accountability controls

- Every case has an owner or is explicitly unassigned, a priority, linked boundary, run ID, and creation time.
- Every transition records actor, previous/new state, reason, wall timestamp, and relevant simulation timestamp.
- Resolution and dismissal require a disposition and reason. Evidence is linked, not overwritten.
- Reviewers can record disagreement and reopen a case. No silent deletion of decisions.
- Role rules: analyst creates/triages; reviewer approves missions and records observations; supervisor resolves/dismisses/reopens. Demo identities are seeded and explicitly labeled simulated.
- P0 may use a local identity selector; it is not secure authentication. P1 enforces role checks server-side, but remains a local demo unless real authentication is added.
- Reprocessing creates a new analysis/evidence revision and preserves earlier versions.
- Store SHA-256 hashes for original images and exports. Hashes detect changes relative to stored values; a local append-only log is not independently tamper-proof or legally certified chain of custody.

Accountability metrics concern case ownership and traceable decisions. The MVP makes no claim to detect staff collusion or prove institutional misconduct.

## 10. Architecture and interfaces

### 10.1 Recommended implementation

Use **React + TypeScript + Vite** for the application, **Three.js through React Three Fiber** for the 3D scene, and **FastAPI + Python** for simulation, reconciliation, CV, and case APIs. Use **SQLite** for structured records and local disk for PNG evidence. This keeps the implementation local, inspectable, and GPU-independent. Pin actual dependency versions when building; this PRD does not prescribe unverified latest versions.

Use ordinary HTTP commands and **Server-Sent Events (SSE)** for telemetry/alert updates. A WebSocket is optional, not required. Serve the compiled frontend locally with the backend for the final demonstration to reduce moving parts. No paid cloud service or external model API is required.

```text
Presenter controls ──> Simulator ──> Observed interval readings
                         │                      │
                         │                      v
                  Truth store          Reconciliation + rules
                  (evaluation only)            │
                                               v
React UI <──────── snapshots / SSE ───── Alerts + case service
   │                                           │
   v                                           v
3D scene + virtual camera ── RGB PNG ──> CV worker ──> Evidence
                                               │
                                               v
                                     SQLite + image files + export
```

The truth store is a separate module/database namespace excluded from ordinary analyst endpoints. The scene renderer may need physical geometry to render an injected wire, but the image-analysis API receives no truth IDs or labels.

### 10.2 Module ownership

- `simulation`: seeded profiles, incident truth, measurement generation, deterministic stepping.
- `analytics`: baseline fitting, validity gates, balances, persistence, localization, alert deduplication.
- `scene`: graph-to-3D mapping, selection, camera viewpoints, drone animation, RGB capture.
- `inspection`: mission state, image validation, OpenCV processing, evidence files.
- `cases`: transitions, role checks, notes, audit events, exports.

### 10.3 API contract

- `POST /runs`: seed, scenario configuration, and topology version → run ID.
- `GET /runs/{id}/snapshot`: coherent asset, reading, balance, and alert state at one simulation sequence.
- `POST /runs/{id}/control`: play/pause/step/speed; validate command and current run.
- `POST /runs/{id}/incidents`: presenter-only incident injection; never part of analyst inference.
- `GET /runs/{id}/events?after_seq=N`: SSE stream with monotonically increasing sequence IDs.
- `GET /assets/{id}/history?run_id=...`: aligned readings/balances for a bounded range.
- `POST /cases`: alert ID and idempotency key → existing or new case.
- `PATCH /cases/{id}`: expected revision, assignment/state/disposition/reason → new revision.
- `POST /cases/{id}/missions`: target asset IDs and approved waypoint preset → mission.
- `POST /missions/{id}/frames`: PNG, camera pose, capture sequence, and approved-geometry version → processing job.
- `GET /missions/{id}`: mission state, errors, and evidence references.
- `GET /cases/{id}/export?format=json|md`: frozen report with provenance and synthetic labels.

Reject invalid transitions and stale updates with explicit errors. Retries must not create duplicate cases, missions, or audit events. On SSE reconnection, fetch a fresh snapshot if the requested sequence is no longer available. Apply only monotonic sequences for the active run.

## 11. Data contracts and schemas

Use UUIDs or stable prefixed IDs, UTC ISO-8601 timestamps, explicit units, and a schema version. Foreign keys connect evidence to the exact case/run/analysis revision. Floating-point calculations must retain full precision until display rounding.

### 11.1 Asset and topology

```typescript
type Asset = {
  id: string;
  kind: 'feeder' | 'transformer' | 'branch' | 'household' | 'pole';
  label: string;
  parent_id: string | null;
  meter_id: string | null;
  position_m: [number, number, number];
  topology_version: string;
  provenance: 'synthetic' | 'real';
};
type Connection = {
  id: string;
  from_asset_id: string;
  to_asset_id: string;
  approved: boolean; // approved topology only in analytics API
  geometry_points_m: [number, number, number][];
  topology_version: string;
};
```

The private simulator can store injected geometry separately. `approved=false` incident connections are never returned to the detector as an answer key. Validate radial connectivity and parent membership before starting a run.

### 11.2 Observed interval reading

```json
{
  "schema_version": "1.0",
  "run_id": "run-042",
  "meter_id": "meter-branch-03",
  "asset_id": "branch-03",
  "interval_start": "2026-10-24T12:00:00Z",
  "interval_end": "2026-10-24T12:15:00Z",
  "energy_import_kwh": 12.5,
  "energy_export_kwh": 0.0,
  "quality": "valid",
  "received_at": "2026-10-24T12:15:01Z",
  "topology_version": "topology-1",
  "revision": 1,
  "provenance": "synthetic"
}
```

`quality` is `valid`, `missing`, `stale`, `invalid`, or `estimated`. Energy is nullable for missing values. Estimated readings do not pass the P0 full-coverage gate. MVP scenarios have no exports; nonzero export input returns an unsupported-flow quality state until bidirectional accounting is implemented.

### 11.3 Balance and alert

`Balance` requires `id`, `run_id`, `boundary_asset_id`, `interval_start/end`, `input_meter_id`, `output_meter_ids`, `input_kwh`, `output_sum_kwh`, `authorized_unmetered_kwh`, `expected_loss_kwh`, `residual_kwh`, `residual_ratio`, `sigma_kwh`, `threshold_kwh`, `completeness_ratio`, `validity`, `invalid_reasons[]`, `topology_version`, and `analysis_version`.

`Alert` requires `id`, `run_id`, `boundary_asset_id`, `first_interval`, `last_interval`, `rule_id`, `rule_version`, `consecutive_intervals`, `priority`, `reason_codes[]`, `balance_ids[]`, `status`, and `candidate_meter_ids[]`. Candidate meter membership is optional and never a confirmed attribution.

### 11.4 Private scenario truth

`ScenarioTruth` requires `event_id`, `run_id`, `type`, `target_asset_id`, `start/end`, `parameters`, `true_unmetered_kwh_by_interval`, `injected_geometry_refs[]`, and `seed`. Event types include `visible_unmetered_load`, `meter_underregistration`, `missing_telemetry`, `legitimate_load_change`, `hidden_bypass`, `topology_mismatch`, and `technical_loss_change`.

Store truth separately from observations. Never include `is_theft`, incident type, or true hidden load in a meter-reading feature payload.

### 11.5 Mission and evidence

`Mission` requires `id`, `case_id`, `run_id`, `target_asset_ids[]`, `status`, `approved_by`, `approved_at`, `waypoints_m[]`, `created_at`, `capture_sequence`, `failure_reason`, and `provenance`.

`Evidence` requires `id`, `case_id`, `mission_id`, `run_id`, `captured_sim_time`, `captured_wall_time`, `original_image_path`, `original_sha256`, `annotated_image_path`, `camera_pose`, `image_width/height`, `detector_version`, `parameters`, `approved_geometry_version`, `observations[]`, `observation_status`, `limitations[]`, and `provenance`.

Each observation stores a pixel bounding box or line endpoints, label `candidate_extra_connection`, and a clearly named `geometric_match_score`. `observation_status` is `candidate_found`, `no_visible_candidate`, or `inconclusive`. Scores must not be named `theft_probability`.

### 11.6 Case and audit event

`Case` requires `id`, `run_id`, `alert_id`, `boundary_asset_id`, `state`, `priority`, `assigned_to`, `created_by`, `created_at`, `updated_at`, `revision`, `disposition`, `decision_reason`, `evidence_ids[]`, and `provenance`.

`AuditEvent` requires `id`, `case_id`, `actor_id`, `actor_role`, `action`, `from_state`, `to_state`, `reason`, `wall_timestamp`, `simulation_timestamp`, `object_revision`, and referenced evidence/analysis IDs.

### 11.7 Provenance policy

Every reading, image, evidence card, report, and evaluation result identifies its source. Use distinct values for `synthetic`, `real`, and, for derived outputs, `mixed` where necessary. A real photograph displayed beside synthetic telemetry does not convert the case into a real-world detection. Any real asset used later needs its origin, permission/license, capture context, and annotation method recorded.

## 12. Nonfunctional requirements

- **NFR-01 — Responsiveness:** On the team's declared reference laptop and browser, target ≥30 FPS during normal orbit with 24 homes. Record device specifications. Reduce shadows/geometry if necessary.
- **NFR-02 — Analysis latency:** Target p95 ≤500 ms per interval update for all 38 streams, excluding artificial playback delays, measured over at least 100 updates.
- **NFR-03 — Inspection latency:** Target ≤3 seconds processing per 640×480 frame after upload on the reference device. Show progress and a retryable error after a bounded timeout.
- **NFR-04 — Determinism:** Same seed, topology, versions, and actions produce identical telemetry and alert intervals. Store camera presets for reproducible evidence; do not promise byte-identical GPU render output across devices.
- **NFR-05 — Local reliability:** After dependencies are installed, core demo works without internet access. Cases and evidence survive browser refresh/backend restart. Resume via a saved run snapshot or deterministic replay to the saved interval.
- **NFR-06 — Integrity:** Validate IDs, units, time ordering, finite numbers, image type/dimensions, and maximum upload size of 5 MB per PNG. Prevent arbitrary file paths in uploads/exports.
- **NFR-07 — Privacy:** Use fictional IDs and locations. No names, billing records, faces, or private property footage are required. Avoid recording irrelevant scene content.
- **NFR-08 — Accessibility:** Keyboard-accessible primary controls, clear focus, readable contrast, text equivalents for scene states, and a reduced-motion option.
- **NFR-09 — Observability:** Log run ID, sequence, processing duration, rule version, and errors. Never mix wall-time and simulation-time latency in metrics.
- **NFR-10 — Security boundary:** Bind the local prototype to localhost by default. Demo identity selection is not production authentication. No real customer data may be introduced under that access model.

## 13. Demo scenarios and presentation

### 13.1 Scenario A — visible unmetered overhead connection

Start clean, then inject an added physical load on branch-03 through a visible extra overhead connection. Upstream input rises while household meter totals exclude that load. After three qualifying intervals, branch-03 is flagged; unrelated branches remain normal. The operator creates a case, approves a mission, sees a candidate line in scene-derived imagery, and requests field verification with a reason.

Expected result: smallest monitored section found, useful visual candidate attached, no automatic theft verdict.

### 13.2 Scenario B — missing telemetry, not a loss accusation

One household meter stops reporting while actual demand continues. Show a quality warning, incomplete balance, and no valid branch theft classification. Restore the reading and recompute with a revision event.

Expected result: missing data is not converted to zero consumption or an inspection accusation.

### 13.3 Scenario C — clean and legitimate behavior changes

Run a clean scenario with normal modeled technical losses. Separately increase or reduce a legitimate household load while both upstream and household readings change consistently.

Expected result: no persistent unexplained-loss case. A consumption-pattern change alone cannot trigger a theft conclusion.

### 13.4 Scenario D — meter fault / under-registration

Reduce one meter's reported energy without adding a visible external wire. The section residual and consumption-change reason appear, but imagery finds no reliable candidate.

Expected result: retain the case and route it to meter inspection; do not distinguish fault from intentional tampering without further evidence.

### 13.5 Scenario E — hidden bypass or occluded wire

Inject unexplained load with no camera-visible connection, or hide the connection behind scene geometry.

Expected result: electrical anomaly persists; RGB output is no visible candidate or inconclusive. Lack of visible evidence is not exoneration.

### 13.6 Scenario F — mapping or technical-loss mismatch

Use a stale consumer mapping or increased actual conductor loss while analytics retain baseline assumptions.

Expected result: the system surfaces an unexplained or inconsistent balance and alternative explanations. A reviewer records a mapping/model investigation rather than asserting theft. Perfect automatic cause classification is not an MVP requirement.

### 13.7 Five-minute presentation sequence

1. **0:00–0:35:** Explain the operational problem and synthetic-data boundary.
2. **0:35–1:15:** Explore the live 3D topology and a clean branch balance.
3. **1:15–2:10:** Inject Scenario A, accelerate replay, and open the persistent alert with its arithmetic.
4. **2:10–3:15:** Approve the targeted drone mission and show original/annotated RGB evidence.
5. **3:15–4:15:** Assign the case, record uncertainty and field-check action, and export its audit trail.
6. **4:15–5:00:** Show the missing-data control and explain why RGB cannot prove every theft mechanism.

Maintain a labeled recording and saved run as presentation backup. The recording is not evidence that the application is currently running live.

## 14. Acceptance criteria and verification

All P0 criteria below must pass before describing the MVP as complete. P1 criteria are separately reported.

- **AC-01 — Functional twin:** Given the baseline run, the scene shows the specified topology and all selectable assets. Clicking branch-03 opens its actual three meter streams and current balance. Simulation stepping changes both the view and measurements consistently.
- **AC-02 — Balance arithmetic:** Given the worked 12.5/10.5/0.4 kWh fixture, the stored residual is 1.6 kWh and the displayed ratio is 12.8%, within 0.001 kWh calculation tolerance before rounding. Boundary-cut validation rejects double-counted descendants.
- **AC-03 — Persistence and localization:** Given a sustained residual above the frozen threshold, the section alert first appears on the third consecutive qualifying valid interval. A missing/invalid interval breaks the qualifying streak. The smallest valid monitored branch is highlighted without inventing household certainty.
- **AC-04 — Negative controls:** A clean run, a balanced legitimate load change, and a missing-meter run do not produce a theft finding. Missing telemetry visibly changes the balance to incomplete.
- **AC-05 — Live drone capture:** After approval, the drone visibly follows its target route and saves at least two scene-derived RGB frames linked to mission, run, pose, and simulation sequence. Capture excludes analytic/debug overlays.
- **AC-06 — Functional CV:** On predefined synthetic candidate-present and candidate-absent fixtures, the pixel pipeline returns an annotated candidate and a clean result respectively. Removing the wire from the RGB image removes its visual detection. Access to scenario labels/object-ID masks is absent from the inference interface.
- **AC-07 — Human review:** A reviewer can record inconclusive evidence and request field inspection. A resolution/dismissal without a disposition and reason is rejected. No endpoint automatically disconnects or penalizes a household.
- **AC-08 — Accountability:** Create, assign, inspect, review, dismiss/resolve, and reopen actions are retained with actor and timestamps. Earlier image/analysis revisions remain available.
- **AC-09 — Persistence/export:** Refresh or restart retains a completed case and its original image hash. Export includes provenance, balance inputs, rule version, decisions, and evidence references; linked PNG downloads are usable.
- **AC-10 — Reset/replay:** A reset creates a new run without modifying the old case. Repeating the same seed/actions reproduces reading values and alert onset intervals.
- **AC-11 — Performance/reliability:** Record the NFR latency/FPS measurements and complete three consecutive end-to-end demos without an unrecovered error.
- **AC-12 — Truthful presentation:** Synthetic labels appear on workspace, evidence, and report. The interface uses unexplained loss/suspected anomaly language and distinguishes CV match scores from theft probability.
- **AC-13 — P1 robustness:** Meter-fault, hidden-bypass, occlusion, and topology/model-mismatch scenarios retain the correct uncertainty and review path. Backend role checks reject unauthorized transitions.

Verification combines deterministic analytical fixtures, API transition checks, image positive/negative controls, and one manual end-to-end rehearsal. Do not spend the build window on broad visual snapshot testing or tests that simply repeat implementation internals.

## 15. Success metrics and evaluation

### 15.1 Hackathon delivery gates

- All P0 acceptance criteria pass, with any P1 omissions stated.
- Full alert-to-evidence-to-review loop can be demonstrated within five minutes.
- 100% of state changes and exported evidence carry required provenance and audit metadata.
- No automatic theft verdict or enforcement action is generated.
- Three consecutive rehearsals complete successfully on the reference device.

### 15.2 Synthetic evaluation protocol

Use four calibration seeds and **12 held-out scenario-day runs** with distinct seeds. Generate each run's seven clean baseline days independently. Freeze detector thresholds before evaluating the held-out days. Include at least three clean/control runs and distribute visible load, under-registration, missing telemetry, hidden/occluded connection, and mapping/model-shift conditions across the remaining runs. Record the exact event counts; this is a small diagnostic suite, not a statistically representative benchmark.

Define an eligible positive event as persistent unmetered/under-registered consumption lasting at least four complete intervals with residual exceeding the configured noise/threshold envelope. Evaluate lower-amplitude events separately and disclose that eligibility favors detectable events. Do not claim success by excluding difficult scenarios without reporting them.

Use event-level matching: one alert matches one injected event only when the smallest observable boundary is correct and alert onset falls between event start and one interval after event end. Duplicate alerts do not count as extra true positives. False alerts are unmatched unexplained-loss alerts on eligible valid boundaries. Data-quality alerts are reported separately.

### 15.3 Targets, definitions, and limitations

- **Eligible-event recall:** Matched eligible events / all eligible events. Target ≥80% in the declared synthetic suite; disclose denominator and missed conditions.
- **Localization accuracy:** Matched events assigned to the correct smallest observable boundary / matched eligible events. Target ≥90%; do not score unsupported household attribution as success.
- **Clean-section false-alert rate:** Unmatched loss alerts / valid clean branch-hours. Target ≤1 per 100 clean branch-hours; report raw alert count and exposure because the suite is small.
- **Detection delay:** Time from incident onset to first qualifying alert, in simulation minutes. Report median and p95 along with the three-interval persistence rule.
- **CV candidate precision/recall:** On held-out rendered views, match candidate boxes to privately labeled visible connection regions at IoU ≥0.5. Target ≥80% precision and ≥80% recall on the documented controlled-view subset; report sample counts and occlusion results separately.
- **Energy estimation error:** Absolute difference between summed branch residual and injected unmetered energy across disjoint boundaries, divided by injected energy, for eligible synthetic events. Target ≤20% where the loss model is stable; show model-shift errors separately.
- **Workflow completion:** Reviewed cases with owner, evidence or explicit absence, disposition, reason, and full audit history / all completed demo cases. Target 100%.
- **Inspection focus:** Targeted branch missions / all potential branch missions. Show the number of sections inspected; this is a simulated workload measure, not demonstrated operational cost savings.

Anomaly metrics measure unexplained-loss detection, not intent or guilt. Synthetic precision/recall does not establish real-world performance. Report CV and energy-detector metrics independently; combining them into one “theft accuracy” conceals distinct failure modes.

No recovered-revenue metric is claimed. An optional `unexplained_kwh × illustrative_tariff` calculation must be labeled hypothetical energy-value exposure, not proven theft value, recovered money, or avoided loss.

## 16. Four-person delivery plan

### 16.1 Ownership

**Person A — 3D/frontend:** Scene, picking, camera, drone route, RGB capture, performance.

**Person B — Simulation/analytics:** Topology, profiles, physical-versus-observed energy, balances, thresholds, scenarios, deterministic fixtures.

**Person C — Backend/workflow:** APIs, SQLite, case lifecycle, audit events, file storage, export, role checks.

**Person D — Inspection/integration/demo:** OpenCV pipeline, image fixtures, UI integration support, acceptance checks, evaluation, and presentation. D owns the integration checklist; everyone integrates continuously.

### 16.2 First 24 hours — core vertical slice

**Hours 0–2: Contract freeze.** Agree IDs, units, topology, event schemas, module interfaces, CV views, and scope. Commit one sample run snapshot and balance fixture. A builds the skeleton scene; B and C agree the telemetry endpoint; D proves a line detector on one rendered frame.

**Hours 2–6: Shared live simulation.** A renders all assets and selection. B streams valid interval readings and balances. C persists run/case records and exposes snapshot/SSE. D verifies clean/candidate image controls. Gate: clicking an asset shows readings computed from the shared run.

**Hours 6–10: Detection and case creation.** B adds incident injection, validity gates, persistence, and localization. C implements case creation/assignment and events. A adds alert highlighting and charts. D validates missing data and the image-upload contract. Gate: clean-to-anomaly case flow works.

**Hours 10–15: Inspection integration.** A implements route and RGB capture. D connects real pixel processing. C persists mission/evidence metadata. B ensures snapshots preserve the capture sequence. Gate: one approved mission produces original and annotated evidence.

**Hours 15–19: Review and export.** C completes reasons, transitions, audit export, and restart persistence. A/D finish evidence review UI. B tests arithmetic, deduplication, and reset semantics. Gate: an exported case can be read without the application.

**Hours 19–22: Verification.** Run every P0 criterion, measure latency/FPS, fix blocking integration issues, and record limitations. Feature freeze at hour 22.

**Hours 22–24: Rehearsal and packaging.** Three full demos, a labeled backup recording, setup instructions, sample scenario buttons, and final presentation. Preserve time for recovery rather than adding visual effects.

### 16.3 Hours 24–48 — robustness and differentiation

**Hours 24–30:** Add under-registration, hidden/occluded connection, topology mismatch, and model-shift scenarios. Strengthen missing/revised-data handling.

**Hours 30–36:** Run held-out synthetic evaluation, vary camera views, enforce backend role rules, and complete P1 persistence checks.

**Hours 36–42:** Improve accessibility, feedback states, exports, and scene performance. Compare detection results with the explainable baseline only if all core flows remain stable.

**Hours 42–48:** Freeze features, fix acceptance failures, publish actual measured results with denominators, rehearse, and package the final demo and source.

### 16.4 Scope-cut order

Cut scenery detail, shadows, extra viewpoints, optional statistical models, additional chart types, and secondary scenario controls first. Preserve the functional 3D scene, actual reconciliation, honest image evidence, human review, and synthetic labeling. If CV remains incomplete, disclose the unmet criterion rather than replacing it with a concealed scripted output.

### 16.5 Handoff package

Deliver runnable source, pinned dependencies, a concise README with local startup steps, scenario seeds, sample topology, acceptance results, evaluation output, demo recording, and sample case exports. Include asset licenses. This PRD is the specification; those implementation artifacts are future build deliverables.

## 17. Risks, tradeoffs, and mitigations

**Insufficient instrumentation:** A residual can only be localized to observable boundaries. Keep boundary coverage explicit and avoid household-level claims without suitable measurements.

**Technical-loss uncertainty:** Incorrect loss assumptions mimic nontechnical loss. Show expected losses and uncertainty, include a model-shift control, and route ambiguous cases to review.

**Telemetry quality and topology errors:** Misalignment or wrong parent mapping creates false imbalances. Apply validity gates, topology versions, and explicit recomputation.

**Synthetic shortcut learning:** Identical incident colors, object labels, or truth fields can make metrics meaningless. Keep truth private, hide capture overlays, vary views, and test image-only controls.

**CV fragility:** Thin wires, clutter, occlusion, and camera mismatch limit line detection. Constrain and disclose the supported visual subset; return inconclusive where necessary. Never treat a missed candidate as proof of absence.

**False accusation:** Legitimate behavior and meter faults resemble tampering. Use neutral language, require reasoned human decisions, retain disagreements, and exclude enforcement.

**3D integration cost:** Detailed scenery can consume the entire hackathon. Use simple meshes and fixed inspection viewpoints; prioritize state consistency over photorealism.

**Overlapping energy accounting:** Summing nested residuals inflates loss estimates. Validate disjoint cuts and store aggregation boundaries in every report.

**Demo reliability:** Browser capture, backend startup, or processing may fail. Keep local operation, bounded timeouts, saved runs, retry actions, and a disclosed backup recording.

**Real deployment constraints:** Real flight would require utility permission, applicable aviation/airspace checks, trained operators, privacy controls, and professionally defined electrical clearances. These are future pilot prerequisites; this document provides no regulatory clearance or real flight procedure.

## 18. Post-hackathon path and references

### 18.1 Evidence required before a real pilot

1. Partner with a utility to identify a bounded, adequately metered pilot section and a legitimate investigation workflow.
2. Validate asset mapping, clock synchronization, meter uncertainty, authorized unmetered loads, and technical-loss estimates.
3. Obtain permitted, appropriately protected data and separate confirmed findings, faults, authorized loads, and unresolved cases.
4. Evaluate on unseen feeders/time periods with independently verified outcomes; measure inspection burden and false accusations as well as recall.
5. Test whether imagery improves decisions beyond energy accounting alone. If it does not, retain field/meter inspection as the appropriate next step.
6. Add real authentication, access controls, retention policy, security review, operational audit controls, and approved field procedures before using actual customer data or aircraft.

### 18.2 Sources and how they are used

Sources were checked for this specification on 24 October 2026. They establish problem context and inspection/accounting relevance. All network sizes, thresholds, performance targets, staffing assumptions, and synthetic benchmark targets are product design choices rather than figures taken from these sources.

- **[S1] Ministry of Power / Press Information Bureau, 18 January 2026 — Power distribution utilities record positive PAT after years of losses.** Reports FY2024–25 AT&C loss of 15.04%; does not quantify theft alone. [Official release](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2215761&lang=1&reg=1).
- **[S2] Glauner et al. — The Challenge of Non-Technical Loss Detection using Artificial Intelligence: A Survey.** Research context for theft, meter faults, billing errors, and limitations of detection. [Authors' paper](https://arxiv.org/abs/1606.00626).
- **[S3] Bureau of Energy Efficiency — Energy Audit in DISCOM.** Official context for annual energy audits and periodic distribution energy accounting. [BEE resource](https://www.beeindia.gov.in/show_content.php?lang=1&level=3&lid=64&ls_id=351).
- **[S4] Ministry of Power / Press Information Bureau, 2 February 2026 — Progress on Smart Meter Installation under RDSS.** Describes metering of consumers, distribution transformers, and feeders. Does not guarantee local data access or completeness. [Official release](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2222217&lang=2&reg=3).
- **[S5] Idaho National Laboratory, GridTechPedia — Drones for Maintenance Inspections, updated July 2026.** Establishes overhead-asset visual/sensor inspection as a relevant drone application; not evidence of theft-classification accuracy. [INL overview](https://gridtechpedia.inl.gov/technology/drones-for-maintenance-inspections/).

### 18.3 Definition of done

The hackathon MVP is done when a judge can interact with the synthetic 3D network, watch a real computed imbalance emerge, understand its measurement boundary and uncertainty, approve a simulated drone capture, inspect honest image-processing output, record a human decision, and download a persistent, traceable case report. Any omitted criterion or simulated component is disclosed directly.
