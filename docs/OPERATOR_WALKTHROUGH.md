# Local operator walkthrough

Run the root start.ps1 and open http://127.0.0.1:8000.

## Month replay

Open Presenter scenarios and choose Open September 2022 replay. Select a day or interval. Check coverage and null readings before interpreting balances. This fixture is a clean month with deliberate missing readings; a data-quality event is not a persistent-loss alert. Data onboarding remains pending.

## Reproducible investigation and review

1. In Presenter scenarios, choose Visible unmetered load and Start new deterministic run. This is a separate synthetic laboratory, not historical BESCOM telemetry.
2. Step three times to interval 4. Select Branch 03 and open Workers, impact and evaluation.
3. Run W1-W4. Leave the first check to the planner or explicitly request a registered first check. Inspect provider attribution, missing inputs, competing explanations and follow-up evidence.
4. As Demo analyst, choose Open case review. Assign a fictional owner and triage the case.
5. Switch to Demo reviewer. Choose Continue without visual evidence. Record observations and uncertainty using Save note.
6. Enter a decision reason, leave disposition inconclusive where appropriate, choose Request field inspection and Save review. Saving a note clears the note field; the review still needs its own reason.
7. Confirm the saved decision and audit trail. Export JSON and Markdown. Both include matching worker investigations, planner history and execution traces. No drone mission is required.
8. Return to Network overview to change time. Case archive reopens the original interval. A case for an existing alert keeps its original interval; later investigations remain separate.

Resolving/dismissing/reopening requires Demo supervisor. Identities are simulated local role gates. A recommendation or field-check request does not mean a real inspection or repair occurred. Unexplained energy is not a theft finding.

## Verified in this increment

56 backend tests pass; production build passes with the existing large-bundle warning. Desktop browser rehearsal saved assignment, note and field-check outcome, and requested both exports. Their content hashes were verified independently. Example outputs are in rehearsal/case-review.json and rehearsal/case-review.md. Smaller-screen and assistive-technology coverage is not yet exhaustive.

## Evaluation view

Open Workers, impact and evaluation, then Evaluation. The pinned first-action pilot shows Granite and fixed-rule rubric matches separately from B0/B1 event-detection metrics. Expand Pilot decisions, failures and rubric to inspect every result. Policy-valid does not imply a good next action: the initial live pilot retained three Granite rubric mismatches. Full adaptive B2, independent blinded review and field validation remain pending.

To reproduce offline, run .venv/Scripts/python.exe tests/planner_pilot.py --provider rules --cases 9. For a live pinned pilot, use --provider watsonx instead (at most nine model requests). Both replace docs/planner-pilot-results.json; preserve an earlier report first when comparing runs. Candidate changes mark saved results stale. The rubric follows conservative existing triage rules, so rule agreement is expected by construction.

Normal and nonpersistent measurements now permit only abstention or a summary. Diagnostic check requests in those states are policy-blocked even when explicitly requested by an operator. Model/topology review and incomplete data retain their own permitted checks. The original 6/9 pilot remains in planner-pilot-before-triage-guard.json; the current same-case regression matches 9/9 after the policy change.

## Recovery controls

Refreshing restores the current case, simulated identity, interval and open investigation view. Note drafts stay in the same browser tab until saved or explicitly discarded; closing the tab can lose an unsaved draft. Saving assignment preserves the draft. On a revision conflict, inspect the refreshed case and retry with the preserved note.

If investigation submission loses its response, choose Resume submitted investigation. The original request key and options are reused. Use Retry status when loading a known job fails; do not create another job merely because a connection dropped. An open worker panel keeps its original interval as replay advances.

Escape closes dialogs and restores focus to the launcher. On phone-width screens the case review appears before optional visual content. Local client regression tests: npm run test:client (Node 24 verified). Production build: npm run build.
