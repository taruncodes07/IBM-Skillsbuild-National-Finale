"""Acceptance tests for the PRD v4.0 gaps closed in this increment.

AC-13 coverage-aware localization, AC-14 quantitative ranking and abstention,
AC-05 Scenario G matched-residual differentiation, FR-07/AC-08/Demo-A3 ground-first.
Synthetic fixtures only; nothing here claims field accuracy.
"""
import pytest

from backend import coverage, ranking
from backend.analytics import reconcile
from backend.simulation import generate, matched_residual_incidents, MATCHED_RESIDUAL
from backend.topology import ASSETS, BY_ID

# tests/ is not a package here, matching the convention in tests/evaluate.py.
from test_acceptance import client, post, patch, case, move, ground  # noqa: F401


EVENT = [dict(type='visible_unmetered_load', target_asset_id='branch-03', start=0, end=90, severity=1.2)]


# --------------------------------------------------------------------------- AC-14

def test_ac14_published_table_recomputes_from_logged_components():
    """Every illustrative ranking in PRD section 5 Table 4 recomputes within 0.001."""
    for row in ranking.CALIBRATION_FIXTURE:
        if not row['eligible']:
            continue
        got = ranking.score_from_components(row['ig'], row['reliability'], row['access'],
                                            row['cost_inr'], row['minutes'])
        assert abs(got - row['expected_score']) < 0.001, row['label']


def test_ac14_components_are_all_logged_for_every_ranked_action():
    out = ranking.rank(dict(diagnostic_status='UNEXPLAINED_ENERGY', billing_status='NOT_AVAILABLE',
                            ground_question_open=False, completed_actions=()))
    assert out['ranked'], 'expected at least one eligible action'
    for entry in out['ranked']:
        for key in ('action_id', 'question', 'prerequisite_status', 'information_gain_bits',
                    'information_gain_range', 'reliability', 'access', 'cost', 'expected_minutes',
                    'normalisation', 'score', 'sensitivity', 'rank', 'likelihood_confidence'):
            assert key in entry, f'{entry["action_id"]} missing {key}'
        recomputed = ranking.score_from_components(
            entry['information_gain_bits'], entry['reliability'], entry['access'],
            entry['cost']['total_inr'], entry['expected_minutes'])
        assert abs(recomputed - entry['score']) < 1e-9
        assert entry['cost']['currency'] == 'INR'
    assert out['policy_version'] == ranking.POLICY_VERSION
    ranks = [e['rank'] for e in out['ranked']]
    assert ranks == sorted(ranks) and ranks[0] == 1


def test_ac14_unapproved_aerial_action_is_rejected_not_scored():
    """A camera cannot be chosen before ground review specifies what it must answer."""
    out = ranking.rank(dict(diagnostic_status='UNEXPLAINED_ENERGY', billing_status='NOT_AVAILABLE',
                            ground_question_open=False, completed_actions=()))
    rejected = {r['action_id']: r['rejection_reason'] for r in out['rejected']}
    assert 'AERIAL_OBSERVATION' in rejected
    assert 'NO_GROUND_GAP' in rejected['AERIAL_OBSERVATION']
    assert all(e['action_id'] != 'AERIAL_OBSERVATION' for e in out['ranked'])


def test_ac14_cost_and_access_changes_alter_rank_as_expected():
    base = ranking.score_from_components(0.9, 0.85, 0.90, 500.0, 35)
    dearer = ranking.score_from_components(0.9, 0.85, 0.90, 1800.0, 35)
    harder = ranking.score_from_components(0.9, 0.85, 0.40, 500.0, 35)
    slower = ranking.score_from_components(0.9, 0.85, 0.90, 500.0, 110)
    assert dearer < base and harder < base and slower < base
    assert harder < dearer, 'access should dominate a moderate cost increase here'


def test_ac14_normal_measurements_abstain_and_reject_every_check():
    out = ranking.rank(dict(diagnostic_status='WITHIN_MODEL_RANGE', billing_status='NOT_AVAILABLE',
                            ground_question_open=False, completed_actions=()))
    assert out['recommended_action'] == 'ABSTAIN_NO_ACTION'
    assert out['ranked'] == []
    assert all('NO_PERSISTENT_SIGNAL' in r['rejection_reason'] for r in out['rejected'])


