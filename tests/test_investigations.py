import asyncio
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import engine,providers,investigations
from backend.contracts import PlannerProposal, FinanceInput
from backend.finance import calculate
from backend.main import app
from backend.workers import execute,rule_plan,validate_policy,permitted_actions


def analytical_snapshot(scenario='clean'):
    run=engine.create_run(42,scenario)
    for _ in range(3):engine.step(run)
    return engine.snapshot(run['id'])


def test_workers_missing_data_abstain_and_policy_rejects_escalation():
    snapshot=analytical_snapshot('missing_telemetry')
    workers,fusion=execute(snapshot,'branch-03',[])
    assert [w['worker'] for w in workers]==['W1','W2','W3','W4']
    assert workers[0]['status']=='INSUFFICIENT_DATA'
    assert workers[1]['findings']['residual_kwh_low'] is None
    assert fusion['diagnostic_status']=='DATA_INCOMPLETE'
    assert 'REQUEST_MISSING_DATA' in permitted_actions(workers,fusion)
    assert 'REQUEST_METER_REVIEW' not in permitted_actions(workers,fusion)
    proposal=PlannerProposal.model_validate(rule_plan('branch-03',workers,fusion))
    assert proposal.next_action=='REQUEST_MISSING_DATA'
    assert validate_policy(proposal,'branch-03',workers,fusion)['allowed']
    proposal.next_action='REQUEST_METER_REVIEW'
    assert not validate_policy(proposal,'branch-03',workers,fusion)['allowed']


def test_workers_preserve_alternatives_bounds_and_evidence_policy():
    snapshot=analytical_snapshot('visible_unmetered_load')
    workers,fusion=execute(snapshot,'branch-03',[])
    physics=workers[1]['findings']
    assert physics['technical_loss_kwh_low']<=physics['technical_loss_kwh_central']<=physics['technical_loss_kwh_high']
    assert fusion['diagnostic_status']=='UNEXPLAINED_ENERGY'
    assert len(fusion['candidates'])>=4
    assert workers[3]['findings']['candidate_area_ids']==['branch-03']
    assert workers[3]['findings']['inspection_eligible'] is False
    proposal=PlannerProposal.model_validate(rule_plan('branch-03',workers,fusion))
    proposal.evidence_ids=['invented-evidence']
    assert not validate_policy(proposal,'branch-03',workers,fusion)['allowed']
    proposal.evidence_ids=fusion['evidence_ids'];proposal.target_area_id='household-07'
    assert not validate_policy(proposal,'branch-03',workers,fusion)['allowed']


def test_w3_rejects_future_baseline_and_keeps_unavailable_billing():
    snapshot=analytical_snapshot()
    future=dict(snapshot,seq=snapshot['seq']+96)
    workers,_=execute(snapshot,'branch-03',[future]*7)
    commercial=workers[2]['findings']
    assert commercial['history_status']=='INSUFFICIENT_HISTORY'
    assert commercial['billing_mismatch_kwh'] is None
    assert commercial['collection_status']=='COLLECTION_UNKNOWN'


def test_significant_single_interval_waits_for_persistence():
    run=engine.create_run(42,'visible_unmetered_load')
    engine.step(run)
    snapshot=engine.snapshot(run['id'])
    workers,fusion=execute(snapshot,'branch-03',[])
    assert fusion['diagnostic_status']=='PERSISTENCE_PENDING'
    assert rule_plan('branch-03',workers,fusion)['next_action']=='ABSTAIN_NO_ACTION'


def test_provider_failover_uses_gemini_after_granite_failure(monkeypatch):
    calls=[];events=[]
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True),gemini=dict(configured=True)))
    async def proposal(provider,context):
        calls.append(provider)
        if provider=='watsonx':raise providers.ProviderUnavailable('AUTH_HTTP_401')
        return dict(provider='gemini',model='mock-gemini',usage={},proposal={})
    monkeypatch.setattr(providers,'propose',proposal)
    result=asyncio.run(providers.select_plan({},lambda kind,producer,body:events.append((kind,producer))))
    assert calls==['watsonx','gemini']
    assert result['provider']=='gemini'
    assert ('provider_failed','watsonx') in events


