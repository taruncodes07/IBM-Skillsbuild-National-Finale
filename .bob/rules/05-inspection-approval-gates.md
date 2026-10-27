# Preserve human approval and ground-review requirements for inspection flights

The inspection workflow has two mandatory human gates that must never be
bypassed, automated, or soft-coded around.

## Gate 1 — Ground observation before flight approval

A mission may only be created (`POST /api/cases/{cid}/missions`) when:

1. The case state is `ground_review`, `inspection_requested`, `evidence_ready`,
   or `under_review`.
2. An `open_ground_question` exists: a ground observation that was **not**
   resolved from the ground and carries a non-empty `outstanding_question`.
3. The ground observation's `visibility` is **not** `'clear'` — a clear ground
   view does not justify aerial inspection.
4. The request carries `approved: true` — explicit reviewer approval.

```python
# ❌ FORBIDDEN — auto-approving a mission without a ground question
m = await api('/cases/' + cid + '/missions', 'POST', {'approved': True, ...})

# ✅ CORRECT — the UI checks openQuestion before showing the approve button
if not openQuestion:
    raise Error('Record a ground observation that leaves an overhead question...')
if openQuestion.visibility === 'clear':
    raise Error('The ground view was clear...')
```

## Gate 2 — Policy validation before any planner action executes

The LangGraph `policy_node` calls `validate_policy()` independently of the
planner. **The policy check runs even for operator-requested initial checks.**
A proposal is executed only when `policy['allowed'] == True`.

```python
# ❌ FORBIDDEN — executing a check without running policy
result = followups.execute_check(inv, proposal.next_action, ...)

# ✅ CORRECT — route_after_policy gates execution
def route_after_policy(state):
    if state['policy']['allowed'] and proposal in followups.LOCAL_CHECKS:
        return 'followup'
    return 'complete'
```

## WITHIN_MODEL_RANGE / PERSISTENCE_PENDING policy

When `diagnostic_status` is `'WITHIN_MODEL_RANGE'` or `'PERSISTENCE_PENDING'`,
**no diagnostic check is authorized**. Only `ABSTAIN_NO_ACTION` or
`GENERATE_CASE_SUMMARY` are permitted. Any model rationale suggesting a check
in these states is overridden by a deterministic authorization note in
`complete_node`.

## Role requirements

| Action | Required role |
|---|---|
| Ground observation | `reviewer` or `supervisor` |
| Mission approval | `reviewer` or `supervisor` |
| Frame upload | `reviewer` or `supervisor` |
| Case resolve/dismiss/reopen | `supervisor` |
| Triage | `analyst` or `supervisor` |

These are enforced by `main.py role()` checks — do not remove them.
