"""Report freshness is independent across detection and full workflow runs."""
import json
from backend import benchmark


def save(tmp_path,name,report):
    docs=tmp_path/'docs';docs.mkdir(exist_ok=True)
    (docs/name).write_text(json.dumps(report),encoding='utf-8')


def test_stale_detection_does_not_hide_current_adaptive_report(monkeypatch,tmp_path):
    monkeypatch.setattr(benchmark,'ROOT',tmp_path)
    monkeypatch.setattr(benchmark,'fingerprint',lambda:'current')
    save(tmp_path,'independent-results.json',dict(code_hash='old',status='COMPLETED'))
    save(tmp_path,'adaptive-results.json',dict(code_hash='current',status='COMPLETED',cases=[
        dict(id='case-1',status='FAILED',trace=['trace'],checks=['check'],planner_history=['round'],provider_attempts=['attempt'])]))
    result=benchmark.results()
    assert result['status']=='STALE'
    assert result['adaptive']['status']=='COMPLETED'
    assert result['adaptive']['cases']==[dict(id='case-1',status='FAILED')]


def test_modified_candidate_never_shows_stale_adaptive_scores(monkeypatch,tmp_path):
    monkeypatch.setattr(benchmark,'ROOT',tmp_path)
    monkeypatch.setattr(benchmark,'fingerprint',lambda:'current')
    save(tmp_path,'adaptive-results.json',dict(code_hash='old',status='COMPLETED',cases=[],policies={'watsonx':{'successful_cases':18}}))
    result=benchmark.results()
    assert result['status']=='NOT_RUN'
    assert result['adaptive']['status']=='STALE'
    assert 'policies' not in result['adaptive']