def test_double_encoded_granite_tool_arguments_keep_strict_validation():
    proposal=dict(next_action='REQUEST_MISSING_DATA',target_area_id='branch-03',evidence_ids=['ev-1'],
                  competing_causes=[],justification='Restore missing readings.',requires_human_approval=True)
    for raw in (proposal,json.dumps(proposal),json.dumps(json.dumps(proposal))):
        assert providers.parse_tool_arguments(raw).model_dump()==proposal
    for raw in (json.dumps([proposal]),json.dumps(None),json.dumps(json.dumps(json.dumps(proposal)))):
        with pytest.raises(providers.ProviderUnavailable):providers.parse_tool_arguments(raw)
    with pytest.raises(ValueError):providers.parse_tool_arguments(json.dumps(json.dumps(dict(next_action='UNREGISTERED_TOOL'))))


def test_retries_are_bounded_and_both_failures_return_rules_signal(monkeypatch):
    calls=[]
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True),gemini=dict(configured=True)))
    async def fail(provider,context):
        calls.append(provider);raise providers.ProviderUnavailable('HTTP_503')
    monkeypatch.setattr(providers,'propose',fail)
    result=asyncio.run(providers.select_plan({},lambda *args:None))
    assert result is None
    assert calls==['watsonx','watsonx','gemini','gemini']


@pytest.mark.parametrize('provider',['watsonx','gemini'])
def test_provider_wire_contract_parses_only_registered_function(monkeypatch,provider):
    proposal=dict(next_action='ABSTAIN_NO_ACTION',target_area_id='branch-03',evidence_ids=['ev-1'],
                  competing_causes=[],justification='No sufficient residual evidence.',requires_human_approval=False)
    def respond(request):
        if '/identity/token' in str(request.url):return httpx.Response(200,json=dict(access_token='dummy-test-token'))
        payload=json.loads(request.content)
        parameters=payload['tools'][0]['function']['parameters']
        assert parameters['properties']['next_action']['enum']==['ABSTAIN_NO_ACTION']
        assert payload['model'] if provider=='gemini' else payload['model_id']
        if provider=='gemini':
            assert str(request.url)=='https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
            assert payload['tool_choice']['function']['name']==providers.TOOL_NAME
            assert request.headers['Authorization']=='Bearer dummy-not-a-real-credential'
        return httpx.Response(200,json=dict(choices=[dict(message=dict(tool_calls=[dict(function=dict(name=providers.TOOL_NAME,arguments=json.dumps(proposal)))]))],usage={'completion_tokens':12}))
    original=httpx.AsyncClient
    monkeypatch.setattr(providers.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(respond)))
    for name in ['WATSONX_API_KEY','WATSONX_PROJECT_ID','GEMINI_API_KEY']:monkeypatch.setenv(name,'dummy-not-a-real-credential')
    monkeypatch.setenv('WATSONX_URL','https://unit-test.cloud.ibm.com');monkeypatch.setenv('GEMINI_MODEL_ID','mock-gemini')
    result=asyncio.run(providers.propose(provider,dict(evidence_ids=['ev-1'],allowed_actions=['ABSTAIN_NO_ACTION'])))
    assert result['proposal']==proposal
    assert 'dummy-test-token' not in json.dumps(result)


def test_finance_separates_invoice_cash_and_physical_effects():
    result=calculate(FinanceInput(action_kind='meter_correction',newly_billable_kwh=100,
                                 assumed_tariff_inr=6,assumed_collection_fraction=.5,inspection_cost_inr=400))
    assert result['invoice_value_inr']==600
    assert result['modeled_cash_inr']==300
    assert result['net_modeled_benefit_inr']==-100
    assert result['actual_bescom_savings_inr'] is None
    with pytest.raises(ValueError):calculate(FinanceInput(action_kind='meter_correction',physical_saved_kwh=10))
    with pytest.raises(ValueError):calculate(FinanceInput(newly_billable_kwh=10))


