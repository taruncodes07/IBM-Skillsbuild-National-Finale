"""Small first-action pilot, separate from the unrun full B2 study.

One request per case, pinned provider, no failover, no tool execution.
Truth and the scoring rubric never enter the provider context.
"""
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmark_independent import observed_case
from backend.analytics import reconcile,detect
from backend.topology import ASSETS
from backend.workers import execute,rule_plan,permitted_actions,validate_policy
from backend.contracts import PlannerProposal
from backend import providers
from backend.benchmark import fingerprint

ROOT=Path(__file__).resolve().parents[1]
MECHANISMS=['clean','demand_change','missing','mapping','extra_load','underregistration','technical_loss','authorized_unmetered','weak_load']
RUBRIC_VERSION='first-action-pilot-1'
RUBRIC={
    'DATA_INCOMPLETE':['REQUEST_MISSING_DATA','REQUEST_TOPOLOGY_CHECK'],
    'UNEXPLAINED_ENERGY':['REQUEST_ELECTRICAL_RECHECK','REQUEST_METER_REVIEW','REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION','GENERATE_CASE_SUMMARY'],
    'REVIEW_MODEL_OR_TOPOLOGY':['REQUEST_TOPOLOGY_CHECK','REQUEST_ELECTRICAL_RECHECK'],
    'PERSISTENCE_PENDING':['ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY'],
    'WITHIN_MODEL_RANGE':['ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY'],
}


def make_cases(count=9):
    if not 1<=count<=9:raise ValueError('Pilot is limited to nine cases')
    rng=random.Random(20221117)
    baseline={a['id']:[.4]*96 for a in ASSETS if a['kind']=='household'}
    cases=[]
    for i,mechanism in enumerate(MECHANISMS[:count]):
        target=f'branch-{rng.randint(1,8):02}'
        alerts=[];streaks={}
        for seq in range(3):
            readings=observed_case(rng,seq,target,mechanism)
            balances=reconcile(f'pilot-{i+1:02}',seq,readings)
            alerts,_,streaks=detect(f'pilot-{i+1:02}',seq,balances,readings,alerts,streaks,baseline)
        snapshot=dict(run=dict(id=f'pilot-{i+1:02}',source=dict(source_kind='SYNTHETIC_CHALLENGE')),seq=seq,readings=readings,balances=balances,alerts=alerts)
        workers,fusion=execute(snapshot,target,[])
        # Timings are not evidence and must not change the frozen input hash.
        summaries=[{k:v for k,v in w.items() if k!='elapsed_ms'} for w in workers]
        context=dict(area_id=target,sequence=seq,source=dict(source_kind='SYNTHETIC_CHALLENGE'),workers=summaries,fusion=fusion,allowed_actions=permitted_actions(workers,fusion),completed_checks=[],decision_budget=1,
                     evaluation_scope='Choose one next action only. No check will execute in this pilot. The available local checks are electrical-window summary, registered-topology validation and measured-area localization. External checks remain human tasks.')
        digest=hashlib.sha256(json.dumps(context,sort_keys=True,allow_nan=False).encode()).hexdigest()
        cases.append(dict(id=f'pilot-{i+1:02}',mechanism=mechanism,target=target,input_hash=digest,context=context,workers=workers,fusion=fusion))
    return cases


def score_proposal(case,raw):
    proposal=PlannerProposal.model_validate(raw)
    policy=validate_policy(proposal,case['target'],case['workers'],case['fusion'])
    expected=RUBRIC[case['fusion']['diagnostic_status']]
    return dict(policy_allowed=policy['allowed'],policy_reason=policy['reason'],
                rubric_match=policy['allowed'] and proposal.next_action in expected,
                acceptable_actions=expected,proposal=proposal.model_dump())


