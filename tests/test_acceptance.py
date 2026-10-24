import base64,hashlib,json,statistics,time,math,subprocess,sys,os
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend import engine,store,inspection
from backend.analytics import reconcile,expected_loss,balance_terms
from backend.simulation import generate
from backend.topology import ASSETS,CHILDREN,validate_cut,BY_ID,CONNECTIONS

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c: yield c

def post(c,path,body,actor='analyst',status=200):
    r=c.post('/api'+path,json=body,headers={'X-Actor':actor}); assert r.status_code==status,r.text
    return r.json()
def patch(c,path,body,actor='analyst',status=200):
    r=c.patch('/api'+path,json=body,headers={'X-Actor':actor}); assert r.status_code==status,r.text
    return r.json()
def step(c,rid,count=1):
    s=None
    for _ in range(count): s=post(c,f'/runs/{rid}/control',{'command':'step'})
    return s
def run(c,scenario='visible_unmetered_load',seed=42): return post(c,'/runs',dict(seed=seed,scenario=scenario))
def case(c,seed=42):
    s=run(c,seed=seed);s=step(c,s['run']['id'],3);a=s['alerts'][0]
    created=post(c,'/cases',{'alert_id':a['id'],'idempotency_key':'one'})
    return created
def move(c,case,state,actor='reviewer',reason='Recorded uncertainty and requested a field check.',disposition='inconclusive'):
    return patch(c,'/cases/'+case['id'],dict(expected_revision=case['revision'],state=state,reason=reason,disposition=disposition),actor)

def fixture_image(target='branch-03',positive=False,decorative=False,blank=False,view=0):
    # Pixel controls intentionally independent of the private simulator.
    x,_,z=BY_ID[target]['position_m']; pose=dict(position=[x+(20 if view==0 else -20),12,z+26],target=[x,6.7,z+4],fov=45)
    image=np.full((480,640,3),22,np.uint8)
    if blank: return image,pose
    for conn in CONNECTIONS:
        p=inspection.project(conn['geometry_points_m'],pose)
        cv2.line(image,tuple(int(v) for v in p[0]),tuple(int(v) for v in p[-1]),(169,191,196),2,cv2.LINE_AA)
    if positive:
        a,b=inspection.project([[x,8,z],[x+12,5.5,z+8]],pose)
        cv2.line(image,tuple(int(v) for v in a),tuple(int(v) for v in b),(169,191,196),2,cv2.LINE_AA)
    if decorative: cv2.line(image,(55,50),(220,80),(169,191,196),2,cv2.LINE_AA)
    return image,pose

def test_topology_and_boundary_arithmetic():
    assert sum(a['meter_id'] is not None for a in ASSETS)==38
    assert {k:sum(a['kind']==k for a in ASSETS) for k in ['feeder','transformer','branch','household']}==dict(feeder=2,transformer=4,branch=8,household=24)
    with pytest.raises(ValueError): validate_cut('branch-03',['household-07','household-07','household-09'])
    with pytest.raises(ValueError): validate_cut('transformer-02',['branch-03','branch-04','household-07'])
    obs=generate(42,0,[])['readings'];obs['branch-03']['energy_import_kwh']=12.5
    for i in ['household-07','household-08','household-09']:obs[i]['energy_import_kwh']=3.5
    # Explicit worked-example loss is 0.4, independent of calibrated demo coefficients.
    residual,ratio=balance_terms(12.5,10.5,0,.4)
    store.put('fixture',dict(id='balance-worked-fixture',input_kwh=12.5,output_sum_kwh=10.5,expected_loss_kwh=.4,residual_kwh=residual,residual_ratio=ratio))
    stored=store.get('balance-worked-fixture')
    assert stored['residual_kwh']==pytest.approx(1.6,abs=.001);assert stored['residual_ratio']==pytest.approx(.128)
    b=next(b for b in reconcile('fixture',0,obs) if b['boundary_asset_id']=='branch-03')
    assert b['residual_kwh']==pytest.approx(12.5-10.5-expected_loss('branch',10.5))

