"""Persisted, bounded LangGraph investigation. Model proposals never execute directly."""
import asyncio
import hashlib
import json
import time
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langsmith import tracing_context

from . import store, providers
from . import followups
from .contracts import PlannerProposal
from .workers import execute, rule_plan, validate_policy, permitted_actions

TASKS=set()
MAX_EXTRA_CHECKS=3


class State(TypedDict,total=False):
    id: str
    workers: list
    fusion: dict
    planner: dict
    policy: dict
    checks: list
    planner_history: list
    budget: dict
    pinned_provider: str


def event(inv_id,kind,producer,body,*,commit=True):
    record=dict(id=store.uid('trace'),investigation_id=inv_id,event_type=kind,producer=producer,
                wall_timestamp=store.now(),**body)
    store.put('trace',record,commit=commit)


async def analytical_node(state):
    inv=store.get(state['id'])
    snapshot=inv['observations']
    past=inv['followup_inputs']['prior_same_time']
    event(inv['id'],'started','mandatory_pipeline',dict(sequence=inv['sequence']))
    workers,fusion=execute(snapshot,inv['area_id'],past)
    for worker in workers:
        event(inv['id'],'tool_completed',worker['worker'],dict(status=worker['status'],evidence_ids=worker['evidence_ids'],elapsed_ms=worker['elapsed_ms']))
    inv.update(workers=workers,fusion=fusion,status='planning');store.put('investigation',inv)
    return dict(workers=workers,fusion=fusion,checks=[],planner_history=[],budget=providers.new_budget())


async def planner_node(state):
    inv=store.get(state['id'])
    allowed=permitted_actions(state['workers'],state['fusion'])
    if len(state['checks'])>=MAX_EXTRA_CHECKS or time.monotonic()>=state['budget']['deadline']:
        allowed=[action for action in allowed if action not in followups.LOCAL_CHECKS]
    # Suppress a repeated local action/target against identical frozen inputs.
    completed={(check['action'],check['target_area_id']) for check in state['checks']}
    local_targets={inv['area_id'],*state['workers'][3]['findings']['candidate_area_ids']}
    allowed=[action for action in allowed if action not in followups.LOCAL_CHECKS or
             any((action,target) not in completed for target in local_targets)]
    context=dict(investigation_id=inv['id'],area_id=inv['area_id'],sequence=inv['sequence'],
                 source=inv['source'],workers=state['workers'],fusion=state['fusion'],
                 allowed_actions=allowed,completed_checks=state['checks'],
                 remaining_analytical_checks=MAX_EXTRA_CHECKS-len(state['checks']),
                 remaining_provider_calls=state['budget']['max_provider_calls']-state['budget']['provider_calls'])
    context['automatic_check_catalog']={
        'REQUEST_ELECTRICAL_RECHECK':'Summarize the last up-to-16 frozen interval balances, missing intervals and persistence.',
        'REQUEST_TOPOLOGY_CHECK':'Validate the registered meter cut, graph versions and interval alignment; no field mapping verification.',
        'REQUEST_LOCALIZATION':'Calculate a fictional coverage bounding box for already-supported measured regions; no drone or exact household attribution.'}
    # No full renderer snapshot, private truth, labels, household names or hidden geometry.
    operator_check=inv.get('initial_check') if not state['planner_history'] else None
    if operator_check:
        selected=dict(provider='human',model='operator-request',usage={},proposal=dict(
            next_action=operator_check,target_area_id=inv['area_id'],evidence_ids=state['fusion']['evidence_ids'],
            competing_causes=[],justification='The operator requested this registered analytical check before automatic planning.',
            requires_human_approval=False))
        event(inv['id'],'human_check_requested',inv['requested_by'],dict(action=operator_check))
    else:
        selected=None if state.get('pinned_provider')=='rules' else await providers.select_plan(
            context,lambda kind,producer,body:event(inv['id'],kind,producer,body),
            preferred_provider=state.get('pinned_provider'),budget=state['budget'])
    if selected is None:
        proposal=rule_plan(inv['area_id'],state['workers'],state['fusion'])
        if proposal['next_action'] not in allowed:
            proposal.update(next_action='GENERATE_CASE_SUMMARY',requires_human_approval=True,
                justification='Available automatic checks are exhausted or already completed. Preserve the evidence and request human mapping or field review.')
        selected=dict(provider='rules',model='fixed-plan-1.0',usage={},
                      proposal=proposal)
        event(inv['id'],'fallback','rules',dict(reason='Fixed rule planner retained' if state.get('pinned_provider')=='rules' else 'No configured provider completed a valid tool call within the remaining budget'))
    history=[*state['planner_history'],dict(round=len(state['planner_history'])+1,
              timestamp=store.now(),**selected)]
    inv.update(planner=selected,planner_history=history,
               budget_usage=dict(extra_checks=len(state['checks']),provider_calls=state['budget']['provider_calls']))
    store.put('investigation',inv)
    update=dict(planner=selected,planner_history=history,budget=state['budget'])
    if selected['provider']!='human':update['pinned_provider']=selected['provider']
    return update