def test_real_graph_api_persists_workers_trace_and_idempotency(monkeypatch):
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=False),gemini=dict(configured=False)))
    with TestClient(app) as client:
        snapshot=client.post('/api/runs',json=dict(scenario='missing_telemetry')).json();rid=snapshot['run']['id']
        snapshot=client.post(f'/api/runs/{rid}/control',json=dict(command='step')).json()
        body=dict(run_id=rid,sequence=1,area_id='branch-03',idempotency_key='graph-test')
        response=client.post('/api/investigations',json=body)
        assert response.status_code==200
        iid=response.json()['id']
        assert client.post('/api/investigations',json=body).json()['id']==iid
        for _ in range(100):
            detail=client.get('/api/investigations/'+iid).json()
            if detail['status'] not in ('queued','planning','running'):break
            time.sleep(.02)
        assert detail['status']=='completed',detail
        assert len(detail['workers'])==4
        assert detail['planner']['provider']=='rules'
        assert detail['planner']['proposal']['next_action']=='REQUEST_MISSING_DATA'
        assert any(e['event_type']=='fallback' for e in detail['trace'])
        assert sum(e['event_type']=='tool_completed' for e in detail['trace'])==4
        assert 'observations' not in detail


def test_case_exports_include_completed_worker_and_provider_trace(monkeypatch):
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=False),gemini=dict(configured=False)))
    snapshot=analytical_snapshot('visible_unmetered_load');rid=snapshot['run']['id']
    with TestClient(app) as client:
        case=client.post('/api/cases',json=dict(alert_id=snapshot['alerts'][0]['id'],sequence=3,idempotency_key='export-worker')).json()
        inv=client.post('/api/investigations',json=dict(run_id=rid,sequence=3,area_id='branch-03',idempotency_key='export-worker')).json()
        for _ in range(100):
            detail=client.get('/api/investigations/'+inv['id']).json()
            if detail['status']=='completed':break
            time.sleep(.02)
        report=client.get(f"/api/cases/{case['id']}/export").json()
        assert report['investigations'][0]['planner']['provider']=='rules'
        assert report['investigations'][0]['trace']
        markdown=client.get(f"/api/cases/{case['id']}/export?format=md").text
        assert 'Worker investigations and planner provenance' in markdown
        assert 'Provider: rules' in markdown


def test_human_review_without_visual_mission_exports_frozen_case(monkeypatch):
    """Full operator path keeps evidence and disposition after the run advances."""
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=False),gemini=dict(configured=False)))
    snapshot=analytical_snapshot('visible_unmetered_load');rid=snapshot['run']['id']
    with TestClient(app) as client:
        inv=client.post('/api/investigations',json=dict(run_id=rid,sequence=3,area_id='branch-03',idempotency_key='human-flow')).json()
        for _ in range(100):
            result=client.get('/api/investigations/'+inv['id']).json()
            if result['status']=='completed':break
            time.sleep(.02)
        assert result['status']=='completed'
        body=dict(alert_id=snapshot['alerts'][0]['id'],sequence=3,idempotency_key='human-flow')
        case=client.post('/api/cases',json=body).json();cid=case['id']
        assert client.post('/api/cases',json=body).json()['id']==cid
        def update(actor,**values):
            nonlocal case
            response=client.patch('/api/cases/'+cid,headers={'X-Actor':actor},json=dict(expected_revision=case['revision'],**values))
            assert response.status_code==200,response.text
            case=response.json()
        update('analyst',assigned_to='Demo analyst')
        update('analyst',state='triaged')
        update('reviewer',state='under_review')
        update('reviewer',note='Meter fault remains possible; visual evidence deferred.')
        update('reviewer',state='field_check_required',reason='Verify meter calibration in the field.',disposition='inconclusive')
        frozen=client.get(f'/api/cases/{cid}/export').json()
        assert frozen['missions']==[] and frozen['evidence']==[]
        assert frozen['case']['state']=='field_check_required'
        assert frozen['case']['assigned_to']=='Demo analyst'
        assert frozen['investigations'][0]['id']==inv['id']
        assert frozen['investigations'][0]['trace']
        assert any('visual evidence deferred' in a['reason'] for a in frozen['audit'])
        client.post(f'/api/runs/{rid}/control',json=dict(command='step'))
        report=client.get(f'/api/cases/{cid}/export').json()
        assert report['case']['analysis_sequence']==3
        assert report['analysis']==frozen['analysis']
        markdown=client.get(f'/api/cases/{cid}/export?format=md')
        assert markdown.status_code==200
        assert 'Verify meter calibration in the field.' in markdown.text
        assert 'Worker investigations and planner provenance' in markdown.text
        import hashlib
        assert hashlib.sha256(markdown.content).hexdigest()==markdown.headers['X-Content-SHA256']


