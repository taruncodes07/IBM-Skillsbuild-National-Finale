# Full adaptive evaluation and product QA

## Current B2 regression rerun — 26 October 2026

Reran the unchanged full-workflow evaluator against merged main commit `1dd59d3`.
The current results are in `adaptive-results.json`; the original report is preserved
as `adaptive-results-2026-10-25.json`. The sections below describe the historical run.

- Granite (`ibm/granite-4-h-small`): 18/18 completed and matched the declared rubric;
  zero provider failures, policy rejections or skipped cases. Six cases executed eight
  local checks; two replanning rounds cited derived-check evidence. Total case time:
  109.344 seconds. Provider-reported usage: 60,745 prompt and 5,970 completion tokens.
- Rules: 18/18 completed and matched the rubric, with zero automatic checks or provider
  calls; total case time 1.603 seconds.
- Both arms passed the bounded/unique-check, chronological evidence-reference and
  normal/nonpersistent-signal checks. Granite was pinned with fallback disabled.
  Operator cases and evidence were untouched; evaluation used disposable storage.

The original seed, case-generation protocol and scoring rubric were retained. These
are previously evaluated synthetic realizations rerun for regression validation,
not newly unseen cases. The old Granite score was 15/18; the new 18/18 result is one
stochastic rerun on changed code, not evidence of a causal improvement or superiority
over rules. The rubric permits immediate human handoff and does not measure the
information value of a check, real-world accuracy or cause identification.

This B2 suite exercises the persisted investigation graph at full metering coverage.
It does not exercise every new coverage profile, the separate next-check ranking API,
ground observations or drone flights. Those features have separate deterministic and
integration tests. Gemini and external deployment remain deferred.

Report-freshness regression tests: 2 passed. No runtime/evaluator source was changed
for this rerun. The historical first-action pilot remains stale by design.
The separate free B0/B1 detection diagnostics were also refreshed at the same code
fingerprint: each matched 16/20 eligible events, with zero false alerts over six
valid control branch-hours. Their detection rubric is separate from B2.

## Historical run and QA

25 October 2026. Local changes on `grid-trace-prototype`; no commit or push for this increment.

## Full B2 workflow

The new `tests/adaptive_evaluation.py` executes the production persisted LangGraph: mandatory workers, planner, policy, registered follow-up, replanning and terminal handoff. It uses a disposable SQLite database and disables external LangSmith tracing. It does not modify operator cases.

The protocol, manifest and scoring rubric were saved before model requests. Seed 2026102504 creates 18 new cases with randomized branches, 6–16 interval windows, demand scaling and meter noise. These share the nine known mechanism families and fictional topology with earlier work. They are held-out realizations, not unseen mechanism families or an independently blinded external study. The generator uses independent forward equations; mechanism labels and scoring criteria are never passed to the planner.

Granite was pinned to `ibm/granite-4-h-small`. Gemini and rules failover were disabled for the Granite arm. Both arms used identical frozen inputs and the same three-check, six-request, 60-second investigation limits. Immediate human handoff is permitted; executing more checks does not automatically earn a higher score.

Actual results in `adaptive-results.json`:

- Granite: 18 planned, 17 completed, 15 rubric successes, one policy rejection, zero transport failures and zero skipped cases. Six cases executed seven checks in total. One replanning round explicitly cited a derived check's evidence ID. Total case time 117.460 seconds; provider-reported usage 57,190 prompt and 5,706 completion tokens.
- Rules: 18 planned/completed/successful, zero automatic follow-ups, zero provider calls. Total case time 2.004 seconds. The rules normally hand off directly to a human instead of selecting additional local checks.
- All six normal/demand-shift/weak-signal Granite cases completed with summaries and no diagnostic checks. Executed checks remained bounded and unique; evidence references passed chronological availability checks.

Success requires completion without policy rejection or provider failure, a terminal action matching the predeclared observation-status rubric, valid evidence references, unique bounded checks and no diagnostic escalation on normal/nonpersistent observations. Failed, skipped and blocked cases remain in the denominator.

The three Granite misses remain visible:

1. `heldout-04`: repeated a topology request after its result was supplied. Independent policy blocked the second execution. The first result indicated a mapping mismatch; the model's prose overstates what an automatic registered-graph check could resolve.
2. `heldout-07`: requested missing commercial data for an unexplained residual instead of the rubric's meter review or summary.
3. `heldout-15`: electrical and topology checks completed, followed by a commercial-data request outside that same terminal rubric.

The latter two are rubric mismatches, not proof of unsafe execution or incorrect physical diagnosis: billing data really is unavailable. The limited rubric does not score the value of obtaining it. The results do not establish that Granite improves on the rules. They also do not establish field accuracy, causal identification, household guilt, financial recovery or the benefit of more checks. Most follow-up decisions still cited original worker evidence, so strong claims about adaptive evidence use would be premature.