async def policy_node(state):
    inv=store.get(state['id'])
    proposal=PlannerProposal.model_validate(state['planner']['proposal'])
    policy=validate_policy(proposal,inv['area_id'],state['workers'],state['fusion'])
    if policy['allowed'] and proposal.next_action in followups.LOCAL_CHECKS:
        sig=followups.signature(proposal.next_action,proposal.target_area_id,inv)
        if any(check['signature']==sig for check in state['checks']):
            policy=dict(allowed=False,reason='DUPLICATE_CHECK: identical action, target and frozen inputs')
        elif len(state['checks'])>=MAX_EXTRA_CHECKS:
            policy=dict(allowed=False,reason='CHECK_LIMIT: maximum three analytical follow-ups')
        elif time.monotonic()>=state['budget']['deadline']:
            policy=dict(allowed=False,reason='TIME_LIMIT: shared investigation deadline reached')
    event(inv['id'],'policy_validated' if policy['allowed'] else 'policy_rejected','policy',policy)
    history=[*state['planner_history'][:-1],dict(**state['planner_history'][-1],policy=policy)]
    inv.update(policy=policy,planner_history=history);store.put('investigation',inv)
    return dict(policy=policy,planner_history=history)


def route_after_policy(state):
    if state['policy']['allowed'] and state['planner']['proposal']['next_action'] in followups.LOCAL_CHECKS:
        return 'followup'
    return 'complete'


async def followup_node(state):
    inv=store.get(state['id']);proposal=state['planner']['proposal']
    event(inv['id'],'tool_requested','workflow',dict(action=proposal['next_action'],
          target_area_id=proposal['target_area_id'],evidence_ids=proposal['evidence_ids'],check_index=len(state['checks'])+1))
    # No await between calculation and transaction: single-process database writes stay serialized.
    result=followups.execute_check(inv,proposal['next_action'],proposal['target_area_id'])
    checks=[*state['checks'],result];fusion=followups.fuse(state['fusion'],result)
    inv.update(checks=checks,fusion=fusion,status='planning',
               budget_usage=dict(extra_checks=len(checks),provider_calls=state['budget']['provider_calls']))
    try:
        store.put('followup',result,commit=False)
        store.put('investigation',inv,commit=False)
        event(inv['id'],'tool_completed',result['action'],dict(status=result['status'],
              evidence_ids=[result['evidence_id']],elapsed_ms=result['elapsed_ms'],check_index=len(checks)),commit=False)
        store.DB.commit()
    except Exception:
        store.DB.rollback();raise
    return dict(checks=checks,fusion=fusion)


