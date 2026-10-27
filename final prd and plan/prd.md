# VIDYUT-TRACE
## Final Product Requirements Document (PRD)

**Version:** Final — 24-Hour Hackathon Edition  
**Project type:** AI-assisted electricity distribution loss investigation  
**Target implementation:** One 24-hour hackathon  
**Team:** 3 developers  
**Primary runtime concept:** Stateful multi-agent workflow with deterministic evidence validation  
**Development assistant:** IBM Bob  
**Optional AI runtime:** IBM Granite 4.0 H Small through IBM watsonx.ai, subject to access verification

---

## 1. Executive Summary

VIDYUT-TRACE is an explainable electricity distribution investigation platform. It helps an operator identify the smallest observable network area with an unexplained electricity balance, compare plausible explanations, identify missing evidence, and recommend the next defensible investigation step.

The product combines:

- A small interactive 3D distribution-network digital twin.
- Time-series electricity meter replay.
- Data-quality and meter-boundary validation.
- Electricity balance and residual calculations.
- Quality-aware anomaly detection.
- A multi-agent investigation workflow.
- An explainable evidence ledger.
- Case management and human review.
- A bounded virtual inspection using rendered image frames.
- A scenario replay and evaluation interface.
- A financial-impact view that distinguishes measured, simulated, and unknown values.
- IBM Bob-assisted development with verifiable evidence of actual use.

The 24-hour objective is to deliver one reliable end-to-end demonstration, not to simulate a fully deployed electricity utility platform.

### Product promise

Find the smallest observable network area with unexplained electricity use, explain competing causes, recommend the next defensible check, and preserve human review.

### Explicit non-promises

VIDYUT-TRACE does not:

- Automatically declare that a customer has stolen electricity.
- Treat every distribution loss as theft.
- Infer theft solely from an energy balance gap.
- Claim real financial savings from simulated scenarios.
- Operate a physical drone.
- Treat an image anomaly as proof of an electrical connection, bypass, current flow, theft, or authorization.
- Claim that synthetic data is real BESCOM telemetry.
- Claim that a runtime LLM is being used unless an actual model call is demonstrated.

---

## 2. Problem Statement

Distribution operators can observe a difference between energy entering a network boundary and energy accounted for downstream. That difference may be caused by several factors, including:

- Technical line and transformer losses.
- Meter under-registration or failure.
- Missing, delayed, duplicated, or invalid readings.
- Incorrect network topology or meter mapping.
- Unmetered or unaccounted loads.
- Billing-period mismatches.
- Genuine commercial irregularities.
- Other unexplained measurement or accounting differences.

A raw difference does not identify the cause.

VIDYUT-TRACE makes the investigation process more structured by validating measurements first, comparing plausible causes, recording uncertainty, and recommending the next action based on available evidence.

---

## 3. Goals and Success Criteria

### 3.1 Primary goals

1. Ingest and validate the supplied synthetic meter replay.
2. Display a connected, interactive 3D distribution-network scene.
3. Replay time-series measurements.
4. Calculate a quality-aware energy balance.
5. Identify a persistent unexplained residual when the required data are valid.
6. Explain why an alert was raised.
7. Show competing explanations and missing evidence.
8. Recommend a permitted next action.
9. Create a persistent, reviewable investigation case.
10. Demonstrate genuine IBM Bob usage during development.
11. Provide a repeatable demo that can be run locally.

### 3.2 Minimum success criteria

The 24-hour build is successful when a reviewer can:

- Start the application.
- Load the frozen synthetic dataset.
- Replay the network.
- Inspect a feeder, transformer, branch, and household hierarchy.
- See valid readings and data-quality states.
- Understand an energy balance calculation.
- Trigger or replay at least one explainable investigation.
- See the evidence supporting and contradicting possible explanations.
- See the next recommended action and why it was selected.
- Open and review a persistent case.
- Run at least one negative-control scenario without receiving an unjustified theft conclusion.
- Inspect a genuine IBM Bob development artifact, such as a reviewed diff, test, or documented bug fix.

### 3.3 Secondary goals

If the core workflow is stable:

- Capture an RGB frame from the actual rendered 3D scene.
- Run a bounded OpenCV visual-candidate check.
- Attach the frame and results to a case.
- Export case evidence.
- Add more blinded evaluation scenarios.
- Add an actual Granite runtime call if access and integration are verified.

---

## 4. Users and Operating Context

### Primary user: Distribution investigation operator

Needs to understand:

- Which observable network boundary has a persistent unexplained residual.
- Whether the measurements are reliable enough to support an investigation.
- Which explanations remain plausible.
- What evidence is missing.
- Which check should happen next.
- What evidence supports a final human disposition.

### Secondary user: Reviewer or supervisor

Needs to inspect:

- The underlying readings.
- The energy calculation.
- Data-quality warnings.
- The agent/tool execution trace.
- The evidence ledger.
- Alternative hypotheses.
- The recommended action.
- The case history and human disposition.

### Hackathon context

The demonstration uses a fictional distribution cell inspired by the general context of Bengaluru electricity distribution. It is not a representation of actual BESCOM infrastructure.

---

## 5. Data Sources and Data Integrity

### 5.1 Synthetic replay

**Expected file:**

`VIDYUT_TRACE_v4_SYNTHETIC_30day_meter_streams.csv.gz`

Expected characteristics:

- Date range: 1–30 September 2022.
- Interval: 15 minutes.
- Timestamps: 2,880.
- Streams: 38.
- Expected rows: 109,440.
- Network composition: 2 feeders, 4 distribution transformers, 8 branches, and 24 household meters.
- Exactly two rows are expected to have `quality=missing` and an empty energy value.

The implementation must verify these characteristics against the actual file before relying on them.

**Rules:**

- Preserve the original file unchanged.
- Label all replay values as synthetic.
- Do not describe the file as real BESCOM telemetry.
- Do not fill missing energy values with zero.
- Do not use hidden challenge labels as model inputs.
- Keep scenario ground truth separate from detector inputs.
- Record the dataset filename and, where practical, its hash.

### 5.2 BESCOM reference data

The project references seven Hebbal feeder records from a BESCOM FY2022–23 audit extract.

These records provide contextual reference information. They do not establish that the synthetic meter streams are real BESCOM measurements.

Example reference calculation:

- Feeder: F11–Sanjay Nagar.
- Reported input: 750,193.1048 units.
- Reported sold energy: 680,380.25 units.
- Derived difference: 69,812.8548 units.
- Derived difference as a share of input: approximately 9.306%.

This difference is **not a theft rate**. The observation period is not sufficiently established here to treat it as a monthly loss or monthly savings estimate. Financial values from other periods must not be combined without verified period alignment.

### 5.3 Data provenance

The application must visibly distinguish:

1. Reference data derived from published or supplied BESCOM material.
2. Synthetic replay data.
3. Values generated by the simulator.
4. Calculations derived from observed replay values.
5. Hypotheses proposed by an agent.
6. Results produced by image processing.
7. Scenario ground truth used only for evaluation.
8. Financial estimates that depend on assumptions.

### 5.4 Data-quality handling

Validate:

- Required columns.
- Stream identifiers.
- Timestamp parsing and ordering.
- Expected sampling interval.
- Units.
- Duplicate timestamps.
- Missing readings.
- Invalid numeric values.
- Negative energy values where not allowed by the data model.
- Meter resets or counter rollovers, if relevant to the input format.
- Stale readings.
- Unknown or invalid topology mappings.
- Incompatible aggregation periods.

Missing or invalid measurements must remain missing or invalid. They must not silently become zero.

If the readings required for a balance are incomplete, the result must be marked incomplete rather than interpreted as evidence of loss.

---

## 6. Scope

### 6.1 P0: Required within 24 hours

- Local data ingestion.
- Frozen replay dataset support.
- Data-quality validation.
- Small connected 3D network.
- Time-series replay controls.
- Quality-aware energy balance.
- Explainable residual or alert.
- At least one negative-control test.
- Evidence ledger.
- Deterministic next-action recommendation.
- Persistent investigation case.
- Human review and disposition.
- IBM Bob evidence log.
- Reliable end-to-end demo.

### 6.2 P1: Add if P0 is stable

- Actual RGB frame capture from the rendered scene.
- Basic OpenCV candidate detection.
- Virtual inspection workflow.
- Evidence image storage and hashes.
- Case export.
- Additional scenario tests.
- Comparison of baseline and improved detector results.
- Polished uncertainty and financial panels.

### 6.3 P2: Explicitly outside the 24-hour commitment

- Production-grade three-phase power-flow modelling.
- Calibrated network-wide electrical simulation.
- Integration with live AMI or SCADA systems.
- Real customer billing or payment integration.
- Real drone flights.
- Autonomous physical inspection.
- Field validation of savings.
- Production deployment, utility authorization, and operational security certification.
- A trained theft classifier without a valid, representative, labelled dataset.
- A claim of verified financial recovery or verified theft detection.

