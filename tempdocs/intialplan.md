# Electricity Theft Detection and Inspection Platform

## Purpose

Build an intelligent system that combines fixed electrical measurements, drone-assisted inspections, and structured multi-agent review to detect unexplained energy losses and support accountable investigations.

The platform should answer: **Where is electricity unaccounted for, what could explain it, what evidence is missing, and what should an authorised inspector check next?**

This is a proposed software specification, not an implemented application. Bengaluru is the initial example; network boundaries and integrations must be agreed with the electricity distribution company. Cost estimates are outside this document.

## 1. Scope and operating principles

- Detect measurement errors, abnormal electrical behaviour, and persistent unexplained losses.
- Localise a problem to the smallest network section supported by available measurements.
- Integrate sensor telemetry, customer consumption, network topology and operating events.
- Use drones to inspect flagged, accessible overhead infrastructure and attach evidence to cases.
- Have multiple specialist agents challenge competing explanations before recommending action.
- Preserve human responsibility for inspections, enforcement and case closure.
- Reuse existing utility meters and systems where suitable. Drones supplement ground inspections.

**An unusual number is not proof of theft.** Keep electrical faults, sensor faults, accounting errors and suspected theft as distinct hypotheses. Agent agreement is not independent confirmation. The software must never automatically accuse a customer, impose a penalty or disconnect supply.

## 2. End-to-end workflow

1. Receive sensor readings and utility operating data.
2. Validate readings, units, timing, device health and network assignments.
3. Calculate section energy balances and electrical anomaly indicators.
4. Create an evidence package when an anomaly is sufficiently supported.
5. Run a bounded multi-agent review of alternative explanations.
6. Show an explainable recommendation to an operator.
7. Assign a ground or drone-assisted inspection where appropriate.
8. Ingest inspection evidence and rerun the review if useful.
9. Have an authorised reviewer record the finding and next action.
10. Check subsequent measurements and retain an auditable case history.

## 3. Users and permissions

- **Network operator:** reviews live conditions, data quality and alerts; requests investigations.
- **Electrical analyst:** maintains loss models and examines calculations and network assumptions.
- **Inspector:** receives assignments, captures evidence and records field findings.
- **Drone pilot:** receives approved inspection requests and uploads flight evidence.
- **Supervisor:** reviews escalation, inspection findings and closure decisions.
- **Auditor:** reads case histories and permitted evidence without altering findings.
- **Administrator:** manages identities, devices and integrations; administrative access must not silently override case audit history.

Apply access controls by role and assigned operational region. Customer identities and detailed evidence should only be visible where needed.

## 4. Sensor and meter integration

### 4.1 Device registry

Register every measurement device with its identifier, asset, coordinates, electrical location, phase configuration, manufacturer, accuracy class, CT/PT ratios, firmware, calibration date and communication method.

Track installation, replacement, maintenance, clock status, connectivity and suspected tampering. Keep effective dates so old measurements retain the correct configuration.

### 4.2 Supported inputs

- Transformer-output and branch-boundary energy meters.
- Existing feeder and customer meter readings, where authorised and available.
- Power-quality instruments for more detailed disturbance measurements.
- Utility outage, switching, maintenance and solar import/export records.

Support CSV imports first, followed by authenticated HTTPS or MQTT ingestion. Connect utility protocols through approved gateways or vendor adapters; do not assume all field meters expose a direct internet API.

### 4.3 Measurement fields

Capture timestamp, receipt time, device ID, interval duration, sequence number, units and quality flags. Where supported, capture:

- Per-phase voltage and current.
- Active and reactive power, power factor and frequency.
- Cumulative import/export energy and interval energy.
- Tamper events, communication health and device diagnostics.
- Optional neutral current, harmonics and waveform-event references.

Record measurement capability explicitly. Do not manufacture missing phase, voltage or energy values. Current alone is insufficient for accurate real-energy accounting.

### 4.4 Validation and error detection

