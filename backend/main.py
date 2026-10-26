import asyncio,base64,hashlib,json,math,logging,time
from contextlib import asynccontextmanager
from pathlib import Path
import cv2,numpy as np
from fastapi import FastAPI,HTTPException,Request,Header
from fastapi.responses import StreamingResponse,Response,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from . import store,engine,inspection,coverage,ranking
from .simulation import SCENARIOS,stamp
from .topology import BY_ID,VERSION,ASSETS
from .sources import manifest, month_summary, MONTH_INTERVALS
from . import investigations, providers, finance, benchmark
from .contracts import InvestigationInput, FinanceInput

logging.basicConfig(level=logging.INFO)
ROLES=['analyst','reviewer','supervisor','presenter']
TRANSITIONS={'open':['triaged'],'triaged':['ground_review','under_review'],'ground_review':['inspection_requested','under_review'],'inspection_requested':['evidence_ready','under_review'],'evidence_ready':['under_review'],'under_review':['field_check_required','resolved','dismissed'],'field_check_required':['under_review'],'resolved':['reopened'],'dismissed':['reopened'],'reopened':['triaged']}
DISPOSITIONS=['data-quality issue','authorized load','technical-loss/model issue','meter fault','suspected unmetered consumption requiring field verification','inconclusive']

def require(id,kind=None):
    obj=store.get(id)
    if not obj or (kind and not id.startswith(kind+'-')): raise HTTPException(404,'Record not found')
    return obj
def role(actor,allowed):
    if actor not in allowed: raise HTTPException(403,'Select a simulated '+ ' or '.join(allowed)+' identity for this action')
def bump(case,actor,action,reason='',refs=None,new_state=None):
    old=case['state']
    if new_state: case['state']=new_state
    case['revision']+=1; case['updated_at']=store.now(); store.put('case',case); store.audit(case,actor,action,old,reason,refs)

async def clock_loop():
    elapsed={}; last=time.monotonic()
    while True:
        await asyncio.sleep(.05); now=time.monotonic(); delta=now-last; last=now
        for run in store.all_of('run'):
            if not run['playing']: elapsed[run['id']]=0; continue
            elapsed[run['id']]=elapsed.get(run['id'],0)+delta
            period=15/run['speed']
            while elapsed[run['id']]>=period and run['playing']:
                engine.step(run); elapsed[run['id']]-=period

@asynccontextmanager
async def lifespan(app):
    for inv in store.all_of('investigation'):
        if inv['status'] in ('queued','planning','running'):
            inv.update(status='interrupted',error='Previous process stopped; start a new investigation to retry')
            store.put('investigation',inv)
    for run in store.all_of('run'):
        run['playing']=False; store.put('run',run)
    if not store.all_of('run'): engine.create_run(mode='replay')
    task=asyncio.create_task(clock_loop())
    yield
    task.cancel()
    for job in list(investigations.TASKS): job.cancel()
    if investigations.TASKS: await asyncio.gather(*list(investigations.TASKS),return_exceptions=True)

app=FastAPI(title='Grid Trace local investigation API',lifespan=lifespan)

class RunInput(BaseModel):
    seed:int=Field(default=42,ge=0,le=1000000)
    scenario:Literal[tuple(SCENARIOS)]='clean'
    mode:Literal['laboratory','replay']='laboratory'
    coverage_profile:Literal[tuple(coverage.PROFILES)]=coverage.DEFAULT_PROFILE
class CoverageInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    profile_id:Literal[tuple(coverage.PROFILES)]
class GroundObservation(BaseModel):
    """PRD FR-07. A reviewer records what ground access actually produced."""
    model_config=ConfigDict(extra='forbid')
    idempotency_key:str=Field(min_length=1,max_length=100)
    access:Literal['obtained','refused','unsafe','not_attempted']
    observed_asset_ids:list[str]=Field(default_factory=list,max_length=40)
    visibility:Literal['clear','partial','obstructed','not_visible']
    resolved_from_ground:bool=False
    outstanding_question:str=Field(default='',max_length=600)
    notes:str=Field(default='',max_length=4000)
class Control(BaseModel):
    command:Literal['play','pause','step','speed','seek']
    speed:Literal[1,10,60]=10
    sequence:int|None=Field(default=None,ge=0,le=MONTH_INTERVALS-1)
    expected_revision:int|None=Field(default=None,ge=1)
class Incident(BaseModel):
    type:Literal[tuple(SCENARIOS)]
    target_asset_id:str='branch-03'
    start:int=Field(ge=0,le=MONTH_INTERVALS-1)
    end:int=Field(ge=1,le=MONTH_INTERVALS)
    severity:float=Field(default=1.2,gt=0,le=20,allow_inf_nan=False)
class NewCase(BaseModel):
    alert_id:str
    idempotency_key:str=Field(min_length=1,max_length=100)
    sequence:int|None=Field(default=None,ge=0,le=MONTH_INTERVALS-1)
