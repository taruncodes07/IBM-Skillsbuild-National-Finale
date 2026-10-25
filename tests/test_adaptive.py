"""Behavioral checks for bounded, evidence-producing investigation loops."""
import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient

from backend import engine,investigations,providers,store
from backend.main import app


def snapshot():
    run=engine.create_run(67,'visible_unmetered_load')
    for _ in range(3):engine.step(run)
    return engine.snapshot(run['id'])


def wait(client,iid):
    for _ in range(150):
        response=client.get('/api/investigations/'+iid)
        assert response.status_code==200
        detail=response.json()
        if detail['status'] not in ('queued','planning','running'):return detail
        time.sleep(.02)
    pytest.fail('Investigation did not terminate')


def mock_decision(context,action):
    return dict(provider='watsonx',model='mock-planner',usage={},proposal=dict(
        next_action=action,target_area_id=context['area_id'],
        evidence_ids=[context['fusion']['evidence_ids'][-1]],competing_causes=['METER_FAULT','TECHNICAL_MODEL_ERROR'],
        justification='Synthetic test planner recommendation.',requires_human_approval=action=='REQUEST_METER_REVIEW'))


def start(client,s,key):
    body=dict(run_id=s['run']['id'],sequence=s['seq'],area_id='branch-03',idempotency_key=key)
    response=client.post('/api/investigations',json=body)
    assert response.status_code==200
    return response.json(),body


def test_followup_adds_new_evidence_and_uses_frozen_window_in_exports(monkeypatch):
    s=snapshot();contexts=[]
    expected=sum(next(b for b in store.interval(s['run']['id'],i)['balances'] if b['boundary_asset_id']=='branch-03')['residual_kwh'] for i in range(4))
    async def select(context,emit,**kwargs):
        contexts.append(json.loads(json.dumps(context)))
        kwargs['budget']['provider_calls']+=1
        if not context['completed_checks']:
            # Simulate a later observation revision while the planner is running.
            current=store.interval(s['run']['id'],3)
            next(b for b in current['balances'] if b['boundary_asset_id']=='branch-03')['residual_kwh']=999
            store.DB.execute('UPDATE intervals SET body=? WHERE run_id=? AND seq=3',(json.dumps(current),s['run']['id']));store.DB.commit()
        return mock_decision(context,'REQUEST_ELECTRICAL_RECHECK' if not context['completed_checks'] else 'REQUEST_METER_REVIEW')
    monkeypatch.setattr(providers,'select_plan',select)
    with TestClient(app) as client:
        case=client.post('/api/cases',json=dict(alert_id=s['alerts'][0]['id'],sequence=3,idempotency_key='adaptive-export')).json()
        inv,body=start(client,s,'frozen-window')
        detail=wait(client,inv['id'])
        assert detail['status']=='completed',detail
        assert len(detail['checks'])==1
        check=detail['checks'][0]
        assert check['findings']['signed_residual_valid_sum_kwh']==pytest.approx(expected)
        assert len(detail['planner_history'])==2
        assert check['evidence_id'] in contexts[1]['fusion']['evidence_ids']
        assert detail['planner']['proposal']['evidence_ids']==[check['evidence_id']]
        assert len(contexts[1]['completed_checks'])==1
        assert detail['budget_usage']==dict(extra_checks=1,provider_calls=2)
        assert 'followup_inputs' not in detail and 'observations' not in detail
        assert 'physical_connections_m' not in json.dumps(contexts)
        assert client.post('/api/investigations',json=body).json()['id']==inv['id']
        assert client.post('/api/investigations',json=dict(body,sequence=0)).status_code==409
        assert len(contexts)==2  # API retry did not schedule another loop.
        exported=client.get(f"/api/cases/{case['id']}/export").json()
        assert exported['investigations'][0]['checks'][0]['evidence_id']==check['evidence_id']
        markdown=client.get(f"/api/cases/{case['id']}/export?format=md").text
        assert check['evidence_id'] in markdown and 'Planner round 2' in markdown


