import asyncio,base64,hashlib,json,math,logging,time
from contextlib import asynccontextmanager
from pathlib import Path
import cv2,numpy as np
from fastapi import FastAPI,HTTPException,Request,Header
from fastapi.responses import StreamingResponse,Response,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from . import store,engine,inspection
from .simulation import SCENARIOS,stamp
from .topology import BY_ID,VERSION

logging.basicConfig(level=logging.INFO)
ROLES=['analyst','reviewer','supervisor','presenter']
TRANSITIONS={'open':['triaged'],'triaged':['inspection_requested','under_review'],'inspection_requested':['evidence_ready','under_review'],'evidence_ready':['under_review'],'under_review':['field_check_required','resolved','dismissed'],'field_check_required':['under_review'],'resolved':['reopened'],'dismissed':['reopened'],'reopened':['triaged']}
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
    for run in store.all_of('run'):
        run['playing']=False; store.put('run',run)
    if not store.all_of('run'): engine.create_run()
    task=asyncio.create_task(clock_loop())
    yield
    task.cancel()

app=FastAPI(title='GridTrace local synthetic investigation API',lifespan=lifespan)

class RunInput(BaseModel):
    seed:int=Field(default=42,ge=0,le=1000000)
    scenario:Literal[tuple(SCENARIOS)]='clean'
class Control(BaseModel):
    command:Literal['play','pause','step','speed']
    speed:Literal[1,10,60]=10
class Incident(BaseModel):
    type:Literal[tuple(SCENARIOS)]
    target_asset_id:str='branch-03'
    start:int=Field(ge=0,le=95)
    end:int=Field(ge=1,le=96)
    severity:float=Field(default=1.2,gt=0,le=20,allow_inf_nan=False)
class NewCase(BaseModel):
    alert_id:str
    idempotency_key:str=Field(min_length=1,max_length=100)
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
    sequence:int=Field(ge=0,le=95)
    expected_revision:int=Field(ge=1)
    energy_import_kwh:float|None=Field(default=None,ge=0,allow_inf_nan=False)
    quality:Literal['valid','missing','stale','invalid','estimated']

@app.get('/api/bootstrap')
async def bootstrap():
    runs=store.all_of('run'); return dict(runs=[{k:v for k,v in r.items() if k in ('id','seed','seq','created_at')} for r in runs],cases=store.all_of('case'),scenarios=SCENARIOS,dispositions=DISPOSITIONS,roles=ROLES)
@app.post('/api/runs')
async def create_run(body:RunInput):
    for r in store.all_of('run'):
        if r['playing']: r['playing']=False; store.put('run',r)
    return engine.snapshot(engine.create_run(body.seed,body.scenario)['id'])
@app.get('/api/runs/{rid}/snapshot')
async def snapshot(rid:str,seq:int|None=None):
    r=require(rid,'run')
    if seq is not None and not 0<=seq<=r['seq']: raise HTTPException(400,'Sequence is not available')
    return engine.snapshot(rid,seq)
@app.post('/api/runs/{rid}/control')
async def control(rid:str,body:Control):
    r=require(rid,'run')
    if body.command in ('play','step') and any(m['run_id']==rid and m['status'] in ('approved','flying','capturing','processing') for m in store.all_of('mission')):
        raise HTTPException(409,'Finish or cancel the active mission before advancing its frozen scene')
    if body.command=='step':
        if r['playing']: raise HTTPException(409,'Pause before single stepping')
        engine.step(r)
    else:
        if body.command=='speed': r['speed']=body.speed
        else: r['playing']=body.command=='play'
        r['event_seq']+=1; store.put('run',r)
    return engine.snapshot(rid)
@app.post('/api/runs/{rid}/incidents')
async def incident(rid:str,body:Incident,x_actor:str=Header(default='analyst')):
    role(x_actor,['presenter']); r=require(rid,'run')
    if body.target_asset_id not in BY_ID or BY_ID[body.target_asset_id]['kind']!='branch': raise HTTPException(400,'Target must be a monitored branch')
    if body.start<=r['seq'] or body.end<=body.start: raise HTTPException(400,'Incident must start after the current interval and end after its start')
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
async def history(aid:str,run_id:str,start:int=0,end:int=95):
    r=require(run_id,'run')
    if aid not in BY_ID: raise HTTPException(404,'Unknown asset')
    return [dict(seq=i,reading=s['readings'].get(aid),balance=next((b for b in s['balances'] if b['boundary_asset_id']==aid),None)) for i in range(max(0,start),min(end,r['seq'])+1) if (s:=store.interval(run_id,i))]