class CasePatch(BaseModel):
    expected_revision:int
    assigned_to:str|None=None
    state:str|None=None
    disposition:str|None=None
    reason:str=Field(default='',max_length=4000)
    note:str=Field(default='',max_length=4000)
class MissionInput(BaseModel):
    approved:bool=False
    idempotency_key:str=Field(min_length=1,max_length=100)
    waypoint_preset:Literal['overhead-v1']='overhead-v1'
class MissionPatch(BaseModel):
    status:Literal['flying','capturing','completed','failed','cancelled']
    reason:str=Field(default='',max_length=1000)
class Pose(BaseModel):
    position:tuple[float,float,float]
    target:tuple[float,float,float]
    fov:float=Field(ge=20,le=80)
class FrameInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    png_base64:str=Field(max_length=7000000)
    camera_pose:Pose
    capture_sequence:int
    approved_geometry_version:Literal['topology-1']
    frame_key:str=Field(min_length=1,max_length=80)
    capture_source:Literal['webgl_scene','pixel_control_fixture']
class ReadingRevision(BaseModel):
    asset_id:str
    sequence:int=Field(ge=0,le=MONTH_INTERVALS-1)
    expected_revision:int=Field(ge=1)
    energy_import_kwh:float|None=Field(default=None,ge=0,allow_inf_nan=False)
    quality:Literal['valid','missing','stale','invalid','estimated']

@app.get('/api/bootstrap')
async def bootstrap():
    runs=store.all_of('run'); return dict(runs=[{k:v for k,v in r.items() if k in ('id','seed','seq','created_at')} for r in runs],cases=store.all_of('case'),scenarios=SCENARIOS,dispositions=DISPOSITIONS,roles=ROLES)

@app.get('/api/sources')
async def sources():
    return dict(development=manifest(), bescom=dict(status='PENDING', source_kind='ACTUAL_EXTRACT',
                reason='Historical BESCOM extract has not been onboarded'),
                frozen_replay=dict(status='PENDING',reason='Original frozen September file has not been onboarded'))

@app.get('/api/health')
async def health():
    return dict(application='Grid Trace', storage='OK' if store.DB.execute('SELECT 1').fetchone() else 'FAILED',
                sources='DEVELOPMENT_ONLY', planner='GRANITE_GROK_RULES', providers=providers.configuration(), vision='DEFERRED')

@app.post('/api/investigations')
async def start_investigation(body:InvestigationInput,x_actor:str=Header(default='analyst')):
    role(x_actor,['analyst','supervisor'])
    run=require(body.run_id,'run')
    if body.area_id not in BY_ID or BY_ID[body.area_id]['kind'] not in ('feeder','transformer','branch'):
        raise HTTPException(400,'Choose a measured feeder, transformer or branch')
    if body.sequence>run['seq']: raise HTTPException(400,'Select an available interval first')
    try: inv=investigations.create(body,engine.snapshot(run['id'],body.sequence),actor=x_actor)
    except ValueError as exc: raise HTTPException(409,str(exc))
    return investigations.public(inv)

@app.get('/api/investigations')
async def list_investigations(run_id:str|None=None):
    return [investigations.public(inv) for inv in store.all_of('investigation') if run_id is None or inv['run_id']==run_id]

@app.get('/api/investigations/{iid}')
async def get_investigation(iid:str):
    return dict(**investigations.public(require(iid,'investigation')),trace=investigations.trace(iid))

@app.post('/api/finance/scenario')
async def finance_scenario(body:FinanceInput):
    if body.scope_asset not in BY_ID: raise HTTPException(400,'Unknown scope asset')
    try: result=finance.calculate(body)
    except ValueError as exc: raise HTTPException(400,str(exc))
    result.update(id=store.uid('finance'),created_at=store.now())
    store.put('finance',result)
    return result

@app.get('/api/benchmark')
async def benchmark_results():
    return benchmark.results()

@app.get('/api/runs/{rid}/month')
async def month(rid:str):
    run=require(rid,'run')
    if run.get('mode')!='replay': raise HTTPException(400,'Month summary requires a replay run')
    return month_summary(run['seed'])
@app.post('/api/runs')
async def create_run(body:RunInput):
    if body.mode=='replay' and body.scenario!='clean':
        raise HTTPException(400,'Replay is read-only; use the laboratory for injected scenarios')
    for r in store.all_of('run'):
        if r['playing']: r['playing']=False; store.put('run',r)
    return engine.snapshot(engine.create_run(body.seed,body.scenario,body.mode,body.coverage_profile)['id'])
@app.get('/api/runs/{rid}/snapshot')
async def snapshot(rid:str,seq:int|None=None):
    r=require(rid,'run')
    if seq is not None and not 0<=seq<=r['seq']: raise HTTPException(400,'Sequence is not available')
    return engine.snapshot(rid,seq)
