# Rule 01: Architecture & Structural Standards

## 1. System Layering & Separation of Concerns

Grid Trace follows a strict decoupled architecture:
1. **Presentation Layer (`frontend/`):** React 18/19, TypeScript, Three.js / React Three Fiber. Responsible for rendering the spatial 3D digital twin, HUD overlays, pipeline ledger, and telemetry charts. Does not perform electrical power balance calculations.
2. **API & Orchestration Layer (`backend/main.py`, `engine.py`):** FastAPI application managing run lifecycles, clock ticks, snapshot generation, and investigation runs.
3. **Analytical & Reconciler Layer (`backend/analytics.py`, `topology.py`, `ranking.py`):** Pure deterministic computations. Reconciles observed energy flows, detects imbalances, evaluates technical losses, and ranks next-best checks.
4. **Autonomous Investigation Workflow (`backend/investigations.py`, `workers.py`):** LangGraph state machine executing W1–W4 workers and orchestrating Granite / Gemini LLM reasoning bounded by deterministic policy guardrails.
5. **Physical Simulation Layer (`backend/simulation.py`):** Synthetic ground-truth generator for testing and demonstration scenarios. **Completely isolated from analytics.**

---

## 2. Hard Invariants & Boundary Rules

### A. Physical Truth Isolation Boundary
- `backend/analytics.py` and `backend/workers.py` must **never import** `simulation.py`, `SCENARIOS`, or read `store.private_truth`.
- Analytical modules and workers must operate **exclusively** on public observed telemetry snapshots (`snapshot['readings']`, `snapshot['balances']`, `snapshot['alerts']`).
- Private scenario truths are only accessible via authenticated endpoints (e.g., `GET /api/runs/{id}/truth` with `X-Actor: presenter`).

### B. Hierarchical Cut Disjointness
- All energy balance cuts across network sections must evaluate **only immediate instrumented downstream children**.
- Any cut that includes nested descendants or fails `validate_cut()` in `backend/topology.py` must be rejected immediately to avoid double-counting downstream energy.

### C. Power vs. Energy Arithmetic Normalization
- 15-minute smart meter readings provide energy in kilowatt-hours ($\text{kWh}$).
- Technical quadratic loss formulations $b \cdot P^2 \cdot \Delta t$ require average real power $P$ in kilowatts ($\text{kW}$).
- Power must be computed as $P = \text{kWh} / 0.25\text{ h}$ prior to evaluating loss coefficients.

### D. Missing Telemetry & Null Preservation
- If a meter interval reading is missing or unobserved, it must be preserved as `None` / `null`.
- Never impute missing intervals with zeros or historical baseline means. Zero-filling turns unobserved intervals into false positive theft or defect alerts.

---

## 3. Tooling Distinction: Bob vs. Runtime Planner

- **IBM Bob** is the offline **development assistant** providing code suggestions, test verification, and refactoring aid during engineering sessions.
- **Granite / Gemini** are **runtime LLM providers** invoked via provider adapters in `backend/providers.py` inside the LangGraph investigation workflow.
- Do not conflate Bob's development evidence with runtime autonomous decisions.
