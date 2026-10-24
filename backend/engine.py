import statistics,time,logging
from . import store
from .simulation import generate,stamp
from .analytics import reconcile,detect,RULE_VERSION
from .topology import ASSETS,CONNECTIONS,VERSION,CHILDREN

def create_run(seed=42,scenario='clean'):
    rid=store.uid('run'); baseline={a['id']:[[] for _ in range(96)] for a in ASSETS if a['kind']=='household'}; residuals={}
    # Seven clean days per independently seeded run, not copied from scenario truth.
    for seq in range(-672,0):
        obs=generate(seed,seq,[])['readings']
        for hid,slots in baseline.items(): slots[seq%96].append(obs[hid]['energy_import_kwh'])
        for b in reconcile(rid,seq,obs): residuals.setdefault(b['boundary_asset_id'],[]).append(b['residual_kwh'])
    sigma={k:max(.015,statistics.stdev(v)) for k,v in residuals.items()}
    means={k:[statistics.mean(slot) for slot in slots] for k,slots in baseline.items()}
    inc=[] if scenario=='clean' else [dict(type=scenario,target_asset_id='branch-03',start=1,end=80,severity=.85 if scenario=='meter_underregistration' else 1.2)]
    run=dict(id=rid,seed=seed,seq=-1,event_seq=0,playing=False,speed=10,scenario_settings=inc,topology_version=VERSION,rule_version=RULE_VERSION,created_at=store.now(),baseline=means,sigmas=sigma,streaks={},meter_streaks={},provenance='synthetic')
    store.put('run',run); step(run); return store.get(rid)

def step(run):
    seq=run['seq']+1
    if seq>=96: run['playing']=False; store.put('run',run); return
    started=time.perf_counter(); generated=generate(run['seed'],seq,run['scenario_settings']); obs=generated['readings']
    for r in obs.values(): r['run_id']=run['id']
    balances=reconcile(run['id'],seq,obs,run['sigmas']); previous=store.interval(run['id'],seq-1)
    alerts,quality,streaks=detect(run['id'],seq,balances,obs,previous['alerts'] if previous else [],run['streaks'],run['baseline'])
    for hid in run['baseline']:
        r=obs[hid]; low=r['quality']=='valid' and r['energy_import_kwh'] is not None and run['baseline'][hid][seq%96]>=.15 and r['energy_import_kwh']<.5*run['baseline'][hid][seq%96]
        run['meter_streaks'][hid]=run['meter_streaks'].get(hid,0)+1 if low else 0
    for a in alerts:
        a['candidate_meter_ids']=[m for m in a['candidate_meter_ids'] if run['meter_streaks'].get(m.removeprefix('meter-'),0)>=3]
    body=dict(seq=seq,simulation_time=stamp(seq+1),readings=obs,balances=balances,alerts=alerts,quality_events=quality,physical_connections_m=generated['geometry'],physical_occluders=generated['occluders'])
    store.save_interval(run['id'],seq,body,generated['truth'])
    run.update(seq=seq,event_seq=run['event_seq']+1,streaks=streaks); store.put('run',run)
    logging.info('run=%s seq=%d duration_ms=%.2f rule=%s',run['id'],seq,(time.perf_counter()-started)*1000,RULE_VERSION)

def snapshot(rid,seq=None):
    run=store.get(rid); interval=store.interval(rid,run['seq'] if seq is None else seq)
    history=[]
    for i in range(max(0,interval['seq']-23),interval['seq']+1):
        row=store.interval(rid,i); history.append(dict(seq=i,balances=row['balances']))
    public={k:v for k,v in run.items() if k not in ('scenario_settings','baseline','sigmas','streaks','meter_streaks')}
    return dict(run=public,assets=ASSETS,connections=CONNECTIONS,**interval,history=history,wall_time=store.now(),schema_version='1.0')

def revise_reading(run,seq,asset_id,value,quality,actor):
    """Recompute from stored observations only, preserving every prior analysis."""
    run['analysis_revision']=run.get('analysis_revision',1)+1
    revision=run['analysis_revision'];previous=[];streaks={};meter_streaks={}
    for i in range(run['seq']+1):
        observed=store.interval(run['id'],i)
        archived=dict(id=f"{run['id']}-sequence-{i}-revision-{observed.get('analysis_revision',1)}",**observed)
        store.put('analysis-revision',archived)
        if i==seq:
            r=observed['readings'][asset_id];r['energy_import_kwh']=value;r['quality']=quality;r['revision']+=1;r['received_at']=store.now()
        balances=reconcile(run['id'],i,observed['readings'],run['sigmas'])
        for b in balances:b['id']+=f'-r{revision}';b['analysis_revision']=revision
        alerts,quality_events,streaks=detect(run['id'],i,balances,observed['readings'],previous,streaks,run['baseline'])
        for hid in run['baseline']:
            r=observed['readings'][hid];baseline=run['baseline'][hid][i%96]
            low=baseline>=.15 and r['quality']=='valid' and r['energy_import_kwh'] is not None and r['energy_import_kwh']<.5*baseline
            meter_streaks[hid]=meter_streaks.get(hid,0)+1 if low else 0
        for a in alerts:
            a['balance_ids']=[f"balance-{run['id']}-{k}-{a['boundary_asset_id']}-r{revision}" for k in range(a['first_interval'],a['last_interval']+1)]
            a['candidate_meter_ids']=[m for m in a['candidate_meter_ids'] if meter_streaks.get(m.removeprefix('meter-'),0)>=3]
        observed.update(balances=balances,alerts=alerts,quality_events=quality_events,analysis_revision=revision)
        store.DB.execute('UPDATE intervals SET body=? WHERE run_id=? AND seq=?',(__import__('json').dumps(observed,allow_nan=False),run['id'],i))
        previous=alerts
    run['streaks']=streaks;run['meter_streaks']=meter_streaks;run['event_seq']+=1
    store.put('run',run)
    store.put('recomputation',dict(id=store.uid('recompute'),run_id=run['id'],sequence=seq,asset_id=asset_id,actor=actor,analysis_revision=revision,wall_timestamp=store.now(),simulation_timestamp=stamp(run['seq']+1),reason='Explicit later observed reading revision; previous analyses retained'))
