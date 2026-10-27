# Preserve missing readings as null

A missing or invalid meter reading must remain `null` (`None` in Python) in
every data structure — observations, balances, readings API responses, and
exports. It must never be replaced with zero, a prior value, or an interpolated
estimate.

## Why this matters

Replacing a missing value with zero produces a false residual that looks like
unexplained energy. The system's detection thresholds are calibrated on real
absence; imputed zeros corrupt streak counting and alert generation.

## Rules

**Python backend:**
```python
# ❌ BAD — zero-fills a missing reading
household_sum += readings[k].get('energy_import_kwh') or 0

# ✅ GOOD — explicitly exclude missing values from sums
valid = [readings[k]['energy_import_kwh'] for k in ids
         if readings[k]['quality'] == 'valid'
         and readings[k]['energy_import_kwh'] is not None]
household_sum = sum(valid)
```

**API responses:** `energy_import_kwh: number | null` in TypeScript types;
render as `"—"` in the UI, never as `0`.

**balance_terms:** returns `(None, None)` if any input is `None`. The
`validity` field on the balance becomes `'data_incomplete'`, not `'valid'`.

**Quality values:** `'missing'`, `'invalid'`, `'stale'` all prevent a reading
from contributing to the reconciled balance. A missing/stale reading breaks the
consecutive-interval streak for persistent alerts.

## Enforcement points

- `analytics.py reconcile()`: checks `r['quality'] == 'valid' and r['energy_import_kwh'] is not None`
- `sources.py month_summary()`: feeder sum must exclude `None`; use `r['energy_import_kwh']` directly, not `or 0`
- `workers.py execute()`: sets `raw = None` when either input or output is `None`
- Reading revision API: requires explicit `quality` field; `'valid'` requires a non-null energy value
