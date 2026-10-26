# Developer 1: Data, Simulation, and Energy Analytics Documentation
## VIDYUT-TRACE / GridTrace — Mathematical & Analytical Architecture

**Author:** Developer 1 (Role B: Simulation and Analytics)
**Specification:** GridTrace PRD v5.0 (24-Hour Build Edition)
**Status:** Validated & Tested

---

## 1. Network Topology & Boundaries

The physical topology follows a fictional radial distribution network inspired by Bengaluru (Hebbal–Sanjaynagar cell):

* **Feeder Level (2 Feeders):** `feeder-01`, `feeder-02`
* **Distribution Transformer Level (4 DTs):** `transformer-01` through `transformer-04`
* **Monitored Branch Level (8 Branches):** `branch-01` through `branch-08`
* **Consumer Household Level (24 Meters):** `household-01` through `household-24`
* **Total Instrumented Measurement Streams:** 38 streams

### P0 10-Stream Slice (PRD v5.0 Section 1 & Section 4)
For the 24-hour P0 evaluation, a clean, minimal 10-stream slice is isolated:
* **1 Feeder:** `feeder-01`
* **1 Transformer:** `transformer-02`
* **2 Branches:** `branch-03`, `branch-04`
* **6 Households:** `household-07`, `household-08`, `household-09`, `household-10`, `household-11`, `household-12`

---

## 2. Energy Balance & Accounting Formulas (Section 6)

For every monitored boundary $s$ and aligned 15-minute interval $t$ ($0.25\text{ h}$):

$$R(s, t) = E_{in}(s, t) - \sum_{m \in \text{cut}(s)} E_{out}(m, t) - E_{auth}(s, t) - L_{expected}(s, t)$$

Where:
* $E_{in}(s, t)$: Boundary interval import energy ($\text{kWh}$)
* $\sum E_{out}$: Sum of immediate disjoint downstream metered outputs ($\text{kWh}$)
* $E_{auth}$: Authorized unmetered energy ($\text{kWh}$, configured to $0.000$ for this demonstration)
* $L_{expected}$: Modeled technical dissipation in conductors and transformers ($\text{kWh}$)
* $R(s, t)$: Unexplained residual energy ($\text{kWh}$)
* $\text{Residual Ratio} = \frac{R(s, t)}{\max(E_{in}, 10^{-6})}$

### Reduced-Order Technical Loss Model
Conductor and transformer dissipation is approximated using a versioned quadratic model:

$$L_{expected} = a \cdot \Delta t + b \cdot \left(\frac{E_{out}}{\Delta t}\right)^2 \cdot \Delta t$$

Where $\Delta t = 0.25\text{ h}$, $P_{load} = E_{out} / 0.25\text{ kW}$, and coefficients $(a [\text{kW}], b [1/\text{kW}])$ are:
* **Branch:** $(0.035, 0.0012)$
* **Transformer:** $(0.045, 0.00012)$
* **Feeder:** $(0.08, 0.00004)$

### Worked Fixture (Gate G-02)
$$12.500\text{ kWh (in)} - 10.500\text{ kWh (out)} - 0.000 - 0.400\text{ kWh (loss)} = \mathbf{1.600\text{ kWh unexplained (12.8\%)}}$$

---

## 3. Dynamic Thresholding & 3-Interval Persistence (Section 6)

To prevent transient noise or meter jitter from creating false alarms:

$$\text{Threshold}(s) = \max\left(0.250\text{ kWh}, \; 0.08 \times E_{in}, \; 3 \times \sigma_{residual}\right)$$

Where $\sigma_{residual}$ is the clean baseline standard deviation (floored at $0.015\text{ kWh}$).

* **Persistence Rule (Gate G-03):** An active alert fires **only on the 3rd consecutive valid qualifying interval** ($R > \text{Threshold}$).
* **Missing Data Rule:** If any required meter drops offline, the cut is marked `data_incomplete`. The persistence streak is immediately reset to $0$. Missing values are preserved as `None` / `null` and are **never zero-filled**.

---

## 4. Next-Best-Check Scoring Engine (Section 7)

Information-gathering checks are quantitatively ranked using:

$$S(a) = IG(a) \times R \times A - 0.35 \times C_n - 0.15 \times T_n$$

* $IG$: Information Gain in bits
* $R$: Observation reliability ($0$–$1$)
* $A$: Probability of obtaining access ($0$–$1$)
* $C_n = \min(C / 2000, 1)$ ($C$ in INR)
* $T_n = \min(T / 120, 1)$ ($T$ in minutes)

### Standard Catalog & Computed Scores:
1. **Meter record cross-check:** $0.55 \times 0.95 \times 1.0 - 0.35 \times \frac{100}{2000} - 0.15 \times \frac{10}{120} = \mathbf{0.493}$
2. **Targeted ground inspection:** $0.90 \times 0.85 \times 0.90 - 0.35 \times \frac{500}{2000} - 0.15 \times \frac{35}{120} = \mathbf{0.557}$
3. **Aerial view (drone):** Ineligible when feature flag is off per PRD v5.0 Section 11.

### Policy & Abstention Gates:
* **Best Score $\le 0.05$:** System abstains and lists missing evidence.
* **Sensitivity Bounds:** Parameters vary by $\pm 20\%$. Competitors within $0.05$ of the winner trigger a human choice notice.
* **Data Incomplete:** Hard gate directs to `REPAIR_OR_VALIDATE_DATA` (`REQUEST_MISSING_DATA`) and withholds loss dispatch.

---

## 5. Coverage Modes (Section 6 & Gate G-05)

1. **`full`:** All meters required $\implies$ Localize to smallest complete branch.
2. **`partial`:** Complete aggregate cut works; incomplete branch returns `data_incomplete`. Never zero-fill.
3. **`feeder_and_dt_only`:** Feeder and DT evaluated $\implies$ Branches return `insufficient_observability`. No branch or household accusation.
4. **`feeder_only`:** Feeder evaluated $\implies$ DTs and branches return `insufficient_observability`.

---

## 6. Assumptions & Limitations

1. **Synthetic Nature:** All network topologies, readings, and incidents are synthetic demonstrations. Unexplained residuals do not establish real-world theft or legal culpability.
2. **Simplified Power Flow:** AC power flow equations (reactive power $Q$, voltage angle $\theta$) are omitted in favor of the $(a, b)$ reduced-order loss model for 24-hour deterministic reproducibility.
3. **Household Non-Attribution:** Individual meters are never accused of theft; only section-level residuals are localized.
