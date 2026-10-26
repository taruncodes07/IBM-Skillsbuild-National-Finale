# Three valid qualifying intervals for persistent alerts

An alert becomes `status='active'` only after **three consecutive** valid
intervals where the section residual exceeds the threshold. A single missing
or invalid reading in the sequence resets the streak to zero.

## Threshold formula

```
threshold = max(0.25 kWh, 0.08 × input_kwh, 3 × sigma)
```

Where `sigma` is the clean-baseline standard deviation of section residuals,
floored at `0.015 kWh`. This is computed in `analytics.py reconcile()`.

## Streak rules

```python
# analytics.py detect() — correct pattern
if qualifies:
    streaks[sid] = streaks.get(sid, 0) + 1
else:
    streaks[sid] = 0   # ← MUST reset; do not preserve partial streaks

if streaks[sid] >= 3 and not already_active:
    # promote to active alert
```

- `qualifies` requires `validity == 'valid'` AND `residual > threshold`.
  A `'data_incomplete'` interval always resets the streak.
- Negative residuals (`residual < 0`) produce a quality review event, not a
  streak increment.
- Changing the coverage profile clears all streaks (`engine.set_coverage()`).
  Coverage changes must not silently carry over streaks earned under a
  different meter cut (PRD AC-13).

## Do not bypass

These changes are forbidden without updating the full test suite and
re-running the B0/B1 evaluator:

- Lowering the consecutive-interval threshold below 3.
- Counting `'data_incomplete'` intervals as qualifying.
- Allowing streaks to survive a coverage change.
- Using a different sigma floor or threshold formula.

## Enforcement

- `test_acceptance.py` — verifies alert promotion at exactly interval 3.
- `test_developer1_analytics.py` — verifies streak reset on missing data.
- B0/B1 evaluator (`tests/benchmark_independent.py`) — detection recall is
  calibrated to this threshold; changes will invalidate the saved artifact.
