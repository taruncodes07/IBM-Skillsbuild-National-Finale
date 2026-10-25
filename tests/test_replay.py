from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend import engine, store
from backend.main import app
from backend.sources import DevelopmentMonthSource, month_summary


def test_development_source_boundaries_and_provenance():
    source=DevelopmentMonthSource(77)
    first=source.read_interval(0)['readings']
    last=source.read_interval(2879)['readings']
    assert len(first)==len(last)==38
    assert first['feeder-01']['interval_start']=='2022-08-31T18:30:00Z'
    assert last['feeder-01']['interval_start']=='2022-09-30T18:15:00Z'
    assert last['feeder-01']['interval_end']=='2022-09-30T18:30:00Z'
    assert first==source.read_interval(0)['readings']
    assert source.manifest['source_kind']=='DEV_FIXTURE'
    assert source.manifest['official_source_status']=='PENDING'
    assert source.manifest['hash_kind']=='GENERATOR_AND_CONFIG'
    assert source.manifest['source_hash']!=DevelopmentMonthSource(78).manifest['source_hash']
    with pytest.raises(ValueError): source.read_interval(2880)
    with pytest.raises(ValueError): source.read_interval(-1)


def test_month_rollups_keep_missing_values_and_disjoint_cuts():
    source=DevelopmentMonthSource(77)
    report=month_summary(77)
    assert len(report['days'])==30
    assert sum(d['expected_readings'] for d in report['days'])==109440
    assert sum(d['missing_readings'] for d in report['days'])==3
    first=report['days'][0]
    expected=sum(source.read_interval(seq)['readings'][f'feeder-{i:02}']['energy_import_kwh'] for seq in range(96) for i in [1,2])
    assert first['feeder_input_kwh']==pytest.approx(expected)
    assert first['missing_readings']==1
    assert first['household_sum_complete'] is False
    assert source.read_interval(95)['readings']['household-07']['energy_import_kwh'] is None
    assert source.read_interval(96)['readings']['household-08']['quality']=='missing'


def test_seek_is_repeatable_and_revisiting_does_not_advance_streaks():
    run=engine.create_run(72,mode='replay')
    engine.seek(run,96)
    observed=engine.snapshot(run['id'])
    assert observed['seq']==96
    assert observed['run']['seq']==96
    assert any(b['validity']=='data_incomplete' for b in observed['balances'])
    streaks=dict(run['streaks'])
    engine.seek(run,0)
    assert engine.snapshot(run['id'])['seq']==0
    assert run['seq']==96
    engine.step(run)
    assert engine.snapshot(run['id'])['seq']==1
    assert run['streaks']==streaks
    engine.seek(run,96)
    repeated=engine.snapshot(run['id'])
    assert repeated['readings']==observed['readings']
    assert repeated['balances']==observed['balances']
    count=store.DB.execute('SELECT count(*) FROM intervals WHERE run_id=?',(run['id'],)).fetchone()[0]
    assert count==97


def test_final_interval_seek_and_end_of_month():
    run=engine.create_run(73,mode='replay')
    engine.seek(run,2879)
    final=engine.snapshot(run['id'])
    assert final['seq']==2879
    assert len(final['readings'])==38
    assert not run['playing']
    assert datetime.fromisoformat(final['simulation_time'].replace('Z','+00:00')).isoformat()=='2022-09-30T18:30:00+00:00'
    engine.step(run)
    assert run['seq']==2879
    with pytest.raises(ValueError): engine.seek(run,2880)


def test_replay_api_revision_and_read_only_gates():
    with TestClient(app) as client:
        response=client.post('/api/runs',json=dict(seed=74,mode='replay'))
        assert response.status_code==200
        snapshot=response.json();rid=snapshot['run']['id']
        stale=snapshot['run']['revision']
        sought=client.post(f'/api/runs/{rid}/control',json=dict(command='seek',sequence=95,expected_revision=stale))
        assert sought.status_code==200
        assert sought.json()['seq']==95
        assert client.post(f'/api/runs/{rid}/control',json=dict(command='seek',sequence=0,expected_revision=stale)).status_code==409
        assert client.post(f'/api/runs/{rid}/control',json=dict(command='seek')).status_code==400
        assert client.post(f'/api/runs/{rid}/incidents',headers={'X-Actor':'presenter'},json=dict(type='hidden_bypass',start=100,end=110)).status_code==409
        assert client.post(f'/api/runs/{rid}/readings/revise',json=dict(asset_id='household-07',sequence=95,expected_revision=1,quality='valid',energy_import_kwh=1)).status_code==409
        assert client.post('/api/runs',json=dict(mode='replay',scenario='hidden_bypass')).status_code==400
        assert client.get('/api/sources').json()['bescom']['status']=='PENDING'
        assert client.get('/api/health').json()['application']=='Grid Trace'


def test_case_uses_selected_interval_after_backward_seek():
    with TestClient(app) as client:
        snapshot=client.post('/api/runs',json=dict(scenario='visible_unmetered_load')).json()
        rid=snapshot['run']['id']
        for _ in range(6): client.post(f'/api/runs/{rid}/control',json=dict(command='step'))
        selected=client.post(f'/api/runs/{rid}/control',json=dict(command='seek',sequence=3)).json()
        alert=selected['alerts'][0]
        case=client.post('/api/cases',json=dict(alert_id=alert['id'],idempotency_key='history-case',sequence=3)).json()
        assert case['analysis_sequence']==3
        exported=client.get(f"/api/cases/{case['id']}/export").json()
        assert exported['analysis']['seq']==3
        assert len(exported['contributing_intervals'])==3
        assert exported['audit'][0]['simulation_timestamp']==exported['analysis']['simulation_time']
