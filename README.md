# Grid Trace

Local development milestone: September 2022 replay, W1-W4 workers, evidence fusion, LangGraph orchestration, Granite/Gemini transport adapters, worker-linked case exports, conditional finance and diagnostic baseline results are implemented. The app currently uses clearly labeled development fixtures; original source onboarding and Gemini live verification are pending. See [docs/BUILD_STATUS.md](docs/BUILD_STATUS.md) and [docs/PROVIDERS.md](docs/PROVIDERS.md). The older verification records below describe the original scenario laboratory.

A local, simulation-backed electricity-distribution investigation application. **Synthetic demonstration:** every asset, reading, incident, flight and image is synthetic. Unexplained energy and visible line candidates do not establish theft, authorization or energization.

Implemented with React 19, TypeScript, Vite, Three.js/React Three Fiber, FastAPI, SQLite and OpenCV. No paid API, remote model, external font or cloud service is needed at runtime. The supplied concept images guide the dark three-column workspace; scenery is procedural geometry rather than photographic reconstruction.

## Run locally

Docker option: from this directory run `docker compose up --build -d`, then open **http://127.0.0.1:8080/**. Docker Desktop must be running. Runtime credentials come from the optional `.env`; cases/evidence persist in a separate named volume. See [docs/DOCKER.md](docs/DOCKER.md) for setup, stopping and data details.

Reference environment: Windows 11, Python 3.14.3, Node 24.14.0, npm 11.9.0. Python 3.12+ and Node 20.19+ are recommended; the exact lock was exercised on the reference versions.

From this directory in PowerShell:

```powershell
.\start.ps1
```

Open **http://127.0.0.1:8000**. The script creates a project virtual environment, installs locked dependencies and builds the frontend before starting FastAPI. Dependency installation needs internet; subsequent operation is local. If PowerShell's script policy prevents the convenience script, run the commands individually rather than changing machine policy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm ci --no-audit --no-fund
npm run build
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

For frontend development, keep the API server running, then `npm run dev` in another terminal and open the Vite URL. Vite proxies `/api` and `/evidence`. The production server serves `dist` directly; restart it after the first build or backend edits. Stop with Ctrl+C.

SQLite, immutable original PNGs, annotated PNGs and hashed report files live under `data/`. `GRIDTRACE_DATA` can point to a different local directory. Keep the whole directory to preserve runs and evidence. Starting a new run never deletes an existing run or case. On restart, replay is paused; persisted intervals are used directly. Tests and evaluation use separate temporary databases.

## Demonstrate the workflow

1. Open **Simulation laboratory** (flask icon). Choose `Visible unmetered load`, seed **42**, and start a new run. Interval 0 is clean; the event starts at interval 1.
2. Step three times, or play at 10×. `branch-03` gains an alert after three qualifying valid intervals. Explore input, the three household streams, technical loss, residual, threshold and the exact meter cut. The scene's highlight uses this alert.
3. As **Demo analyst**, open the investigation, assign a fictional owner and triage it.
4. Select **Demo reviewer**. Record a ground observation, including visibility and the specific overhead question that remains unanswered. If the ground view is obstructed or partial, approve the simulated inspection. A clear or resolved ground view does not justify a flight. The API pauses telemetry and locks the capture sequence. A 15-second route is independent of telemetry speed. The frontend renders two 640×480 RGB frames using two calibrated virtual cameras; scene overlays are hidden for offscreen rendering. Original images are uploaded to the local backend and processed by OpenCV.
5. Inspect original/annotated output, candidate geometry scores and the limitations. Begin human review. Record a reason, choose `Inconclusive` or another appropriate disposition, and request field inspection. An RGB-negative result does not dismiss the energy signal.
6. **Demo supervisor** can resolve/dismiss with a reason and disposition, or reopen a previous decision. Every change remains in the audit history. Export JSON, Markdown and the separate original/annotated PNG downloads.
7. Start `Missing telemetry`, `Clean`, and `Legitimate load change` controls. A missing household reading remains null and blocks branch-loss classification. Select a household and use **Revise / restore this observed reading** to supply a replacement and explicitly recompute. Original analyses remain accessible through the revisions API.

The identity selector is a simulated, backend-enforced role gate. It is **not authentication**. Bind to localhost and use fictional data only.

## Simulation and accounting

- `backend/topology.py` defines 2 feeders, 4 transformers, 8 monitored branches, 24 household meters and 8 branch poles. There are 38 measurement streams. Coordinates are local meters; no geographic position is claimed.
- Every new seed independently generates seven clean baseline days (672 intervals). Same-time household means and section residual standard deviations are retained. The scenario laboratory has 96 intervals starting 1 September 2022 00:00 IST. Month replay has 2,880 intervals across September 2022. The interface names Asia/Kolkata; wall and simulation time are separate.
- `backend/simulation.py` constructs physical household demand and losses, then observed readings with ±0.2% meter noise. Private truth is persisted separately from public observations. Hidden loads increase upstream physical inputs; under-registration only changes the affected meter observation.
- `backend/analytics.py` imports neither simulator nor truth store. It receives observed readings, approved topology and clean-baseline parameters. Each section uses its immediate downstream instrumented cut, never a mix of descendants. Only disjoint sections may be aggregated.
- Accounting: `R = input − downstream interval kWh − declared authorized energy − expected loss`. Authorized unmetered energy is explicitly configured to zero for this topology.
- Expected loss is `a × 0.25 h + b × downstream_kW² × 0.25 h`. Configured `(a [kW], b [1/kW])`: branch `(0.035, 0.0012)`, transformer-secondary wiring `(0.045, 0.00012)`, feeder-to-transformer-secondary `(0.08, 0.00004)`. The latter includes intervening conductors and transformer losses. These are synthetic accounting approximations, not power-flow solutions.
- Threshold: `max(0.25 kWh, 0.08 × input, 3σ)`, with clean-residual σ floored at `0.015 kWh`. Three consecutive complete valid excess intervals produce one active section/rule alert. A missing/invalid interval breaks the streak. Negative residuals are stored and routed to quality review.
- Meter watchlist requires an already anomalous branch, demand floor `0.15 kWh`, and below 50% of the meter's own seven-day same-time baseline for three intervals. It is a consumption-change reason with small-sample uncertainty, not household attribution.
- Playback is server-owned: 15 s per interval at 1×, 1.5 s at 10× and 0.25 s at 60×. Every interval is calculated and persisted. Seed, topology version, incident schedule and analysis version determine replay; wall time does not enter the accounting.

