
```markdown
# VIDYUT-TRACE (GridTrace × VoltGuard)
## National Finale UI/UX & Interactive Demo Specification

**Objective:** Replace scattered windows, confusing toggles, and disconnected modals with a **single-screen, zero-clutter "Grid Operations Cockpit"** where judges can visually track the entire lifecycle:
**Replay ➔ Validate (W1) ➔ Localize & Fuse (W2–W4) ➔ Recommend Next Check ➔ Fly Conditional Drone & Run OpenCV ➔ Human Sign-off & Audit.**

---

## 1. The Golden UI Rule: "One Screen, Four Zones, Zero Floating Modals"

Judges lose track when windows pop up over the 3D scene or when they have to scroll through multiple pages. Lock the viewport (`100vw x 100vh`, `overflow: hidden`) into **4 fixed structural zones**:


```

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ [TOP BAR]  Brand | Synthetic Provenance Badge | Replay Controls (Play/Step/Speed) | Mode │
├───────────────────────┬──────────────────────────────────────────┬───────────────────────┤
│                       │                                          │                       │
│  [LEFT PANEL: 25%]    │          [CENTER VIEWPORT: 47%]          │  [RIGHT PANEL: 28%]   │
│                       │                                          │                       │
│  1. Network Hierarchy │       Interactive 3D Digital Twin        │  1. Live Agent Pipeline│
│     (F-01 > DT > BR)  │       (React Three Fiber)                │     (W1 ➔ W2 ➔ W3 ➔ W4│
│                       │                                          │      + Granite/Policy)│
│  2. Sectional Energy  │   ┌──────────────────────────────────┐   │                       │
│     Balance Waterfall │   │ [PIP DRONE HUD - Appears ONLY    │   │  2. Evidence Ledger & │
│     (E_in - E_out = R)│   │  during approved aerial mission] │   │     Competing Causes  │
│                       │   └──────────────────────────────────┘   │                       │
│  3. Data Validity &   │                                          │  3. Next-Best-Check & │
│     3-Interval Streak │   [Bottom Pill: Scenario Switcher]       │     Human Case Gate   │
│                       │                                          │                       │
├───────────────────────┴──────────────────────────────────────────┴───────────────────────┤
│ [BOTTOM DRAWER - Collapsible]  Eval Metrics (B0/B1/B2) | BESCOM Ref | IBM Bob Proof Log  │
└──────────────────────────────────────────────────────────────────────────────────────────┘

