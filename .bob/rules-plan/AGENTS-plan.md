# Grid Trace — Plan Mode Context

Extends the root `AGENTS.md`. Use when planning architecture, designing
features, or writing technical specifications before implementation.

## Architectural constraints that plans must respect

1. **Simulation/analytics separation** — any plan that routes simulator output
   into analytical workers is rejected. See rule `03-simulation-truth-boundary.md`.

2. **Investigation workflow is bounded** — at most 3 follow-up checks, 6
   provider calls, 60-second shared deadline per investigation. Plans that
   require unbounded loops or external side effects from the workflow are
   out of scope.

3. **Human gates are non-negotiable** — ground observation before flight,
   policy validation before any check execution. Plans must preserve both.

4. **Storage is append-mostly** — `intervals` and `private_truth` tables are
   immutable after write. The audit table has database triggers preventing
   UPDATE/DELETE. Plans that require in-place mutation of these tables need
   a migration strategy.

5. **No authentication** — the role selector is a demo simulation gate, not
   real auth. Plans must not add features that would require real authentication
   without explicitly noting this boundary.

## Planning outputs

Plans should produce a markdown file (e.g. `*-plan.md`) at the workspace root
with:
- Top-level goal and scope
- Sub-tasks with intent, expected outcomes, and ordered steps
- Pointers to relevant files and modules
- Status checkboxes updated as work proceeds

## Evaluation impact

Any plan that touches `analytics.py`, `workers.py`, `investigation.py`,
or the detection thresholds must note that the B0/B1/B2 evaluator artifacts
will become STALE and require a rerun.