The older 36-case B0/B1 detection diagnostics were refreshed at the same code fingerprint: each detects 16/20 eligible events, zero false alerts over only six valid control branch-hours. Those are a separate detection suite; their recall must not be compared numerically with the 18-case terminal-action success count. The legacy B2 placeholder in that detection-only JSON refers to its own 36-case suite. The Evaluation UI displays the new full-workflow results separately and only B0/B1 from the detection report. The earlier nine-case first-action pilot is retained as a historical artifact and becomes stale under the expanded fingerprint.

## Product QA performed

- Full backend suite: 63 passed after adding seven repeated-journey/recovery tests. Two additional report-freshness tests passed separately afterward: 65 verified backend tests in total. Client recovery suite: 10 passed. TypeScript and production build passed.
- Five repeated API journeys with different seeds: create scenario, investigate using rules, triage, review, field-check handoff, conflicting revision rejection, frozen export after replay advancement. No visual mission required.
- Restart/cancellation tests: queued/planning/running records become interrupted at startup; a second startup preserves that state; no automatic provider spend or retry. Cancellation persists interruption. Reusing the original key returns the original record; an explicit new key runs a new investigation. These test lifecycle recovery and persisted states, not arbitrary OS or disk failures.
- Three consecutive Chromium browser journeys, seeds 711/712/713: start visible-load scenario, step three intervals, create case, triage, switch reviewer, continue without visual evidence, save field-review reason, download JSON and Markdown. All three exports were parsed and checked: interval sequence 3, four audit events, field-check-required state, zero missions/evidence. Raw screenshots and exports are local under ignored `output/playwright/`.
- A separate real Granite investigation completed through the UI, preserving the same case interval. Reviewer submission was rejected with the expected simulated-role error; switching to analyst allowed the investigation. These role gates are demonstration controls, not authentication.
- Browser offline save: note remains in the textarea and tab storage, an actionable error appears, reconnect and refresh restore reviewer identity, case interval and draft. Continuing human review saves the draft as the transition reason in the audit trail.
- Network and review views fit 360×800, 390×844, 768×1024, 1024×768 and 1440×900 without document/main horizontal overflow. Initial and completed investigation dialogs fit 360, 768 and 1440 pixel widths without internal horizontal overflow. Fixture disclosure stays visible.
- Dialog opens with focus inside, reverse Tab wraps inside, Escape closes and returns focus to the launcher. Asset navigation and case review provide alternatives to 3D picking.
- Axe 4.10.3 WCAG A/AA scans found an inaccessible scrolling capture panel; adding a named focusable region fixed it. A calendar label on a generic div was fixed with `role="group"`. After fixes, review and completed investigation scans reported no confirmed violations. Gradient/overlap contrast checks remain marked incomplete by axe; screenshot review was performed, but full contrast certification, screen-reader testing and real-device testing are not claimed.
- Screenshots exposed a feeder label rendering above dialogs. Both selected and feeder labels now use a bounded scene z-index. A missing favicon was also fixed.

## Local performance

Windows, AMD Ryzen 9 270 / Radeon 780M, about 15 GiB reported RAM, Node 24.19.0. Chromium, loopback network, cached production assets; no mobile CPU or network throttling.

Three case-review reloads reached the visible review heading in 227, 154 and 199 ms. DOMContentLoaded was 54, 22 and 56 ms. This does not measure complete 3D rendering or cold mobile startup.

Ten requests per endpoint against the isolated QA server:

- Health: median 2.13 ms, maximum 3.53 ms, 255 response bytes.
- Bootstrap: median 8.26 ms, maximum 12.10 ms, 1,416 bytes.
- Snapshot: median 18.27 ms, maximum 24.12 ms, 82,399 bytes.
- Benchmark: median 29.87 ms, maximum 33.02 ms, 31,430 bytes. Full trace/check histories stay in the saved artifact instead of this response.

Final production bundle: main JavaScript 272.01 kB (82.64 kB gzip); lazy scene 893.31 kB (241.71 kB gzip); CSS 34.52 kB (8.28 kB gzip). The scene remains large and Vite warns about it. Weak-device, cold-load and deployed-network performance still need measurement before broad rollout.

## Reproduce and final local check

Use the project virtual environment. On Windows set TEMP and TMP to the project `.test-tmp` directory before tests/evaluation. Run `python -m pytest -q`, `npm run test:client`, and `npm run build`. Full live evaluation: `python tests/adaptive_evaluation.py --provider watsonx`; rules-only dry run: `--provider rules`. A live rerun spends provider quota and records stochastic new decisions; preserve the original artifact first if comparison is needed. The code fingerprint hides stale scores after runtime/evaluator changes.

For the final local check, refresh localhost:8000, open Workers → Evaluation, inspect the full B2 counts and misses, then run a visible-load scenario and review/export a case. Gemini live troubleshooting, real BESCOM onboarding, Docker/deployment and optional drone/CV remain deferred. Independent blind evaluation, broader browser/device coverage and formal accessibility certification remain future validation.