@app.post('/api/runs/{rid}/control')
async def control(rid:str,body:Control):
    r=require(rid,'run')
    if body.expected_revision is not None and body.expected_revision!=r.get('revision',1):
        raise HTTPException(409,'Replay changed; refresh and retry with its current revision')
    if body.command in ('play','step','seek') and any(m['run_id']==rid and m['status'] in ('approved','flying','capturing','processing') for m in store.all_of('mission')):
        raise HTTPException(409,'Finish or cancel the active mission before advancing its frozen scene')
    if body.command=='seek':
        if body.sequence is None: raise HTTPException(400,'Seek requires an interval sequence')
        try: engine.seek(r,body.sequence)
        except ValueError as exc: raise HTTPException(400,str(exc))
    elif body.command=='step':
        if r['playing']: raise HTTPException(409,'Pause before single stepping')
        engine.step(r)
    else:
        if body.command=='play' and r.get('selected_seq',r['seq'])>=r.get('interval_count',96)-1:
            raise HTTPException(409,'End of replay; select an earlier interval first')
        if body.command=='speed': r['speed']=body.speed
        else: r['playing']=body.command=='play'
        r['event_seq']+=1; r['revision']=r.get('revision',1)+1; store.put('run',r)
    return engine.snapshot(rid)
@app.post('/api/runs/{rid}/incidents')
async def incident(rid:str,body:Incident,x_actor:str=Header(default='analyst')):
    role(x_actor,['presenter']); r=require(rid,'run')
    if r.get('mode')=='replay': raise HTTPException(409,'Replay is read-only; inject incidents in a laboratory run')
    if body.target_asset_id not in BY_ID or BY_ID[body.target_asset_id]['kind']!='branch': raise HTTPException(400,'Target must be a monitored branch')
    if body.start<=r['seq'] or body.end<=body.start or body.end>r.get('interval_count',96): raise HTTPException(400,'Incident must lie in future intervals within this run')
    r['scenario_settings'].append(body.model_dump()); r['event_seq']+=1; store.put('run',r); return dict(accepted=True)
@app.get('/api/runs/{rid}/truth')
async def truth(rid:str,x_actor:str=Header(default='analyst')):
    role(x_actor,['presenter']); require(rid,'run'); return dict(events=store.get(rid)['scenario_settings'],disclosure='Private simulation truth; never reviewer evidence')
@app.get('/api/runs/{rid}/events')
async def events(rid:str,request:Request,after_seq:int=-1):
    require(rid,'run')
    async def stream():
        last=after_seq
        while not await request.is_disconnected():
            r=store.get(rid)
            if r['event_seq']>last:
                last=r['event_seq']; yield f'id: {last}\nevent: snapshot\ndata: '+json.dumps(dict(run_id=rid,event_seq=last))+'\n\n'
            else: yield ': heartbeat\n\n'
            await asyncio.sleep(.25)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
@app.get('/api/assets/{aid}/history')
async def history(aid:str,run_id:str,start:int=0,end:int|None=None):
    r=require(run_id,'run')
    if aid not in BY_ID: raise HTTPException(404,'Unknown asset')
    last=r.get('selected_seq',r['seq']) if end is None else min(end,r['seq'])
    return [dict(seq=i,reading=s['readings'].get(aid),balance=next((b for b in s['balances'] if b['boundary_asset_id']==aid),None)) for i in range(max(0,start),last+1) if (s:=store.interval(run_id,i))]
@app.post('/api/runs/{rid}/readings/revise')
async def revise_reading(rid:str,body:ReadingRevision,x_actor:str=Header(default='analyst')):
    role(x_actor,['analyst','supervisor']);run=require(rid,'run')
    if run.get('mode')=='replay': raise HTTPException(409,'Replay source is read-only; revisions are available in the laboratory')
    if run['playing']: raise HTTPException(409,'Pause before explicit recomputation')
    if any(m['run_id']==rid and m['status'] in ('approved','flying','capturing','processing') for m in store.all_of('mission')): raise HTTPException(409,'Finish or cancel the mission before recomputing its capture observations')
    row=store.interval(rid,body.sequence)
    if row is None or body.asset_id not in row['readings']: raise HTTPException(400,'Unknown measured asset or interval')
    r=row['readings'][body.asset_id]
    if r['revision']!=body.expected_revision: raise HTTPException(409,'Duplicate or stale reading revision')
    if body.quality=='valid' and body.energy_import_kwh is None: raise HTTPException(400,'Valid readings require an energy value')
    if body.quality=='missing' and body.energy_import_kwh is not None: raise HTTPException(400,'Missing readings must be null')
    engine.revise_reading(run,body.sequence,body.asset_id,body.energy_import_kwh,body.quality,x_actor)
    return engine.snapshot(rid)