def test_duplicate_action_with_new_citation_is_blocked(monkeypatch):
    async def select(context,emit,**kwargs):
        return mock_decision(context,'REQUEST_TOPOLOGY_CHECK')
    monkeypatch.setattr(providers,'select_plan',select)
    with TestClient(app) as client:
        inv,_=start(client,snapshot(),'duplicate-check')
        detail=wait(client,inv['id'])
        assert detail['status']=='policy_rejected'
        assert len(detail['checks'])==1
        assert 'DUPLICATE_CHECK' in detail['policy']['reason']
        assert len(detail['planner_history'])==2
        assert detail['planner_history'][0]['proposal']['evidence_ids']!=detail['planner_history'][1]['proposal']['evidence_ids']


def test_three_distinct_checks_finish_without_a_fourth_execution(monkeypatch):
    actions=['REQUEST_ELECTRICAL_RECHECK','REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION','REQUEST_METER_REVIEW']
    async def select(context,emit,**kwargs):
        index=len(context['completed_checks'])
        if index==3:
            assert context['remaining_analytical_checks']==0
            assert not any(action in context['allowed_actions'] for action in actions[:3])
        return mock_decision(context,actions[index])
    monkeypatch.setattr(providers,'select_plan',select)
    with TestClient(app) as client:
        inv,_=start(client,snapshot(),'three-checks')
        detail=wait(client,inv['id'])
        assert detail['status']=='completed',detail
        assert len(detail['checks'])==3
        assert len(detail['planner_history'])==4
        assert detail['next_task']['status']=='RECOMMENDED'
        assert len({check['evidence_id'] for check in detail['checks']})==3
        assert all(item['independence']=='DERIVED_FROM_SAME_OBSERVATIONS' for item in detail['fusion']['followup_observations'])
        assert detail['checks'][2]['findings']['household_attribution']=='UNSUPPORTED'


def test_policy_enforces_check_limit_even_if_model_ignores_enum(monkeypatch):
    monkeypatch.setattr(investigations,'MAX_EXTRA_CHECKS',1)
    async def select(context,emit,**kwargs):
        return mock_decision(context,'REQUEST_ELECTRICAL_RECHECK' if not context['completed_checks'] else 'REQUEST_LOCALIZATION')
    monkeypatch.setattr(providers,'select_plan',select)
    with TestClient(app) as client:
        inv,_=start(client,snapshot(),'enforced-limit')
        detail=wait(client,inv['id'])
        assert detail['status']=='policy_rejected'
        assert len(detail['checks'])==1
        assert 'CHECK_LIMIT' in detail['policy']['reason']


def test_provider_retries_share_one_budget_across_rounds(monkeypatch):
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True),gemini=dict(configured=True)))
    calls=[];events=[]
    async def fail(provider,context):
        calls.append(provider);raise providers.ProviderUnavailable('HTTP_503')
    monkeypatch.setattr(providers,'propose',fail)
    budget=providers.new_budget();budget['max_provider_calls']=3
    emit=lambda kind,producer,body:events.append(kind)
    assert asyncio.run(providers.select_plan({},emit,budget=budget)) is None
    assert asyncio.run(providers.select_plan({},emit,budget=budget)) is None
    assert len(calls)==3 and budget['provider_calls']==3
    assert 'budget_exhausted' in events


def test_working_gemini_provider_stays_pinned_within_case(monkeypatch):
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True),gemini=dict(configured=True)))
    calls=[]
    async def propose(provider,context):
        calls.append(provider)
        if provider=='watsonx':raise providers.ProviderUnavailable('AUTH_HTTP_401')
        return dict(provider='gemini',model='mock-gemini',usage={},proposal={})
    monkeypatch.setattr(providers,'propose',propose)
    budget=providers.new_budget()
    first=asyncio.run(providers.select_plan({},lambda *args:None,budget=budget))
    asyncio.run(providers.select_plan({},lambda *args:None,budget=budget,preferred_provider=first['provider']))
    assert calls==['watsonx','gemini','gemini']


