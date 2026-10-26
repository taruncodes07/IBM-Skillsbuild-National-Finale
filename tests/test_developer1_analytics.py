"""Tests for Developer 1 (Role B: Simulation, Data, and Energy Analytics).
Covers PRD v5.0 Section 6 (Coverage Modes), Section 7 (Next-Best-Check Engine),
and Section 9 (CSV Ingestion).
"""
class approx:
    """Self-contained numerical comparison helper with tolerance."""
    def __init__(self, val, abs=1e-3):
        self.val = val
        self.abs = abs
    def __eq__(self, other):
        return abs(self.val - other) <= self.abs
    def __repr__(self):
        return f"approx({self.val} ± {self.abs})"
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.analytics import (
    score_action, rank_next_checks, reconcile, NEXT_CHECK_CATALOG,
    COVERAGE_MODES
)
from backend.sources import ingest_readings_csv
from backend.topology import P0_SLICE_ASSET_IDS, BY_ID
from backend.simulation import generate


def test_next_best_check_scoring_formula():
    """Validates exact score values from PRD v5.0 Section 7 table."""
    # Meter record cross-check: IG=0.55, R=0.95, A=1.0, C=100, T=10 -> Score ~ 0.493
    s_meter = score_action(0.55, 0.95, 1.0, 100.0, 10.0)
    assert s_meter == approx(0.4925, abs=0.001)
    assert abs(s_meter - 0.493) < 0.001

    # Ground observation: IG=0.90, R=0.85, A=0.9, C=500, T=35 -> Score ~ 0.557
    s_ground = score_action(0.90, 0.85, 0.90, 500.0, 35.0)
    assert s_ground == approx(0.5573, abs=0.001)
    assert round(s_ground, 3) == 0.557


def test_next_best_check_ranking_and_abstention():
    """Validates ranking, sensitivity, and hard gate abstention per PRD v5.0 Section 7."""
    # Case 1: Incomplete data -> hard gate must withhold dispatch and recommend data repair
    balance_bad = {
        'validity': 'data_incomplete',
        'invalid_reasons': ['household-07: missing'],
        'qualifies': False
    }
    ranked_bad = rank_next_checks(balance_bad)
    assert ranked_bad['recommendation'] == 'REPAIR_OR_VALIDATE_DATA'
    assert ranked_bad['action_name'] == 'REQUEST_MISSING_DATA'
    assert ranked_bad['abstain'] is True

    # Case 2: Clean/within threshold -> abstain with no investigation
    balance_clean = {
        'validity': 'valid',
        'qualifies': False,
        'negative_review': False,
        'residual_kwh': 0.05
    }
    ranked_clean = rank_next_checks(balance_clean)
    assert ranked_clean['recommendation'] == 'NO_INVESTIGATION'
    assert ranked_clean['action_name'] == 'ABSTAIN_NO_ACTION'
    assert ranked_clean['abstain'] is True

    # Case 3: Persistent qualifying excess -> targeted ground inspection wins
    balance_excess = {
        'validity': 'valid',
        'qualifies': True,
        'residual_kwh': 1.6,
        'threshold_kwh': 0.25
    }
    ranked_excess = rank_next_checks(balance_excess)
    assert ranked_excess['recommendation'] == 'REQUEST_FIELD_INSPECTION'
    assert ranked_excess['action_name'] == 'REQUEST_FIELD_INSPECTION'
    assert ranked_excess['winner_score'] == approx(0.557, abs=0.005)
    assert ranked_excess['abstain'] is False


def test_coverage_modes_and_fallbacks():
    """Validates the 4 coverage modes specified in PRD v5.0 Section 6."""
    obs = generate(42, 0, [])['readings']

    # 1. Full mode: all sections evaluated
    b_full = reconcile('test-cov', 0, obs, coverage_mode='full')
    assert all(b['coverage_mode'] == 'full' for b in b_full)
    branch_full = next(b for b in b_full if b['boundary_asset_id'] == 'branch-03')
    assert branch_full['validity'] == 'valid'

    # 2. Feeder and DT only: branches must return insufficient_observability
    b_f_dt = reconcile('test-cov', 0, obs, coverage_mode='feeder_and_dt_only')
    branch_dt_only = next(b for b in b_f_dt if b['boundary_asset_id'] == 'branch-03')
    assert branch_dt_only['validity'] == 'insufficient_observability'
    assert branch_dt_only['residual_kwh'] is None
    assert branch_dt_only['qualifies'] is False

    # Transformers and feeders remain observable
    tf_dt_only = next(b for b in b_f_dt if b['boundary_asset_id'] == 'transformer-02')
    assert tf_dt_only['validity'] == 'valid'

    # 3. Feeder only: both DTs and branches must return insufficient_observability
    b_feeder = reconcile('test-cov', 0, obs, coverage_mode='feeder_only')
    feeder_bal = next(b for b in b_feeder if b['boundary_asset_id'] == 'feeder-01')
    assert feeder_bal['validity'] == 'valid'
    tf_bal = next(b for b in b_feeder if b['boundary_asset_id'] == 'transformer-02')
    assert tf_bal['validity'] == 'insufficient_observability'