@app.get('/api/runs/{rid}/analysis-revisions')
async def analysis_revisions(rid:str):
    require(rid,'run');return dict(recomputations=[r for r in store.all_of('recomputation') if r['run_id']==rid],revisions=[r for r in store.all_of('analysis-revision') if r['id'].startswith(rid)])
@app.get('/api/coverage/profiles')
async def coverage_profiles():
    return dict(profiles=coverage.describe_profiles(),default=coverage.DEFAULT_PROFILE,
                disclosure=('Published metering counts parameterise a fictional network; they do '
                            'not establish communication health, mapping correctness, or that '
                            'GridTrace was tested on any utility.'))

@app.get('/api/runs/{rid}/coverage')
async def get_coverage(rid:str):
    run=require(rid,'run')
    return coverage.summary(run.get('coverage_profile',coverage.DEFAULT_PROFILE),ASSETS)

@app.post('/api/runs/{rid}/coverage')
async def set_coverage(rid:str,body:CoverageInput,x_actor:str=Header(default='analyst')):
    """Changing installed inventory is a presenter control; it resets persistence streaks."""
    role(x_actor,['presenter'])
    run=require(rid,'run')
    if any(m['run_id']==rid and m['status'] not in ('completed','failed','cancelled') for m in store.all_of('mission')):
        raise HTTPException(409,'Finish or cancel the active mission before changing coverage')
    engine.set_coverage(run,body.profile_id,x_actor)
    return coverage.summary(body.profile_id,ASSETS)

@app.get('/api/balances/{bid}/actions')
async def balance_actions(bid:str,run_id:str,case_id:str|None=None):
    """Ranked next checks for one boundary balance (PRD FR-06, AC-14)."""
    run=require(run_id,'run')
    interval=store.interval(run_id,run.get('selected_seq',run['seq']))
    if interval is None: raise HTTPException(404,'No analysed interval for this run')
    balance=next((b for b in interval['balances'] if b['id']==bid or b['boundary_asset_id']==bid),None)
    if balance is None: raise HTTPException(404,'Unknown balance for this run and interval')
    validity=balance['validity']
    if validity=='insufficient_observability':
        status='INSUFFICIENT_OBSERVABILITY'
    elif validity!='valid':
        status='DATA_INCOMPLETE'
    elif balance['negative_review']:
        status='REVIEW_MODEL_OR_TOPOLOGY'
    elif any(a['boundary_asset_id']==balance['boundary_asset_id'] and a['status']=='active' for a in interval['alerts']):
        status='UNEXPLAINED_ENERGY'
    elif balance['qualifies']:
        status='PERSISTENCE_PENDING'
    else:
        status='WITHIN_MODEL_RANGE'
    reasons=' '.join(balance['invalid_reasons']).lower()
    kind=('BOTH' if 'topology mismatch' in reasons and ('missing' in reasons or 'invalid energy' in reasons)
          else 'TOPOLOGY_MISMATCH' if 'topology mismatch' in reasons
          else 'MISSING_READINGS')
    if status=='INSUFFICIENT_OBSERVABILITY':
        return dict(balance_id=balance['id'],boundary_asset_id=balance['boundary_asset_id'],
                    diagnostic_status=status,policy_version=ranking.POLICY_VERSION,
                    ranked=[],rejected=[],recommended_action='ABSTAIN_NO_ACTION',
                    abstain_reason=('This boundary is not instrumented under the active coverage '
                                    'profile. No reconciled residual exists to investigate.'),
                    missing_evidence_question='Which sectional measurement would make this boundary reconcilable?',
                    uninstrumented_asset_ids=balance.get('uninstrumented_asset_ids',[]),
                    inventory_version=run.get('inventory_version'),
                    coverage_profile=run.get('coverage_profile',coverage.DEFAULT_PROFILE))
    context=dict(diagnostic_status=status,incomplete_kind=kind,billing_status='NOT_AVAILABLE',
                 ground_question_open=bool(case_id and open_ground_question(case_id)),
                 completed_actions=tuple(), area_id=balance['boundary_asset_id'], balance_id=balance['id'])
    result=ranking.rank(context)
    result.update(balance_id=balance['id'],boundary_asset_id=balance['boundary_asset_id'],
                  diagnostic_status=status,inventory_version=run.get('inventory_version'),
                  coverage_profile=run.get('coverage_profile',coverage.DEFAULT_PROFILE))
    return result