def test_ac14_unstable_winner_is_surfaced_for_human_choice():
    out = ranking.rank(dict(diagnostic_status='UNEXPLAINED_ENERGY', billing_status='NOT_AVAILABLE',
                            ground_question_open=False, completed_actions=()))
    if out['tied_actions']:
        assert out['human_choice_required'] == (not out['winner_stable_under_sensitivity'])
    for entry in out['ranked']:
        s = entry['sensitivity']
        assert s['low'] <= entry['score'] <= s['high']
        assert s['fraction'] == ranking.SENSITIVITY_FRACTION


def test_ac14_unknown_likelihoods_produce_a_range_not_a_point():
    spec = ranking.ACTIONS['REQUEST_BILLING_AUDIT']
    assert spec['likelihood_confidence'] == 'UNKNOWN'
    out = ranking.rank(dict(diagnostic_status='UNEXPLAINED_ENERGY', billing_status='AVAILABLE',
                            ground_question_open=False, completed_actions=()))
    entry = next(e for e in out['ranked'] if e['action_id'] == 'REQUEST_BILLING_AUDIT')
    low, high = entry['information_gain_range']
    assert low == 0.0 and high >= low


def test_entropy_and_information_gain_are_well_formed():
    assert ranking.entropy([1.0]) == 0.0
    assert abs(ranking.entropy([.5, .5]) - 1.0) < 1e-12
    prior = ranking.uniform_prior()
    for action_id, spec in ranking.ACTIONS.items():
        ig = ranking.information_gain(prior, spec['likelihoods'], spec['outcomes'])
        assert 0.0 <= ig <= ranking.entropy(prior.values()) + 1e-9, action_id


# --------------------------------------------------------------------------- AC-13

def test_ac13_profiles_are_deterministic_and_documented():
    for pid in coverage.PROFILES:
        first = coverage.installed_meters(pid, ASSETS)
        assert first == coverage.installed_meters(pid, ASSETS)
        summary = coverage.summary(pid, ASSETS)
        assert summary['reference'] and summary['note'] and summary['inventory_version']
        assert 'fictional' in summary['disclosure'].lower()


def test_ac13_same_event_localizes_differently_by_coverage():
    """The headline claim: instrumentation decides what can be concluded."""
    readings = generate(42, 5, EVENT)['readings']

    full = reconcile('cov', 5, readings, None, coverage.installed_meters('full_sectional', ASSETS))
    assert any(b['boundary_asset_id'] == 'branch-03' and b['qualifies'] for b in full)

    for pid in ('bescom_like', 'tgspdcl_like', 'pgvcl_like'):
        sparse = reconcile('cov', 5, readings, None, coverage.installed_meters(pid, ASSETS))
        b3 = next(b for b in sparse if b['boundary_asset_id'] == 'branch-03')
        assert b3['validity'] == 'insufficient_observability', pid
        assert b3['residual_kwh'] is None and not b3['qualifies'], pid
        assert b3['uninstrumented_asset_ids'], pid
        assert not any(BY_ID[b['boundary_asset_id']]['kind'] == 'branch' and b['qualifies']
                       for b in sparse), f'{pid} must not localize to a branch it cannot measure'


def test_ac13_uninstrumented_cut_never_becomes_a_zero_filled_residual():
    readings = generate(42, 5, EVENT)['readings']
    sparse = reconcile('cov', 5, readings, None, coverage.installed_meters('pgvcl_like', ASSETS))
    for b in sparse:
        if b['validity'] == 'insufficient_observability':
            assert b['residual_kwh'] is None and b['input_kwh'] is None and b['output_sum_kwh'] is None
            assert b['completeness_ratio'] == 0.0


def test_ac13_observability_is_reported_separately_from_data_quality():
    """An absent meter is a permanent limit; a missing reading is a repairable fault."""
    from backend.analytics import detect
    readings = generate(42, 5, EVENT)['readings']
    balances = reconcile('cov', 5, readings, None, coverage.installed_meters('pgvcl_like', ASSETS))
    _, quality, _ = detect('cov', 5, balances, readings, [], {}, {})
    kinds = {q['kind'] for q in quality}
    assert kinds == {'observability'}
    assert all('Install sectional measurement' in q['recommended'] for q in quality)


def test_ac13_insufficient_observability_abstains_in_the_ranker():
    out = ranking.rank(dict(diagnostic_status='WITHIN_MODEL_RANGE', billing_status='NOT_AVAILABLE',
                            ground_question_open=False, completed_actions=()))
    assert out['recommended_action'] == 'ABSTAIN_NO_ACTION'


