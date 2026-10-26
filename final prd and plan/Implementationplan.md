# VIDYUT-TRACE
## 24-Hour Implementation Plan — Three Developers

**Duration:** One 24-hour hackathon  
**Team:** Exactly 3 developers  
**Goal:** A working, reproducible, explainable end-to-end demo  
**Development assistant:** IBM Bob  
**Optional runtime AI:** IBM Granite through watsonx.ai, only if verified

---

## 1. Definition of Success

At the end of hour 24, a reviewer should be able to:

1. Start the application.
2. Load the frozen synthetic replay.
3. View and control the network replay.
4. Inspect a connected 3D distribution network.
5. See validated meter readings and a boundary energy balance.
6. Understand an explainable alert or candidate investigation.
7. Inspect supporting, contradicting, and missing evidence.
8. See the recommended next action.
9. Open a persistent case and record a human disposition.
10. See a negative-control test.
11. Review genuine evidence of IBM Bob's contribution to development.

The core workflow takes priority over visual polish, additional agents, computer vision, or optional LLM integration.

---

## 2. Independent Ownership

Each developer owns a separate primary subsystem. Each must expose a defined interface so the others can work independently.

### Developer 1 — Data, Simulation, and Energy Analytics

**Primary ownership:** Data pipeline, time-series replay data, validation, energy balance, quality rules, calculation tests.

**Responsibilities**

- Inspect the supplied dataset before assuming its schema.
- Implement CSV ingestion.
- Verify timestamp, unit, quality, and stream fields.
- Preserve missing values.
- Validate duplicate, stale, invalid, and incomplete readings.
- Define the reduced demo topology.
- Implement replay data access.
- Calculate boundary energy balance and residual percentage.
- Implement persistence rules for candidate alerts.
- Create calculation and data-quality tests.
- Supply stable data endpoints or Python functions to Developer 3.
- Document assumptions and known limitations.

**IBM Bob usage**

- Ask Bob to review the ingestion and validation design.
- Use Bob to draft or critique tests for missing, duplicate, and invalid readings.
- Ask Bob to review the energy-balance calculation and identify possible double-counting or unit errors.
- Keep the actual diffs, test commands, outputs, and review decisions.

**Deliverables**

- Working ingestion and validation.
- Stable network and reading data contract.
- Energy-balance calculation.
- At least four automated tests.
- A sample output that the frontend can render.
- A short note describing how Bob helped and what was accepted or rejected.

**Do not own:** Main 3D interface, full case-management UI, or LLM orchestration.

---

### Developer 2 — Frontend and 3D Operations Cockpit

**Primary ownership:** React interface, connected 3D network, replay controls, asset selection, visual state and optional rendered-frame capture.

**Responsibilities**

- Set up React, TypeScript, and Vite.
- Create the application layout.
- Render feeders, transformers, branches, and households.
- Use the agreed asset IDs and topology contract.
- Implement play, pause, step, and speed controls.
- Show the current replay timestamp.
- Display readings and quality states.
- Highlight a selected or investigated network boundary.
- Build panels for energy balance, evidence, and case status.
- Integrate with the agreed API contract.
- If time permits, capture an RGB frame from the actual rendered scene.

**IBM Bob usage**

- Ask Bob to scaffold or review a React/Three.js component.
- Ask Bob to explain rendering or state-management bugs.
- Use Bob to generate or improve component tests.
- Ask Bob to review accessibility and interaction states.
- Preserve real code diffs, test output, and the human decision on suggested changes.

**Deliverables**

- Running frontend.
- Connected 3D scene with selectable assets.
- Replay controls.
- Readings and quality indicators.
- Energy and evidence panels.
- Case review interface.
- Optional real rendered-frame capture.

**Do not own:** The authoritative energy calculation, investigation policy, or database state transitions.

---

### Developer 3 — Investigation Workflow, Case Management, Integration, and Demo

**Primary ownership:** Case lifecycle, evidence fusion, allowed next actions, policy gate, persistence, end-to-end integration, and demo rehearsal.

**Responsibilities**

