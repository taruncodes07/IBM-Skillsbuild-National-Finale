"""Cross-branch contracts and CSV validation regressions."""
import pytest
from backend import analytics, coverage
from backend.sources import ingest_readings_csv
from backend.simulation import generate
from backend.topology import ASSETS


def test_installed_inventory_cannot_be_overridden_by_legacy_full_mode():
    readings = generate(42, 0, [])['readings']
    installed = coverage.installed_meters('pgvcl_like', ASSETS)
    balances = analytics.reconcile('merged', 0, readings, None, installed, coverage_mode='full')
    assert all(b['validity'] == 'insufficient_observability' for b in balances)
    assert all(b['residual_kwh'] is None and not b['qualifies'] for b in balances)
    with pytest.raises(ValueError, match='coverage mode'):
        analytics.reconcile('merged', 0, readings, coverage_mode='unknown')


def test_csv_text_does_not_get_interpreted_as_a_windows_path():
    text = 'stream_id,timestamp,value,unit,quality\n' + 'm,2022-09-01T00:00:00Z,1,kWh,valid\n' * 20
    result = ingest_readings_csv(text)
    assert result['total_rows'] == 20
    assert result['valid_count'] == 1
    assert len(result['duplicates_detected']) == 19


def test_csv_rejects_infinite_energy_and_bad_time_and_normalizes_duplicate_keys():
    result = ingest_readings_csv('stream_id,timestamp,value,unit,quality\n'
        'm,2022-09-01T00:00:00Z,inf,kWh,valid\n'
        'n,not-a-time,1,kWh,valid\n'
        'p,2022-09-01T00:00:00Z,1,kWh,valid\n'
        'p,2022-09-01T05:30:00+05:30,1,kWh,valid\n')
    assert result['records'][0]['value'] is None
    assert result['records'][0]['quality'] == 'invalid'
    assert result['validation_errors']
    assert result['records'][-1]['quality'] == 'duplicate'
    assert result['valid_count'] == 1


def test_empty_legacy_action_catalog_abstains():
    out = analytics.rank_next_checks(dict(validity='valid', qualifies=True), candidate_actions={})
    assert out['abstain'] and not out['candidates']