def summarize(rows):
    completed=[r for r in rows if r['status']=='COMPLETED']
    return dict(total_cases=len(rows),completed_cases=len(completed),failed_cases=sum(r['status']=='FAILED' for r in rows),skipped_cases=sum(r['status']=='SKIPPED' for r in rows),
                policy_allowed_cases=sum(r.get('policy_allowed',False) for r in rows),rubric_matches=sum(r.get('rubric_match',False) for r in rows),
                rules_rubric_matches=sum(r['rules']['rubric_match'] for r in rows),
                elapsed_seconds=round(sum(r.get('elapsed_seconds',0) for r in rows),3),
                prompt_tokens=sum(r.get('usage',{}).get('prompt_tokens',0) for r in rows),completion_tokens=sum(r.get('usage',{}).get('completion_tokens',0) for r in rows))


async def evaluate(provider,count):
    frozen=fingerprint();rows=[];consecutive_failures=0
    cases=make_cases(count)
    config=providers.configuration().get(provider,{})
    model=config.get('model','fixed-plan-1.0')
    if provider!='rules' and not config.get('configured'):raise SystemExit('Selected provider is not configured')
    output=ROOT/'docs'/'planner-pilot-results.json'
    report=dict(status='RUNNING',code_hash=frozen,provider=provider,model=model,rubric_version=RUBRIC_VERSION,rubric=RUBRIC,
                generated_at=datetime.now(timezone.utc).isoformat(),seed=20221117,
                protocol=dict(cases=count,max_requests_per_case=1,timeout_seconds=25,failover=False,tools_executed=0,early_stop_after_consecutive_failures=2),
                disclosure='Small synthetic first-action pilot with a predeclared observation-based rubric. Same worker evidence and rubric are used for the rules comparison. This is not the full adaptive B2 study, an independent blinded study, a causal diagnosis score or field accuracy. Rubric matches do not measure intervention savings or superiority.',cases=rows)
    def save():
        report['summary']=summarize(rows)
        temporary=output.with_suffix('.tmp')
        temporary.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8');temporary.replace(output)
    save()
    for case in cases:
        rules=score_proposal(case,rule_plan(case['target'],case['workers'],case['fusion']))
        row=dict(id=case['id'],mechanism=case['mechanism'],target=case['target'],input_hash=case['input_hash'],diagnostic_status=case['fusion']['diagnostic_status'],rules=rules,status='SKIPPED',usage={})
        if consecutive_failures>=2:row['reason']='Stopped after two consecutive provider failures; denominator retained'
        else:
            started=time.perf_counter()
            try:
                result=dict(provider='rules',model='fixed-plan-1.0',usage={},proposal=rules['proposal']) if provider=='rules' else await asyncio.wait_for(providers.propose(provider,case['context']),timeout=25)
                if result['provider']!=provider or result['model']!=model:raise providers.ProviderUnavailable('PINNED_PROVIDER_CHANGED')
                row.update(status='COMPLETED',**score_proposal(case,result['proposal']),usage=result['usage'])
                consecutive_failures=0
            except (providers.ProviderUnavailable,ValueError,KeyError,IndexError,asyncio.TimeoutError,providers.httpx.HTTPError) as exc:
                row.update(status='FAILED',reason=str(exc) if isinstance(exc,providers.ProviderUnavailable) else type(exc).__name__)
                consecutive_failures+=1
            row['elapsed_seconds']=round(time.perf_counter()-started,3)
        rows.append(row);save()
        print(json.dumps(dict(case=row['id'],status=row['status'],action=row.get('proposal',{}).get('next_action'),rubric_match=row.get('rubric_match'),reason=row.get('reason'))),flush=True)
    report['status']='COMPLETED' if fingerprint()==frozen else 'STALE'
    save();print(json.dumps(dict(status=report['status'],provider=provider,summary=report['summary'])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider',choices=['rules','watsonx','gemini'],default='rules')
    parser.add_argument('--cases',type=int,choices=range(1,10),default=9)
    args=parser.parse_args();asyncio.run(evaluate(args.provider,args.cases))