- Define the shared case and evidence schemas with the team.
- Implement deterministic evidence fusion.
- Implement the allowed action enum and validation.
- Enforce data-quality gates before recommendations.
- Implement case creation, review, disposition, and persistence.
- Build the backend API or coordinate its integration.
- Connect Developer 1's data/analytics outputs to Developer 2's interface.
- Implement the worker/tool trace.
- Create the end-to-end test.
- If time permits, implement a bounded OpenCV candidate check.
- Verify whether Granite is available and integrate it only if there is enough time.
- Prepare and rehearse the final demo.

**IBM Bob usage**

- Ask Bob to review the workflow and case-state transitions.
- Use Bob to generate an integration-test skeleton.
- Ask Bob to investigate an actual integration failure.
- Use Bob for a separate review of the policy gate and allowed action enum.
- Save the real diffs, commands, test output, and accepted or rejected recommendations.

**Deliverables**

- Evidence ledger and deterministic fusion.
- Allowed next-action selection.
- Policy gate.
- Persistent case lifecycle.
- Human review and disposition.
- Integrated API.
- End-to-end test.
- Demo script and known-limitations list.
- IBM Bob evidence summary.

**Do not own:** The detailed 3D implementation or the primary energy-accounting formulas.

---

## 3. Shared Contract — Freeze by Hour 1

Before substantial parallel implementation, agree on these items:

### Asset IDs

Use stable IDs, for example:

- `F-01`
- `DT-01`
- `BR-01`
- `BR-02`
- `H-01`

These are illustrative demo IDs. Map them to the actual dataset and topology where appropriate.

### Reading record

Minimum fields:

- `stream_id`
- `timestamp`
- `value`
- `unit`
- `quality`

Optional fields may include:

- `asset_id`
- `source_file`
- `source_row`
- `is_synthetic`

Do not assume that a missing reading has a numeric value.

### Balance result

Minimum fields:

- Boundary or asset ID.
- Start and end timestamps.
- Input energy.
- Accounted downstream energy.
- Residual.
- Residual percentage and denominator.
- Validity status.
- Data-quality warnings.
- Assumptions and limitations.

### Evidence record

Minimum fields:

- Evidence ID.
- Source worker or tool.
- Related asset and time range.
- Claim.
- Status.
- Value and unit, if applicable.
- Limitations.
- Source reference.

### Recommendation record

Minimum fields:

- Allowed action.
- Reason.
- Evidence IDs.
- Approval requirement.

### Case record

Minimum fields:

- Case ID.
- Status.
- Boundary.
- Time range.
- Balance result.
- Evidence.
- Recommendation.
- Review status.
- Human disposition.

**Integration rule:** Do not independently invent incompatible field names or state enums. If a contract changes, agree on the change and update all consumers.

---

## 4. Hour-by-Hour Plan

### Hours 0–1: Kickoff and scope freeze

**All developers**

- Read the final PRD.
- Inspect the repository and supplied data.
- Confirm the local runtime and available dependencies.
- Create a shared task board.
- Agree on asset IDs, evidence schema, API responses, and case states.
- Choose one reduced demo network.
- Define the minimum end-to-end path.

**IBM Bob**

- Use Bob to critique the proposed architecture and identify integration risks.
- Record what Bob actually reviewed and which recommendations the team accepted.

**Checkpoint:** All three developers can describe the same data contract and demo path.

### Hours 1–3: Independent skeletons

**Developer 1**

- Inspect the actual dataset columns and quality values.
- Build the ingestion and validation skeleton.
- Confirm timestamp and unit semantics.
- Produce a small validated sample.

**Developer 2**

- Build the application shell.
- Render the initial network geometry.
- Add asset selection and replay controls using mocked data that matches the shared contract.

**Developer 3**

- Build the backend skeleton.
- Implement the evidence and case schemas.
- Define allowed actions and case transitions.
- Add a health endpoint.

**Checkpoint:** Each subsystem runs independently.

### Hours 3–5: First working components

**Developer 1**

- Complete the main validation rules.
- Implement energy balance and residual calculations.
- Add tests for missing readings and duplicates.

**Developer 2**

