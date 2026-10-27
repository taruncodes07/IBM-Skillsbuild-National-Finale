# Hackathon presentation demo

The team's project dataset is described as real-world-derived with partially synthesized
columns. The current operational replay and the new paired comparison use the existing
deterministic network generator; `data/sample_readings.csv` is not connected to that
runtime. Describe the comparison as a simulation, rather than a measured field result.

## Present the impact

1. Choose **Compare loss** in the top bar, then **Run comparison**.
2. Both paths share seed 42, household demand and a 1.2 kWh/interval unmetered load
   on Branch 03 from 02:00 IST. The actual accounting/persistence detector receives
   observations only. It flags the section at 02:45.
3. Under the selected assumptions, a simulated crew responds one hour after detection
   (03:45) and removes 90% of the unmetered load. Losses match before this intervention.
4. The animated chart and timeline show monitoring, detection and response. Pause or
   scrub to explain the sequence. **Show outcome** jumps to the end of the day.
5. Defaults produce approximately 127.2 kWh lost without intervention and 37.8 kWh
   with Grid Trace plus the assumed repair, saving 89.3 kWh (70.3% less network loss).
   Values are independently rounded; technical losses remain in both paths.
6. Change to the clean control, 0% removal, next-day response or sparse metering to
   show that savings are not guaranteed. Each produces zero savings in this horizon.
7. Download the JSON report to retain every interval and the exact assumptions.

Losses are calculated once over disjoint feeder input minus household delivery, using
simulator physical truth for evaluation. Nested branch/transformer residuals are not
summed. Detection uses the same seven-day calibration and three-valid-interval rules
as operational runs. No provider call, case creation or database mutation is required.

## Show the digital twin

- **Rotate POV** slowly orbits the full network. Dragging the view stops rotation.
- **Scene motion** controls energy markers, alert pulses and decorative road traffic.
  Markers show direction, not measured electron speed or calibrated power magnitude.
- Light walls, roof surfaces, sky fill and opposing key lights keep buildings readable
  from multiple angles. Reduced-motion preferences disable decorative motion and orbit.

## Find the drone simulation

**Drone tour** above the network launches a 15-second camera-follow flight from the
base to the selected asset's connection. **End drone tour** cancels the preview.
This presentation tour creates no approval, mission record, image or evidence.

For the actual RGB capture workflow:

1. Choose **Unexplained loss**; Branch 03 is ready with a persistent alert.
2. As Analyst, **Open case**, then **Triage case**.
3. Switch to Reviewer, **Begin ground review**, then **Record ground observation**.
4. Record an obstructed/partial view and the overhead question it leaves unanswered.
5. **Approve drone inspection**. The virtual flight captures two RGB views from the
   scene; review the OpenCV overlays and export the case evidence.

The detection/repair comparison is separate from the audited investigation workflow.
An automated detection does not represent a completed real crew repair.