async def complete_node(state):
    inv=store.get(state['id'])
    inv.update(workers=state['workers'],fusion=state['fusion'],planner=state['planner'],policy=state['policy'],
               checks=state['checks'],planner_history=state['planner_history'],
               budget_usage=dict(extra_checks=len(state['checks']),provider_calls=state['budget']['provider_calls']),
               status='completed' if state['policy']['allowed'] else 'policy_rejected',completed_at=store.now())
    proposal=state['planner']['proposal']
    # Terminal actions remain recommendations; no field check is marked completed.
    inv['next_task']=dict(action=proposal['next_action'],status='RECOMMENDED' if state['policy']['allowed'] else 'BLOCKED',
                          requires_human_review=proposal['next_action']!='ABSTAIN_NO_ACTION')
    if state['policy']['allowed'] and state['fusion']['diagnostic_status'] in ('WITHIN_MODEL_RANGE','PERSISTENCE_PENDING'):
        inv['next_task'].update(authorized_scope='EXISTING_EVIDENCE_ONLY',authorized_note='No diagnostic check is authorized. Abstain or summarize the existing evidence; any additional checks mentioned in model rationale are not approved.')
    inv['completion_reason']=('POLICY_STOP: '+state['policy']['reason'] if not state['policy']['allowed'] else
                              'NO_FURTHER_ACTION' if proposal['next_action']=='ABSTAIN_NO_ACTION' else 'HUMAN_REVIEW_REQUIRED')
    store.put('investigation',inv)
    event(inv['id'],inv['status'],'workflow',dict(evidence_ids=state['fusion']['evidence_ids']))
    return {}


graph=StateGraph(State)
graph.add_node('workers',analytical_node)
graph.add_node('planner',planner_node)
graph.add_node('policy',policy_node)
graph.add_node('followup',followup_node)
graph.add_node('complete',complete_node)
graph.add_edge(START,'workers');graph.add_edge('workers','planner');graph.add_edge('planner','policy')
graph.add_conditional_edges('policy',route_after_policy,{'followup':'followup','complete':'complete'})
graph.add_edge('followup','planner');graph.add_edge('complete',END)
WORKFLOW=graph.compile()


async def process(inv_id):
    try:
        with tracing_context(enabled=False):
            await WORKFLOW.ainvoke(dict(id=inv_id),config={'recursion_limit':20})
    except asyncio.CancelledError:
        inv=store.get(inv_id);inv.update(status='interrupted',error='Application stopped; retry explicitly');store.put('investigation',inv)
        raise
    except Exception as exc:
        inv=store.get(inv_id);inv.update(status='failed',error=type(exc).__name__);store.put('investigation',inv)
        event(inv_id,'failed','workflow',dict(reason=type(exc).__name__))


def schedule(inv_id):
    task=asyncio.create_task(process(inv_id));TASKS.add(task);task.add_done_callback(TASKS.discard)


def create(body,snapshot,actor='analyst'):
    key=f'{body.run_id}:{body.idempotency_key}'
    for inv in store.all_of('investigation'):
        if inv['dedup_key']==key:
            if inv['area_id']!=body.area_id or inv['sequence']!=body.sequence or inv.get('initial_check')!=body.initial_check:
                raise ValueError('Idempotency key already belongs to another area or interval')
            return inv
    observations={k:snapshot[k] for k in ('run','seq','readings','balances','alerts')}
    keys=('seq','readings','balances','alerts')
    window=[{k:frame[k] for k in keys} for seq in range(max(0,body.sequence-15),body.sequence+1)
            if (frame:=store.interval(body.run_id,seq)) is not None]
    prior=[{k:frame[k] for k in keys} for d in range(1,8) if body.sequence-96*d>=0
           and (frame:=store.interval(body.run_id,body.sequence-96*d)) is not None]
    inv=dict(id=store.uid('investigation'),dedup_key=key,run_id=body.run_id,area_id=body.area_id,
             initial_check=body.initial_check,requested_by=actor,
             sequence=body.sequence,source=snapshot['run'].get('source',{}),observations=observations,
             followup_inputs=dict(window=window,prior_same_time=prior),
             limits=dict(max_extra_checks=MAX_EXTRA_CHECKS,max_provider_calls=6,case_timeout_seconds=60),
             checks=[],planner_history=[],budget_usage=dict(extra_checks=0,provider_calls=0),
             status='queued',workers=[],fusion=None,planner=None,policy=None,created_at=store.now())
    store.put('investigation',inv);event(inv['id'],'queued','workflow',dict(sequence=body.sequence))
    schedule(inv['id'])
    return inv


def public(inv):
    return {k:v for k,v in inv.items() if k not in ('observations','followup_inputs','dedup_key')}


def trace(inv_id):
    return sorted((e for e in store.all_of('trace') if e['investigation_id']==inv_id),key=lambda e:e['wall_timestamp'])