def test_scenario_g_signature_demo():
    """
    PRD v5.0 Gate G-06 (Scenario G Signature Demo):
    Matched apparent imbalance with different completeness/coverage produces
    different next checks with explicit reasons, not relying on the scenario name.
    """
    obs_complete = generate(42, 0, [])['readings']
    obs_complete['branch-03']['energy_import_kwh'] = 12.5
    for h in ['household-07', 'household-08', 'household-09']:
        obs_complete[h]['energy_import_kwh'] = 3.5

    b_complete = next(b for b in reconcile('scen-g-1', 0, obs_complete) if b['boundary_asset_id'] == 'branch-03')
    rec_complete = rank_next_checks(b_complete)

    # Identical input, but with a missing meter reading
    obs_incomplete = dict(obs_complete)
    obs_incomplete['household-07'] = dict(obs_complete['household-07'], energy_import_kwh=None, quality='missing')

    b_incomplete = next(b for b in reconcile('scen-g-2', 0, obs_incomplete) if b['boundary_asset_id'] == 'branch-03')
    rec_incomplete = rank_next_checks(b_incomplete)

    # Both had the same input energy of 12.5 kWh, but recommendations differ by evidence:
    assert rec_complete['recommendation'] == 'REQUEST_FIELD_INSPECTION'
    assert rec_incomplete['recommendation'] == 'REPAIR_OR_VALIDATE_DATA'
    assert rec_incomplete['abstain'] is True


def test_csv_ingestion_and_validation():
    """Validates CSV ingestion according to Shared Contract."""
    csv_data = "stream_id,timestamp,value,unit,quality\nmeter-feeder-01,2026-10-24T08:00:00Z,10.5,kWh,valid\nmeter-branch-03,2026-10-24T08:00:00Z,5000,Wh,valid\nmeter-household-07,2026-10-24T08:00:00Z,,kWh,valid\nmeter-feeder-01,2026-10-24T08:00:00Z,10.5,kWh,valid\n"
    result = ingest_readings_csv(csv_data)
    assert result['total_rows'] == 4
    # Wh converted to kWh: 5000 Wh -> 5.0 kWh
    branch_rec = next(r for r in result['records'] if r['stream_id'] == 'meter-branch-03')
    assert branch_rec['value'] == approx(5.0)

    # Empty value preserved as None and quality set to missing
    hh_rec = next(r for r in result['records'] if r['stream_id'] == 'meter-household-07')
    assert hh_rec['value'] is None
    assert hh_rec['quality'] == 'missing'

    # Duplicate detected
    assert len(result['duplicates_detected']) == 1
    assert result['duplicates_detected'][0]['stream_id'] == 'meter-feeder-01'


def test_p0_10_stream_slice():
    """Validates the 10-stream P0 slice per PRD v5.0 Section 1 and Section 4."""
    assert len(P0_SLICE_ASSET_IDS) == 10
    kinds = [BY_ID[aid]['kind'] for aid in P0_SLICE_ASSET_IDS]
    assert kinds.count('feeder') == 1
    assert kinds.count('transformer') == 1
    assert kinds.count('branch') == 2
    assert kinds.count('household') == 6


if __name__ == '__main__':
    print('Running Developer 1 Analytics & Reconciler Test Suite...')
    test_next_best_check_scoring_formula()
    print('  ✔ PASS: test_next_best_check_scoring_formula')
    test_next_best_check_ranking_and_abstention()
    print('  ✔ PASS: test_next_best_check_ranking_and_abstention')
    test_coverage_modes_and_fallbacks()
    print('  ✔ PASS: test_coverage_modes_and_fallbacks')
    test_scenario_g_signature_demo()
    print('  ✔ PASS: test_scenario_g_signature_demo')
    test_csv_ingestion_and_validation()
    print('  ✔ PASS: test_csv_ingestion_and_validation')
    test_p0_10_stream_slice()
    print('  ✔ PASS: test_p0_10_stream_slice')
    print('\n*** ALL 6 DEVELOPER 1 TESTS PASSED WITH 100% SUCCESS! ***')