- Reject malformed packets; quarantine unknown devices and unsupported units.
- Detect duplicates, stale messages, impossible values, counter resets and rollover.
- Identify gaps, clock drift, inconsistent intervals and out-of-order packets.
- Flag flatlined readings, phase swaps, reversed CT polarity and incorrect scaling for investigation.
- Preserve raw readings and link corrected or derived values to their source and transformation version.
- Separate missing data from zero consumption. Mark estimated values and their uncertainty.
- Monitor gateway availability, clock synchronisation and device calibration status.

Support store-and-forward buffering and idempotent replay after connection failures. A delayed upload must not produce duplicate alerts.

### 4.5 Sampling and aggregation

Use a configurable common energy-accounting interval, such as 15 minutes, where devices support it. Keep native resolution available. Averages cannot establish short-duration voltage sags or transients; those require suitable instruments and higher-resolution event capture.

## 5. Network model and deterministic detection

### 5.1 Electrical topology

Represent feeders, transformers, branches, switching points and customer connections as a versioned graph. Keep geographical location separate from electrical connectivity. Include private transformers, authorised unmetered loads and distributed generation where relevant.

Use the topology valid at the measurement time. Track switching changes and prevent normal network reconfiguration from appearing as theft.

### 5.2 Section energy balance

For matching intervals and a defined measurement boundary:

**Unexplained energy = energy entering − energy leaving − legitimate consumption inside the boundary − estimated technical losses.**

Use a consistent signed convention for import and export. Do not subtract downstream customer consumption again if it is already included in an outgoing boundary meter. Reject incomplete or overlapping accounting boundaries.

Technical losses must be estimated using an appropriate electrical model and available parameters. Record model uncertainty alongside meter accuracy and missing-data uncertainty.

### 5.3 Detection features

- Repeated unexplained energy above a configurable uncertainty allowance.
- Sudden consumption changes and unexpected changes in load profiles.
- Unusual phase imbalance, voltage behaviour or overload indicators.
- Disagreement between neighbouring measurement boundaries.
- Meter tamper events correlated with other evidence.
- Comparisons before and after inspection or corrective action.

Voltage changes, tamper flags and consumption changes are supporting indicators, not standalone theft findings. Separate urgent electrical safety alerts from the slower theft-review workflow.

### 5.4 Alert output

Every alert should include section ID, time window, unexplained kWh, residual percentage, data coverage, uncertainty, supporting readings, applicable topology and calculation versions, competing explanations and the next useful check.

Thresholds must be configurable, validated locally and versioned. Begin with explainable rules and statistical baselines before adding learned models.

## 6. Drone inspection integration

### 6.1 Inspection requests

An operator can create a drone inspection request from an alert. Include the suspected section, asset locations, inspection objectives, known hazards, priority and evidence required.

The pilot or authorised operations team must approve the flight plan and check applicable airspace access and operating conditions. The platform must not assume an alert authorises flight. Provide a ground-inspection alternative for inaccessible areas.

### 6.2 Camera evidence

- Upload photographs and video with capture time, coordinates, camera direction where available, flight ID and asset association.
- Allow inspectors to mark visible connections and attach observations.
- Preserve original media and separate annotations from originals.
- Identify uncertain or obstructed views rather than treating a missed connection as proof that no theft exists.
- Support optional image models for candidate connection detection, with human review and recorded model versions.

Visual evidence can identify a connection, but authorised network records and field checks establish whether it is legitimate.

### 6.3 Experimental electromagnetic payload

Support ingestion of magnetic field vectors, sample rate, sensor axes, calibration, payload position/orientation, drone position, time synchronisation and relevant aircraft operating metadata.

The processing pipeline should compensate for drone interference, align measurements with conductor geometry, estimate uncertainty and compare inferred currents with suitable reference measurements. Preserve raw data and processing versions.

Treat EM inference as an experimental evidence source. It must pass controlled validation before affecting operational prioritisation. It cannot establish whether a load is authorised, and must not be treated as a billing-grade energy measurement by default.

### 6.4 Limits and alternatives

Drone inspection is mainly useful for accessible overhead wiring. Underground connections, indoor bypasses and meter under-registration require ground inspection. Thermal images may support equipment-condition checks but do not independently establish theft.

