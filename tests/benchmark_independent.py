"""Standalone evaluator: independent forward equations; no simulator imports.

Truth is created/scored here and is never supplied to workers or planners.
This modest diagnostic suite is not a field validation or full blind team study.
"""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import random
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.analytics import reconcile,detect
from backend.topology import ASSETS,CHILDREN,SECTIONS,VERSION
from backend.workers import execute
from backend.benchmark import fingerprint


def observed_case(rng,seq,target,mechanism):
    physical={a['id']:rng.uniform(.25,.65) for a in ASSETS if a['kind']=='household'}
    if mechanism=='demand_change':physical[CHILDREN[target][0]]*=2
    for boundary in reversed(SECTIONS):
        sid=boundary['id'];out=sum(physical[c] for c in CHILDREN[sid])
        # Independent linear loss law, deliberately different from detector quadratic.
        loss=.025+.018*out
        added=(rng.uniform(.7,1.5) if mechanism in ('extra_load','authorized_unmetered') else
               .08 if mechanism=='weak_load' else .8 if mechanism=='technical_loss' else 0) if sid==target else 0
        physical[sid]=out+loss+added
    start=datetime(2022,9,10,tzinfo=timezone(timedelta(hours=5,minutes=30)))+timedelta(minutes=15*seq)
    readings={}
    for asset in ASSETS:
        if not asset['meter_id']:continue
        aid=asset['id'];value=physical[aid]*rng.uniform(.997,1.003);quality='valid';topology=VERSION
        if aid==CHILDREN[target][0]:
            if mechanism=='missing':value=None;quality='missing'
            if mechanism=='underregistration':value*=.1
            if mechanism=='mapping':topology='unverified-mapping'
        readings[aid]=dict(asset_id=aid,meter_id=asset['meter_id'],energy_import_kwh=value,
                           energy_export_kwh=0,quality=quality,topology_version=topology,
                           interval_start=start.isoformat(),interval_end=(start+timedelta(minutes=15)).isoformat())
    return readings


def evaluate():
    frozen=fingerprint();rng=random.Random(20221025);rows=[]
    mechanisms=['clean','demand_change','missing','mapping','extra_load','underregistration','technical_loss','authorized_unmetered','weak_load']
    baseline={a['id']:[.4]*96 for a in ASSETS if a['kind']=='household'}
    for index in range(36):
        mechanism=mechanisms[index%len(mechanisms)];target=f'branch-{rng.randint(1,8):02}'
        alerts=[];streaks={}
        for seq in range(3):
            readings=observed_case(rng,seq,target,mechanism)
            balances=reconcile(f'challenge-{index}',seq,readings)
            alerts,_,streaks=detect(f'challenge-{index}',seq,balances,readings,alerts,streaks,baseline)
        snapshot=dict(run=dict(id=f'challenge-{index}',source=dict(source_kind='SYNTHETIC_CHALLENGE')),
                      seq=seq,readings=readings,balances=balances,alerts=alerts)
        workers,fusion=execute(snapshot,target,[])
        balance=next(b for b in balances if b['boundary_asset_id']==target)
        b0=balance['input_kwh'] is not None and balance['output_sum_kwh'] is not None and balance['input_kwh']-balance['output_sum_kwh']>.25
        b1=fusion['diagnostic_status']=='UNEXPLAINED_ENERGY'
        eligible=mechanism in ('extra_load','underregistration','technical_loss','authorized_unmetered','weak_load')
        rows.append(dict(id=f'case-{index+1:02}',mechanism=mechanism,target=target,
                         eligible_event=eligible,b0=b0,b1=b1,valid=balance['validity']=='valid'))
    def score(policy):
        eligible=sum(r['eligible_event'] for r in rows)
        matched=sum(r['eligible_event'] and r[policy] for r in rows)
        false=sum(not r['eligible_event'] and r[policy] for r in rows)
        clean_hours=sum(not r['eligible_event'] and r['valid'] for r in rows)*.75
        return dict(status='COMPLETED',metrics=dict(matched_events=matched,eligible_events=eligible,
                    eligible_event_recall=matched/eligible,false_alerts=false,
                    valid_control_branch_hours=clean_hours,false_alerts_per_100_control_hours=false/clean_hours*100))
    assert fingerprint()==frozen,'Candidate changed during evaluation'
    report=dict(status='COMPLETED',code_hash=frozen,generated_at=datetime.now(timezone.utc).isoformat(),
                disclosure='36 independently constructed synthetic diagnostic cases; includes weak events and parameter mismatch. This is not a blinded external team study, a rendered CV test or field accuracy. Authorized unmetered loads count as unexplained accounting events, not wrongdoing.',
                policies=dict(B0=score('b0'),B1=score('b1'),B2=dict(status='NOT_RUN: requires a separately configured and pinned live planner provider')),
                cases=rows)
    output=Path(__file__).resolve().parents[1]/'docs'/'independent-results.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(code_hash=frozen,policies=report['policies']),indent=2))


if __name__=='__main__':evaluate()
