"""Repeated API journeys and persistence recovery, using isolated test storage."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from backend import engine, investigations, providers, store
from backend.contracts import InvestigationInput
from backend.main import app


@pytest.mark.parametrize('seed',[101,202,303,404,505])
def test_repeat_investigate_review_export_without_visual_mission(monkeypatch,seed):
    async def offline(*args,**kwargs):return None
    monkeypatch.setattr(providers,'select_plan',offline)
    with TestClient(app) as client:
        created=client.post('/api/runs',json=dict(seed=seed,scenario='visible_unmetered_load'))
        assert created.status_code==200,created.text
        run=created.json()['run']
        for _ in range(3):assert client.post(f"/api/runs/{run['id']}/control",json=dict(command='step')).status_code==200
        snapshot=client.get(f"/api/runs/{run['id']}/snapshot").json()
        alert=next(a for a in snapshot['alerts'] if a['boundary_asset_id']=='branch-03')
        body=dict(alert_id=alert['id'],sequence=snapshot['seq'],idempotency_key=f'qa-{seed}')
        case=client.post('/api/cases',json=body).json()
        assert client.post('/api/cases',json=body).json()['id']==case['id']
        invbody=InvestigationInput(run_id=run['id'],sequence=snapshot['seq'],area_id='branch-03',idempotency_key=f'qa-inv-{seed}')
        with monkeypatch.context() as scoped:
            scoped.setattr(investigations,'schedule',lambda _:None)
            inv=investigations.create(invbody,snapshot)
        asyncio.run(investigations.process(inv['id']))
        assert store.get(inv['id'])['status']=='completed'
        original_revision=case['revision']
        for state,actor in [('triaged','analyst'),('under_review','reviewer'),('field_check_required','reviewer')]:
            updated=client.patch('/api/cases/'+case['id'],headers={'x-actor':actor},
                json=dict(expected_revision=case['revision'],state=state,reason='Synthetic QA rehearsal; physical cause unconfirmed.'))
            assert updated.status_code==200,updated.text
            case=updated.json()
        assert client.patch('/api/cases/'+case['id'],json=dict(expected_revision=original_revision,note='stale')).status_code==409
        before=client.get('/api/cases/'+case['id']+'/export').json()
        client.post(f"/api/runs/{run['id']}/control",json=dict(command='step'))
        after=client.get('/api/cases/'+case['id']+'/export').json()
        assert before['analysis']==after['analysis']
        assert after['missions']==[] and after['evidence']==[]
        assert after['investigations'][0]['id']==inv['id']
        assert len(after['audit'])==4
        assert inv['id'] in client.get('/api/cases/'+case['id']+'/export?format=md').text


def test_startup_interrupts_abandoned_jobs_without_reexecuting(monkeypatch):
    run=engine.create_run(601,'visible_unmetered_load');engine.step(run)
    snapshot=engine.snapshot(run['id'])
    with monkeypatch.context() as scoped:
        scoped.setattr(investigations,'schedule',lambda _:None)
        abandoned=[]
        for status in ('queued','planning','running'):
            body=InvestigationInput(run_id=run['id'],sequence=snapshot['seq'],area_id='branch-03',idempotency_key='restart-'+status)
            inv=investigations.create(body,snapshot);inv['status']=status;store.put('investigation',inv);abandoned.append(inv['id'])
    async def forbidden(*args,**kwargs):pytest.fail('Startup must not spend model requests')
    monkeypatch.setattr(providers,'select_plan',forbidden)
    with TestClient(app) as client:
        for iid in abandoned:
            detail=client.get('/api/investigations/'+iid).json()
            assert detail['status']=='interrupted' and detail['checks']==[]
            assert 'start a new investigation' in detail['error']
    # A second startup preserves interruption and performs no automatic retries.
    with TestClient(app):assert all(store.get(iid)['status']=='interrupted' for iid in abandoned)


def test_cancelled_workflow_persists_interruption_then_explicit_retry(monkeypatch):
    run=engine.create_run(602,'visible_unmetered_load')
    for _ in range(3):engine.step(run)
    snapshot=engine.snapshot(run['id'])
    async def exercise():
        entered=asyncio.Event()
        async def stalled(*args,**kwargs):
            entered.set();await asyncio.Event().wait()
        with monkeypatch.context() as scoped:
            scoped.setattr(providers,'select_plan',stalled)
            scoped.setattr(investigations,'schedule',lambda _:None)
            body=InvestigationInput(run_id=run['id'],sequence=snapshot['seq'],area_id='branch-03',idempotency_key='cancel-original')
            inv=investigations.create(body,snapshot)
            task=asyncio.create_task(investigations.process(inv['id']))
            await asyncio.wait_for(entered.wait(),3);task.cancel()
            with pytest.raises(asyncio.CancelledError):await task
            assert store.get(inv['id'])['status']=='interrupted'
            # Same-key delivery only returns the original; new explicit key retries.
            assert investigations.create(body,snapshot)['id']==inv['id']
        async def rules(*args,**kwargs):return None
        with monkeypatch.context() as scoped:
            scoped.setattr(providers,'select_plan',rules)
            scoped.setattr(investigations,'schedule',lambda _:None)
            retry=investigations.create(body.model_copy(update={'idempotency_key':'cancel-retry'}),snapshot)
            await investigations.process(retry['id'])
            assert retry['id']!=inv['id'] and store.get(retry['id'])['status']=='completed'
            assert store.get(inv['id'])['status']=='interrupted'
    asyncio.run(exercise())
