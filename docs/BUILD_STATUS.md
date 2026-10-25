# Grid Trace local build status

Updated 25 October 2026. Based on source commit 8e8a59fe452bf42f1c9c96b7a853af64db9fcc73. The prototype is maintained on branch `grid-trace-prototype`. Earlier no-commit/no-push statements below are historical build records.

## Latest: full adaptive evaluation and broader QA

Full production-graph evaluation now ran on 18 held-out synthetic realizations: Granite 17 completed / 15 terminal-rubric successes, rules 18/18. One repeated check was safely policy-blocked; two commercial-data requests fell outside the declared terminal rubric. No model superiority or field-accuracy claim. See [B2_AND_QA_REPORT.md](B2_AND_QA_REPORT.md) and adaptive-results.json for the protocol, all traces and limitations.

Verified: 63-test full backend suite plus two report-freshness tests, 10 client tests, production build, five API journeys and three consecutive browser review/export journeys. Phone/tablet/desktop layouts, offline draft recovery, keyboard focus and axe checks were exercised. Fixed scene labels over dialogs, calendar semantics, keyboard access to the capture panel and favicon. Manual contrast certification and real-device testing remain incomplete. This increment is local and uncommitted. Earlier status sections below are historical records.
## Implemented

- September 2022 replay: 2,880 intervals, IST seeking, coverage summaries, revision controls and read-only source metadata. Development fixtures remain explicitly labeled DEV_FIXTURE.
- Typed W1 accounting, W2 bounded physics, W3 prior-only history and unavailable commercial fields, W4 measured-area localization, competing hypotheses and evidence fusion.
- Actual LangGraph adaptive execution: workers, planner, independent policy, read-only follow-up, then replanning. Inputs are frozen. At most three local checks, six provider attempts and a shared 60-second deadline; duplicate checks are blocked.
- Local follow-ups summarize electrical windows, validate registered topology and refine measured-region bounds. Derived evidence is explicitly dependent on the original observations. External inspection remains a human task.
- Granite primary, Gemini fallback and deterministic rules. A successful fallback remains pinned. Optional operator-requested first checks are attributed to the operator before model replanning.
- Worker panel, check results, planner history, persisted trace, case review and JSON/Markdown exports. Conditional finance separates physical energy, invoices, cash and costs.

## Verification

- Original baseline: 17 tests passed. Current backend suite: 56 passed. Frontend production build passes with the existing large-bundle warning.
- Live Granite adaptive run: operator electrical check, Granite-selected topology check, then allowed missing-data request. Two checks, three decisions (operator, Granite, Granite), two model calls.
- Browser verification: operator electrical check completed, new evidence displayed, Granite recommended human meter review, decision history retained.
- Independent diagnostic evaluator refreshed: B0 and B1 each matched 16/20 eligible synthetic events, zero false alerts across only six valid control branch-hours. B2 remains NOT_RUN. These are small diagnostics, not field accuracy or a blinded study.

## Remaining gates

1. Gemini configuration and live fallback verification; Granite works in Frankfurt (see LIVE_GRANITE_CHECK.md).
2. Independently owned blinded B0/B1/B2 action-selection study with equal budgets and pinned providers.
3. Original BESCOM and frozen replay files, verified hashes, grain and mapping. Official source gate remains PENDING.
4. Recorded operator rehearsals, wider accessibility/responsive checks and reference-laptop performance measurements.
5. Optional drone/CV last; visual evidence remains deferred.

## Local use

Run ./start.ps1 from the project root, then open http://127.0.0.1:8000. Open Workers, impact and evaluation. Leave First analytical check on planner choice, or explicitly request a local first check, then run an investigation.

Inside app/, use npm run build, .venv/Scripts/python.exe -m pytest -q, and .venv/Scripts/python.exe tests/benchmark_independent.py. Tests use isolated databases. Windows tests required project-local TEMP/TMP and permission for local sockets. External LangSmith tracing is disabled.

## Operator workflow increment

Completed investigations now hand off directly to case review. Case review locks timeline controls to its interval, shows role guidance and saved decisions, and supports the no-drone path. Assignment, notes, review and export operations give visible feedback. Provider polling can be retried; the investigation dialog supports Escape and keyboard focus containment. Existing cases retain their original interval even when opened from a later investigation.

Browser rehearsal: assigned Demo analyst, triaged, switched to reviewer, saved an uncertainty note, requested field verification, and requested JSON/Markdown downloads. Saved copies in docs/rehearsal/ were checked for matching response hashes, six audit events, two linked investigations and zero visual missions. A regression test confirms the exported case analysis stays unchanged after the source run advances. Wider device/accessibility validation remains pending.

Replay/browser recovery check: selected 2 September at interval 97; the missing household meter remained null and the boundary displayed Data incomplete. Case archive then reopened the saved laboratory case at its original interval 4, with the decision intact and playback disabled. See OPERATOR_WALKTHROUGH.md for the repeatable demo path.

## Fallback provider update

At the user's request, Gemini replaces Grok for new investigations. Order: watsonx/Granite, then Google Gemini, then deterministic rules. Gemini transport, schema validation, retry limits, provider pinning and both-model failure are covered by mocked tests. Gemini credentials/model are still required for live verification. Historical Grok records are preserved.

## Live pinned planner pilot

Added a standalone first-action evaluator and UI results, separate from full B2. Seed 20221117 uses nine synthetic cases from independent forward equations. One configured Granite request per case, no fallback, no executed tools, and at most 25 seconds per request. Scoring labels and the rubric are excluded from model context. Input hashes and code fingerprints are retained; failures/skips stay in the denominator, and two consecutive failures stop further requests.