def test_ac13_coverage_endpoints_and_streak_reset(client):
    profiles = client.get('/api/coverage/profiles').json()
    assert {p['id'] for p in profiles['profiles']} == set(coverage.PROFILES)

    snapshot = post(client, '/runs', dict(seed=42, scenario='visible_unmetered_load',
                                          coverage_profile='full_sectional'))
    rid = snapshot['run']['id']
    assert client.get(f'/api/runs/{rid}/coverage').json()['profile_id'] == 'full_sectional'

    for _ in range(4):
        post(client, f'/runs/{rid}/control', dict(command='step'))
    before = client.get(f'/api/runs/{rid}/snapshot').json()
    assert any(a['status'] == 'active' for a in before['alerts'])

    post(client, f'/runs/{rid}/coverage', dict(profile_id='tgspdcl_like'), 'analyst', 403)
    after = post(client, f'/runs/{rid}/coverage', dict(profile_id='tgspdcl_like'), 'presenter')
    assert after['profile_id'] == 'tgspdcl_like'
    run = client.get(f'/api/runs/{rid}/snapshot').json()['run']
    assert run['inventory_version'] == coverage.inventory_version('tgspdcl_like')

    post(client, f'/runs/{rid}/control', dict(command='step'))
    fresh = client.get(f'/api/runs/{rid}/snapshot').json()
    b3 = next(b for b in fresh['balances'] if b['boundary_asset_id'] == 'branch-03')
    assert b3['validity'] == 'insufficient_observability'


def test_ac13_scenario_h_run_reports_an_observability_gap(client):
    """Scenario H: sparse RDSS-style rollout cannot support branch localization."""
    snapshot = post(client, '/runs', dict(seed=42, scenario='visible_unmetered_load',
                                          coverage_profile='tgspdcl_like'))
    rid = snapshot['run']['id']
    for _ in range(4):
        post(client, f'/runs/{rid}/control', dict(command='step'))
    fresh = client.get(f'/api/runs/{rid}/snapshot').json()
    assert not any(a['status'] == 'active' for a in fresh['alerts'])
    assert any(q['kind'] == 'observability' for q in fresh['quality_events'])
    actions = client.get(f'/api/balances/branch-03/actions?run_id={rid}').json()
    assert actions['diagnostic_status'] == 'INSUFFICIENT_OBSERVABILITY'
    assert actions['recommended_action'] == 'ABSTAIN_NO_ACTION'
    assert actions['uninstrumented_asset_ids']


# --------------------------------------------------------------------------- AC-05

def test_ac05_scenario_g_holds_apparent_excess_comparable():
    magnitudes = {}
    for scenario in MATCHED_RESIDUAL:
        readings = generate(42, 5, matched_residual_incidents(scenario, start=0, end=90))['readings']
        b = next(x for x in reconcile('g', 5, readings) if x['boundary_asset_id'] == 'branch-03')
        magnitudes[scenario] = b['residual_kwh']
    present = [v for v in magnitudes.values() if v is not None]
    assert len(present) >= 3
    assert max(present) - min(present) < 0.5, magnitudes
    assert magnitudes['matched_residual_incomplete'] is None


def test_ac05_same_excess_different_evidence_gives_different_next_check():
    recommendations = {}
    for scenario in MATCHED_RESIDUAL:
        readings = generate(42, 5, matched_residual_incidents(scenario, start=0, end=90))['readings']
        b = next(x for x in reconcile('g', 5, readings) if x['boundary_asset_id'] == 'branch-03')
        if b['validity'] == 'valid':
            status, kind = 'UNEXPLAINED_ENERGY', None
        else:
            reasons = ' '.join(b['invalid_reasons']).lower()
            status = 'DATA_INCOMPLETE'
            kind = 'TOPOLOGY_MISMATCH' if 'topology mismatch' in reasons else 'MISSING_READINGS'
        out = ranking.rank(dict(diagnostic_status=status, incomplete_kind=kind,
                                billing_status='NOT_AVAILABLE', ground_question_open=False,
                                completed_actions=()))
        recommendations[scenario] = out['recommended_action']
    assert recommendations['matched_residual_incomplete'] == 'REQUEST_MISSING_DATA'
    assert len(set(recommendations.values())) > 1, recommendations


# --------------------------------------------------------------------------- FR-07 / AC-08 / Demo-A3