```

---

## 2. Zone-by-Zone Component Breakdown (Checking Every PRD Requirement)

### ZONE A: Top Command Bar (Global State & Provenance)
1. **Persistent Provenance Banner (FR-11 / Sec 5.3):**
   - Pill badge: `SYNTHETIC REPLAY: VIDYUT_TRACE_v4 (109,440 rows)` | `Ref: BESCOM Hebbal F11-Sanjay Nagar (9.31% gap)`.
2. **Time-Series Replay Scrubber (FR-03):**
   - `Play/Pause`, `Step +15m`, Speed (`1x`, `10x`, `60x`), and current timestamp (`2022-09-14 14:45:00`).
3. **Guided Demo Stepper (Anti-Clutter Navigation):**
   - A 4-button preset bar at the top right so the presenter never fumbles with raw filters during the 5-minute pitch:
     - `[1. Clean Baseline]`
     - `[2. Scenario B: Missing Meter (NULL)]`
     - `[3. Scenario A: Branch Residual + Drone Check]`
     - `[4. IBM Bob Proof & Eval]`

---

### ZONE B: Left Panel — Topology & Physics Accounting (Dev 1 + Dev 2)
1. **Interactive Asset Tree (FR-02):**
   - Compact tree: `F-01` ➔ `DT-01` ➔ `BR-01` / `BR-02` ➔ `H-01..H-06`.
   - Clicking any node smoothly orbits the 3D camera to that boundary and filters the math panel below.
   - Status dots next to each node: 🟢 `Balanced` | 🟡 `Data Incomplete (NULL)` | 🔴 `Persistent Residual (>3 intervals)`.
2. **Sectional Energy Balance Card (FR-04 & FR-05):**
   - Shows a visual horizontal stacked bar / waterfall for the selected boundary:
     - **Boundary Input ($E_{\text{in}}$):** `12.50 kWh`
     - **Downstream Cut ($\sum E_{\text{out}}$):** `- 10.50 kWh`
     - **Expected Tech Loss ($L_{\text{expected}}$):** `- 0.40 kWh` *(or tagged `Uncalibrated / Assumed` per FR-05)*
     - **Unexplained Residual ($R$):** `= 1.60 kWh (12.8%)`
3. **Persistence & Quality Gate Tracker (FR-06):**
   - 3 visual interval boxes showing the consecutive 15-minute streak: `[Int t-2: 12.4%] ➔ [Int t-1: 12.9%] ➔ [Int t: 12.8%] = ALERT QUALIFIED`.
   - When `quality=missing` hits, the box turns Amber: `[Int t: NULL - STREAK BROKEN - DATA INCOMPLETE]`.

---

### ZONE C: Center 3D Viewport & Drone Inspection Motion (Dev 2)

#### 1. Clean 3D Network Visuals
- Avoid noisy floating text labels over every house. Show labels **only** for the currently selected branch/transformer and hovered asset.
- Color-code power lines by state:
  - Normal load: Cyan/Blue pulse along conductor lines.
  - `DATA_INCOMPLETE`: Dashed Amber line.
  - Persistent unexplained residual: Glowing Red/Orange boundary highlight around the specific branch (`BR-01`)—**never** putting a "guilty" red skull or theft label on an individual house.

#### 2. How the Drone Moves & What It Does Visually (FR-08 & FR-15)
Instead of opening a separate window when a drone inspection is approved, execute a **3-Stage In-Scene Sequence**:

- **Stage 1: Waypoint Path Appears (0–1 sec)**
  - Once the human reviewer clicks `[Approve Virtual Drone Inspection]`, a glowing cyan dotted flight path with 3 numbered waypoints (`WP-1: Launch`, `WP-2: Pole Cross-Arm Hover`, `WP-3: Service Drop Angle`) appears above the target branch (`BR-01`).
- **Stage 2: Drone Flight & Camera Cone Animation (1–4 sec)**
  - The 3D quadcopter mesh smoothly lerps along the spline from `WP-1` to `WP-2`.
  - Render a **semi-transparent frustum cone (spotlight beam)** projecting from the drone's camera gimbal onto the overhead pole conductors so judges visually see *what* the drone is scanning.
- **Stage 3: Picture-in-Picture (PiP) Drone HUD Overlay (4–7 sec)**
  - A sleek Picture-in-Picture HUD slides into the bottom-right corner of the 3D canvas showing:
    1. **Tab 1: Raw Scene RGB Capture (640×480)** with UI overlays stripped, showing camera pose `(x, y, z, pitch, yaw)` and `SHA-256` hash.
    2. **Tab 2: OpenCV Canny/Hough Wire Overlay** showing green projected CAD lines (approved topology) and a bright magenta bounding highlight around the unmatched line segment.
    3. **Result Badge:** `CANDIDATE_FOUND (IoU/Geo Score: 0.84)` + Mandatory Disclaimer Banner: *"Visual geometry candidate only. Does not prove current flow, energization, or theft."*

---

### ZONE D: Right Panel — Live Agent Trace, Evidence & Human Gate (Dev 3)

This solves the *"How do judges see agents at work?"* problem. Divide the right panel into three stacked cards that animate top-to-bottom when an investigation runs:

#### Card 1: Live Multi-Worker Execution Trace (FR-08 & FR-11)
A vertical stepper showing each worker lighting up in sequence (`Pending` ➔ `Running spinner` ➔ `Completed badge` + latency in `ms`):

- **[W1] Metering & Accounting Worker** (`18 ms`)
  - *Output:* `Inventory 6/6 valid | Disjoint cut verified | Streak: 3/3 intervals > threshold.`
- **[W2] Electrical Physics Worker** (`12 ms`)
  - *Output:* `Line impedance uncalibrated in CSV; conservative 3.2% technical loss bound applied. Residual exceeds physics bound.`
- **[W3] Commercial & Baseline Worker** (`15 ms`)
  - *Output:* `Downstream meters H-01..H-06 show stable baseline; no billing invoice mismatch data available.`
- **[W4] Spatial Localization & Vision Worker** (`42 ms` / `2.1s with CV`)
  - *Output:* `Smallest boundary localized to BR-01. Ground view obstructed; aerial RGB candidate detected.`
- **[Planner + Policy Gate] Deterministic / IBM Granite (`ibm/granite-4-h-small`)**
  - *Badge:* Shows either `Granite 4.0 H Small (Verified)` or `Deterministic Planner (Fallback Active)`.
  - *Policy Gate Check:* `Action validated against 9-enum whitelist. Zero truth-leak verified.`

#### Card 2: Competing Hypotheses & Evidence Ledger (FR-07 & FR-09)
Instead of a wall of text, show 3 compact progress/confidence bars side-by-side so judges see the system weighing alternatives:
- **Unaccounted / Bypass Load:** `Supported (E_in > E_out + L_exp, CV Candidate)`
- **Data / Telemetry Failure:** `Contradicted (All 6 child streams valid)`
- **Meter Under-Registration:** `Plausible (Requires physical meter test)`
- **Missing Evidence Explicitly Listed:** *"Physical energization verification & service connection authorization records."*

#### Card 3: Allowed Next Action & Human Review Gate (FR-10, FR-13, FR-14)
- **Recommended Action Pill (Strictly from FR-10 Enum):**
  - e.g., `PROPOSE_VIRTUAL_DRONE` ➔ transitions after flight to `REQUEST_ELECTRICAL_RECHECK` or `REQUEST_METER_REVIEW`.
- **Ground-First Log Input (FR-07):**
  - A 1-click preset dropdown for the presenter: *"Ground lead notes: Overhead mid-span obscured by compound roof at Pole P-04."*
- **Human Disposition Buttons:**
  - `[Approve Next Check]` | `[Override / Dismiss]` | `[Export Case (JSON / MD)]`
  - Shows persistent Case ID (`CASE-2022-0914-BR01`) and status (`AWAITING_REVIEW` ➔ `APPROVED_FOR_NEXT_CHECK`).

---

### ZONE E: Collapsible Bottom Drawer — Evaluation, Finance & IBM Bob Proof (FR-12, FR-16, FR-17)

Keep this collapsed during the 3D walkthrough, then click `[Expand Engineering & Evaluation Drawer]` for the final 60 seconds of the pitch:

1. **Tab 1: IBM Bob Engineering Evidence (10-Mark Rubric Clincher):**
   - Renders `docs/bob-evidence/` directly in the UI!
   - Shows a clean 3-column view: **Prompt / Defect** (`Missing meter treated as 0 kWh`) ➔ **Actual Git Diff** (syntax-highlighted patch) ➔ **Pytest Output** (`8 passed in 0.42s`).
2. **Tab 2: Baseline Comparison Table (B0 vs. B1 vs. B2):**
   - Side-by-side metrics on the held-out scenarios showing how **B0 (Static Threshold)** triggers false dispatches on missing meters, while **B1/B2 (VIDYUT-TRACE)** achieves `0` false dispatches via `DATA_INCOMPLETE` abstention.
3. **Tab 3: Honest Financial Impact Breakdown (FR-16):**
   - Separates `Physical Unexplained Energy (kWh)` from `Simulated Billable Value (₹)` and `Inspection Cost (₹)`, explicitly labeled as *Simulated / Conditional*.

---

## 3. How to Clean Up the Current Clutter (Actionable Checklist for Your 3 Devs)

1. **Kill Duplicate Scenario Controls:**
   - Remove scattered "Inject Theft", "Break Meter", and "Reset" buttons from the sidebar. Consolidate all demo state transitions into the **4-button Guided Demo Stepper** in the Top Bar.
2. **Stop Auto-Flying the Drone:**
   - The drone should remain parked at its substation pad until a case reaches `AWAITING_REVIEW` and the human operator clicks `[Approve Virtual Drone Inspection]`. This makes the flight a dramatic, intentional 5-second visual highlight.
3. **Replace Raw JSON Dumps with Visual Pills:**
   - Never render raw JSON on the main screen. Use structured badges (`DATA_INCOMPLETE`, `CANDIDATE_FOUND`, `REQUEST_MISSING_DATA`) and put raw JSON behind the `[Export Case (JSON/MD)]` button.
4. **Synchronize Selection Across All Panels:**
   - Selecting `BR-01` in the 3D scene **must** automatically highlight `BR-01` in the Left Asset Tree, load `BR-01`'s waterfall math, and filter the Right Panel to `BR-01`'s active investigation case.

```