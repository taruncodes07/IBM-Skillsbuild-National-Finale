# Validate units, timestamps, topology, and meter coverage

Every reading that enters the reconciliation pipeline must pass four checks
before it can contribute to a balance. Failures must set `reasons` entries and
produce a `'data_incomplete'` or `'insufficient_observability'` balance — never
silently proceed.

## 1. Units

Accepted energy unit is **kWh** (15-minute intervals). The CSV ingestor accepts
`'kwh'` and `'wh'`; Wh values are converted by dividing by 1 000 before storage.
Any other unit is an error.

```python
# ❌ BAD
value = float(row['value'])

# ✅ GOOD
raw = float(row['value'])
value = raw * 0.001 if unit == 'wh' else raw
```

## 2. Timestamps

- Every reading must carry an explicit timezone (ISO 8601 with offset).
- `interval_start` and `interval_end` for all readings in a cut must be
  identical; a mismatch produces `reasons.append(meter_id + ': interval mismatch')`.
- Timestamps must be parseable via `datetime.fromisoformat`; a `ValueError`
  is a validation error, not a crash path.

## 3. Topology version

Each reading carries a `topology_version` string. If it differs from the
currently loaded `VERSION` constant, add `reasons.append(meter_id + ': topology mismatch')`.
This produces a quality-review event, not silent acceptance.

## 4. Meter coverage (observability)

Before reconciling a section:
1. Call `coverage.observability(sid, cut, installed)`.
2. If the result is `'INSUFFICIENT_OBSERVABILITY'`, emit a balance with
   `validity='insufficient_observability'` and `uninstrumented_asset_ids` set.
3. Never use a zero as a stand-in for an absent meter.

```python
observability, absent = coverage.observability(sid, cut, installed)
if observability == 'INSUFFICIENT_OBSERVABILITY':
    # emit insufficient balance, continue to next section
    continue
```

## Enforcement checklist

- `analytics.py reconcile()`: all four checks applied per reading per section
- `sources.py ingest_readings_csv()`: unit normalisation, timezone check, duplicate detection
- `main.py ReadingRevision`: Pydantic `quality` enum enforced; `'valid'` requires non-null energy
- `simulation.py generate()`: emits `topology_version=VERSION`; mismatch scenario emits `'topology-stale'`
