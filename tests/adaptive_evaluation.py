"""Held-out synthetic full-workflow evaluation, with pinned providers and no failover.

Runs the production graph and persistence, not a recreated planner loop. Mechanisms
and scoring stay outside provider context. This is internal validation, not a blind
external study. Uses a disposable database; never touches the operator's cases.
"""
import argparse
import atexit
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_DATABASE = tempfile.TemporaryDirectory(prefix='gridtrace-b2-')
os.environ['GRIDTRACE_DATA'] = _DATABASE.name
from benchmark_independent import observed_case
from backend import investigations, providers, store
from backend.analytics import reconcile, detect
from backend.benchmark import fingerprint
from backend.main import InvestigationInput
from backend.topology import ASSETS
atexit.register(store.DB.close)

SEED = 2026102504  # Distinct from both the diagnostic suite and first-action pilot.
MECHANISMS = ('clean', 'demand_change', 'missing', 'mapping', 'extra_load',
              'underregistration', 'technical_loss', 'authorized_unmetered', 'weak_load')
TERMINAL = {
    'WITHIN_MODEL_RANGE': {'ABSTAIN_NO_ACTION', 'GENERATE_CASE_SUMMARY'},
    'PERSISTENCE_PENDING': {'ABSTAIN_NO_ACTION', 'GENERATE_CASE_SUMMARY'},
    'DATA_INCOMPLETE': {'REQUEST_MISSING_DATA', 'REQUEST_TOPOLOGY_CHECK', 'GENERATE_CASE_SUMMARY'},
    'REVIEW_MODEL_OR_TOPOLOGY': {'REQUEST_METER_REVIEW', 'GENERATE_CASE_SUMMARY'},
    'UNEXPLAINED_ENERGY': {'REQUEST_METER_REVIEW', 'GENERATE_CASE_SUMMARY'},
}
PROTOCOL = dict(version='adaptive-heldout-1', seed=SEED, cases=18,
    max_checks=3, max_provider_calls=6, case_timeout_seconds=60,
    failover=False, early_stop_after_consecutive_provider_failures=2,
    terminal_rubric={k: sorted(v) for k, v in TERMINAL.items()},
    success_definition='Completed without policy rejection or provider failure; terminal action matches the predeclared observation-status rubric; checks bounded, unique and evidence-grounded. No mandatory number of checks: immediate human handoff can be appropriate.',
    heldout_definition='New seed, target assignments, 6-16 interval windows, demand multipliers and meter noise. Same nine mechanism families as prior work; not unseen mechanism families or independently blinded data.')


def make_cases():
    rng = random.Random(SEED)
    baseline = {a['id']: [.4]*96 for a in ASSETS if a['kind']=='household'}
    cases = []
    for index in range(PROTOCOL['cases']):
        mechanism = MECHANISMS[index % len(MECHANISMS)]
        target = f'branch-{rng.randint(1,8):02}'
        alerts = []; streaks = {}; frames = []
        intervals = rng.randint(6,16)
        scale = rng.uniform(.7,1.4)
        for seq in range(intervals):
            readings = observed_case(rng, seq, target, mechanism)
            for reading in readings.values():
                if reading['energy_import_kwh'] is not None:
                    reading['energy_import_kwh'] *= scale * rng.uniform(.998,1.002)
            balances = reconcile(f'heldout-{index+1:02}', seq, readings)
            alerts, _, streaks = detect(f'heldout-{index+1:02}',seq,balances,readings,alerts,streaks,baseline)
            frames.append(dict(seq=seq,readings=readings,balances=balances,alerts=alerts))
        source = dict(source_kind='SYNTHETIC_CHALLENGE')
        snapshot = dict(run=dict(id=f'heldout-{index+1:02}',source=source),**frames[-1])
        digest = hashlib.sha256(json.dumps(dict(snapshot=snapshot,window=frames),sort_keys=True,allow_nan=False).encode()).hexdigest()
        cases.append(dict(id=f'heldout-{index+1:02}',mechanism=mechanism,target=target,
                          snapshot=snapshot,frames=frames,input_hash=digest))
    return cases