---

## 7. Functional Requirements

### FR-01: Data ingestion

The system must load the provided synthetic dataset and validate its structure before replay.

It must show ingestion success or failure, record the dataset identity, and expose data-quality warnings.

### FR-02: Network digital twin

The 3D view must show a connected hierarchy of:

- Feeders.
- Distribution transformers.
- Branches.
- Household meters.

Each displayed asset must have a stable identifier and an explicit relationship to the data model.

The 24-hour demo may use a reduced network of one transformer, two branches, and six households, provided it is clearly labelled as a reduced demonstration network and not confused with the full supplied topology.

### FR-03: Time-series replay

Provide:

- Play and pause.
- Step forward.
- Replay speed control.
- Current timestamp.
- Current reading values.
- Visible quality states.
- Selection of a network asset.
- Highlighting of an affected network area.

### FR-04: Energy balance

At a valid boundary, calculate:

`Residual = Boundary input energy − Accounted downstream energy`

Where justified by the available measurements, show:

- Input energy.
- Downstream accounted energy.
- Calculated residual.
- Residual percentage with a clearly stated denominator.
- Data-quality status.
- Applicable observation interval.
- Uncertainty or known limitations.

The implementation must define which meters belong to each boundary and prevent double-counting.

Do not add incompatible time periods or treat an invalid reading as zero.

If authorized unmetered-load adjustments are available, record them explicitly. Otherwise, mark the adjustment as unavailable rather than inventing it.

### FR-05: Technical-loss estimation

The intended architecture supports electrical-loss estimation, but credible estimates require suitable engineering inputs.

Potential inputs include:

- Network topology.
- Conductor resistance and reactance.
- Conductor length.
- Voltage and current.
- Power factor.
- Transformer parameters.
- Loading profiles.
- Appropriate phase and measurement conventions.

The 24-hour demo must not fabricate these values. If required inputs are unavailable, show the technical-loss estimate as unavailable or uncalibrated.

A simplified estimate may be shown only when its assumptions are explicit.

### FR-06: Persistent residual detection

A candidate alert should require:

- Valid readings for the required boundary.
- Valid timestamps.
- A known topology mapping.
- A defined threshold or comparison rule.
- A documented persistence rule.

The recommended demo rule is to require three consecutive valid intervals before raising a persistent-residual candidate alert.

Invalid intervals must not count as zero-residual intervals. A data-quality failure must not automatically count as a confirmed loss event.

### FR-07: Investigation hypotheses

Possible explanations may include:

- Data-quality failure.
- Meter under-registration.
- Incorrect topology or meter mapping.
- Technical losses.
- Unaccounted or unmetered load.
- Billing mismatch, when matched-period billing data exist.
- Unexplained residual requiring further investigation.

Each hypothesis must distinguish:

- Supporting evidence.
- Contradicting evidence.
- Missing evidence.
- Confidence or uncertainty.
- Evidence source and time window.
- The next useful verification step.

A hypothesis is not a finding of theft.

### FR-08: Multi-agent investigation workflow

#### W1 — Metering and accounting

Mandatory first worker.

Responsibilities:

- Validate the readings.
- Check timestamps, units, quality, duplicates, and missing values.
- Check the required topology mapping.
- Calculate eligible boundary balances.
- Mark the case `DATA_INCOMPLETE` when essential inputs are not reliable.
- Prevent invalid balances from triggering downstream conclusions.

#### W2 — Electrical physics

Responsibilities:

- Estimate technical losses only when sufficient electrical and network parameters exist.
- Report assumptions and uncertainty.
- Identify missing engineering inputs.
- Abstain when the data cannot support a credible estimate.

A full calibrated `pandapower` implementation is not required for the 24-hour build.

#### W3 — Commercial and anomaly analysis

Responsibilities:

- Identify consumption shifts or unusual patterns.
- Check billing mismatches only when matched-period invoices are available.
- Check payment or collection information only when appropriate records exist.
- Identify data that is unavailable.

The frozen synthetic replay does not provide verified theft labels, meter-event history, billing records, or payment records. The application must not invent these fields or claim to have trained a theft classifier from them.

#### W4 — Localization and vision

Responsibilities:

- Localize the smallest supported observable area.
- Inspect actual rendered RGB frames when the optional visual workflow is enabled.
- Compare visual candidates with the approved scene or wire geometry.
- Return a bounded outcome:
  - `CANDIDATE_FOUND`
  - `NO_VISIBLE_CANDIDATE`
  - `INCONCLUSIVE`

Visual results are investigative clues only. They do not prove theft, hidden bypasses, current flow, or permission to inspect a real site.

### FR-09: Evidence fusion

A deterministic fusion layer must combine the workers' structured findings.

It must:

- Preserve evidence provenance.
- Track supporting and contradicting evidence.
- Avoid double-counting the same measurement.
- Preserve uncertainty.
- Expose missing information.
- Reject invalid or incomplete cases when appropriate.
- Select the smallest defensible observable boundary.
- Produce a reviewable case summary.

The LLM must not independently determine that theft has occurred.

### FR-10: Next-action recommendation

The workflow may choose only from the following action enum:

- `REQUEST_ELECTRICAL_RECHECK`
- `REQUEST_METER_REVIEW`
- `REQUEST_BILLING_AUDIT`
- `REQUEST_TOPOLOGY_CHECK`
- `REQUEST_LOCALIZATION`
- `PROPOSE_VIRTUAL_DRONE`
- `REQUEST_MISSING_DATA`
- `GENERATE_CASE_SUMMARY`
- `ABSTAIN_NO_ACTION`

The action must include a reason, evidence references, and any required human approval.

A policy gate must reject unsupported or malformed actions.

### FR-11: IBM Granite runtime

The proposed runtime is IBM Granite 4.0 H Small through IBM watsonx.ai.

Provisional model ID:

`ibm/granite-4-h-small`

The team must verify model availability in its IBM account and region before relying on it.

If enabled, the model should select among allowed actions and explain the recommendation using the structured evidence supplied to it.

Proposed runtime limits:

- Maximum three additional action requests per case.
- Maximum 500 output tokens per call.
- 15-second timeout.
- Schema validation on all responses.
- No direct database mutations.
- No physical drone permissions.
- No unrestricted tool execution.

If access is unavailable, use a disclosed deterministic planner fallback. Do not describe the fallback as Granite.

### FR-12: IBM Bob development workflow

IBM Bob is a development assistant, separate from the application's runtime investigation agents.

Use Bob to support:

- Architecture planning.
- Component implementation.
- Code explanation.
- Bug reproduction and fixing.
- Test generation.
- Independent code review.
- Refactoring and documentation.
- Integration troubleshooting.

Record real evidence of Bob usage, such as prompts where available, diffs, commits, test results, accepted or rejected suggestions, and human review.

Do not fabricate Bob conversations, claim unperformed tests, or confuse Bob-assisted coding with runtime AI inference.

### FR-13: Case management

Each case should record:

- Case ID.
- Creation time.
- Relevant timestamp range.
- Network boundary.
- Data-quality status.
- Balance result.
- Evidence references.
- Competing hypotheses.
- Missing information.
- Recommended action.
- Human review status.
- Notes.
- Final disposition and reason.
- Revision or reopen history, where implemented.

Suggested case states:

- `NEW`
- `DATA_INCOMPLETE`
- `INVESTIGATING`
- `AWAITING_REVIEW`
- `APPROVED_FOR_NEXT_CHECK`
- `CLOSED`
- `REOPENED`

A case must be persisted locally. A page refresh must not erase it.

### FR-14: Human review

A human reviewer must be able to:

- Inspect the calculation.
- Inspect evidence and uncertainty.
- View the recommendation.
- Approve or reject the proposed next step.
- Record a reason.
- Close or reopen the case where supported.

A proposed virtual inspection requires explicit human approval.

### FR-15: Virtual inspection and image analysis

If time permits:

1. Select a localized area.
2. Explain why visual inspection may be useful.
3. Require human approval.
4. Capture an RGB frame from the actual rendered scene.
5. Record the frame and scene/asset provenance.
6. Run a bounded OpenCV candidate check.
7. Store the outcome with the case.
8. Allow a reviewer to inspect the original frame and result.

The implementation must not substitute an unrelated stock image for the rendered scene while claiming it is a captured inspection frame.

If capture or analysis fails, return an explicit failure or inconclusive state.

### FR-16: Financial impact

Keep these quantities separate:

- Physical energy potentially avoided.
- Newly billable energy.
- Cash collected.
- Avoided operating costs.
- Inspection costs.
- Repair costs.
- Conditional simulated net benefit.

Every financial figure must disclose whether it is measured, calculated, simulated, or unavailable.