@app.get('/api/cases')
async def cases(): return store.all_of('case')
@app.post('/api/cases')
async def create_case(body:NewCase,x_actor:str=Header(default='analyst')):
    role(x_actor,['analyst','supervisor'])
    for c in store.all_of('case'):
        if c['alert_id']==body.alert_id: return c
    alert=None; r=None
    for run in store.all_of('run'):
        selected_seq=run.get('selected_seq',run['seq']) if body.sequence is None else body.sequence
        interval=store.interval(run['id'],selected_seq)
        if interval is None: continue
        for a in interval['alerts']:
            if a['id']==body.alert_id: alert=a; r=run; break
        if alert: break
    if not alert or alert['status']!='active': raise HTTPException(400,'Choose an active, persistent alert')
    c=dict(id=store.uid('case'),run_id=r['id'],alert_id=alert['id'],boundary_asset_id=alert['boundary_asset_id'],state='open',priority=alert['priority'],assigned_to=None,created_by=x_actor,created_at=store.now(),updated_at=store.now(),revision=1,disposition=None,decision_reason=None,evidence_ids=[],provenance='synthetic',idempotency_key=body.idempotency_key,analysis_sequence=selected_seq,source=r.get('source'))
    frozen=store.interval(r['id'],selected_seq)
    store.put('case-analysis',dict(id=c['id']+'-analysis',analysis={k:v for k,v in frozen.items() if not k.startswith('physical_')},contributing_intervals=[{k:v for k,v in store.interval(r['id'],i).items() if not k.startswith('physical_')} for i in range(alert['first_interval'],selected_seq+1)]))
    store.put('case',c); store.audit(c,x_actor,'created',None,refs=alert['balance_ids']); return c
@app.get('/api/cases/{cid}')
async def case_detail(cid:str):
    c=require(cid,'case'); return dict(case=c,audit=store.audits(cid),missions=[m for m in store.all_of('mission') if m['case_id']==cid],evidence=[e for e in store.all_of('evidence') if e['case_id']==cid],ground=ground_observations(cid),open_ground_question=open_ground_question(cid),transitions=TRANSITIONS[c['state']])
@app.patch('/api/cases/{cid}')
async def update_case(cid:str,body:CasePatch,x_actor:str=Header(default='analyst')):
    c=require(cid,'case')
    if body.expected_revision!=c['revision']: raise HTTPException(409,'Case changed; refresh and retry with the current revision')
    if body.state:
        if body.state not in TRANSITIONS[c['state']]: raise HTTPException(409,'Invalid case transition')
        allowed=['supervisor'] if body.state in ('resolved','dismissed','reopened') else (['analyst','supervisor'] if body.state=='triaged' else ['reviewer','supervisor'])
        role(x_actor,allowed)
        if body.state in ('resolved','dismissed') and (not body.reason.strip() or body.disposition not in DISPOSITIONS): raise HTTPException(400,'Resolution/dismissal requires an allowed disposition and a reason')
        if body.state=='inspection_requested': raise HTTPException(400,'Use explicit mission approval to request inspection')
        if body.state=='evidence_ready': raise HTTPException(400,'Evidence-ready state is set only when an approved mission completes')
        if body.disposition:
            if body.disposition not in DISPOSITIONS: raise HTTPException(400,'Unknown disposition')
            c['disposition']=body.disposition
        if body.reason: c['decision_reason']=body.reason
    if body.assigned_to is not None:
        role(x_actor,['analyst','supervisor']); c['assigned_to']=body.assigned_to.strip()[:100] or None
    if body.note: role(x_actor,['reviewer','supervisor','analyst'])
    bump(c,x_actor,'transition' if body.state else ('note' if body.note else 'assignment'),body.note or body.reason,new_state=body.state)
    return c
def ground_observations(cid):
    return sorted((g for g in store.all_of('ground') if g['case_id']==cid),key=lambda g:g['recorded_at'])

def open_ground_question(cid):
    """The most recent ground observation that leaves an overhead question unanswered."""
    for g in reversed(ground_observations(cid)):
        if g['resolved_from_ground']: return None
        if g['outstanding_question'].strip(): return g
    return None

@app.get('/api/cases/{cid}/ground-observations')
async def list_ground(cid:str):
    require(cid,'case')
    return dict(observations=ground_observations(cid),open_question=open_ground_question(cid))