def test_expired_case_budget_never_sends_a_provider_request(monkeypatch):
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True),gemini=dict(configured=True)))
    async def forbidden(*args):pytest.fail('An expired budget must not call a provider')
    monkeypatch.setattr(providers,'propose',forbidden)
    budget=providers.new_budget();budget['deadline']=time.monotonic()-1
    assert asyncio.run(providers.select_plan({},lambda *args:None,budget=budget)) is None
    assert budget['provider_calls']==0


def test_operator_first_check_is_attributed_to_human_and_then_replanned(monkeypatch):
    contexts=[]
    async def select(context,emit,**kwargs):
        contexts.append(context)
        return mock_decision(context,'REQUEST_METER_REVIEW')
    monkeypatch.setattr(providers,'select_plan',select)
    s=snapshot()
    with TestClient(app) as client:
        response=client.post('/api/investigations',json=dict(run_id=s['run']['id'],sequence=s['seq'],
           area_id='branch-03',idempotency_key='operator-first',initial_check='REQUEST_ELECTRICAL_RECHECK'))
        assert response.status_code==200
        detail=wait(client,response.json()['id'])
        assert detail['status']=='completed'
        assert [p['provider'] for p in detail['planner_history']]==['human','watsonx']
        assert len(detail['checks'])==1 and len(contexts)==1
        assert detail['checks'][0]['evidence_id'] in contexts[0]['fusion']['evidence_ids']
        assert any(e['event_type']=='human_check_requested' and e['producer']=='analyst' for e in detail['trace'])


def test_provider_ignoring_normal_signal_enum_is_stopped_before_followup(monkeypatch):
    contexts=[]
    async def select(context,emit,**kwargs):
        contexts.append(context)
        # A bad provider ignores the advertised enum; policy must still stop it.
        return mock_decision(context,'REQUEST_ELECTRICAL_RECHECK')
    monkeypatch.setattr(providers,'select_plan',select)
    run=engine.create_run(42,'clean')
    with TestClient(app) as client:
        inv,_=start(client,engine.snapshot(run['id']),'normal-guard')
        detail=wait(client,inv['id'])
        assert contexts[0]['allowed_actions']==['ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY']
        assert detail['status']=='policy_rejected'
        assert detail['checks']==[]
        assert detail['next_task']['status']=='BLOCKED'
        assert 'NO_PERSISTENT_SIGNAL' in detail['policy']['reason']
        assert not any(e['event_type']=='tool_requested' for e in detail['trace'])


def test_operator_request_does_not_bypass_normal_signal_guard(monkeypatch):
    async def forbidden(*args,**kwargs):pytest.fail('A blocked operator check must not trigger replanning')
    monkeypatch.setattr(providers,'select_plan',forbidden)
    run=engine.create_run(42,'clean')
    with TestClient(app) as client:
        response=client.post('/api/investigations',json=dict(run_id=run['id'],sequence=0,area_id='branch-03',initial_check='REQUEST_TOPOLOGY_CHECK',idempotency_key='operator-normal-guard'))
        assert response.status_code==200
        detail=wait(client,response.json()['id'])
        assert detail['status']=='policy_rejected'
        assert detail['checks']==[] and detail['planner']['provider']=='human'
        assert 'NO_PERSISTENT_SIGNAL' in detail['policy']['reason']


def test_normal_summary_keeps_raw_rationale_separate_from_authorized_scope(monkeypatch):
    async def select(context,emit,**kwargs):
        result=mock_decision(context,'GENERATE_CASE_SUMMARY')
        result['proposal']['justification']='Run REQUEST_ELECTRICAL_RECHECK next.'
        return result
    monkeypatch.setattr(providers,'select_plan',select)
    run=engine.create_run(42,'clean')
    with TestClient(app) as client:
        inv,_=start(client,engine.snapshot(run['id']),'contradictory-rationale')
        detail=wait(client,inv['id'])
        assert detail['status']=='completed' and detail['checks']==[]
        assert detail['next_task']['authorized_scope']=='EXISTING_EVIDENCE_ONLY'
        assert 'No diagnostic check is authorized' in detail['next_task']['authorized_note']
        assert 'No diagnostic check is authorized' in detail['policy']['reason']
        assert detail['planner']['proposal']['justification']=='Run REQUEST_ELECTRICAL_RECHECK next.'