Start with manual flight-evidence uploads. Add approved vendor flight-system integrations later; autonomous dispatch and unrestricted city-wide flight are outside the initial scope.

## 7. Multi-agent evidence review

### 7.1 Objective

Use structured adversarial review to test whether an anomaly is better explained by theft, normal network behaviour, equipment faults, or incomplete data. The agents are decision-support tools, not a court or a substitute for electrical calculations and inspections.

The agents must examine the same versioned case evidence. Deterministic services perform calculations; language-model agents interpret and challenge the results using cited evidence.

### 7.2 Agent roles

**Data-quality agent**

Checks completeness, clock alignment, device configuration, units, calibration, missing phases and counter resets. Can recommend that a case be held for better data.

**Electrical-network agent**

Checks topology, legitimate demand, technical-loss assumptions, solar exports, switching events and plausible electrical faults. Proposes non-theft explanations and ways to distinguish them.

**Theft-hypothesis agent**

Builds the strongest evidence-supported case for unauthorised consumption. Identifies persistent unaccounted energy, inconsistencies and relevant inspection evidence. Must explicitly list contradictions and cannot invent a connection or offender.

**Sceptical-review agent**

Challenges the theft hypothesis, looks for double counting and alternative causes, and tests whether sensor and drone evidence are actually independent. Checks whether inspection findings are being overstated.

**Inspection-evidence agent**

Reviews available drone imagery, EM validation status and ground reports. Separates direct observations from image-model suggestions and records what remains unobservable.

**Adjudicator agent**

Summarises agreements, unresolved disagreements and evidence gaps. Recommends a disposition and next check. It must preserve uncertainty rather than force consensus.

### 7.3 Bounded debate protocol

1. **Evidence freeze:** create an immutable case snapshot with source IDs, calculations and quality flags.
2. **Independent analysis:** specialist agents submit their initial assessments without viewing each other's conclusions.
3. **Challenge round:** agents inspect opposing arguments, identify unsupported claims and request specific additional checks.
4. **Evidence update:** approved read-only tools retrieve available data or recompute authorised analyses. Record missing evidence explicitly.
5. **Final assessment:** agents revise or retain their views with reasons.
6. **Adjudication:** generate a structured recommendation for human review.

Use one challenge round initially, configurable execution limits and a timeout. Avoid indefinite debates. On failure, show the deterministic alert and mark agent review incomplete.

### 7.4 Required agent response fields

- Case and evidence-snapshot identifiers.
- Hypothesis under review.
- Supporting and contradicting evidence IDs.
- Data-quality concerns and untested assumptions.
- Alternative explanations.
- Requested inspection or measurement.
- Assessment: supported, weakly supported, unsupported or insufficient evidence.
- Short explanation and limitations.

Reject citations to nonexistent evidence. Do not display model-generated percentages as calibrated theft probabilities. Agreement among agents using the same model and data does not create independent evidence.

### 7.5 System recommendations

- **Data issue:** correct or replace a measurement before assessing losses.
- **Likely operational/equipment issue:** route to maintenance or an electrical analyst.
- **No significant unexplained loss detected:** close or monitor, with reasons; do not claim theft was conclusively absent.
- **Unexplained loss; inspection recommended:** prioritise an appropriate investigation.
- **Insufficient evidence:** request missing measurements or records.

Only an authorised human can record a finding such as theft confirmed by inspection. Keep inspection findings separate from legal proceedings or final legal determinations.

### 7.6 Agent access and safeguards

Agents receive only the minimum necessary case data. Provide read-only tools for measurements, topology, calculations and evidence metadata. Treat text in uploaded reports and images as untrusted case content, not instructions.

Agents cannot change raw data, dispatch aircraft, modify device configurations, close cases, disconnect customers, issue penalties or contact external parties. Persist model versions, tool calls, structured conclusions and concise decision rationales; do not depend on private internal reasoning for auditability.

Evaluate whether the multi-agent system improves decisions compared with rules alone and a single reviewer. More agents must not be assumed to improve accuracy.

## 8. Operator dashboard and case management

### Main screens

