# Keep simulator ground truth out of analytical inputs

`backend/simulation.py` is the private physical truth. It must never be
imported by any module that workers, planners, or the policy boundary can reach.

## Hard import boundary

```python
# ❌ NEVER — in analytics.py, workers.py, followups.py, ranking.py, or any
#            module called from the investigation workflow:
from .simulation import generate, loss, MATCHED_RESIDUAL
from . import simulation
import backend.simulation

# ❌ NEVER — access private truth table from analytical code:
store.DB.execute('SELECT body FROM private_truth WHERE ...')
```

```python
# ✅ CORRECT — simulation.py is only imported in:
#   engine.py  (orchestrator that feeds observations to analytics)
#   main.py    (truth endpoint, presenter-only, separate route)
#   tests/     (with explicit fixture isolation)
```

## What analytical code may receive

Workers (W1–W4) and follow-up checks receive only the public snapshot keys:

| Allowed | Forbidden |
|---|---|
| `snapshot['readings']` | `snapshot['truth']` |
| `snapshot['balances']` | private_truth store |
| `snapshot['alerts']` | `generate()` return value |
| `snapshot['run']` (public fields) | `simulation.ASSETS`, `simulation.CHILDREN` directly |

`topology.py` constants (`BY_ID`, `CHILDREN`, `SECTIONS`) are approved for
analytical use — they are static topology, not simulated values.

## Investigation workflow

Observations are frozen at investigation creation (`investigations.create()`).
The frozen snapshot is stored in `inv['observations']`. Follow-up checks read
`inv['observations']` and `inv['followup_inputs']`; they never call
`store.interval()` for new data or access `private_truth`.

## Verification

The test suite includes `test_developer1_analytics.py` and `test_acceptance.py`
which assert that analytics functions produce correct outputs without access to
the private simulation path. Do not break this isolation when editing either
module.