@app.post('/api/runs/{rid}/readings/revise')
async def revise_reading(rid:str,body:ReadingRevision,x_actor:str=Header(default='analyst')):
    role(x_actor,['analyst','supervisor']);run=require(rid,'run')
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
@app.get('/api/cases')
async def cases(): return store.all_of('case')
@app.post('/api/cases')
async def create_case(body:NewCase,x_actor:str=Header(default='analyst')):
    role(x_actor,['analyst','supervisor'])
    for c in store.all_of('case'):
        if c['alert_id']==body.alert_id: return c
    alert=None; r=None
    for run in store.all_of('run'):
        for a in store.interval(run['id'],run['seq'])['alerts']:
            if a['id']==body.alert_id: alert=a; r=run; break
    if not alert or alert['status']!='active': raise HTTPException(400,'Choose an active, persistent alert')
    c=dict(id=store.uid('case'),run_id=r['id'],alert_id=alert['id'],boundary_asset_id=alert['boundary_asset_id'],state='open',priority=alert['priority'],assigned_to=None,created_by=x_actor,created_at=store.now(),updated_at=store.now(),revision=1,disposition=None,decision_reason=None,evidence_ids=[],provenance='synthetic',idempotency_key=body.idempotency_key,analysis_sequence=r['seq'])
    frozen=store.interval(r['id'],r['seq'])
    store.put('case-analysis',dict(id=c['id']+'-analysis',analysis={k:v for k,v in frozen.items() if not k.startswith('physical_')},contributing_intervals=[{k:v for k,v in store.interval(r['id'],i).items() if not k.startswith('physical_')} for i in range(alert['first_interval'],r['seq']+1)]))
    store.put('case',c); store.audit(c,x_actor,'created',None,refs=alert['balance_ids']); return c
@app.get('/api/cases/{cid}')
async def case_detail(cid:str):
    c=require(cid,'case'); return dict(case=c,audit=store.audits(cid),missions=[m for m in store.all_of('mission') if m['case_id']==cid],evidence=[e for e in store.all_of('evidence') if e['case_id']==cid],transitions=TRANSITIONS[c['state']])
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
@app.post('/api/cases/{cid}/missions')
async def mission(cid:str,body:MissionInput,x_actor:str=Header(default='analyst')):
    role(x_actor,['reviewer','supervisor']); c=require(cid,'case')
    for m in store.all_of('mission'):
        if m['case_id']==cid and m['idempotency_key']==body.idempotency_key: return m
    if not body.approved: raise HTTPException(400,'Explicit reviewer approval is required')
    if c['state'] not in ('triaged','inspection_requested','evidence_ready','under_review'): raise HTTPException(409,'Triage the case before approving inspection')
    if any(m['case_id']==cid and m['status'] not in ('completed','failed','cancelled') for m in store.all_of('mission')): raise HTTPException(409,'A mission is already active')
    r=require(c['run_id'],'run'); r['playing']=False; r['event_seq']+=1; store.put('run',r)
    x,_,z=BY_ID[c['boundary_asset_id']]['position_m']
    m=dict(id=store.uid('mission'),case_id=cid,run_id=c['run_id'],target_asset_ids=[c['boundary_asset_id'],'pole-'+c['boundary_asset_id']],status='approved',approved_by=x_actor,approved_at=store.now(),waypoints_m=[[x+20,12,z+26],[x-20,12,z+26],[x+10,14,z+30]],created_at=store.now(),capture_sequence=r['seq'],failure_reason=None,provenance='synthetic',idempotency_key=body.idempotency_key,frame_keys={})
    frozen=store.interval(r['id'],r['seq'])
    store.put('capture-analysis',dict(id=m['id']+'-snapshot',observations={k:v for k,v in frozen.items() if not k.startswith('physical_')}))
    store.put('mission',m); bump(c,x_actor,'mission_approved',refs=[m['id']],new_state='inspection_requested' if c['state']=='triaged' else None); return m
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
    report['analysis']={k:v for k,v in analysis.items() if not k.startswith('physical_')}
    if format=='json': content=json.dumps(report,indent=2,allow_nan=False); media='application/json'
    else:
        bal=next(b for b in analysis['balances'] if b['boundary_asset_id']==c['boundary_asset_id'])
        content=f"# GridTrace case {cid}\n\n{report['disclosure']}\n\nBoundary: {c['boundary_asset_id']} · Run: {c['run_id']} · Seed: {run['seed']}\n\nState: {c['state']} · Owner: {c['assigned_to'] or 'Unassigned'}\n\nDisposition: {c['disposition']}\n\nReason: {c['decision_reason']}\n\n## Frozen interval balance\n\n```json\n{json.dumps(bal,indent=2)}\n```\n\n## Evidence (separate PNG files)\n"
        for e in detail['evidence']: content+=f"\n- {e['id']}: {e['observation_status']} · {e['original_image_path']} · SHA-256 `{e['original_sha256']}` · annotated: {e['annotated_image_path']} · SHA-256 `{e['annotated_sha256']}` · {e['detector_version']} · pose {json.dumps(e['camera_pose'])}\n"
        content+='\n## Contributing observed intervals\n\n```json\n'+json.dumps(contributing,indent=2)+'\n```\n\n## Audit history\n'
        for a in detail['audit']: content+=f"\n- {a['wall_timestamp']} · {a['actor_id']} · {a['action']} · {a['from_state']} → {a['to_state']} · {a['reason']}\n"
        media='text/markdown'
    raw=content.encode(); digest=hashlib.sha256(raw).hexdigest(); filename=f'{cid}-{digest[:12]}.{format}'
    (store.ROOT/filename).write_bytes(raw)
    return Response(raw,media_type=media,headers={'Content-Disposition':f'attachment; filename="{filename}"','X-Content-SHA256':digest})

app.mount('/evidence',StaticFiles(directory=store.ROOT/'evidence'),name='evidence')
DIST=Path(__file__).resolve().parents[1]/'dist'
if DIST.exists(): app.mount('/',StaticFiles(directory=DIST,html=True),name='frontend')
