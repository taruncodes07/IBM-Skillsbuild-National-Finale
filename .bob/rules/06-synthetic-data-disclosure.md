# Label synthetic data and assumed losses; never interpret residuals as proof of theft

This is a demonstration system. Every reading, alert, image, and investigation
result is synthetic. The system **must never** frame an energy residual or
an image candidate as proof of theft, authorization failure, household guilt,
or recovered revenue.

## Required disclosures in data and UI

### Readings and sources

Every development-fixture reading carries `provenance: 'synthetic'` and
`source_kind: 'DEV_FIXTURE'`. The source manifest must carry:

```python
'official_source_status': 'PENDING'   # never omit or change to 'VERIFIED'
'disclosure': 'Generated test readings, not BESCOM telemetry...'
```

### Balances and worker outputs

W2 always lists its assumptions explicitly:

```python
assumptions=[
    'Technical-loss range is 0.5–1.5 times the configured reduced-order estimate.',
    'Meter residual bound uses 3 times the development residual sigma; it is not a '
    'calibrated 95% confidence interval.',
]
uncertainty={'kind': 'ASSUMPTION_BOUNDS', 'physical_calibration': 'NOT_AVAILABLE'}
```

The expected-loss formula (`a·0.25h + b·(output/0.25)²·0.25h`) is a
**reduced-order approximation**, not a power-flow solution. Do not remove the
`'ASSUMED_REDUCED_ORDER'` model validity tag.

### Case exports and evidence

Every export JSON and Markdown must carry:

```
disclosure: 'Synthetic demonstration. Unexplained loss is not proven theft.
             RGB cannot verify authorization or energization.'
```

Evidence records carry:

```
limitations: ['Visible line geometry cannot establish ownership, authorization,
               current or energization.',
              'No visible candidate does not clear an electrical imbalance.']
```

### Finance / impact calculator

Output must carry:

```python
'status': 'MODELED_ONLY'
'actual_collection_status': 'COLLECTION_UNKNOWN'
'actual_bescom_savings_inr': None
'caveat': 'Hypothetical intervention assumptions; not verified BESCOM recovery...'
```

## Forbidden in code, comments, and UI text

- "theft confirmed", "theft detected", "theft probability"
- "household X is responsible" or any household-level attribution
- "revenue recovered" without `MODELED_ONLY` qualification
- Removing the `'allowed_inference': 'Investigation recommendation only; no theft verdict.'` field from fusion output

## Correct framing

```
✅ "Persistent unexplained energy — investigate further"
✅ "Candidate extra overhead connection visible — verify in field"
✅ "Investigation signal; no finding of theft"

❌ "Theft detected at branch-03"
❌ "household-07 is bypassing the meter"
❌ "Recovery value: ₹12,400"  ← without MODELED_ONLY caveat
```