- **Network overview:** topology-aware map, current alerts, device health and coverage.
- **Section analysis:** matched incoming/outgoing energy, legitimate consumption, estimated losses, uncertainty and residuals over time.
- **Agent review:** each hypothesis, supporting/contradicting evidence and adjudicator recommendation.
- **Inspection queue:** assignments, due dates, flight access notes, ground alternatives and status.
- **Evidence viewer:** linked photographs, video, sensor events, annotations and reports.
- **Outcome dashboard:** verified findings, false alerts, completed actions and follow-up loss trends.

Keep the case workflow explicit: new → data validation → review → inspection requested → inspection completed → supervisor review → action recorded → follow-up → closed or reopened.

Record faulty meters, authorised loads, confirmed theft, mixed causes and inconclusive inspections separately. A model alert must never be reused as a confirmed training label.

## 9. Data model and integration contracts

### Core entities

- Asset, device and effective-dated configuration.
- Network connection and topology version.
- Raw measurement, interval aggregate and quality issue.
- Customer connection with pseudonymous identifier.
- Utility event and loss-model version.
- Alert, evidence snapshot and calculation result.
- Agent run, assessment and recommendation.
- Inspection, flight, media asset and ground finding.
- Corrective action, follow-up evaluation and audit event.

Use timestamps with explicit time zones, standard units and stable identifiers. Store evidence in access-controlled object storage with integrity hashes and versioning; keep references in the database. Hashes support integrity checking but do not establish that the original evidence was accurate.

### Initial API groups

- `POST /telemetry/batches`: authenticated, idempotent meter ingestion.
- `POST /imports`: validated historical-data upload with job status.
- `GET /assets` and `GET /topology`: authorised network views.
- `GET /sections/{id}/balance`: reproducible section calculations.
- `GET /alerts`: filtered alerts with coverage and uncertainty.
- `POST /cases/{id}/reviews`: create a bounded agent-review job.
- `GET /cases/{id}/reviews`: retrieve structured assessments.
- `POST /cases/{id}/inspections`: human-authorised assignment.
- `POST /inspections/{id}/evidence`: metadata and controlled media upload.
- `POST /inspections/{id}/findings`: record an authorised field finding.
- `POST /cases/{id}/decisions`: supervisor decision with required reason.
- `GET /cases/{id}/audit`: permitted case history.

Return job identifiers for long-running processing. Version APIs and schemas; distinguish measurement time from ingestion and review time.

## 10. Suggested software architecture

- **Frontend:** React and TypeScript for maps, charts, case review and evidence viewing.
- **Backend:** Python and FastAPI for authenticated APIs and domain services.
- **Database:** PostgreSQL with PostGIS; introduce time-series partitioning as volumes require.
- **Object storage:** protected storage for drone media, reports and raw payload files.
- **Background processing:** queued ingestion, aggregation, detection, review and media-processing jobs.
- **Integration layer:** sensor adapters, approved utility connectors and drone-evidence imports.
- **Agent orchestrator:** controlled state-machine workflow with typed outputs, bounded execution and read-only tools.
- **Observability:** ingestion lag, missing intervals, calculation failures, review failures and case-processing metrics.

Keep measurement calculations independent of the language-model provider. The platform should still ingest data, calculate balances and show alerts when agents are unavailable.

## 11. Security, privacy and accountability

- Authenticate devices and users; encrypt network traffic and rotate credentials.
- Restrict customer data, location details and evidence by role and region.
- Prevent duplicate submissions, unauthorised device enrolment and silent configuration changes.
- Preserve append-only audit records with controlled retention and tested recovery.
- Keep evidence access logs and document correction history.
- Minimise capture of unrelated people and properties; redact where required before wider sharing.
- Approve data retention and any external model processing with the utility.
- Require reasons for dismissing or closing alerts; escalate overdue cases without treating delay as proof of corruption.

These features support accountability but do not independently establish or eliminate corruption.

## 12. Development data and evaluation

### Public starting points