Actual run: nine completed, zero failed/skipped, nine policy-valid proposals, six triage-rubric matches for Granite and nine for rules. Total request time 38.484 seconds; reported usage 17,305 prompt and 2,136 completion tokens. Granite requested extra checks for the clean, demand-change and weak-signal cases. Rule agreement is expected because the conservative observation-based rubric reflects the existing triage rules; this does not establish real-world superiority. No causal diagnosis or intervention-value score is claimed. The full adaptive B2 study remains NOT_RUN.

56 backend tests pass and the frontend production build passes with its existing bundle warning. The Evaluation tab displays summary, per-case proposals, failures and hashes. Gemini remains deferred; its authentication works, while live generation returned 503/timeouts. No commits or pushes.

## Conservative triage guard

Added a deterministic policy gate and matching planner affordances: WITHIN_MODEL_RANGE and PERSISTENCE_PENDING permit only ABSTAIN_NO_ACTION or GENERATE_CASE_SUMMARY. Model or operator requests for diagnostic checks in these states are blocked before execution. Persistent unexplained energy and model/topology review retain informative checks. The UI labels rejected actions Blocked proposal.

The original live pilot is preserved in planner-pilot-before-triage-guard.json (6/9 rubric matches). The same-seed regression rerun completed all nine Granite requests with 9/9 policy-valid proposals and 9/9 rubric matches; normal and legitimate-demand cases selected summaries, and the weak-signal case abstained. This is a policy-constrained regression result, not a held-out study or evidence of improved general model accuracy. Full B2 remains pending. Production build passes with the existing bundle warning.

Final verification: a contradictory model rationale was observed during a clean browser run. The structured action was a summary, but the prose suggested a recheck. Normal/nonpersistent summaries now carry a deterministic EXISTING_EVIDENCE_ONLY authorization note. The UI presents this note as the operative next step and keeps original model prose in a separately labeled disclosure. Raw model output is retained for audit. A regression test confirms contradictory prose cannot authorize execution.

Final suite: 56 passed. Final code-fingerprinted Granite pilot: 9/9 completed, policy-valid and rubric-matched; zero failed/skipped, 38.466 seconds, 17,350 prompt tokens and 2,074 completion tokens. The clean, legitimate-demand and weak-signal cases selected summaries. Earlier reports remain preserved. Browser verification explicitly requested an electrical recheck on a clean interval and confirmed POLICY_REJECTED, zero checks and zero provider calls. No full B2/field accuracy claim; Gemini remains deferred.

## Product recovery and usability pass

Client changes only; provider policy, the 56-test backend baseline and saved planner pilot remain unchanged. Ten new Node client tests pass (npm run test:client, Node 24 used here); TypeScript and the Vite production build pass.

- Case/run/asset/interval and simulated identity restore after refresh. Open investigation views restore at their pinned interval. Source replay advancing behind an open panel no longer changes its investigation context or case handoff interval.
- Reviewer note drafts survive refresh in tab-local session storage and can be discarded explicitly. Saving an assignment does not clear a note. A stale case revision refreshes the case and retains the draft for review before retry. Browser storage failure uses an in-memory fallback for the current session.
- Unconfirmed investigation submissions retain the original idempotency key, first-check choice and actor across retries. Rapid submissions share one in-flight request; definitive client errors clear it, while transient errors preserve it. Saved-result loading blocks starting another job until status is known; missing results can be replaced explicitly.
- Offline/timeout messages explain recovery; export waits are bounded. Modal Escape, focus containment and return-to-launcher behavior are supported. The 390 x 844 browser frame showed the phone view with review controls first, readable wrapping and the source disclosure visible. This is not exhaustive device or assistive-technology certification.
- Heavy 3D code loads separately. Initial JS is 272.19 KB (82.67 KB gzip), with an 893.29 KB scene chunk. This improves shell loading separation rather than reducing the total download; the scene bundle warning remains.

Actual desktop rehearsal restored the existing field-check case at interval 4, Demo reviewer and an unsaved note after refresh. The saved case remained revision 6. The investigation panel also reopened at interval 4 after refresh; Escape returned focus to its launcher. The rehearsal-only draft was then discarded without saving it. Read-only local measurements (three requests each) had medians of 3.0 ms for health, 4.1 ms for cases and 16.1 ms for a 51,179-byte snapshot. These are small local observations, not performance acceptance targets. No commits or pushes.

## Branch checkpoint

Prepared grid-trace-prototype with 56 backend tests, 10 client tests and the production build passing. Credentials, local databases, dependencies, build output and temporary diagnostics are excluded. Sample Markdown whitespace is normalized for Git. No changes are being merged into main.

## Docker increment

Added a multi-stage Docker image and Compose configuration: optional runtime .env, loopback port 8080, named SQLite/evidence volume, unprivileged user, one worker, HTTP health check and bounded shutdown. Built and ran successfully on Linux/amd64. All 65 backend tests passed inside the image; container recreation preserved a synthetic case, audit trail, frozen analysis and evidence. A real Granite request from inside Docker succeeded. See docs/DOCKER.md. Existing host data is separate from Docker's named volume. No commit or push for this increment.

## UI and simulated-drone update

Refreshed navigation, replay/scenario controls and inspection layout. Added a large drone view, following camera, route/progress/altitude display, image tabs and explicit launch controls. Fixed reduced-motion flight progression, interrupted-mission recovery, oversized labels and context changes during capture. Verified a normal flight and refresh/retry flight: two missions, two frame keys each, four processed images total. Thirteen client tests, 17 backend acceptance tests and production build passed. Five inspection widths and an axe scan passed with manual contrast review still outstanding. See docs/UI_AND_INSPECTION_UPDATE.md. Local only; no deployment, commit or push.