def test_both_configured_models_failing_still_runs_workers_and_rules(monkeypatch):
    monkeypatch.setattr(providers,'configuration',lambda:dict(watsonx=dict(configured=True),gemini=dict(configured=True)))
    async def fail(provider,context):
        raise providers.ProviderUnavailable('AUTH_HTTP_401' if provider=='watsonx' else 'HTTP_403')
    monkeypatch.setattr(providers,'propose',fail)
    with TestClient(app) as client:
        snapshot=client.post('/api/runs',json=dict(scenario='missing_telemetry')).json();rid=snapshot['run']['id']
        client.post(f'/api/runs/{rid}/control',json=dict(command='step'))
        inv=client.post('/api/investigations',json=dict(run_id=rid,area_id='branch-03',sequence=1,idempotency_key='both-models-fail')).json()
        for _ in range(100):
            result=client.get('/api/investigations/'+inv['id']).json()
            if result['status']=='completed':break
            time.sleep(.02)
        assert result['status']=='completed'
        assert len(result['workers'])==4
        assert result['planner']['provider']=='rules'
        assert result['planner']['proposal']['next_action']=='REQUEST_MISSING_DATA'
        assert result['policy']['allowed']
        assert [e['producer'] for e in result['trace'] if e['event_type']=='provider_failed']==['watsonx','gemini']
        assert any(e['event_type']=='fallback' and e['producer']=='rules' for e in result['trace'])


@pytest.mark.parametrize('scenario,steps,status',[
    ('clean',3,'WITHIN_MODEL_RANGE'),
    ('legitimate_load_change',3,'WITHIN_MODEL_RANGE'),
    ('visible_unmetered_load',1,'PERSISTENCE_PENDING'),
])
def test_no_persistent_signal_blocks_checks_independently_of_model(scenario,steps,status):
    from typing import get_args
    from backend.contracts import Action
    run=engine.create_run(42,scenario)
    for _ in range(steps):engine.step(run)
    workers,fusion=execute(engine.snapshot(run['id']),'branch-03',[])
    assert fusion['diagnostic_status']==status
    assert permitted_actions(workers,fusion)==['ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY']
    for action in get_args(Action):
        proposal=PlannerProposal.model_validate(dict(rule_plan('branch-03',workers,fusion),next_action=action))
        policy=validate_policy(proposal,'branch-03',workers,fusion)
        assert policy['allowed']==(action in ('ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY'))
        if not policy['allowed']:assert policy['reason'].startswith('NO_PERSISTENT_SIGNAL:')


def test_persistent_loss_and_bad_mapping_keep_informative_checks():
    workers,fusion=execute(analytical_snapshot('visible_unmetered_load'),'branch-03',[])
    assert fusion['diagnostic_status']=='UNEXPLAINED_ENERGY'
    for action in ['REQUEST_ELECTRICAL_RECHECK','REQUEST_METER_REVIEW','REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION']:
        assert action in permitted_actions(workers,fusion)
        proposal=PlannerProposal.model_validate(dict(rule_plan('branch-03',workers,fusion),next_action=action))
        assert validate_policy(proposal,'branch-03',workers,fusion)['allowed']
    negative=dict(fusion,diagnostic_status='REVIEW_MODEL_OR_TOPOLOGY')
    assert 'REQUEST_TOPOLOGY_CHECK' in permitted_actions(workers,negative)
    proposal=PlannerProposal.model_validate(dict(rule_plan('branch-03',workers,negative)))
    assert validate_policy(proposal,'branch-03',workers,negative)['allowed']