- Connect replay controls to the shared data model.
- Render the current reading state.
- Add quality indicators and selected-asset highlighting.

**Developer 3**

- Implement deterministic evidence fusion.
- Add policy-gated next-action selection.
- Create a case from a structured investigation result.

**Checkpoint:** Data, UI, and workflow can exchange valid sample records.

### Hours 5–7: First integration

**All developers**

- Integrate the actual ingestion output with the frontend.
- Connect the balance result to the energy panel.
- Connect the investigation result to the case view.
- Fix contract mismatches before adding features.

**Developer 1**

- Verify calculation outputs independently.
- Test invalid and incomplete input behaviour.

**Developer 2**

- Remove mock readings where actual endpoints are available.
- Verify asset IDs match the backend.

**Developer 3**

- Persist cases.
- Add an explicit incomplete-data state.
- Record the selected action and its rationale.

**Checkpoint:** One replay interval can travel from the data layer through the calculation and into the UI.

### Hours 7–9: Explainable investigation

**Developer 1**

- Implement the persistence rule for candidate alerts.
- Ensure invalid intervals do not count as zero-residual intervals.
- Add a negative-control data test.

**Developer 2**

- Display the energy waterfall or equivalent balance view.
- Highlight the investigated network boundary.
- Add the evidence and uncertainty panels.

**Developer 3**

- Connect the evidence ledger to the UI.
- Show supporting, contradicting, and missing evidence.
- Add allowed-action validation and rejection behaviour.

**Checkpoint:** A reviewer can explain why an investigation was raised and which measurements support it.

### Hours 9–11: Case review and data integrity

**Developer 1**

- Test the expected missing values.
- Check unit consistency and boundary membership.
- Document unavailable engineering parameters.

**Developer 2**

- Complete the case-detail interface.
- Display the synthetic-data label and quality warnings.
- Ensure missing readings are visibly distinct from zero.

**Developer 3**

- Complete human review and disposition.
- Verify that a case survives a page refresh.
- Add an audit record for the review decision.

**Checkpoint:** The demo has a persistent, reviewable case.

### Hours 11–13: Negative controls and failure handling

**All developers**

- Run the balanced or clean-consumption negative control.
- Run a missing-meter or invalid-input scenario.
- Confirm that invalid data cannot trigger a confident theft conclusion.
- Confirm that malformed recommendations are rejected.

**Developer 1**

- Fix calculation and validation failures.

**Developer 2**

- Improve visibility of data-quality and incomplete states.

**Developer 3**

- Fix case-state, policy-gate, and error-handling failures.

**Checkpoint:** The system demonstrates restraint as well as detection.

### Hours 13–15: IBM Bob evidence and optional inspection

**All developers**

- Review the genuine Bob-assisted work already completed.
- Save diffs, tests, and review decisions.
- Do not invent usage records after the fact.

**Developer 1**

- Review calculation tests with Bob and document the actual result.

**Developer 2**

- If stable, implement capture of an RGB frame from the actual rendered scene.
- Record the frame's asset and timestamp provenance.

**Developer 3**

- If the core workflow is stable, add the optional inspection endpoint and basic OpenCV candidate classification.

**Checkpoint:** Bob's development contribution can be demonstrated. Optional inspection is attempted only if the core workflow remains stable.

### Hours 15–17: Optional Granite decision and evaluation

**Developer 1**

- Add additional calculation tests or test fixtures.
- Check baseline threshold behaviour.

**Developer 2**

- Polish scene selection, energy view, and evidence presentation.

**Developer 3**

- Verify IBM Granite access and model availability.
- If available, implement a narrow structured-output call with strict action validation.
- If unavailable or unstable, retain the disclosed deterministic planner.
- Add the first B0/B1 comparison if time permits.

**Checkpoint:** The application does not depend on an unverified model endpoint.

### Hours 17–19: End-to-end hardening

**All developers**

- Run from a clean startup.
- Reload the frozen replay.
- Run the normal and negative-control scenarios.
- Verify case persistence.
- Verify that the evidence and recommendation correspond to the displayed readings.
- Remove dead controls and broken optional paths.

**Checkpoint:** One reliable demo path works from a clean start.