A distribution balance gap is not equivalent to recoverable revenue or collected cash.

### FR-17: Evaluation

The evaluation interface should distinguish:

- B0: static-threshold baseline.
- B1: deterministic, data-quality-aware workflow.
- B2: hybrid workflow with Granite, only if the actual runtime is available.

All variants must receive the same initial evidence, assets, and evaluation budget.

Keep the input replay frozen. Use separate blinded challenge cases with hidden labels. Do not expose hidden labels, scenario IDs, or ground-truth masks to the detector or vision workflow.

Measure, where data permits:

- Detection recall.
- False-alert rate.
- Localization quality.
- Detection delay.
- Abstention rate.
- Image-candidate performance.
- Data-quality failure handling.

B2 is allowed to tie or perform worse than B0 or B1. Report actual outcomes rather than assuming the LLM improves performance.

---

## 8. Architecture

### 8.1 Proposed stack

- Frontend: React, TypeScript, Vite.
- 3D: Three.js or React Three Fiber.
- Backend: Python and FastAPI.
- Data processing: Python and Pandas.
- Storage: SQLite and local evidence-file storage.
- Vision: OpenCV, optional within the 24-hour schedule.
- Live updates: Server-Sent Events or a simpler polling mechanism.
- Runtime LLM: IBM watsonx.ai Granite, optional and access-dependent.
- Development assistant: IBM Bob.

Choose the simplest stack the team can integrate reliably.

### 8.2 Logical components

1. Data ingestion and validation.
2. Network topology model.
3. Replay and simulation service.
4. Energy accounting engine.
5. Investigation workers.
6. Evidence fusion and policy gate.
7. Optional Granite action planner.
8. Case management and audit history.
9. Optional virtual inspection and vision service.
10. Frontend operations cockpit.
11. Evaluation and financial-impact panels.

### 8.3 Workflow

1. Load the frozen replay.
2. Validate data and topology.
3. Run W1 first.
4. Stop or mark the case incomplete if essential inputs fail.
5. Run W2 and W3 only where relevant and supported by data.
6. Fuse the structured evidence.
7. Ask the deterministic planner or verified Granite runtime to select an allowed next action.
8. Validate the action through the policy gate.
9. Request human approval before a virtual inspection.
10. Capture an actual rendered frame and run W4 if enabled.
11. Fuse the new evidence.
12. Save the case.
13. Obtain a human disposition.
14. Record evaluation and financial assumptions separately.

---

## 9. Interface Requirements

The main operations cockpit should include:

### 9.1 Network view

- Interactive 3D network.
- Feeder, transformer, branch, and household selection.
- Current network status.
- Highlighted investigation boundary.
- Replay controls.

### 9.2 Energy and data-quality panel

- Boundary input.
- Downstream accounted energy.
- Residual and percentage.
- Validity state.
- Missing or stale readings.
- Applicable time window.
- Uncertainty and assumptions.

### 9.3 Evidence panel

- Supporting evidence.
- Contradicting evidence.
- Missing evidence.
- Hypotheses.
- Data lineage.
- Worker/tool trace.

### 9.4 Case panel

- Case state.
- Recommended next action.
- Rationale.
- Human approval or rejection.
- Notes and disposition.

### 9.5 Inspection panel

Optional within 24 hours:

- Captured RGB frame.
- Capture timestamp and asset provenance.
- Visual candidate result.
- Original and annotated images, if available.
- Explicit inconclusive/error states.

### 9.6 Evaluation and finance panel

- Scenario outcomes.
- Baseline comparisons.
- Actual metric denominators.
- Synthetic-data warnings.
- Financial assumptions.
- Separate energy, billing, cash, and cost quantities.

---

## 10. API and Data Contracts

The team should freeze a small shared API contract during the first hour.

Suggested endpoints:

- `GET /health`
- `GET /api/network`
- `POST /api/replay/load`
- `GET /api/replay/status`
- `POST /api/replay/control`
- `GET /api/readings`
- `GET /api/balance`
- `POST /api/investigations`
- `GET /api/investigations/{case_id}`
- `POST /api/investigations/{case_id}/review`
- `POST /api/investigations/{case_id}/inspection-approval`
- `POST /api/investigations/{case_id}/inspection` — optional
- `GET /api/evaluation` — optional

The exact route list may be simplified, but the payload shapes must be agreed upon before parallel development.

Suggested evidence record:

```json
{
  "evidence_id": "ev-001",
  "source": "metering_worker",
  "asset_id": "DT-01",
  "timestamp_start": "2022-09-01T00:00:00",
  "timestamp_end": "2022-09-01T00:15:00",
  "claim": "Boundary residual is positive",
  "status": "supported",
  "value": 12.5,
  "unit": "kWh",
  "limitations": ["synthetic replay"],
  "source_reference": "replay-row-reference"
}
```

This is an illustrative schema; implementation must align it with the actual data and units.

Suggested recommendation record:

```json
{
  "action": "REQUEST_MISSING_DATA",
  "reason": "A required downstream reading is missing",
  "evidence_ids": ["ev-001"],
  "human_approval_required": false
}
```

All values and identifiers above are examples, not actual dataset findings.

---

## 11. Non-Functional Requirements

- **Reproducibility:** The same frozen input and code should produce repeatable deterministic calculations.
- **Explainability:** Every alert must expose the rule and evidence used.
- **Safety:** No automatic theft declaration or physical inspection.
- **Data integrity:** Missing data remains missing.
- **Provenance:** Synthetic and reference data must be distinguishable.
- **Auditability:** Preserve recommendations, reviews, and dispositions.
- **Resilience:** An optional LLM or vision failure must not corrupt the case.
- **Performance:** The reduced demo network should be responsive on a normal development laptop.
- **Local operation:** The core demo should work without live utility access.
- **Honest reporting:** Unimplemented and unverified capabilities must be labelled as such.

---

## 12. Test Scenarios

At minimum, implement tests for:

1. Valid balanced boundary.
2. Valid boundary with a persistent residual.
3. Missing required high-load meter.
4. Duplicate reading.
5. Invalid timestamp or interval.
6. Unknown topology mapping.
7. Negative-control consumption change that should not be labelled theft.
8. High uncertainty or unavailable technical-loss parameters.
9. LLM timeout or malformed action, if the runtime is enabled.
10. Inspection capture or vision failure, if the optional inspection path is enabled.

Expected behaviour must be specified before reviewing the results.

---

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| IBM Granite access unavailable | Keep deterministic planner fallback; disclose that Granite was not used at runtime. |
| Dataset schema differs from expectation | Inspect and validate the actual file before coding calculations. |
| Three developers integrate incompatible contracts | Freeze the API, evidence schema, asset IDs, and branch strategy early. |
| Full scope exceeds 24 hours | Prioritize one reliable end-to-end path; make vision and Granite optional. |
| Synthetic results are presented as real | Display persistent synthetic-data labels and provenance. |
| Energy residual is interpreted as theft | Use competing hypotheses, quality gates, and human review. |
| Bob usage is claimed without evidence | Save genuine diffs, tests, prompts where available, and human review notes. |
| Visual candidate is treated as proof | Limit its meaning to a candidate or inconclusive result. |
| Financial impact is overstated | Separate physical energy, billable energy, cash, avoided cost, and conditional benefit. |

---

## 14. Acceptance Criteria

The project is ready for demonstration when:

- [ ] The frozen dataset loads or produces a clear validation error.
- [ ] Synthetic data is clearly labelled.
- [ ] The 3D network corresponds to the data model.
- [ ] Replay controls work.
- [ ] Required readings are quality-checked.
- [ ] The balance calculation uses compatible periods and valid measurements.
- [ ] Missing readings are not silently replaced with zero.
- [ ] A persistent-residual candidate can be explained from evidence.
- [ ] A negative control does not create an unsupported theft conclusion.
- [ ] The recommended action belongs to the allowed enum.
- [ ] An investigation case survives a page refresh.
- [ ] Human review and disposition are recorded.
- [ ] Genuine IBM Bob development evidence is available.
- [ ] The demo can be rehearsed from a clean startup.
- [ ] Optional capabilities are clearly identified as optional or unverified.

---

## 15. Final Scope Decision

The team must optimize for a trustworthy end-to-end demonstration, not feature count.

**Required:** data validation, energy accounting, connected 3D scene, explainable alert, evidence ledger, next action, persistent case, human review, negative-control test, and genuine IBM Bob evidence.

**Optional:** virtual inspection, OpenCV, additional scenario comparisons, financial polish, and Granite runtime integration.

**Not promised:** real theft detection, calibrated network-wide loss estimates, real financial recovery, live BESCOM integration, or real drone operations.

The demo succeeds when a reviewer can trace a recommendation back to valid measurements, understand uncertainty, and see how the system avoids making a stronger claim than the evidence supports.