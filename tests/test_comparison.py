"""Physical accounting and causal timing of the hackathon paired simulation."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.comparison import ComparisonInput, compare


def test_same_demand_and_no_saving_until_detected_then_repaired():
    report = compare(ComparisonInput())
    assert report['detection_sequence'] == 10
    assert report['repair_sequence'] == 15
    points = report['points']
    assert len(points) == 96
    assert all(p['without_kwh'] == p['with_kwh'] for p in points[:15])
    assert all(p['saved_kwh'] == 0 for p in points[:15])
    assert all(p['unmetered_with_kwh'] == pytest.approx(.12) for p in points[15:])
    for p in points:
        assert p['without_kwh'] == pytest.approx(p['technical_without_kwh'] + p['unmetered_without_kwh'])
        assert p['with_kwh'] == pytest.approx(p['technical_with_kwh'] + p['unmetered_with_kwh'])
        assert p['technical_with_kwh'] > 0
    assert points[-1]['saved_kwh'] == pytest.approx(sum(p['without_kwh']-p['with_kwh'] for p in points))


@pytest.mark.parametrize('settings', [dict(scenario='clean'), dict(repair_effectiveness=0),
                                     dict(repair_delay_minutes=1440), dict(coverage_profile='pgvcl_like')])
def test_no_invented_savings_when_clean_ineffective_too_late_or_unobservable(settings):
    report = compare(ComparisonInput(**settings))
    assert all(p['saved_kwh'] == 0 for p in report['points'])
    if settings.get('scenario') == 'clean' or settings.get('coverage_profile'):
        assert report['detection_sequence'] is None
        assert report['repair_sequence'] is None


def test_zero_delay_is_after_detection_and_hidden_bypass_is_detectable():
    report = compare(ComparisonInput(scenario='hidden_bypass', repair_delay_minutes=0))
    assert report['repair_sequence'] == report['detection_sequence'] + 1
    assert report['points'][report['detection_sequence']]['saved_kwh'] == 0


def test_api_is_reproducible_and_validates_assumptions():
    with TestClient(app) as client:
        first = client.post('/api/comparison', json={})
        assert first.status_code == 200
        assert first.json() == client.post('/api/comparison', json={}).json()
        for body in ({'repair_effectiveness': 1.1}, {'repair_delay_minutes': 7}, {'coverage_profile': 'fake'}):
            assert client.post('/api/comparison', json=body).status_code == 422