async def run_case(case, provider, model):
    for frame in case['frames']:
        store.DB.execute('INSERT OR REPLACE INTO intervals VALUES(?,?,?)',
                         (case['id'],frame['seq'],json.dumps(frame)))
    store.DB.commit()
    body = InvestigationInput(run_id=case['id'],sequence=case['snapshot']['seq'],
                             area_id=case['target'],idempotency_key=provider)
    attempts = []; contexts = []
    async def pinned(context,emit,*,budget,**kwargs):
        # Execute production retry/budget logic, while excluding other providers.
        contexts.append(json.loads(json.dumps(context)))
        if provider=='rules': return None
        original_config = providers.configuration
        def config():
            return {key:dict(value,configured=value['configured'] and key==provider)
                    for key,value in original_config().items()}
        def log(kind,producer,body):
            attempts.append(dict(event=kind,provider=producer,**body));emit(kind,producer,body)
        with patch.object(providers,'configuration',config):
            result = await original_select(context,log,preferred_provider=provider,budget=budget)
        if result is None: raise providers.ProviderUnavailable('PINNED_PROVIDER_FAILED_NO_FALLBACK')
        if result['provider']!=provider or result['model']!=model:
            raise providers.ProviderUnavailable('PINNED_PROVIDER_CHANGED')
        return result
    original_select = providers.select_plan
    started = time.perf_counter()
    with patch.object(investigations,'schedule',lambda _:None):
        inv = investigations.create(body,case['snapshot'],'evaluation')
    failure = None
    try:
        with patch.object(providers,'select_plan',pinned):
            from langsmith import tracing_context
            with tracing_context(enabled=False):
                await asyncio.wait_for(investigations.WORKFLOW.ainvoke(dict(id=inv['id']),config={'recursion_limit':20}),65)
    except (providers.ProviderUnavailable,asyncio.TimeoutError) as exc:
        failure = str(exc) if isinstance(exc,providers.ProviderUnavailable) else 'WORKFLOW_TIMEOUT'
    detail = store.get(inv['id'])
    checks = detail.get('checks',[]); history = detail.get('planner_history',[])
    fusion = detail.get('fusion') or {}; status = fusion.get('diagnostic_status')
    # Verify each model round only cites evidence available before that round.
    original_ids = {eid for w in detail.get('workers',[]) for eid in w['evidence_ids']}
    references_valid = all(set(h['proposal']['evidence_ids']) <=
        (original_ids | {c['evidence_id'] for c in checks[:i]}) for i,h in enumerate(history))
    checks_safe = len(checks)<=3 and len({c['signature'] for c in checks})==len(checks)
    grounded_replans = sum(bool(set(h['proposal']['evidence_ids']) & {c['evidence_id'] for c in contexts[i]['completed_checks']})
                          for i,h in enumerate(history) if i<len(contexts) and contexts[i]['completed_checks'])
    normal_safe = status not in ('WITHIN_MODEL_RANGE','PERSISTENCE_PENDING') or not checks
    terminal = detail.get('planner',{}).get('proposal',{}).get('next_action')
    matched = terminal in TERMINAL.get(status,set())
    completed = failure is None and detail['status']=='completed'
    usage = [h.get('usage',{}) for h in history]
    return dict(id=case['id'],mechanism=case['mechanism'],target=case['target'],input_hash=case['input_hash'],
        provider=provider,model=model,status='FAILED' if failure else detail['status'].upper(),reason=failure,
        diagnostic_status=status,terminal_action=terminal,terminal_rubric_match=matched,
        successful=completed and matched and checks_safe and references_valid and normal_safe,
        bounded_unique_checks=checks_safe,evidence_references_valid=references_valid,normal_signal_safe=normal_safe,
        executed_checks=len(checks),planner_rounds=len(history),replans_citing_derived_evidence=grounded_replans,
        elapsed_seconds=round(time.perf_counter()-started,3),
        prompt_tokens=sum(u.get('prompt_tokens',0) for u in usage),
        completion_tokens=sum(u.get('completion_tokens',0) for u in usage),
        provider_attempts=attempts,checks=checks,planner_history=history,
        trace=investigations.trace(inv['id']))


def summarize(rows):
    return dict(total_cases=len(rows),completed_cases=sum(r['status']=='COMPLETED' for r in rows),
        successful_cases=sum(r.get('successful',False) for r in rows),
        failed_cases=sum(r['status']=='FAILED' for r in rows),skipped_cases=sum(r['status']=='SKIPPED' for r in rows),
        policy_rejected_cases=sum(r['status']=='POLICY_REJECTED' for r in rows),
        cases_executing_checks=sum(r.get('executed_checks',0)>0 for r in rows),
        executed_checks=sum(r.get('executed_checks',0) for r in rows),
        replans_citing_derived_evidence=sum(r.get('replans_citing_derived_evidence',0) for r in rows),
        elapsed_seconds=round(sum(r.get('elapsed_seconds',0) for r in rows),3),
        prompt_tokens=sum(r.get('prompt_tokens',0) for r in rows),completion_tokens=sum(r.get('completion_tokens',0) for r in rows))


async def evaluate(provider):
    frozen = fingerprint(); cases = make_cases(); config = providers.configuration()
    if provider!='rules' and not config[provider]['configured']: raise SystemExit('Pinned provider not configured')
    report = dict(status='RUNNING',code_hash=frozen,generated_at=datetime.now(timezone.utc).isoformat(),
        protocol=PROTOCOL,case_manifest=[{k:c[k] for k in ('id','mechanism','target','input_hash')} for c in cases],
        provider=provider,model=config.get(provider,{}).get('model','fixed-plan-1.0'),
        disclosure='Internal held-out synthetic full-workflow evaluation. Truth labels are scored outside the planner. Same known mechanism families and topology; no field accuracy, causal identification, savings, independent blinding or model superiority is established.',
        policies={},cases=[])
    output = ROOT/'docs'/('adaptive-results.json' if provider!='rules' else 'adaptive-rules-results.json')
    def save():
        report['policies']={p:summarize([r for r in report['cases'] if r['provider']==p]) for p in ('rules',provider)}
        temporary = output.with_suffix('.tmp'); temporary.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
        for attempt in range(6):
            try:
                temporary.replace(output);break
            except PermissionError:
                if attempt==5:raise
                time.sleep(.1*(attempt+1))
    save()  # Protocol and entire generated case set are frozen before requests.
    for policy in dict.fromkeys(('rules',provider)):
        failures=0;model=config.get(policy,{}).get('model','fixed-plan-1.0')
        for case in cases:
            if failures>=2:
                row=dict(id=case['id'],provider=policy,model=model,input_hash=case['input_hash'],
                         mechanism=case['mechanism'],status='SKIPPED',reason='Two consecutive provider failures; denominator retained')
            else:
                row=await run_case(case,policy,model)
                failures=failures+1 if row['status']=='FAILED' else 0
            report['cases'].append(row);save()
            print(json.dumps({k:row.get(k) for k in ('id','provider','status','terminal_action','executed_checks','successful','reason')}),flush=True)
    report['status']='COMPLETED' if fingerprint()==frozen else 'STALE';save()
    print(json.dumps(dict(status=report['status'],policies=report['policies'])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',choices=['rules','watsonx'],default='rules')
    args=parser.parse_args();asyncio.run(evaluate(args.provider))