### Hours 19–21: User experience and evidence packaging

**Developer 1**

- Prepare a short explanation of the calculation, data assumptions, and tests.

**Developer 2**

- Improve layout, labels, timestamps, network highlights, and evidence visibility.

**Developer 3**

- Prepare the case export or a concise evidence report.
- Prepare the Bob usage log.
- Document the actual status of Granite and computer vision.

**Checkpoint:** The team can explain the system without overstating its capabilities.

### Hours 21–23: Demo rehearsal

**All developers**

- Rehearse the entire demo.
- Use a known scenario and record the exact steps.
- Test the negative control.
- Verify that the demo does not rely on fragile external services.
- Prepare a backup screenshot or short recorded capture if allowed by the event.

**Checkpoint:** The demonstration is repeatable and time-bounded.

### Hours 23–24: Freeze and handoff

**All developers**

- Stop adding nonessential features.
- Fix only high-impact bugs.
- Verify the startup instructions.
- Record known limitations.
- Confirm the final code and evidence are saved.
- Rehearse the final explanation once more.

**Final checkpoint:** The application runs, the core workflow is explainable, and claims match what was actually implemented and tested.

---

## 5. IBM Bob Usage Plan

IBM Bob is a development assistant, not the application's runtime investigation agent.

### Recommended tasks

| Work area | Example Bob task | Evidence to retain |
|---|---|---|
| Architecture | Review the service boundaries and shared contracts | Actual review notes and human decisions |
| Data ingestion | Identify edge cases in CSV validation | Real code diff and test output |
| Energy accounting | Review units, denominators, and double-counting risks | Calculation tests and review record |
| Frontend | Help implement or debug a 3D component | Actual component diff and test/build output |
| Investigation | Review evidence and action schemas | Real review changes |
| Testing | Draft tests for missing and duplicate readings | Test file and actual test results |
| Integration | Diagnose a reproduced API mismatch | Error, proposed fix, diff, and rerun result |
| Documentation | Explain the architecture and document limitations | Reviewed documentation changes |

### Bob evidence protocol

For each significant Bob-assisted task, retain:

1. The actual task or prompt, where available.
2. The relevant starting state or bug.
3. The proposed change.
4. The actual diff or commit.
5. The test command.
6. The real test output.
7. Which suggestions were accepted or rejected.
8. Who reviewed the change.

Only claim a test passed when it was actually run and passed.

### Demo evidence

Choose one clear example where Bob materially helped the team, such as:

- Finding an edge case in missing-reading handling.
- Improving a calculation test.
- Fixing a frontend integration bug.
- Identifying a case-state inconsistency.

Show the original issue, Bob-assisted change, and verification result.

**Do not fabricate a Bob transcript or claim that Bob wrote code it did not write.**

---

## 6. Granite Runtime Decision

Granite is a separate, optional runtime component.

Provisional model ID:

`ibm/granite-4-h-small`

Verify model availability and credentials before committing to it.

If it is available:

- Send only structured case evidence and allowed context.
- Request one allowed action and a short rationale.
- Validate the returned schema.
- Reject unapproved action types.
- Limit the number of additional requests per case.
- Apply a timeout.
- Persist the model/tool trace.
- Keep the human review gate.

If it is not available, use a deterministic planner and label it as such.

**Never claim that Bob is the runtime LLM or that Granite was called when only a local rule-based planner was used.**

---

## 7. Scope Priorities

### P0 — Must work

- [ ] Frozen synthetic replay loads.
- [ ] Data-quality validation works.
- [ ] Energy balance uses valid, compatible readings.
- [ ] Reduced 3D network is connected and selectable.
- [ ] Replay controls work.
- [ ] Candidate alert is explainable.
- [ ] Missing data blocks unsupported conclusions.
- [ ] Evidence ledger displays provenance.
- [ ] Next action uses the allowed enum.
- [ ] Case persists and supports human review.
- [ ] Negative-control test passes.
- [ ] Genuine Bob development evidence is available.
- [ ] Demo runs reliably from a clean start.

### P1 — Only after P0 is stable

