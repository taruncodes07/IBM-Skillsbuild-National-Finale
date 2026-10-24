"""Declared small synthetic suite. Does not claim scene-rendered CV evaluation."""
import os,tempfile,json,time,statistics,platform,sys,logging
from pathlib import Path
os.environ['GRIDTRACE_DATA']=tempfile.mkdtemp(prefix='gridtrace-eval-')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import engine,store,inspection
from backend.simulation import stamp
from test_acceptance import fixture_image
logging.getLogger().setLevel(logging.WARNING)

def evaluate():
    calibrations=[]
    for seed in [11,23,37,49]:
        r=engine.create_run(seed,'clean');calibrations.append(dict(seed=seed,max_sigma_kwh=max(r['sigmas'].values()),baseline_intervals=672))
    scenarios=['clean','clean','legitimate_load_change','missing_telemetry','visible_unmetered_load','visible_unmetered_load','hidden_bypass','occlusion','meter_underregistration','meter_underregistration','topology_mismatch','technical_loss_change']
    rows=[];latency=[];matches=0;eligible=0;false=0;clean_hours=0;delays=[];errors=[]
    for seed,scenario in zip(range(101,113),scenarios):
        r=engine.create_run(seed,scenario);rid=r['id'];first={};residual=0;injected=0
        for seq in range(96):
            if seq:
                t=time.perf_counter();engine.step(r);latency.append((time.perf_counter()-t)*1000)
            s=store.interval(rid,seq)
            for a in s['alerts']:
                if a['status']=='active' and a['boundary_asset_id'] not in first:first[a['boundary_asset_id']]=seq
            for b in s['balances']:
                if b['boundary_asset_id'].startswith('branch-') and b['validity']=='valid' and (b['boundary_asset_id']!='branch-03' or scenario in ('clean','legitimate_load_change')):clean_hours+=.25
            if 1<=seq<80:
                b=next(b for b in s['balances'] if b['boundary_asset_id']=='branch-03')
                if b['residual_kwh'] is not None:residual+=b['residual_kwh']
                if scenario in ('visible_unmetered_load','hidden_bypass','occlusion'):injected+=1.2
        positive=scenario in ('visible_unmetered_load','hidden_bypass','occlusion','meter_underregistration')
        if positive:
            eligible+=1
            if first.get('branch-03',1000)<=80: matches+=1;delays.append((first['branch-03']+1-1)*15)
        false+=sum(sid!='branch-03' or scenario in ('clean','legitimate_load_change','missing_telemetry') for sid in first)
        error=abs(residual-injected)/injected if injected else None
        if error is not None:errors.append(error)
        rows.append(dict(seed=seed,scenario=scenario,first_alert_sequence_by_boundary=first,eligible_positive=positive,estimated_unexplained_kwh=residual,injected_unmetered_kwh=injected,relative_energy_error=error))
    cvrows=[];cvtime=[]
    for view in range(2):
        for label,options in [('positive',dict(positive=True)),('negative',{}),('decorative',dict(decorative=True)),('blank',dict(blank=True))]:
            im,pose=fixture_image(view=view,**options);t=time.perf_counter();out,_=inspection.detect(im,pose,'branch-03');cvtime.append((time.perf_counter()-t)*1000)
            cvrows.append(dict(view=view,fixture=label,status=out['observation_status'],candidate_regions=len(out['observations'])))
    report=dict(disclosure='Synthetic diagnostic suite only. CV fixtures are rasterized pixel controls, NOT actual GPU scene captures. No held-out rendered IoU precision/recall is claimed.',reference=dict(platform=platform.platform(),processor=platform.processor(),python=platform.python_version(),browser='Unavailable; browser QA and FPS unverified'),calibration_runs=calibrations,held_out_runs=rows,eligible_event_recall=dict(matched=matches,eligible=eligible,ratio=matches/eligible),localization=dict(correct=matches,matched=matches),control_false_alerts=dict(count=false,valid_clean_branch_hours=clean_hours,rate_per_100_hours=false/clean_hours*100),detection_delay_sim_minutes=dict(median=statistics.median(delays),p95=sorted(delays)[math_ceil(.95*len(delays))-1]),energy_error=dict(mean=statistics.mean(errors),max=max(errors)),interval_latency_ms=dict(samples=len(latency),p95=sorted(latency)[math_ceil(.95*len(latency))-1],max=max(latency)),pixel_control_results=cvrows,cv_latency_ms=dict(samples=len(cvtime),max=max(cvtime)),browser_verification=dict(live_scene_capture='UNVERIFIED',layout='UNVERIFIED',fps='UNMEASURED',three_end_to_end_browser_rehearsals='NOT RUN'))
    Path('docs/verification-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('held_out_runs','pixel_control_results')},indent=2))

def math_ceil(v):return int(v)+int(v!=int(v))
if __name__=='__main__':evaluate()