Scenario configuration and calibration/evaluation seeds are in [scenarios.json](scenarios.json). `occlusion` adds an ordinary opaque scene panel in front of the added line; its visual behavior remains unverified. Topology-mismatch produces quality review rather than automatic cause attribution. Model shift can produce an unexplained-loss alert requiring a model investigation.

## Image processing

`backend/inspection.py` receives RGB pixels, camera pose and target boundary. It projects approved connection paths from backend topology, selects an overhead observation band, converts pixels to grayscale, applies Canny and probabilistic Hough detection, compares segments against the union of approved paths and groups unmatched pole-attached line segments. No incident type, extra-wire object ID, truth mask or injected bounding box reaches this function. Added and approved wires share the same scene material.

Frozen parameters: Canny `45/125`, Hough vote threshold `22`, minimum line length `38 px`, gap `10 px`, approved-path tolerance `7 px`, pole attachment tolerance `30 px`, candidate length `45 px`. The overhead crop derives only from approved geometry and calibration. Results are `candidate_found`, `no_visible_candidate`, or `inconclusive`. Sparse/blank observations are inconclusive; clutter can cause false candidates. These parameters support controlled synthetic views, not general field imagery. Pixel controls are explicitly tagged `pixel_control_fixture`, separate from UI uploads tagged `webgl_scene`.

Original and annotated PNG hashes, source declaration, pose, calibration/geometry version, run, simulation sequence, timestamps, detector parameters and limitations are stored. Reinspection creates new evidence records. A processing failure preserves the original file, records a mission failure and allows retry/cancellation or continuing without visual evidence. Local hashes and append-only application audit triggers are not independently certified chain of custody.

The implementation follows [OpenCV's Hough line documentation](https://docs.opencv.org/4.13.0/d9/db0/tutorial_hough_lines.html) and [React Three Fiber's rendering hooks](https://r3f.docs.pmnd.rs/api/hooks).

## APIs and modules

Interactive API documentation: http://127.0.0.1:8000/docs

- `POST /api/runs`, `GET /api/runs/{id}/snapshot`, `POST /api/runs/{id}/control`
- `POST /api/runs/{id}/incidents` and explicit `GET /api/runs/{id}/truth` require `X-Actor: presenter`.
- `GET /api/runs/{id}/events?after_seq=N` is an SSE stream. Event IDs increase monotonically per run; the client fetches a coherent fresh snapshot and ignores stale/out-of-run replies.
- `GET /api/assets/{id}/history?run_id=...`
- `POST /api/runs/{id}/readings/revise` requires `asset_id`, `sequence`, `expected_revision`, `energy_import_kwh` and `quality`; `GET /api/runs/{id}/analysis-revisions` retains prior analyses and recomputation records.
- `POST /api/cases`, `PATCH /api/cases/{id}`, `GET /api/cases/{id}`
- `POST /api/cases/{id}/missions`, `PATCH /api/missions/{id}`, `POST /api/missions/{id}/frames`
- `GET /api/cases/{id}/export?format=json|md`, and separate `/evidence/{server-generated-filename}` downloads.

Cases deduplicate by alert. Missions/frames use idempotency keys. Case changes require the current revision; stale or invalid transitions return 409. Mission approval and visual review require reviewer/supervisor; terminal decisions and reopening require supervisor. PNG uploads are limited to 5 MB and 640×480, with dimensions checked before decoding. The local API cannot independently certify that a declared scene capture actually originated from a browser camera; this is a local prototype trust boundary.

## Verification and remaining gates

```powershell
.\.venv\Scripts\python.exe -m pytest -q -s
.\.venv\Scripts\python.exe tests/evaluate.py
```

Read [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) and [docs/verification-results.json](docs/verification-results.json) for actual results and denominators. The automated suite tests full API workflows with pixel fixtures, not rendered browser captures.

**The build is not claimed to have passed every P0 acceptance criterion.** Browser tools exposed no usable browser, and the user requested documenting that limit. Live scene capture (AC-05), real scene-derived CV controls (part of AC-06), layout/runtime interactions, ≥30 FPS and three browser rehearsals (AC-11) remain unverified. Capture and route code is implemented, but no actual browser-captured frame or backup recording was produced in this session. P1 held-out rendered-view/occlusion IoU evaluation and full accessibility QA remain outstanding. Do not interpret rasterized pixel-control success as validation of the 3D scene camera pipeline or real-world vision accuracy.