def test_three_interval_persistence_and_smallest_section(client):
    s=run(client);rid=s['run']['id']; assert not s['alerts']
    for _ in range(2): assert not step(client,rid)['alerts']
    s=step(client,rid);assert len(s['alerts'])==1
    assert s['alerts'][0]['boundary_asset_id']=='branch-03';assert s['alerts'][0]['consecutive_intervals']==3
    assert not s['alerts'][0]['candidate_meter_ids']
    assert 'scenario_settings' not in s['run'];assert 'truth' not in s
    assert client.get('/api/runs/'+rid+'/truth').status_code==403

@pytest.mark.parametrize('scenario',['clean','legitimate_load_change','missing_telemetry'])
def test_negative_controls(client,scenario):
    s=run(client,scenario);s=step(client,s['run']['id'],12)
    assert not any(a['status']=='active' for a in s['alerts'])
    if scenario=='missing_telemetry':
        assert s['readings']['household-07']['energy_import_kwh'] is None
        b=next(b for b in s['balances'] if b['boundary_asset_id']=='branch-03')
        assert b['residual_kwh'] is None and b['validity']=='data_incomplete';assert s['quality_events']

def test_missing_breaks_persistence(client):
    s=run(client);rid=s['run']['id']
    post(client,f'/runs/{rid}/incidents',dict(type='missing_telemetry',target_asset_id='branch-03',start=3,end=4,severity=1),'presenter')
    s=step(client,rid,5);assert not s['alerts']
    s=step(client,rid);assert s['alerts'][0]['first_interval']==4

def test_deterministic_replay(client):
    outputs=[]
    for _ in range(2):
        s=run(client,seed=81);s=step(client,s['run']['id'],5)
        outputs.append(([r['energy_import_kwh'] for r in s['readings'].values()],[(a['boundary_asset_id'],a['first_interval']) for a in s['alerts']]))
    assert outputs[0]==outputs[1]

def test_validity_gates_and_negative_residual():
    for bad in ['quality','topology','time','negative','export']:
        obs=generate(42,1,[])['readings'];r=obs['household-07']
        if bad=='quality':r['quality']='estimated'
        if bad=='topology':r['topology_version']='unknown'
        if bad=='time':r['interval_start']='2020-01-01T00:00:00Z'
        if bad=='negative':r['energy_import_kwh']=-3
        if bad=='export':r['energy_export_kwh']=2
        b=next(b for b in reconcile('fixture',1,obs) if b['boundary_asset_id']=='branch-03')
        assert b['validity']=='data_incomplete' and not b['qualifies']
    obs=generate(42,1,[])['readings'];obs['branch-03']['energy_import_kwh']=0
    b=next(b for b in reconcile('fixture',1,obs) if b['boundary_asset_id']=='branch-03')
    assert b['residual_kwh']<0 and b['negative_review']

@pytest.mark.parametrize('view',[0,1])
def test_image_pixel_positive_negative_controls(view):
    clean,pose=fixture_image(view=view);positive,_=fixture_image(positive=True,view=view);decorative,_=fixture_image(decorative=True,view=view)
    c,_=inspection.detect(clean,pose,'branch-03');p,annotated=inspection.detect(positive,pose,'branch-03');d,_=inspection.detect(decorative,pose,'branch-03')
    assert c['observation_status']=='no_visible_candidate',c
    assert p['observation_status']=='candidate_found',p
    assert d['observation_status']=='no_visible_candidate',d
    assert not np.array_equal(positive,annotated)
    blank,_=fixture_image(blank=True,view=view);b,_=inspection.detect(blank,pose,'branch-03');assert b['observation_status']=='inconclusive'