@app.post('/api/cases/{cid}/ground-observations')
async def add_ground(cid:str,body:GroundObservation,x_actor:str=Header(default='analyst')):
    """PRD FR-07: ground-first. Aerial review is justified only by a recorded, unanswered question."""
    role(x_actor,['reviewer','supervisor']); c=require(cid,'case')
    for g in store.all_of('ground'):
        if g['case_id']==cid and g['idempotency_key']==body.idempotency_key: return g
    if c['state'] in ('resolved','dismissed'): raise HTTPException(409,'Reopen the case before adding observations')
    if body.resolved_from_ground and body.outstanding_question.strip():
        raise HTTPException(400,'A ground-resolved observation cannot also carry an outstanding question')
    if not body.resolved_from_ground and not body.outstanding_question.strip():
        raise HTTPException(400,'Record the exact question the ground view could not answer, or mark it resolved from ground')
    if body.access!='obtained' and body.resolved_from_ground:
        raise HTTPException(400,'An observation without obtained access cannot resolve the question')
    unknown=[a for a in body.observed_asset_ids if a not in BY_ID]
    if unknown: raise HTTPException(400,f'Unknown asset ids: {", ".join(unknown[:5])}')
    g=dict(id=store.uid('ground'),case_id=cid,run_id=c['run_id'],recorded_by=x_actor,recorded_at=store.now(),
           access=body.access,observed_asset_ids=body.observed_asset_ids,visibility=body.visibility,
           resolved_from_ground=body.resolved_from_ground,outstanding_question=body.outstanding_question.strip(),
           notes=body.notes.strip(),idempotency_key=body.idempotency_key,provenance='synthetic',
           limitation='A ground observation records what a person reported seeing. It does not establish authorization, energization or intent.')
    store.put('ground',g)
    bump(c,x_actor,'ground_observation',body.notes.strip() or body.outstanding_question.strip(),refs=[g['id']],
         new_state='ground_review' if c['state']=='triaged' else None)
    return g

@app.post('/api/cases/{cid}/missions')
async def mission(cid:str,body:MissionInput,x_actor:str=Header(default='analyst')):
    role(x_actor,['reviewer','supervisor']); c=require(cid,'case')
    for m in store.all_of('mission'):
        if m['case_id']==cid and m['idempotency_key']==body.idempotency_key: return m
    if not body.approved: raise HTTPException(400,'Explicit reviewer approval is required')
    if c['state'] not in ('ground_review','inspection_requested','evidence_ready','under_review'): raise HTTPException(409,'Record a ground observation before approving aerial inspection')
    question=open_ground_question(cid)
    if question is None:
        raise HTTPException(409,'Aerial review requires a recorded ground observation that leaves a specific overhead question unanswered')
    if question['visibility']=='clear':
        raise HTTPException(409,'The ground view was clear; an aerial viewpoint cannot add the missing observation')
    if any(m['case_id']==cid and m['status'] not in ('completed','failed','cancelled') for m in store.all_of('mission')): raise HTTPException(409,'A mission is already active')
    r=require(c['run_id'],'run'); r['playing']=False; r['event_seq']+=1; store.put('run',r)
    x,_,z=BY_ID[c['boundary_asset_id']]['position_m']
    m=dict(id=store.uid('mission'),case_id=cid,run_id=c['run_id'],target_asset_ids=[c['boundary_asset_id'],'pole-'+c['boundary_asset_id']],status='approved',approved_by=x_actor,approved_at=store.now(),waypoints_m=[[x+20,12,z+26],[x-20,12,z+26],[x+10,14,z+30]],created_at=store.now(),capture_sequence=c['analysis_sequence'],failure_reason=None,provenance='synthetic',idempotency_key=body.idempotency_key,frame_keys={},
           ground_observation_id=question['id'],answering_question=question['outstanding_question'],
           ground_visibility=question['visibility'],
           limitation='Imagery can only answer the recorded overhead question. It cannot establish authorization, energization or cause.')
    frozen=store.interval(r['id'],m['capture_sequence'])
    store.put('capture-analysis',dict(id=m['id']+'-snapshot',observations={k:v for k,v in frozen.items() if not k.startswith('physical_')}))
    store.put('mission',m); bump(c,x_actor,'mission_approved',question['outstanding_question'],refs=[m['id'],question['id']],new_state='inspection_requested' if c['state']=='ground_review' else None); return m
@app.get('/api/missions/{mid}')
async def get_mission(mid:str): return require(mid,'mission')
@app.patch('/api/missions/{mid}')
async def patch_mission(mid:str,body:MissionPatch,x_actor:str=Header(default='analyst')):
    role(x_actor,['reviewer','supervisor']); m=require(mid,'mission'); c=require(m['case_id'],'case')
    allowed={'approved':['flying','cancelled','failed'],'flying':['capturing','failed','cancelled'],'capturing':['completed','failed','cancelled'],'processing':['completed','failed','capturing','cancelled'],'failed':['flying','cancelled']}
    if body.status==m['status']: return m
    if body.status not in allowed.get(m['status'],[]): raise HTTPException(409,'Invalid mission transition')
    if body.status=='completed' and len(m['frame_keys'])<2: raise HTTPException(400,'At least two captured frames are required')
    if body.status in ('failed','cancelled') and not body.reason.strip(): raise HTTPException(400,'A failure/cancellation reason is required')
    m['status']=body.status; m['failure_reason']=body.reason or None; store.put('mission',m)
    bump(c,x_actor,'mission_'+body.status,body.reason,refs=[mid],new_state='evidence_ready' if body.status=='completed' and c['state']=='inspection_requested' else None); return m
