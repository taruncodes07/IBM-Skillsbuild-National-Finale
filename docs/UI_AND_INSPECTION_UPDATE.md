# UI and simulated inspection update

25 October 2026. Local improvement requested after the final walkthrough; deployment remains deferred.

## Product changes

- Labelled desktop navigation: Agents, Network, Inspection, Assets, Cases and Scenarios. Replay has an explicit **Step interval** label. Scenario controls display the selected scenario and use **Start selected scenario**, avoiding confusion with a clean run.
- Refreshed surfaces, spacing, typography, teal actions, measurement cards and network heading. The count now correctly describes all 38 meter streams.
- Inspection has a large live-flight surface, approval/flight/capture/review stages, a progress bar, simulated altitude and waypoint information, and separate **Live flight** / **Captures** views. Images retain Original, Annotated, Compare and zoom controls. Smaller screens put the inspection surface first.
- An explicit reviewer approval launches a more visible quadcopter with rotating propellers, an approved-route line, waypoint markers and a following camera. Drone/analysis overlays are excluded from captured RGB images. The simulated route still takes 15 seconds; two fixed approved camera views go through the existing OpenCV pipeline.
- Reduced-motion mode uses discrete waypoint updates and a stationary camera instead of freezing the drone at its starting position.

## Bugs addressed

- Selected-asset labels could become enormous near the flight camera and obscure the drone. Asset labels are hidden in the dedicated inspection view; target identity remains in its heading.
- Navigation, role selection, scenario controls and scene selection could interrupt the flight context. Controls that change context are locked during the mission, and capture uses the mission's frozen sequence and initiating actor.
- Previously, unmounting a flight view resolved the flight promise as if it had succeeded. It now rejects; loss of WebGL or a stalled flight also produces a retryable failure instead of a silent success.
- Missions left flying/capturing/processing after a page refresh had no useful retry path. Explicit retry records interruption and restarts the same approved mission, preserving existing frame keys. Existing frames are skipped, so a retry does not duplicate them.
- Lost approval responses retain their idempotency key. A known mission clears that pending key before restart; completed responses restore captures instead of trying to fly an already completed mission.
- Saved cases with images restore into their capture view. Success notifications move away from the mission heading and dismiss after eight seconds. Review guidance reflects active flights and available captures.
- The hidden 3D scene pauses while captures are displayed. Graphics loss disables launch until restoration; renderer initialization failure offers an explicit **Retry 3D scene** control while retaining access to case review.

## Verification

- Production TypeScript/Vite build passed. Thirteen client tests passed, including approved-path interpolation, invalid-route rejection, and reduced-motion completion. Seventeen backend acceptance tests passed, covering accounting, mission transitions, images and review/export behavior. The Python runtime was unchanged by this UI increment.
- Chromium browser, isolated database on port 8010: normal approved flight visibly followed the route, locked navigation, completed, and saved two RGB images. Both controlled views produced `candidate_found`, which is only a synthetic image observation, not a finding of theft.
- A second mission was interrupted by page refresh, then explicitly restarted in reduced-motion mode. It reached waypoint 2 and completed. Storage contained exactly two missions, each completed with two frame keys, and four images total. One interruption event remained in the audit history.
- Original image selection and two-image comparison worked. The scene was inspected from screenshots during normal and reduced-motion flight; giant asset labels no longer obscured the drone.
- Inspection document, main region and mission controls fit 360, 390, 768, 1024 and 1440 pixel widths without horizontal overflow. Axe WCAG A/AA scan found no confirmed violations; gradient contrast remained an automated manual-review item. This is not real-device or formal accessibility certification.
- Local screenshots are under ignored `output/playwright/`, notably `drone-in-flight-clean.png`, `drone-captures.png`, `drone-reduced-motion.png` and `inspection-new-390.png`.

The long automated reload/resize session eventually caused Chromium to deny WebGL contexts. This was a real test limitation; the screen-size/axe results do not certify graphics stability. The readiness gate and retry control were added, and rendering was paused behind captured images. A fresh browser then reopened the saved case and completed another normal flight with no console errors: three completed missions and six images total, with exactly two frame keys per mission. The final screenshot is `drone-flight-final.png`. Real-device and longer graphics endurance testing remain outstanding.

## Walkthrough

1. Open Scenarios. Choose **Visible unmetered load**, then **Start selected scenario**.
2. Click **Step interval** three times and **Open case review**.
3. Click **Triage & prepare flight**, then **Use Demo reviewer**.
4. Click **Approve & launch drone**. The camera follows the 15-second route.
5. Review the two captures using Original/Annotated/Compare, then begin human review and save the next action.

This is browser-rendered simulated inspection. No real drone is launched. Manual review without visual evidence remains available. Live physical drone integration, broader CV validation, Gemini troubleshooting and external deployment remain outside this increment. No commit or push was made.