- [SGCC research dataset](https://github.com/henryRDlab/ElectricityTheftDetection): customer consumption histories used for theft-detection research. It is not a pole-level network dataset or a drone dataset.
- [UK Power Networks data](https://dso.ukpowernetworks.co.uk/dso-data): electrical operational data for prototyping, subject to each dataset's coverage and licence.

These sources describe different systems. Do not combine their rows as though they represent matched measurements and confirmed cases on one network. Dataset theft labels also may not identify the exact interval in which theft occurred.

### Local data required

Obtain authorised, preferably pseudonymised readings, topology history, customer assignments, outage/switching events, calibration records and documented inspection results. Record inspected-negative and uninspected cases separately; neither establishes permanent absence of theft.

Create a clearly labelled simulated network for controlled demonstrations. Include normal load changes, lawful unmetered demand, solar export, data gaps, clock drift, scaling errors, topology changes, technical losses and unauthorised loads. Synthetic success is not a field-performance claim.

### Evaluation measures

- Energy-balance accuracy on known test cases.
- Data-quality error detection and recovery after delayed uploads.
- Alert precision, recall where labels support it, and false-alert burden.
- Localisation accuracy at the claimed section resolution.
- Inspector yield at a fixed inspection capacity.
- Agent evidence-citation validity and unsupported-claim rate.
- Improvement over rules-only and single-agent baselines.
- Inspection completion time and sustained post-action loss changes.
- Benefit of camera inspection and incremental value of EM measurements.

Split evaluation by time and network area/customer to prevent leakage. Account for inspection selection bias: inspecting only high-scoring cases does not measure missed theft elsewhere. Use an authorised evaluation sampling plan.

## 13. Phased delivery and acceptance criteria

### Phase 1 — Reliable data and network foundation

Deliver the asset registry, versioned topology, historical imports, simulated network, data validation and section energy accounting.

Acceptance: known energy balances reproduce expected results; missing data is distinguished from zero; replay creates no duplicates; topology changes use the correct effective version.

### Phase 2 — Detection and investigation workflow

Deliver explainable alerts, map and charts, assignments, inspection findings, supervisor review and audit history.

Acceptance: an operator can trace an alert to its source readings, complete an investigation and view follow-up results without altering original evidence.

### Phase 3 — Multi-agent challenge and review

Deliver specialist assessments, one challenge round, evidence checks, adjudication and failure fallback.

Acceptance: agents handle known non-theft cases without forced consensus, cite existing evidence and recommend missing checks. No agent can perform restricted actions. Compare results against deterministic and single-reviewer baselines.

### Phase 4 — Sensor and drone integration

Connect an approved sensor gateway and implement flight-evidence uploads, metadata alignment and image annotations. Add EM ingestion behind an experimental feature flag.

Acceptance: end-to-end telemetry is time-aligned and traceable; inspection media links to the correct case; invalid or uncalibrated EM data cannot silently influence operational recommendations.

### Phase 5 — Field pilot and refinement

Run a controlled utility-approved pilot with ground verification, selected drone inspections and predefined evaluation measures.

Acceptance: demonstrate practical alert quality, known limitations, investigator usefulness and whether drones and multi-agent review add measurable value. Expansion depends on field evidence.

## 14. First complete demonstration

Use a small simulated network with a transformer and several metered branches. Include three independently defined scenarios: legitimate load growth, a faulty measurement and an unexplained load.

Demonstrate ingestion → validation → energy balance → alert → competing agent assessments → inspection assignment → evidence upload → human finding → follow-up.

For the unexplained-load scenario, the correct pre-inspection conclusion is **suspected unauthorised consumption requiring verification**, not automatically confirmed theft. Clearly identify all simulated readings and example imagery.

## 15. Out of scope for the initial release

- Automatic legal accusations, penalties or supply disconnection.
- Autonomous drone launch or unsupported beyond-visual-line-of-sight operations.
- Theft confirmation based solely on EM readings, images or agent consensus.
- Guaranteed detection of indoor or underground theft using drones.
- Claims of city-wide savings or corruption reduction without measured evidence.

## Completion definition

The first usable release must connect measurements to explainable section-level alerts, support documented inspections, provide a bounded multi-agent challenge of competing explanations, and preserve the authorised human decision and its subsequent measured outcome.