def test_fr07_aerial_requires_a_recorded_unanswered_ground_question(client):
    c = case(client); cid = c['id']
    c = move(client, c, 'triaged', 'analyst')
    post(client, f'/cases/{cid}/missions', dict(approved=True, idempotency_key='early'), 'reviewer', 409)
    g = ground(client, cid)
    assert g['outstanding_question'] and not g['resolved_from_ground']
    assert client.get('/api/cases/' + cid).json()['case']['state'] == 'ground_review'
    m = post(client, f'/cases/{cid}/missions', dict(approved=True, idempotency_key='after-ground'), 'reviewer')
    assert m['ground_observation_id'] == g['id']
    assert m['answering_question'] == g['outstanding_question']
    assert 'cannot establish authorization' in m['limitation']


def test_fr07_ground_resolution_blocks_an_unnecessary_flight(client):
    c = case(client); cid = c['id']
    move(client, c, 'triaged', 'analyst')
    ground(client, cid, key='resolved', visibility='clear', resolved=True)
    post(client, f'/cases/{cid}/missions', dict(approved=True, idempotency_key='unneeded'), 'reviewer', 409)


def test_fr07_clear_ground_view_cannot_justify_an_aerial_viewpoint(client):
    c = case(client); cid = c['id']
    move(client, c, 'triaged', 'analyst')
    ground(client, cid, key='clear-but-open', visibility='clear', resolved=False)
    post(client, f'/cases/{cid}/missions', dict(approved=True, idempotency_key='clear'), 'reviewer', 409)


def test_fr07_observation_validation_and_roles(client):
    c = case(client); cid = c['id']
    move(client, c, 'triaged', 'analyst')
    body = dict(idempotency_key='k', access='obtained', observed_asset_ids=['branch-03'],
                visibility='obstructed', resolved_from_ground=False, outstanding_question='', notes='')
    post(client, f'/cases/{cid}/ground-observations', body, 'reviewer', 400)
    post(client, f'/cases/{cid}/ground-observations', {**body, 'outstanding_question': 'q'}, 'analyst', 403)
    post(client, f'/cases/{cid}/ground-observations',
         {**body, 'resolved_from_ground': True, 'outstanding_question': 'q'}, 'reviewer', 400)
    post(client, f'/cases/{cid}/ground-observations',
         {**body, 'observed_asset_ids': ['branch-99'], 'outstanding_question': 'q'}, 'reviewer', 400)
    first = post(client, f'/cases/{cid}/ground-observations', {**body, 'outstanding_question': 'q'}, 'reviewer')
    again = post(client, f'/cases/{cid}/ground-observations', {**body, 'outstanding_question': 'q'}, 'reviewer')
    assert first['id'] == again['id']


def test_ac08_no_drone_path_still_reaches_a_human_decision(client):
    """Ground-first must not trap a case that never needs a flight."""
    c = case(client); cid = c['id']
    c = move(client, c, 'triaged', 'analyst')
    c = move(client, c, 'under_review', 'reviewer')
    c = move(client, c, 'field_check_required', 'reviewer')
    detail = client.get('/api/cases/' + cid).json()
    assert detail['case']['state'] == 'field_check_required'
    assert detail['missions'] == [] and detail['evidence'] == []


def test_ground_observations_are_listed_with_the_open_question(client):
    c = case(client); cid = c['id']
    move(client, c, 'triaged', 'analyst')
    ground(client, cid, key='g1')
    listing = client.get(f'/api/cases/{cid}/ground-observations').json()
    assert len(listing['observations']) == 1
    assert listing['open_question']['id'] == listing['observations'][0]['id']
    ground(client, cid, key='g2', visibility='clear', resolved=True)
    assert client.get(f'/api/cases/{cid}/ground-observations').json()['open_question'] is None


def test_ranked_actions_endpoint_for_a_live_balance(client):
    snapshot = post(client, '/runs', dict(seed=42, scenario='visible_unmetered_load'))
    rid = snapshot['run']['id']
    for _ in range(4):
        post(client, f'/runs/{rid}/control', dict(command='step'))
    out = client.get(f'/api/balances/branch-03/actions?run_id={rid}').json()
    assert out['diagnostic_status'] == 'UNEXPLAINED_ENERGY'
    assert out['ranked'] and out['policy_version'] == ranking.POLICY_VERSION
    assert out['coverage_profile'] == 'full_sectional'
    assert 'Illustrative' in out['disclosure']
    assert client.get(f'/api/balances/branch-99/actions?run_id={rid}').status_code == 404