@pytest.mark.parametrize('seed',[42,56,73])
def test_case_roles_revision_mission_export_and_reopen(client,seed):
    c=case(client,seed=seed);cid=c['id']
    duplicate=post(client,'/cases',dict(alert_id=c['alert_id'],idempotency_key='retry'));assert duplicate['id']==cid
    patch(client,'/cases/'+cid,dict(expected_revision=0,note='stale'),'reviewer',409)
    c=patch(client,'/cases/'+cid,dict(expected_revision=c['revision'],assigned_to='Demo reviewer'))
    c=move(client,c,'triaged','analyst')
    post(client,f'/cases/{cid}/missions',dict(approved=True,idempotency_key='approved'),'analyst',403)
    post(client,f'/cases/{cid}/missions',dict(approved=False,idempotency_key='not-approved'),'reviewer',400)
    m=post(client,f'/cases/{cid}/missions',dict(approved=True,idempotency_key='approved'),'reviewer')
    assert post(client,f'/cases/{cid}/missions',dict(approved=True,idempotency_key='approved'),'reviewer')['id']==m['id']
    patch(client,'/missions/'+m['id'],dict(status='flying'),'reviewer')
    post(client,f"/runs/{c['run_id']}/control",dict(command='step'),status=409)
    original_hash=None
    for i in range(2):
        image,pose=fixture_image(positive=i==0,view=i);raw=cv2.imencode('.png',image)[1].tobytes()
        body=dict(png_base64=base64.b64encode(raw).decode(),camera_pose=pose,capture_sequence=m['capture_sequence'],approved_geometry_version='topology-1',frame_key='test-'+str(i),capture_source='pixel_control_fixture')
        e=post(client,f"/missions/{m['id']}/frames",body,'reviewer');assert e['original_sha256']==hashlib.sha256(raw).hexdigest()
        assert post(client,f"/missions/{m['id']}/frames",body,'reviewer')['id']==e['id']
        original_hash=e['original_sha256'];assert client.get(e['original_image_path']).content==raw
        bad={**body,'frame_key':'bad','is_theft':True};post(client,f"/missions/{m['id']}/frames",bad,'reviewer',422)
    patch(client,'/missions/'+m['id'],dict(status='completed'),'reviewer')
    d=client.get('/api/cases/'+cid).json();c=d['case'];assert c['state']=='evidence_ready'
    c=move(client,c,'under_review');c=move(client,c,'field_check_required');c=move(client,c,'under_review')
    patch(client,'/cases/'+cid,dict(expected_revision=c['revision'],state='dismissed',disposition='inconclusive',reason=''),'supervisor',400)
    patch(client,'/cases/'+cid,dict(expected_revision=c['revision'],state='resolved',disposition='inconclusive',reason='test'),'reviewer',403)
    c=move(client,c,'dismissed','supervisor');c=move(client,c,'reopened','supervisor');c=move(client,c,'triaged','analyst')
    report=client.get(f'/api/cases/{cid}/export?format=json');data=report.json()
    assert hashlib.sha256(report.content).hexdigest()==report.headers['X-Content-SHA256']
    assert data['evidence'][0]['original_sha256']==original_hash
    assert data['analysis']['readings'];assert data['run']['rule_version'];assert len(data['audit'])>=12;assert len(data['contributing_intervals'])==3
    assert client.get(f'/api/cases/{cid}/export?format=md').content.startswith(b'# GridTrace')
    # A fresh Python process opens the same DB and local PNGs after the writer commits.
    script="from backend import store; import hashlib,json,sys; c=store.get(sys.argv[1]); e=store.get(c['evidence_ids'][-1]); raw=(store.ROOT/'evidence'/e['original_image_path'].split('/')[-1]).read_bytes(); print(json.dumps({'case_id':c['id'],'stored_hash':e['original_sha256'],'file_hash':hashlib.sha256(raw).hexdigest(),'events':len(store.audits(c['id']))}))"
    fresh=subprocess.run([sys.executable,'-c',script,cid],capture_output=True,text=True,check=True)
    recovered=json.loads(fresh.stdout);assert recovered['stored_hash']==recovered['file_hash']==original_hash;assert recovered['events']>=12
    run(client,'clean');assert client.get('/api/cases/'+cid).json()['case']['run_id']==c['run_id']
    with pytest.raises(Exception):store.DB.execute('DELETE FROM audit WHERE case_id=?',(cid,))