@app.post('/api/missions/{mid}/frames')
async def frame(mid:str,body:FrameInput,x_actor:str=Header(default='analyst')):
    role(x_actor,['reviewer','supervisor']); m=require(mid,'mission'); c=require(m['case_id'],'case')
    if body.frame_key in m['frame_keys']: return require(m['frame_keys'][body.frame_key],'evidence')
    if m['status'] not in ('flying','capturing','processing'): raise HTTPException(409,'Mission must be flying or capturing')
    if body.capture_sequence!=m['capture_sequence']: raise HTTPException(409,'Frame does not match the frozen mission sequence')
    pose=body.camera_pose.model_dump(); points=np.array([pose['position'],pose['target']])
    if not np.isfinite(points).all() or np.linalg.norm(points[0]-points[1])<.1 or np.linalg.norm(np.cross(points[1]-points[0],[0,1,0]))<.1: raise HTTPException(400,'Invalid camera pose')
    try: raw=base64.b64decode(body.png_base64,validate=True)
    except Exception: raise HTTPException(400,'Invalid PNG encoding')
    if len(raw)>5*1024*1024 or raw[:8]!=b'\x89PNG\r\n\x1a\n': raise HTTPException(400,'Only PNG images up to 5 MB are accepted')
    # Check IHDR before decoding to bound decompression allocation.
    if len(raw)<24 or int.from_bytes(raw[16:20],'big')!=640 or int.from_bytes(raw[20:24],'big')!=480: raise HTTPException(400,'Capture must be 640 × 480 RGB')
    image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    if image is None or image.shape!=(480,640,3): raise HTTPException(400,'PNG could not be decoded')
    eid=store.uid('evidence'); original=eid+'-original.png'; annotated=eid+'-annotated.png'
    (store.ROOT/'evidence'/original).write_bytes(raw)
    m['status']='processing';store.put('mission',m)
    began=time.perf_counter()
    try: result,output=inspection.detect(image,pose,c['boundary_asset_id']); cv2.imwrite(str(store.ROOT/'evidence'/annotated),output)
    except Exception as exc:
        failed=dict(id=eid,case_id=c['id'],mission_id=mid,run_id=m['run_id'],captured_sim_time=stamp(m['capture_sequence']+1),captured_wall_time=store.now(),original_image_path='/evidence/'+original,original_sha256=hashlib.sha256(raw).hexdigest(),annotated_image_path=None,annotated_sha256=None,camera_pose=pose,image_width=640,image_height=480,approved_geometry_version=body.approved_geometry_version,capture_sequence=body.capture_sequence,capture_source=body.capture_source,analysis_revision=store.interval(m['run_id'],m['capture_sequence']).get('analysis_revision',1),processing_ms=(time.perf_counter()-began)*1000,detector_version=inspection.VERSION,parameters=inspection.PARAMETERS,observation_status='inconclusive',observations=[],processing_error=str(exc),limitations=['Processing failed; no visual inference was produced. Retry or continue without visual evidence.']+inspection.LIMITS,provenance='synthetic')
        store.put('evidence',failed);c['evidence_ids'].append(eid)
        m.update(status='failed',failure_reason='Image processing failed; original and capture metadata retained. Retry capture or continue without visual evidence.'); store.put('mission',m); bump(c,x_actor,'processing_failed',str(exc),refs=[eid]); raise HTTPException(500,m['failure_reason'])
    evidence=dict(id=eid,case_id=c['id'],mission_id=mid,run_id=m['run_id'],captured_sim_time=stamp(m['capture_sequence']+1),captured_wall_time=store.now(),original_image_path='/evidence/'+original,original_sha256=hashlib.sha256(raw).hexdigest(),annotated_image_path='/evidence/'+annotated,annotated_sha256=hashlib.sha256((store.ROOT/'evidence'/annotated).read_bytes()).hexdigest(),camera_pose=pose,image_width=640,image_height=480,approved_geometry_version=body.approved_geometry_version,capture_sequence=body.capture_sequence,capture_source=body.capture_source,analysis_revision=store.interval(m['run_id'],m['capture_sequence']).get('analysis_revision',1),processing_ms=(time.perf_counter()-began)*1000,provenance='synthetic',**result)
    store.put('evidence',evidence); m['frame_keys'][body.frame_key]=eid; m['status']='capturing'; store.put('mission',m); c['evidence_ids'].append(eid); bump(c,x_actor,'evidence_captured',refs=[eid]); return evidence

