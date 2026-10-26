"""Standalone verification of the four PRD gaps closed in this increment.

Runs on the Python standard library only - it does NOT need fastapi, pydantic or
langgraph, so it works before the virtual environment is built. It proves the
arithmetic and the accounting; the HTTP behaviour is covered by tests/test_prd_gaps.py.

    python verify_prd_gaps.py
"""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_backend():
    """Import the pure modules without triggering backend/__init__ or heavy deps."""
    pkg = types.ModuleType('backend')
    pkg.__path__ = [str(ROOT / 'backend')]
    sys.modules['backend'] = pkg
    for name in ('topology', 'coverage', 'analytics', 'simulation', 'ranking'):
        spec = importlib.util.spec_from_file_location(f'backend.{name}', ROOT / 'backend' / f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[f'backend.{name}'] = module
        spec.loader.exec_module(module)
    return (sys.modules['backend.topology'], sys.modules['backend.coverage'],
            sys.modules['backend.analytics'], sys.modules['backend.simulation'],
            sys.modules['backend.ranking'])


topology, coverage, analytics, simulation, ranking = load_backend()
FAILURES = []


def check(label, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    if not condition:
        FAILURES.append(label)
    print(f'  [{status}] {label}' + (f'  {detail}' if detail else ''))


EVENT = [dict(type='visible_unmetered_load', target_asset_id='branch-03', start=0, end=90, severity=1.2)]

print('\nAC-14  Quantitative ranking reproduces PRD section 5 Table 4')
for row in ranking.CALIBRATION_FIXTURE:
    if not row['eligible']:
        print(f"  [INFO] {row['label']}: rejected before scoring, as the PRD specifies")
        continue
    got = ranking.score_from_components(row['ig'], row['reliability'], row['access'],
                                        row['cost_inr'], row['minutes'])
    check(f"{row['label']} recomputes within 0.001", abs(got - row['expected_score']) < 0.001,
          f"computed {got:.4f} vs published {row['expected_score']:.3f}")

print('\nAC-14  Policy behaviour')
normal = ranking.rank(dict(diagnostic_status='WITHIN_MODEL_RANGE', billing_status='NOT_AVAILABLE',
                           ground_question_open=False, completed_actions=()))
check('normal measurements abstain and score nothing',
      normal['recommended_action'] == 'ABSTAIN_NO_ACTION' and not normal['ranked'])
unexplained = ranking.rank(dict(diagnostic_status='UNEXPLAINED_ENERGY', billing_status='NOT_AVAILABLE',
                                ground_question_open=False, completed_actions=()))
rejected = {r['action_id']: r['rejection_reason'] for r in unexplained['rejected']}
check('aerial view is rejected before any ground question exists',
      'NO_GROUND_GAP' in rejected.get('AERIAL_OBSERVATION', ''))
check('every ranked action logs recomputable components',
      all(abs(ranking.score_from_components(e['information_gain_bits'], e['reliability'], e['access'],
                                            e['cost']['total_inr'], e['expected_minutes']) - e['score']) < 1e-9
          for e in unexplained['ranked']))
check('sensitivity bounds bracket each score',
      all(e['sensitivity']['low'] <= e['score'] <= e['sensitivity']['high'] for e in unexplained['ranked']))
print(f"  [INFO] recommended: {unexplained['recommended_action']}; "
      f"stable={unexplained['winner_stable_under_sensitivity']}; "
      f"human choice required={unexplained['human_choice_required']}")

print('\nAC-13  Coverage-aware localization (CEA metering counts, 31 March 2025)')
readings = simulation.generate(42, 5, EVENT)['readings']
full = analytics.reconcile('v', 5, readings, None, coverage.installed_meters('full_sectional', topology.ASSETS))
check('full sectional localizes the event to branch-03',
      any(b['boundary_asset_id'] == 'branch-03' and b['qualifies'] for b in full))
for pid in ('bescom_like', 'tgspdcl_like', 'pgvcl_like'):
    sparse = analytics.reconcile('v', 5, readings, None, coverage.installed_meters(pid, topology.ASSETS))
    b3 = next(b for b in sparse if b['boundary_asset_id'] == 'branch-03')
    check(f'{pid}: branch-03 reports insufficient observability, not a false residual',
          b3['validity'] == 'insufficient_observability' and b3['residual_kwh'] is None)
    check(f'{pid}: no branch is localized that cannot be measured',
          not any(topology.BY_ID[b['boundary_asset_id']]['kind'] == 'branch' and b['qualifies'] for b in sparse))

bescom = analytics.reconcile('v', 5, readings, None, coverage.installed_meters('bescom_like', topology.ASSETS))
feeder = next(b for b in bescom if b['boundary_asset_id'] == 'feeder-01')
check('BESCOM-like: the feeder-to-DT cut still reconciles cleanly',
      feeder['validity'] == 'valid' and abs(feeder['residual_kwh']) < feeder['threshold_kwh'],
      f"residual {feeder['residual_kwh']:+.3f} kWh against threshold {feeder['threshold_kwh']:.3f}")
print('  [INFO] The theft sits below the DT meter, so no feeder-level accounting can see it.')
print('         That is an observability limit, not a detector failure.')

print('\nAC-05  Scenario G: comparable apparent excess, different evidence')
residuals, actions = {}, {}
for scenario in simulation.MATCHED_RESIDUAL:
    rd = simulation.generate(42, 5, simulation.matched_residual_incidents(scenario, start=0, end=90))['readings']
    b = next(x for x in analytics.reconcile('g', 5, rd) if x['boundary_asset_id'] == 'branch-03')
    residuals[scenario] = b['residual_kwh']
    if b['validity'] == 'valid':
        status, kind = 'UNEXPLAINED_ENERGY', None
    else:
        reasons = ' '.join(b['invalid_reasons']).lower()
        status = 'DATA_INCOMPLETE'
        kind = 'TOPOLOGY_MISMATCH' if 'topology mismatch' in reasons else 'MISSING_READINGS'
    actions[scenario] = ranking.rank(dict(diagnostic_status=status, incomplete_kind=kind,
                                          billing_status='NOT_AVAILABLE', ground_question_open=False,
                                          completed_actions=()))['recommended_action']
    shown = 'null' if residuals[scenario] is None else f'{residuals[scenario]:.3f}'
    print(f'  [INFO] {scenario:<34} apparent={shown:>6} -> {actions[scenario]}')
present = [v for v in residuals.values() if v is not None]
check('apparent excess stays within a comparable band', max(present) - min(present) < 0.5)
check('a missing reading never becomes a residual', residuals['matched_residual_incomplete'] is None)
check('the same apparent excess produces more than one recommended check', len(set(actions.values())) > 1)

print('\nFR-07  Ground-first wiring (HTTP paths are covered by tests/test_prd_gaps.py)')
spec = ranking.ACTIONS['AERIAL_OBSERVATION']
check('aerial action declares a ground prerequisite', spec.get('requires_ground_question') is True)
opened = ranking.rank(dict(diagnostic_status='UNEXPLAINED_ENERGY', billing_status='NOT_AVAILABLE',
                           ground_question_open=True, completed_actions=()))
check('aerial becomes eligible once a ground question is open',
      any(e['action_id'] == 'AERIAL_OBSERVATION' for e in opened['ranked']))

print('\n' + ('All checks passed.' if not FAILURES else f'{len(FAILURES)} FAILED: ' + ', '.join(FAILURES)))
print('Synthetic fixtures only. Nothing here establishes field accuracy.\n')
sys.exit(1 if FAILURES else 0)