- [ ] Actual RGB capture from the rendered scene.
- [ ] Basic OpenCV candidate detection.
- [ ] Optional virtual inspection workflow.
- [ ] Image provenance and hashes.
- [ ] Case export.
- [ ] More blinded scenarios.
- [ ] B0/B1 comparison.
- [ ] Financial-impact panel.
- [ ] Granite runtime if verified and stable.

### P2 — Do not promise within 24 hours

- Full calibrated network-wide power flow.
- Live BESCOM data integration.
- Real AMI, billing, or payment integration.
- Physical drone operation.
- Production-grade vision-based theft detection.
- Verified real-world energy savings.
- Verified financial recovery.
- A supervised theft classifier without appropriate labelled data.

---

## 8. Test Checklist

### Data and calculation

- [ ] Valid readings produce a reproducible balance.
- [ ] Missing required readings produce an incomplete state.
- [ ] Duplicate readings are detected.
- [ ] Invalid timestamps are rejected or flagged.
- [ ] Unknown topology mappings are flagged.
- [ ] Units and aggregation periods are compatible.
- [ ] Missing values are not replaced with zero.
- [ ] Invalid intervals do not satisfy the persistence rule.

### Investigation workflow

- [ ] A candidate alert cites its supporting measurements.
- [ ] Alternative explanations are visible.
- [ ] Missing evidence is explicit.
- [ ] Unsupported action types are rejected.
- [ ] LLM timeout or malformed output cannot bypass the policy gate.
- [ ] Human review is recorded.
- [ ] Case state persists after a refresh.

### UI

- [ ] The 3D scene reflects the shared topology.
- [ ] Asset selection works.
- [ ] Replay controls work.
- [ ] Quality states are visible.
- [ ] The selected boundary matches the case.
- [ ] Synthetic data is labelled.

### Optional inspection

- [ ] Frame comes from the actual rendered scene.
- [ ] Frame provenance is recorded.
- [ ] Failure produces an explicit error or inconclusive state.
- [ ] A visual candidate is not described as proof of theft.

### IBM Bob

- [ ] At least one genuine Bob-assisted contribution is documented.
- [ ] The relevant code diff or artifact is available.
- [ ] Verification was actually run.
- [ ] Accepted and rejected suggestions are identified.
- [ ] No invented usage evidence is included.

---

## 9. Final Demo Flow

Target a short, repeatable walkthrough.

1. **Open the cockpit:** Explain the fictional network and synthetic replay.
2. **Replay measurements:** Show the timestamp, selected assets, and quality states.
3. **Show the balance:** Explain input, accounted downstream energy, residual, and limitations.
4. **Open an investigation:** Show the candidate alert and the evidence that triggered it.
5. **Compare explanations:** Show competing hypotheses and missing information.
6. **Show the next action:** Explain why the recommendation follows from the evidence.
7. **Review the case:** Demonstrate human approval or rejection and persistent disposition.
8. **Run a negative control:** Show that the system avoids an unsupported theft conclusion.
9. **Show Bob evidence:** Demonstrate a real Bob-assisted code improvement and its verification.
10. **Show optional work:** Only if stable, demonstrate rendered-frame capture, vision, Granite, or evaluation.

Do not spend the demo time on features that do not work reliably.

---

## 10. Final Handoff Checklist

- [ ] Repository starts from documented commands.
- [ ] Data file location is documented.
- [ ] No secrets or API keys are committed.
- [ ] Dataset identity and synthetic-data label are visible.
- [ ] API and schema assumptions are documented.
- [ ] Core tests have actual results.
- [ ] Case persistence works.
- [ ] Optional features are marked accurately.
- [ ] Bob usage evidence is saved.
- [ ] Granite status is documented accurately.
- [ ] Known limitations are listed.
- [ ] Demo steps are rehearsed.
- [ ] Final claims are supported by actual code and test evidence.

## Final rule

**Ship one trustworthy end-to-end workflow, not a collection of disconnected features.**

If a feature threatens the reliability of the core demonstration, defer it. The strongest VIDYUT-TRACE demo is one that can explain what it knows, what it does not know, and what a human should check next.