@app.get('/api/cases/{cid}/export')
async def export(cid:str,format:Literal['json','md']='json'):
    c=require(cid,'case'); detail=await case_detail(cid); run=store.get(c['run_id']); seq=c['analysis_sequence']
    frozen=store.get(c['id']+'-analysis')
    analysis=frozen['analysis'] if frozen else store.interval(c['run_id'],seq)
    contributing=frozen['contributing_intervals'] if frozen else [analysis]
    capture_observations=[dict(capture_sequence=m['capture_sequence'],observations=(store.get(m['id']+'-snapshot') or {}).get('observations',{k:v for k,v in store.interval(c['run_id'],m['capture_sequence']).items() if not k.startswith('physical_')})) for m in detail['missions']]
    report=dict(schema_version='1.0',disclosure='Synthetic demonstration. Unexplained loss is not proven theft. RGB cannot verify authorization or energization. PNG images are separate downloadable files.',**detail,run={k:v for k,v in run.items() if k in ('id','seed','topology_version','rule_version','created_at')},analysis=analysis,contributing_intervals=contributing,capture_observations=capture_observations,aggregation_boundaries=[c['boundary_asset_id']],aggregation_note='Single instrumented boundary; nested residuals are not added.',exported_at=store.now())
    report['investigations']=[dict(**investigations.public(inv),trace=investigations.trace(inv['id'])) for inv in store.all_of('investigation') if inv['run_id']==c['run_id'] and inv['area_id']==c['boundary_asset_id'] and inv['sequence']==c['analysis_sequence']]
    report['analysis']={k:v for k,v in analysis.items() if not k.startswith('physical_')}
    if format=='json': content=json.dumps(report,indent=2,allow_nan=False); media='application/json'
    else:
        bal=next(b for b in analysis['balances'] if b['boundary_asset_id']==c['boundary_asset_id'])
        content=f"# Grid Trace case {cid}\n\n{report['disclosure']}\n\nBoundary: {c['boundary_asset_id']} · Run: {c['run_id']} · Seed: {run['seed']}\n\nState: {c['state']} · Owner: {c['assigned_to'] or 'Unassigned'}\n\nDisposition: {c['disposition']}\n\nReason: {c['decision_reason']}\n\n## Frozen interval balance\n\n```json\n{json.dumps(bal,indent=2)}\n```\n\n## Evidence (separate PNG files)\n"
        for e in detail['evidence']: content+=f"\n- {e['id']}: {e['observation_status']} · {e['original_image_path']} · SHA-256 `{e['original_sha256']}` · annotated: {e['annotated_image_path']} · SHA-256 `{e['annotated_sha256']}` · {e['detector_version']} · pose {json.dumps(e['camera_pose'])}\n"
        content+='\n## Contributing observed intervals\n\n```json\n'+json.dumps(contributing,indent=2)+'\n```\n\n## Audit history\n'
        for a in detail['audit']: content+=f"\n- {a['wall_timestamp']} · {a['actor_id']} · {a['action']} · {a['from_state']} → {a['to_state']} · {a['reason']}\n"
        content+='\n## Worker investigations and planner provenance\n'
        for inv in report['investigations']:
            planner=inv.get('planner') or {}
            content+=f"\n### {inv['id']}\n\nStatus: {inv['status']} · Interval: {inv['sequence']} · Source: {inv['source'].get('source_kind','unknown')}\n\nProvider: {planner.get('provider','not completed')} · Model: {planner.get('model','unknown')}\n"
            for worker in inv['workers']:
                content+=f"\n- {worker['worker']}: {worker['status']} · {worker['model_or_rule_version']} · Evidence: {', '.join(worker['evidence_ids'])}\n"
            if planner.get('proposal'):content+='\nNext check: '+planner['proposal']['next_action']+'\n\n'+planner['proposal']['justification']+'\n'
            for check in inv.get('checks',[]):
                content+=f"\n#### Follow-up: {check['action']}\n\nStatus: {check['status']} · Target: {check['target_area_id']} · Evidence: {check['evidence_id']} · Version: {check['model_or_rule_version']}\n\n```json\n{json.dumps(check['findings'],indent=2)}\n```\n"
                content+='\n'+ '\n'.join('- '+limit for limit in check['limitations'])+'\n'
            for decision in inv.get('planner_history',[]):
                content+=f"\n- Planner round {decision['round']}: {decision['provider']} · {decision['model']} · {decision['proposal']['next_action']} · Policy: {(decision.get('policy') or {}).get('reason','pending')}\n"
            for trace_event in inv['trace']:
                content+=f"\n- {trace_event['wall_timestamp']} · {trace_event['producer']} · {trace_event['event_type']}\n"
        media='text/markdown'
    raw=content.encode(); digest=hashlib.sha256(raw).hexdigest(); filename=f'{cid}-{digest[:12]}.{format}'
    (store.ROOT/filename).write_bytes(raw)
    return Response(raw,media_type=media,headers={'Content-Disposition':f'attachment; filename="{filename}"','X-Content-SHA256':digest})

app.mount('/evidence',StaticFiles(directory=store.ROOT/'evidence'),name='evidence')
DIST=Path(__file__).resolve().parents[1]/'dist'
if DIST.exists(): app.mount('/',StaticFiles(directory=DIST,html=True),name='frontend')
