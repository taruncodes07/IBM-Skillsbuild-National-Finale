"""Private physical simulation. Analytics receives only generate()['readings']."""
import random, math
from datetime import datetime,timedelta,timezone
from .topology import ASSETS, SECTIONS, CHILDREN, BY_ID, VERSION
from .analytics import COEFFICIENTS

START=datetime(2022,8,31,18,30,tzinfo=timezone.utc)  # 1 September 2022 00:00 IST

# Scenario G (PRD section 7): hold the APPARENT imbalance comparable while varying evidence
# quality, so the recommended next check must follow the observed evidence rather than the
# scenario name. Each variant injects the same 1.2 kWh excess on the same branch; only the
# accompanying observation defect differs.
MATCHED_RESIDUAL_SEVERITY=1.2
MATCHED_RESIDUAL_TARGET='branch-03'
# variant -> (primary excess mechanism, accompanying observation defect)
# 'model_shift' carries no unmetered load at all: an elevated technical loss alone produces a
# comparable apparent excess from an entirely different cause, which is the point of the test.
MATCHED_RESIDUAL={
    'matched_residual_complete':('visible_unmetered_load',None),
    'matched_residual_incomplete':('visible_unmetered_load','missing_telemetry'),
    'matched_residual_stale_mapping':('visible_unmetered_load','topology_mismatch'),
    'matched_residual_model_shift':('technical_loss_change',None),
}

SCENARIOS=['clean','visible_unmetered_load','missing_telemetry','legitimate_load_change',
           'meter_underregistration','hidden_bypass','technical_loss_change','topology_mismatch',
           'occlusion',*MATCHED_RESIDUAL]


def matched_residual_incidents(scenario,start=1,end=80,target=MATCHED_RESIDUAL_TARGET):
    """A comparable apparent excess, paired with at most one observation defect."""
    primary,companion=MATCHED_RESIDUAL[scenario]
    events=[dict(type=primary,target_asset_id=target,start=start,end=end,
                 severity=MATCHED_RESIDUAL_SEVERITY)]
    if companion:
        events.append(dict(type=companion,target_asset_id=target,start=start,end=end,severity=1.0))
    return events

def stamp(seq): return (START+timedelta(minutes=15*seq)).isoformat().replace('+00:00','Z')

def loss(kind,energy):
    a,b=COEFFICIENTS[kind]
    return a*.25+b*(energy/.25)**2*.25

def generate(seed,seq,incidents):
    rng=random.Random(seed*1000003+seq)
    demand={}; physical={}; extra_geometry=[]; occluders=[]; active=[]
    for a in ASSETS:
        if a['kind']=='household':
            i=int(a['id'][-2:]); hour=(seq*.25)%24
            peak=.7+1.0*math.exp(-((hour-8)/2)**2)+1.6*math.exp(-((hour-19)/3)**2)
            demand[a['id']]=(.45+(i*7%13)/12)*peak*.25*(.94+rng.random()*.12)
    for event in incidents:
        if event['start']<=seq<event['end']:
            active.append(event)
            hs=CHILDREN[event['target_asset_id']]
            if event['type']=='legitimate_load_change': demand[hs[0]]*=event['severity']
    physical.update(demand)
    for s in reversed(SECTIONS):
        sid=s['id']; downstream=sum(physical[x] for x in CHILDREN[sid]); added=0
        for e in active:
            if e['target_asset_id']==sid:
                if e['type'] in ('visible_unmetered_load','hidden_bypass','occlusion'): added+=e['severity']
                if e['type'] in ('visible_unmetered_load','occlusion'):
                    x,_,z=s['position_m']; extra_geometry.append([[x,8,z],[x+12,5.5,z+8]])
                    if e['type']=='occlusion': occluders.append(dict(position_m=[x+3,7,z+11],size_m=[26,11,1]))
        energy=downstream+added
        physical[sid]=energy+loss(s['kind'],energy)
        if any(e['type']=='technical_loss_change' and e['target_asset_id']==sid for e in active): physical[sid]+=1.0
    readings={}
    for a in ASSETS:
        if not a['meter_id']: continue
        aid=a['id']; val=physical[aid]*(.998+rng.random()*.004); quality='valid'; topo=VERSION
        for e in active:
            if aid==CHILDREN[e['target_asset_id']][0]:
                if e['type']=='missing_telemetry': val=None; quality='missing'
                if e['type']=='meter_underregistration': val*=max(0,1-min(e['severity'],.95))
                if e['type']=='topology_mismatch': topo='topology-stale'
        readings[aid]=dict(schema_version='1.0',run_id='',meter_id=a['meter_id'],asset_id=aid,interval_start=stamp(seq),interval_end=stamp(seq+1),energy_import_kwh=val,energy_export_kwh=0.0,quality=quality,received_at=stamp(seq+1),topology_version=topo,revision=1,provenance='synthetic')
    return dict(readings=readings,geometry=extra_geometry,occluders=occluders,truth=dict(actual_demand_kwh=demand,physical_kwh=physical,events=active))