def test_image_validation(client):
    c=case(client);c=move(client,c,'triaged','analyst');m=post(client,f"/cases/{c['id']}/missions",dict(approved=True,idempotency_key='image-validation'),'reviewer');patch(client,'/missions/'+m['id'],dict(status='flying'),'reviewer')
    pose=fixture_image()[1]
    post(client,f"/missions/{m['id']}/frames",dict(png_base64=base64.b64encode(b'not-png').decode(),camera_pose=pose,capture_sequence=m['capture_sequence'],approved_geometry_version='topology-1',frame_key='bad',capture_source='pixel_control_fixture'),'reviewer',400)
    patch(client,'/missions/'+m['id'],dict(status='capturing'),'reviewer')
    patch(client,'/missions/'+m['id'],dict(status='completed'),'reviewer',400)

def test_observed_revision_restore_and_duplicate_rejection(client):
    s=run(client,'missing_telemetry');rid=s['run']['id'];s=step(client,rid,3)
    # Restoration is an explicit supplied observation, not a detector query of truth.
    replacement=generate(42,2,[])['readings']['household-07']['energy_import_kwh']
    body=dict(asset_id='household-07',sequence=2,expected_revision=1,energy_import_kwh=replacement,quality='valid')
    revised=post(client,f'/runs/{rid}/readings/revise',body)
    restored=client.get(f'/api/runs/{rid}/snapshot?seq=2').json()
    assert restored['readings']['household-07']['revision']==2
    assert next(b for b in restored['balances'] if b['boundary_asset_id']=='branch-03')['validity']=='valid'
    assert revised['analysis_revision']==2
    post(client,f'/runs/{rid}/readings/revise',body,status=409)
    archived=client.get(f'/api/runs/{rid}/analysis-revisions').json()
    assert archived['recomputations'];assert any(r['readings']['household-07']['energy_import_kwh'] is None for r in archived['revisions'])

def test_failed_processing_preserves_original_and_review_path(client,monkeypatch):
    c=case(client);c=move(client,c,'triaged','analyst');m=post(client,f"/cases/{c['id']}/missions",dict(approved=True,idempotency_key='cv-failure'),'reviewer');patch(client,'/missions/'+m['id'],dict(status='flying'),'reviewer')
    image,pose=fixture_image(positive=True);raw=cv2.imencode('.png',image)[1].tobytes()
    def fail(*args):raise RuntimeError('Deliberate processing failure control')
    monkeypatch.setattr(inspection,'detect',fail)
    post(client,f"/missions/{m['id']}/frames",dict(png_base64=base64.b64encode(raw).decode(),camera_pose=pose,capture_sequence=m['capture_sequence'],approved_geometry_version='topology-1',frame_key='failed-view',capture_source='pixel_control_fixture'),'reviewer',500)
    d=client.get('/api/cases/'+c['id']).json();e=d['evidence'][0]
    assert e['observation_status']=='inconclusive' and e['processing_error'];assert e['annotated_image_path'] is None
    assert client.get(e['original_image_path']).content==raw;assert e['camera_pose']==pose
    assert d['missions'][0]['status']=='failed'
    c=move(client,d['case'],'under_review');c=move(client,c,'field_check_required')
    assert c['state']=='field_check_required'

def test_latency_100_intervals():
    durations=[]
    for i in range(100):
        start=time.perf_counter();obs=generate(77,i,[])['readings'];reconcile('latency',i,obs);durations.append((time.perf_counter()-start)*1000)
    p95=sorted(durations)[94];assert p95<500
    print(f'100 simulation+reconciliation intervals p95={p95:.2f}ms')
