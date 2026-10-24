# GridTrace acceptance record

Verification date: 24 October 2026. Synthetic demonstration only.

## Executed checks

- `npm run build`: passed TypeScript and Vite production bundling. The bundled Three.js application is approximately 1.14 MB before gzip; Vite reports the expected large-chunk warning. There is no external runtime asset dependency.
- `python -m pytest -q -s`: **17 passed**. Includes three independent API workflow rehearsals (seeds 42, 56, 73) with two explicitly rasterized pixel-control frames each, and a deliberate processing-failure control retaining original PNG and pose. These are not browser end-to-end rehearsals.
- `python tests/evaluate.py`: four calibration seeds and 12 held-out 96-interval scenario runs, each with independently generated seven-day baseline. Exact output is in `verification-results.json`.
- Local compiled frontend `/` and `/api/bootstrap`: actual HTTP 200 responses from the running FastAPI server. `tests/http_smoke.py` additionally creates a real run over HTTP, steps three intervals, verifies branch-03 localization and all 38 streams, then reads a monotonic SSE event. Exact result: `http-smoke.json`.
- Persistence: a fresh Python subprocess reopened committed cases and PNG files in the same SQLite/data directory and verified original SHA-256 against disk. App startup retains persisted records and pauses playback.

A Starlette deprecation warning notes future migration of its test client away from httpx; the pinned test suite currently passes. No warning was treated as a passed browser check.

## Acceptance criteria

- **AC-01: partially verified.** Exact metered topology, shared stable IDs, interval changes and connected stream APIs pass. Orbit/pan/zoom, geometry picking, focus, text navigator and responsive layout are implemented; no browser was available to exercise them.
- **AC-02: passed analytical checks.** Shared balance calculation stores 12.5 − 10.5 − 0 − 0.4 = 1.6 kWh, ratio 0.128. Boundary validation rejects duplicates and nested descendants. Production balances use the configured section loss model rather than hard-coding this example.
- **AC-03: passed analytical/API checks.** Sustained visible-load event first alerts at affected interval 3, localized to branch-03. A missing interval breaks persistence and delays alert until three further valid intervals. No unsupported household attribution is generated.
- **AC-04: passed analytical/API controls.** Clean, legitimate-load-change and missing-meter runs do not produce persistent loss alerts. Missing readings remain null. Export/topology/time/estimated/negative-input gates and negative residual quality review are tested.
- **AC-05: unverified live capture gate.** Approval, mission states, sequence locking, two-frame completion requirement and provenance persistence pass API tests. The browser route animation and actual WebGL offscreen camera capture implementation have not been run. No substitute images are represented as live scene captures.
- **AC-06: partially verified.** Functional grayscale/Canny/Hough/approved-geometry comparison passes candidate-present and candidate-absent controls in both calibrated views, decorative-line controls and blank-image inconclusive controls. Removing the line from the pixel fixture removes its detection. Fixtures are rasterized geometry, not actual GPU scene renders. Live scene-derived positive/negative controls and held-out rendered IoU precision/recall remain outstanding.
- **AC-07: passed API checks.** Reviewer can record uncertainty and request field inspection. Supervisor-only resolution/dismissal without a reason and disposition is rejected. No penalty/disconnection endpoint exists.
- **AC-08: passed API checks.** Creation, assignment, triage, explicit approval, evidence, review, dismissal and reopening remain in actor/timestamp/revision audit events. SQL triggers reject audit updates/deletes. Fresh observations preserve previous analyses; repeated evidence is additive.
- **AC-09: passed storage/export checks; browser recovery interaction unverified.** Cases, images and hashes survive a fresh process opening the database. JSON/Markdown include frozen observations, all contributing persistence intervals, rule version, actors, decisions, pose and separate PNG paths/hashes. PNG GET returns exactly the uploaded original. GUI refresh requires selecting the stored case from the archive.
- **AC-10: passed deterministic checks.** Identical seed/actions reproduce observed values and alert onset. Reset creates a new run and leaves original cases attached to their original run. Revisions reject duplicates and retain original snapshots.
- **AC-11: partially met.** 1,140 full interval generation/reconciliation/persistence updates were measured; p95 is approximately 2.14 ms and maximum approximately 11.48 ms on the recorded host. Eight controlled pixel processing calls had maximum approximately 33.3 ms. FPS, browser errors, actual browser upload-to-result latency and three consecutive browser rehearsals were not measured.
- **AC-12: implemented; browser presentation unverified.** Workspace, evidence, reports and evaluation labels explicitly disclose synthetic data. No theft likelihood or automatic verdict is produced; geometric scores are named separately. Source review confirms wording; screenshots were unavailable.
- **AC-13 (P1): partial.** Additional scenario generators and backend role checks are implemented. Meter faults can produce electrical anomalies without exterior wire geometry; hidden bypass likewise. Stale topology produces incomplete accounting. Model shift can produce an unexplained-loss signal. The opaque occlusion scene, varied camera clutter and held-out rendered IoU evaluation have not been exercised.

## Diagnostic results

Six eligible events were matched out of six, all at the correct smallest monitored branch. There were zero unmatched loss alerts on 2,088 valid clean branch-hours. Median onset-to-alert delay was 45 simulation minutes and p95 120 minutes; low household demand delayed under-registration eligibility. Technical-loss shift generated a branch anomaly requiring a model review, not a theft finding. Mapping mismatch was routed to data quality.

Mean branch-residual energy error was 1.61% for the four added-load cases with stable loss assumptions (visible, hidden and occluded physical events); maximum was 1.64%. Under-registration and model shift are reported separately in the raw runs and are not included in this injected-load error denominator. No confidence interval or field accuracy is claimed. Events use a large 1.2 kWh injected interval load or 85% under-registration; weak/subthreshold events are not covered by the recall figure.

## Outstanding work before declaring P0 complete

1. Run both actual scene camera presets with and without the extra wire. Inspect that overlays are absent, images are well exposed, and pixel registration supports the detector. Fix camera/contrast/ROI issues if observed.
2. Exercise orbit, pan, zoom, geometry selection, all text navigation, focus/reset, scenario controls, SSE reconnect, refresh, notes, ownership, review, original/annotated zoom and downloads in a browser. Check 375, 768, 1024 and 1440 px layouts and runtime errors.
3. Measure ≥30 FPS target on the reference laptop and real upload-to-processing latency.
4. Complete three consecutive full browser workflows and a clearly labeled backup recording.

These are explicit unmet verification gates, not scripted successes.
