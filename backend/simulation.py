"""Private physical simulation. Analytics receives only generate()['readings']."""
import random, math
from datetime import datetime,timedelta,timezone
from .topology import ASSETS, SECTIONS, CHILDREN, BY_ID, VERSION
from .analytics import COEFFICIENTS

START=datetime(2026,10,24,8,tzinfo=timezone.utc)
SCENARIOS=['clean','visible_unmetered_load','missing_telemetry','legitimate_load_change','meter_underregistration','hidden_bypass','technical_loss_change','topology_mismatch','occlusion']

def stamp(seq): return (START+timedelta(minutes=15*seq)).isoformat().replace('+00:00','Z')

def loss(kind,energy):
    a,b=COEFFICIENTS[kind]
    return a*.25+b*(energy/.25)**2*.25

def generate(seed,seq,incidents):
    rng=random.Random(seed*1000003+seq)
    demand={}; physical={}; extra_geometry=[]; occluders=[]; active=[]
    for a in ASSETS:
        if a['kind']=='household':
            i=int(a['id'][-2:]); hour=(8+seq*.25+5.5)%24
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
