import asyncio
import json

import pytest
import planner_pilot as pilot
from backend import benchmark,providers


def test_pilot_inputs_repeat_and_scoring_labels_stay_out_of_context():
    first=pilot.make_cases();second=pilot.make_cases()
    assert [c['input_hash'] for c in first]==[c['input_hash'] for c in second]
    assert len(first)==9 and len({c['mechanism'] for c in first})==9
    for case in first:
        assert not {'mechanism','acceptable_actions','rubric','expected_action','physical_connections_m'} & case['context'].keys()
        assert 'elapsed_ms' not in json.dumps(case['context'])
    with pytest.raises(ValueError):pilot.make_cases(10)


def test_pilot_rubric_checks_evidence_and_preserves_rule_comparison():
    cases=pilot.make_cases()
    for case in cases:
        raw=pilot.rule_plan(case['target'],case['workers'],case['fusion'])
        assert pilot.score_proposal(case,raw)['rubric_match']
        bad=dict(raw,evidence_ids=['invented-reference'])
        result=pilot.score_proposal(case,bad)
        assert not result['policy_allowed'] and not result['rubric_match']
    missing=next(c for c in cases if c['mechanism']=='missing')
    bad=dict(pilot.rule_plan(missing['target'],missing['workers'],missing['fusion']),next_action='REQUEST_METER_REVIEW')
    assert not pilot.score_proposal(missing,bad)['rubric_match']


def test_pinned_pilot_keeps_failures_and_skips_in_denominator(tmp_path,monkeypatch):
    (tmp_path/'docs').mkdir();monkeypatch.setattr(pilot,'ROOT',tmp_path)
    monkeypatch.setattr(pilot,'fingerprint',lambda:'frozen')
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True,model='mock-granite')))
    requests=[]
    async def fail(provider,context):
        requests.append(provider)
        raise providers.ProviderUnavailable('HTTP_503')
    monkeypatch.setattr(providers,'propose',fail)
    asyncio.run(pilot.evaluate('watsonx',9))
    report=json.loads((tmp_path/'docs'/'planner-pilot-results.json').read_text())
    assert requests==['watsonx','watsonx']
    assert report['summary']['total_cases']==9
    assert report['summary']['failed_cases']==2
    assert report['summary']['skipped_cases']==7
    assert report['summary']['rubric_matches']==0
    assert report['summary']['rules_rubric_matches']==9
    assert report['protocol']['failover'] is False


def test_saved_pilot_is_stale_when_code_changes(tmp_path,monkeypatch):
    (tmp_path/'docs').mkdir();monkeypatch.setattr(benchmark,'ROOT',tmp_path)
    monkeypatch.setattr(benchmark,'fingerprint',lambda:'new-hash')
    (tmp_path/'docs'/'planner-pilot-results.json').write_text(json.dumps(dict(status='COMPLETED',code_hash='old-hash',summary={'rubric_matches':9})))
    result=benchmark.planner_pilot()
    assert result['status']=='STALE' and 'summary' not in result
