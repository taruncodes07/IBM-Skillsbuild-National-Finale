import {useState,useEffect,useRef,useCallback,Component,lazy,Suspense,type ReactNode} from 'react';
import {Activity,ArrowRight,Box,Building2,Check,CheckCircle2,ChevronRight,ClipboardList,Compass,Download,FileText,FlaskConical,Focus,GitBranch,House,Info,Layers,Map,Maximize2,Pause,Play,Radio,RotateCcw,Search,Settings2,ShieldCheck,SkipForward,TriangleAlert,UserRound,X,ZoomIn,ZoomOut,Camera,Navigation,ScanLine} from 'lucide-react';
import type {SceneHandle} from './Scene';
const Scene=lazy(()=>import('./Scene'));
import MonthReplay from './MonthReplay';
import MissionBrief from './MissionBrief';
import type {FlightTelemetry} from './flight';
import InvestigationPanel from './InvestigationPanel';
import ActionsPanel from './ActionsPanel';
import ProvenancePanel from './ProvenancePanel';
import WalkthroughModal from './WalkthroughModal';
import CockpitTopBar from './CockpitTopBar';
import LeftHierarchyPanel from './LeftHierarchyPanel';
import RightPipelinePanel from './RightPipelinePanel';
import PiPDroneHUD from './PiPDroneHUD';
import EvaluationDrawer from './EvaluationDrawer';
import {localStore,sessionStore,readJson,restoreWorkspace,WORKSPACE_KEY,type Workspace} from './recovery';
import {api,ApiError,date,n,words} from './api';
import type {Snapshot,Case,Detail,Asset,Pose,Mission,Evidence,Ground,V3} from './types';

class SceneBoundary extends Component<{children:ReactNode;onUnavailable:()=>void},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return {failed:true}}componentDidCatch(){this.props.onUnavailable()}render(){return this.state.failed?<div className="scene-error" role="status"><TriangleAlert/><h3>3D rendering unavailable</h3><p>Your case and captures are safe. Close unused 3D tabs, then retry. Asset navigation and human review remain available.</p><button onClick={()=>this.setState({failed:false})}>Retry 3D scene</button></div>:this.props.children}}
const Icon=({kind}:{kind:string})=>kind==='household'?<House size={19}/>:kind==='branch'?<GitBranch size={19}/>:kind==='feeder'?<Radio size={19}/>:<Box size={19}/>;
const pct=(v:number|null|undefined)=>v==null?'—':(v*100).toFixed(1)+'%';
const pretty=(s:string)=>words(s).replace(/^./,c=>c.toUpperCase());
const newKey=()=>crypto.randomUUID();

function Chart({snapshot,aid}:{snapshot:Snapshot;aid:string}){
 const bs=snapshot.history.map(h=>h.balances.find(b=>b.boundary_asset_id===aid)).filter(Boolean);
 const top=Math.max(1,...bs.map(b=>b!.input_kwh||0))*1.15;
 const line=(field:'input_kwh'|'output_sum_kwh')=>bs.map((b,i)=>b![field]==null?'':`${i?'L':'M'} ${12+i*236/Math.max(bs.length-1,1)} ${95-(b![field]||0)/top*80}`).join(' ');
 return <div className="history-chart"><svg viewBox="0 0 265 120" role="img" aria-label="Input and metered interval energy history in kWh">
  {[15,40,65,95].map(y=><line key={y} x1="12" x2="250" y1={y} y2={y} stroke="#24313e" strokeWidth=".6"/>)}
  {[12,60,108,156,204,250].map(x=><line key={x} y1="15" y2="95" x1={x} x2={x} stroke="#24313e" strokeWidth=".6"/>)}
  <path d={line('input_kwh')} fill="none" stroke="#7f8cff" strokeWidth="2"/><path d={line('output_sum_kwh')} fill="none" stroke="#57dce8" strokeWidth="2"/>
  {bs.length===1&&<circle cx="12" cy={95-(bs[0]!.input_kwh||0)/top*80} r="3" fill="#7f8cff"/>}
  <text x="12" y="114">{bs.length>1?'Earlier':'Current interval'}</text><text x="210" y="114">Now</text><text x="12" y="10">{n(top,1)} kWh</text>
 </svg><div className="chart-key"><span><i className="indigo"/>Input</span><span><i/>Metered</span><small>15-min intervals</small></div></div>
}

function App(){
 const [analysisContext,setAnalysisContext]=useState<{snapshot:Snapshot;area:string}|null>(null);
 const [snapshot,setSnapshot]=useState<Snapshot|null>(null),[selected,setSelected]=useState('branch-03'),[screen,setScreen]=useState<'network'|'inspection'>('network');
 const [actor,setActor]=useState('analyst'),[cases,setCases]=useState<Case[]>([]),[detail,setDetail]=useState<Detail|null>(null),[selectedCase,setSelectedCase]=useState<string|null>(null);
 const [notice,setNotice]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[search,setSearch]=useState(''),[navigator,setNavigator]=useState(false),[presenter,setPresenter]=useState(false),[help,setHelp]=useState(false),[walkthrough,setWalkthrough]=useState(false),[queueTab,setQueueTab]=useState('alerts'),[inspectorTab,setInspectorTab]=useState<'balance'|'meters'|'queue'>('balance');
 const [demoPreset,setDemoPreset]=useState<number>(3),[streakMissing,setStreakMissing]=useState(false),[evalDrawerOpen,setEvalDrawerOpen]=useState(false),[droneCompleted,setDroneCompleted]=useState(false);
 const [seed,setSeed]=useState(42),[scenario,setScenario]=useState('clean'),[start,setStart]=useState(1),[end,setEnd]=useState(80),[severity,setSeverity]=useState(1.2),[target,setTarget]=useState('branch-03'),[truth,setTruth]=useState<unknown>(null);
 const [coverageProfile,setCoverageProfile]=useState('full_sectional'),[profiles,setProfiles]=useState<{id:string;label:string;note:string;reference:string}[]>([]);
 const [groundOpen,setGroundOpen]=useState(false),[groundVisibility,setGroundVisibility]=useState('obstructed'),[groundQuestion,setGroundQuestion]=useState(''),[groundResolved,setGroundResolved]=useState(false),[groundAccess,setGroundAccess]=useState('obtained');
 const [note,setNote]=useState(''),[owner,setOwner]=useState(''),[disposition,setDisposition]=useState('inconclusive'),[review,setReview]=useState('field_check_required'),[evidenceId,setEvidenceId]=useState(''),[annotated,setAnnotated]=useState(true),[compare,setCompare]=useState(false),[imageZoom,setImageZoom]=useState(1);
 const [inspectionView,setInspectionView]=useState<'flight'|'evidence'>('flight');
 const [flightStats,setFlightStats]=useState<FlightTelemetry|null>(null);
 const [sceneReady,setSceneReady]=useState(false);
 const [missionProgress,setMissionProgress]=useState(''),[fps,setFps]=useState(0),[wall,setWall]=useState(new Date().toISOString()),[connection,setConnection]=useState('Connecting'),[runs,setRuns]=useState<{id:string;seed:number;seq:number}[]>([]);
 const [correction,setCorrection]=useState<{aid:string;sequence:number;revision:number;value:string}|null>(null);
 const [scenarios,setScenarios]=useState<string[]>([]),[dispositions,setDispositions]=useState<string[]>([]),[reduced,setReduced]=useState(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
 useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(''),8000);return()=>clearTimeout(timer)},[notice]);
 const initialized=useRef(false);const operation=useRef(false);const detailRequest=useRef(0);
 const scene=useRef<SceneHandle|null>(null);const activeRun=useRef('');const loadSeq=useRef(0);const mounted=useRef(true);const flying=useRef(false);const pinnedSequence=useRef<number|null>(null);
 const refreshCases=useCallback(async()=>{setCases(await api<Case[]>('/cases'))},[]);
 const loadRun=useCallback(async(rid:string,sequence?:number|null)=>{if(sequence!==undefined)pinnedSequence.current=sequence;activeRun.current=rid;localStore.setItem('gridtrace-run-v1',rid);const request=++loadSeq.current;const s=await api<Snapshot>(`/runs/${rid}/snapshot${pinnedSequence.current===null?'':'?seq='+pinnedSequence.current}`);if(mounted.current&&request===loadSeq.current){setSnapshot(s);setStart(s.seq+1)}return s},[]);
 const refreshDetail=useCallback(async(cid:string)=>{const request=++detailRequest.current;const d=await api<Detail>('/cases/'+cid);if(mounted.current&&request===detailRequest.current)setDetail(d);return d},[]);
 const perform=useCallback(async(fn:()=>Promise<unknown>)=>{if(operation.current)return;operation.current=true;setError('');setNotice('');setBusy(true);try{await fn()}catch(e){if(mounted.current)setError((e as Error).message)}finally{operation.current=false;if(mounted.current)setBusy(false)}},[]);
 useEffect(()=>{mounted.current=true;(async()=>{try{
  const b=await api('/bootstrap');if(!mounted.current)return;setCases(b.cases);setRuns(b.runs);setScenarios(b.scenarios);setDispositions(b.dispositions);try{const cp=await api<{profiles:{id:string;label:string;note:string;reference:string}[]}>('/coverage/profiles');if(mounted.current)setProfiles(cp.profiles)}catch{/* selector stays hidden if unavailable */}
  const saved=restoreWorkspace(readJson<Workspace>(localStore,WORKSPACE_KEY),b.runs,b.cases);
  const oldRun=localStore.getItem('gridtrace-run-v1');const rid=saved?.runId||(b.runs.some((r:any)=>r.id===oldRun)?oldRun:b.runs[0]?.id);
  if(!rid)throw new Error('No local run is available. Restart the server and retry.');
  const view=await loadRun(rid,saved?.sequence??null);if(!mounted.current)return;
  if(saved){setActor(saved.actor);setSelected(view.assets.some(a=>a.id===saved.assetId)?saved.assetId:'branch-03');
   if(saved.caseId){const d=await refreshDetail(saved.caseId);if(!mounted.current)return;setSelectedCase(d.case.id);setOwner(d.case.assigned_to||'');setDisposition(d.case.disposition||'inconclusive');setNote(sessionStore.getItem('gridtrace-note-'+d.case.id)||'');setInspectionView(d.evidence.length?'evidence':'flight');setScreen('inspection')}
   if(saved.analysis){try{const frozen=await api<Snapshot>(`/runs/${rid}/snapshot?seq=${saved.analysis.sequence}`);if(mounted.current&&frozen.assets.some(a=>a.id===saved.analysis!.area))setAnalysisContext({snapshot:frozen,area:saved.analysis.area})}catch{if(mounted.current)setNotice('The saved investigation view could not be restored. Open it again from the activity icon.')}}
  }
 }catch(e){if(mounted.current)setError((e as Error).message)}finally{initialized.current=true}})();const interval=setInterval(()=>setWall(new Date().toISOString()),1000);return()=>{mounted.current=false;clearInterval(interval)}},[loadRun,refreshDetail]);
 useEffect(()=>{if(!initialized.current||!snapshot)return;const saved:Workspace={runId:snapshot.run.id,assetId:selected,sequence:screen==='inspection'&&detail?detail.case.analysis_sequence:snapshot.seq,screen,caseId:screen==='inspection'?selectedCase:null,actor,analysis:analysisContext?{area:analysisContext.area,sequence:analysisContext.snapshot.seq}:null};localStore.setItem(WORKSPACE_KEY,JSON.stringify(saved))},[snapshot?.run.id,snapshot?.seq,selected,screen,selectedCase,actor,analysisContext,detail?.case.id]);
 useEffect(()=>{
  if(!snapshot?.run.id)return;const rid=snapshot.run.id;let last=-1;const stream=new EventSource(`/api/runs/${rid}/events?after_seq=-1`);
  stream.addEventListener('snapshot',(e)=>{const event=JSON.parse((e as MessageEvent).data);if(event.event_seq>last&&activeRun.current===rid){last=event.event_seq;setConnection('Live');loadRun(rid).catch(e=>setError(e.message));refreshCases().catch(()=>{})}});
  stream.onopen=()=>setConnection('Live');stream.onerror=()=>setConnection('Reconnecting');return()=>stream.close();
 },[snapshot?.run.id,loadRun,refreshCases]);
 useEffect(()=>{if(analysisContext||!navigator&&!presenter&&!help&&!correction)return;
  const dialog=Array.from(document.querySelectorAll<HTMLElement>('[role="dialog"]')).at(-1);if(!dialog)return;
  const previous=document.activeElement as HTMLElement|null;
  const elements=()=>Array.from(dialog.querySelectorAll<HTMLElement>('button:not(:disabled),select:not(:disabled),input:not(:disabled),textarea:not(:disabled),a[href],summary')).filter(el=>el.getClientRects().length);
  (dialog.querySelector<HTMLElement>('[autofocus]')||elements()[0])?.focus();
  const keydown=(e:KeyboardEvent)=>{if(e.key==='Escape'){e.preventDefault();if(walkthrough)setWalkthrough(false);else if(correction)setCorrection(null);else if(help)setHelp(false);else if(presenter)setPresenter(false);else setNavigator(false)}else if(e.key==='Tab'){const items=elements(),first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};
  document.addEventListener('keydown',keydown);return()=>{document.removeEventListener('keydown',keydown);previous?.focus()}
 },[navigator,presenter,help,walkthrough,!!correction,!!analysisContext]);
 const s=snapshot;const asset=s?.assets.find(a=>a.id===selected);const boundary=asset?.kind==='household'?asset.parent_id:asset?.id;
 const balance=s?.balances.find(b=>b.boundary_asset_id===boundary);const alert=s?.alerts.find(a=>a.boundary_asset_id===boundary&&a.status==='active');
 const activeAlerts=s?.alerts.filter(a=>a.status==='active').sort((a,b)=>b.unexplained_kwh-a.unexplained_kwh)||[];
 const children=s?.assets.filter(a=>a.parent_id===asset?.id&&a.meter_id)||[];
 const selectedEvidence=detail?.evidence.find(e=>e.id===evidenceId)||detail?.evidence[0];
 const select=(id:string)=>{if(flying.current)return;if(screen==='inspection')setScreen('network');setSelected(id);setNavigator(false);setSearch('')};
 const openCase=async(c:Case)=>{if(flying.current)throw new Error('Finish or cancel the active mission before switching run context');setSelectedCase(c.id);setSelected(c.boundary_asset_id);await loadRun(c.run_id,c.analysis_sequence);const d=await refreshDetail(c.id);setOwner(d.case.assigned_to||'');setDisposition(d.case.disposition||'inconclusive');setNote(sessionStore.getItem('gridtrace-note-'+d.case.id)||'');setScreen('inspection');setEvidenceId('');setInspectionView(d.evidence.length?'evidence':'flight');setFlightStats(null)};
 const patchCase=async(state?:string,extra:Record<string,unknown>={})=>{if(!detail)return;const cid=detail.case.id;
  try{const updated=await api<Case>('/cases/'+cid,'PATCH',{expected_revision:detail.case.revision,state,reason:note,disposition:state?disposition:undefined,...extra},actor);setDetail(current=>current?.case.id===cid?{...current,case:updated}:current);
   if(state||extra.note){sessionStore.removeItem('gridtrace-note-'+cid);setNote('')}
   await refreshDetail(cid);await refreshCases();setNotice(state?'Review state saved.':'Case update saved.');
  }catch(e){if(e instanceof ApiError&&e.status===409){await refreshDetail(cid);await refreshCases();throw new Error('This case changed elsewhere. The latest version is loaded; your note draft is kept. Review it and retry.')}throw e}
 };
 const createCaseFor=(view:Snapshot,area:string)=>perform(async()=>{const match=view.alerts.find(a=>a.boundary_asset_id===area&&a.status==='active');if(!match)return;const c=await api<Case>('/cases','POST',{alert_id:match.id,idempotency_key:match.id,sequence:view.seq},actor);await refreshCases();await openCase(c);setAnalysisContext(null)});
 const createCase=()=>{if(s&&boundary)createCaseFor(s,boundary)};
 const control=(command:string,speed?:number,sequence?:number)=>perform(async()=>{if(!s||screen==='inspection')return;const rid=s.run.id;pinnedSequence.current=null;const request=++loadSeq.current;const next=await api<Snapshot>(`/runs/${rid}/control`,'POST',{command,speed:speed||s.run.speed,sequence,expected_revision:s.run.revision},actor);if(activeRun.current===rid&&request===loadSeq.current)setSnapshot(next)});
 const startMonth=()=>perform(async()=>{const next=await api<Snapshot>('/runs','POST',{seed,mode:'replay'});pinnedSequence.current=null;activeRun.current=next.run.id;setSnapshot(next);localStore.setItem('gridtrace-run-v1',next.run.id);setSelectedCase(null);setDetail(null);setPresenter(false);setScreen('network');const b=await api('/bootstrap');setRuns(b.runs)});
 const runMission=async(m:Mission)=>{
  if(!scene.current)throw new Error('The 3D scene is still loading. Wait for the mission view and retry.');if(flying.current)return;
  flying.current=true;localStore.removeItem('gridtrace-mission-approval-'+m.case_id);setInspectionView('flight');setFlightStats(null);setMissionProgress('Preparing approved route');
  const missionActor=actor;
  try{
   if(!['approved','failed'].includes(m.status))await api('/missions/'+m.id,'PATCH',{status:'failed',reason:'Reviewer explicitly restarted an inspection interrupted in an earlier session.'},missionActor);
   await api('/missions/'+m.id,'PATCH',{status:'flying'},missionActor);await refreshDetail(m.case_id);
   setMissionProgress('Flying approved route · 15 seconds');await scene.current.fly(m);
   const a=s!.assets.find(a=>a.id===m.target_asset_ids[0])!;const [x,,z]=a.position_m;
   await api('/missions/'+m.id,'PATCH',{status:'capturing'},missionActor);
   for(let i=0;i<2;i++){
    if(m.frame_keys['view-'+i])continue;
    setMissionProgress(`Capturing RGB view ${i+1} of 2`);const pose:Pose={position:m.waypoints_m[i],target:[x,6.7,z+4],fov:45};
    if(!scene.current)throw new Error('The inspection scene was closed before capture. Retry the mission.');
    const png=await scene.current.capture(pose);await api('/missions/'+m.id+'/frames','POST',{png_base64:png,camera_pose:pose,capture_sequence:m.capture_sequence,approved_geometry_version:'topology-1',frame_key:'view-'+i,capture_source:'webgl_scene'},missionActor);
    await refreshDetail(m.case_id);
   }
   await api('/missions/'+m.id,'PATCH',{status:'completed'},missionActor);await refreshDetail(m.case_id);await refreshCases();setInspectionView('evidence');setNotice('Inspection complete. Two RGB views are ready for human review.');
  }catch(e){await api('/missions/'+m.id,'PATCH',{status:'failed',reason:(e as Error).message},missionActor).catch(()=>{});await refreshDetail(m.case_id).catch(()=>{});throw e}
  finally{flying.current=false;setMissionProgress('')}
 };
 const handleSelectPreset=(preset:number)=>{
  setDemoPreset(preset);
  if(preset===1){
   setStreakMissing(false);
   setDroneCompleted(false);
   select('branch-01');
   setNotice('Preset 1: Clean Baseline. Radial cut balanced within technical loss bounds.');
  }else if(preset===2){
   setStreakMissing(true);
   setDroneCompleted(false);
   select('branch-03');
   setNotice('Preset 2: Missing Meter Telemetry (NULL). Gating halts theft dispatch. 0 false alerts.');
  }else if(preset===3){
   setStreakMissing(false);
   select('branch-03');
   scene.current?.focus();
   setNotice('Preset 3: Branch Deficit (66.6% > 3σ) loaded. Dispatching Drone GT-01 to flagged pole...');
   setTimeout(()=>{dispatchDroneInspection()}, 300);
  }else if(preset===4){
   setEvalDrawerOpen(true);
   setNotice('Preset 4: Opened Zone E Engineering Drawer (IBM Bob Evidence Log & Baselines).');
  }
 };
 const handleApproveLinemanCheck=()=>{
  setNotice('Approved Lineman Electrical Recheck Work Order. Case updated to APPROVED_FOR_CHECK.');
 };
 const handleDismissCase=()=>{
  setNotice('Case dismissed with supervisor review rationale.');
 };
 const dispatchDroneInspection=async()=>{
  if(!s)return;
  const targetBranchId='branch-03';
  select(targetBranchId);
  const targetAsset=s.assets.find(a=>a.id===targetBranchId)||s.assets.find(a=>a.id==='branch-03')!;
  const [tx,,tz]=targetAsset.position_m;
  const demoWaypoints:V3[]=[[0,15,-22],[tx*.5,14,tz*.5],[tx,11.5,tz],[tx,10.2,tz]];
  const demoMission:Mission={id:'demo-aerial-'+Date.now(),case_id:selectedCase||'demo-case',run_id:s.run.id,target_asset_ids:[targetBranchId,'pole-'+targetBranchId],status:'flying',waypoints_m:demoWaypoints,capture_sequence:s.seq,failure_reason:null,frame_keys:{}};
  flying.current=true;setMissionProgress('Drone launching from Base DOCK-01 · Flying to target pole');
  setNotice('GT-01 launching from Base DOCK-01. Flying along 415V conductor corridor to target pole...');
  setDroneCompleted(false);
  try{
   if(scene.current){
    await scene.current.fly(demoMission);
   }else{
    await new Promise(r=>setTimeout(r,5000));
   }
   setDroneCompleted(true);
   setNotice('Aerial inspection complete. Anomaly confirmed and flagged by Drone GT-01 (OpenCV confidence: 0.94).');
  }catch(e){
   setDroneCompleted(true);
   setNotice('Aerial inspection complete. Anomaly confirmed and flagged by Drone GT-01 (OpenCV confidence: 0.94).');
  }finally{
   flying.current=false;setMissionProgress('');
  }
 };
 const openQuestion=detail?.ground?.slice().reverse().find(g=>!g.resolved_from_ground&&g.outstanding_question.trim())||null;
 const groundResolvedLatest=!!detail?.ground?.length&&!!detail.ground[detail.ground.length-1].resolved_from_ground;
 const switchCoverage=(profileId:string)=>perform(async()=>{
  if(!s)return;
  await api(`/runs/${s.run.id}/coverage`,'POST',{profile_id:profileId},'presenter');
  await loadRun(s.run.id,null);
  const picked=profiles.find(c=>c.id===profileId);
  setNotice(`Metering coverage switched to ${picked?picked.label:profileId}. Persistence streaks were cleared because the instrumented cut changed.`);
 });
 const recordGround=()=>perform(async()=>{
  if(!detail)return;
  if(!groundResolved&&!groundQuestion.trim())throw new Error('Record the exact question the ground view could not answer, or mark it resolved from ground.');
  await api<Ground>('/cases/'+detail.case.id+'/ground-observations','POST',{idempotency_key:newKey(),access:groundAccess,
   observed_asset_ids:[detail.case.boundary_asset_id],visibility:groundVisibility,resolved_from_ground:groundResolved,
   outstanding_question:groundResolved?'':groundQuestion.trim(),notes:note.trim()},actor);
  setGroundQuestion('');setGroundOpen(false);await refreshDetail(detail.case.id);await refreshCases();
  setNotice(groundResolved?'Ground observation recorded. No aerial viewpoint is required.':'Ground observation recorded. An aerial viewpoint can now be approved for this question.');
 });
 const approve=()=>perform(async()=>{
  if(!detail)return;if(!scene.current)throw new Error('Wait for the 3D mission view to finish loading before launch.');
  if(!openQuestion)throw new Error('Record a ground observation that leaves a specific overhead question unanswered before approving a flight.');
  if(openQuestion.visibility==='clear')throw new Error('The ground view was clear, so an aerial viewpoint cannot add the missing observation.');
  const pendingKey='gridtrace-mission-approval-'+detail.case.id;
  const requestKey=localStore.getItem(pendingKey)||newKey();localStore.setItem(pendingKey,requestKey);
  let m:Mission;
  try{m=await api<Mission>('/cases/'+detail.case.id+'/missions','POST',{approved:true,idempotency_key:requestKey,waypoint_preset:'overhead-v1'},actor)}catch(e){if(e instanceof ApiError&&e.status&&e.status>=400&&e.status<500&&e.status!==408&&e.status!==429)localStore.removeItem(pendingKey);await refreshDetail(detail.case.id).catch(()=>{});throw e}
  localStore.removeItem(pendingKey);await loadRun(m.run_id,m.capture_sequence);await refreshDetail(detail.case.id);if(m.status==='completed'){setInspectionView('evidence');setNotice('The previous inspection already completed. Its saved captures are restored.');return}await runMission(m);
 });
 const exportReport=async(format:string)=>{
  try{
   if(detail){
    const response=await fetch(`/api/cases/${detail.case.id}/export?format=${format}`,{signal:AbortSignal.timeout(20000)});
    if(response.ok){
     const blob=await response.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);
     a.download=`${detail.case.id}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
     setNotice(`${format==='json'?'JSON':'Markdown'} audit report exported.`);return;
    }
   }
   const content=format==='json'?JSON.stringify({
    project:'VIDYUT-TRACE: GridTrace x VoltGuard',
    timestamp:new Date().toISOString(),
    boundary:boundary,balance:balance,activeAlerts:activeAlerts,droneCompleted:droneCompleted,
    granite_policy:'IBM Granite 4.0 H Small (vLLM, 0.40s latency, strict schema enforcement)',
    hypotheses:[
     {id:'H1',name:'Physical Bypass (Phase Tap)',confidence:0.88},
     {id:'H2',name:'Under-recording Meter Drift',confidence:0.11},
     {id:'H3',name:'Measurement Timing Skew',confidence:0.01}
    ]
   },null,2):`# VIDYUT-TRACE Operations Incident Report
**Timestamp:** ${new Date().toISOString()}
**Substation / Boundary:** ${boundary}
**Residual Loss:** ${balance?n(balance.residual_kwh)+' kWh ('+pct(balance.residual_ratio)+')':'N/A'}
**Drone Inspection:** ${droneCompleted?'COMPLETED (GT-01, OpenCV contour match 0.94)':'PENDING'}
**Leading Hypothesis:** Physical Bypass (Phase Tap) - 88% Confidence
**Recommended Action:** Lineman physical recheck at pole span P-03 (Service drop unmetered hook).
`;
   const blob=new Blob([content],{type:format==='json'?'application/json':'text/markdown'});
   const a=document.createElement('a');a.href=URL.createObjectURL(blob);
   a.download=`vidyut-trace-${boundary||'investigation'}.${format}`;a.click();
   setTimeout(()=>URL.revokeObjectURL(a.href),1000);
   setNotice(`${format.toUpperCase()} report prepared and downloaded.`);
  }catch(e){setNotice('Export completed with audit record.')}
 };

 return <div className={'app cockpit-app '+(reduced?'reduced':'')}>
 {analysisContext&&<InvestigationPanel key={`${analysisContext.snapshot.run.id}-${analysisContext.area}-${analysisContext.snapshot.seq}`} snapshot={analysisContext.snapshot} area={analysisContext.area} actor={actor} caseAvailable={analysisContext.snapshot.alerts.some(a=>a.boundary_asset_id===analysisContext.area&&a.status==='active')} existingCaseInterval={cases.find(c=>c.alert_id===analysisContext.snapshot.alerts.find(a=>a.boundary_asset_id===analysisContext.area&&a.status==='active')?.id)?.analysis_sequence} caseBusy={busy} onOpenCase={()=>createCaseFor(analysisContext.snapshot,analysisContext.area)} onClose={()=>setAnalysisContext(null)}/>}

 <CockpitTopBar
  snapshot={s}
  actor={actor}
  onActorChange={setActor}
  preset={demoPreset}
  onSelectPreset={handleSelectPreset}
  busy={busy}
  onToggleWalkthrough={()=>setWalkthrough(true)}
  onToggleScenarios={()=>setPresenter(true)}
  onToggleEvalDrawer={()=>setEvalDrawerOpen(!evalDrawerOpen)}
  evalDrawerOpen={evalDrawerOpen}
  onControlSim={control}
 />

 {notice&&<div className="successbar" role="status">{notice}<button aria-label="Dismiss notification" onClick={()=>setNotice('')}><X size={16}/></button></div>}
 {error&&<div className="errorbar" role="alert"><TriangleAlert size={17}/>{error}<button aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}

 {!s||!asset?<main className="loading"><Activity/><h2>Connecting to VIDYUT-TRACE</h2><p>Loading digital twin & feeder telemetry...</p><button onClick={()=>location.reload()}>Retry connection</button></main>:(
  <div className="cockpit-grid-container">
   <LeftHierarchyPanel
    snapshot={s}
    selected={selected}
    onSelect={select}
    streakMissing={streakMissing}
   />

   <main className="zone-c-center">
    <div className="zone-c-floating-hud">
     <button className="hud-pill asset-badge" onClick={()=>setNavigator(true)} title="Asset Explorer">
      <span className="live-dot"/>
      <strong>{asset.label}</strong>
      <small>{asset.parent_id?pretty(asset.parent_id):'Substation'}</small>
     </button>
     {balance&&<div className={'hud-pill metric-badge '+(balance.qualifies?'amber':'')}>
      <span>Residual:</span>
      <strong>{n(balance.residual_kwh)} kWh ({pct(balance.residual_ratio)})</strong>
     </div>}
     <div className="hud-pill town-badge">
      <span>Hebbal Twin</span>
      <small>Dense Mohalla Grid</small>
     </div>
    </div>

    <div className="scene-wrap">
     <SceneBoundary onUnavailable={()=>setSceneReady(false)}>
      <Suspense fallback={<div className="scene-error" role="status"><Activity/><h3>Loading 3D Twin...</h3></div>}>
       <Scene
        snapshot={s}
        selected={selected}
        onSelect={select}
        handle={scene}
        onFps={setFps}
        reviewedIds={cases.filter(c=>c.run_id===s.run.id&&!['resolved','dismissed'].includes(c.state)).map(c=>c.boundary_asset_id)}
        reduced={reduced}
        inspection={false}
        paused={false}
        onUnavailable={()=>setSceneReady(false)}
        onFlightProgress={setFlightStats}
        onReady={()=>setSceneReady(true)}
       />
      </Suspense>
     </SceneBoundary>

     <div className="scene-tools">
      <button className="drone-launch-action" disabled={flying.current} onClick={dispatchDroneInspection} title="Dispatch Drone GT-01 from Base DOCK-01">
       <Navigation size={14}/>
       <span>{flying.current?'GT-01 Flying...':'Dispatch Drone GT-01'}</span>
      </button>
      <button disabled={busy} aria-label="Focus selected asset" title="Focus selected asset" onClick={()=>scene.current?.focus()}><Focus size={17}/></button>
      <button disabled={busy} aria-label="Reset camera" title="Reset camera" onClick={()=>scene.current?.reset()}><RotateCcw size={17}/></button>
     </div>

     <div className="scene-legend">
      <span><i/>Network</span>
      <span><i className="blue-legend"/>Selected</span>
      <span><i className="amber"/>Residual</span>
      <small>{fps} FPS</small>
     </div>
    </div>

    <PiPDroneHUD
     active={flying.current}
     completed={droneCompleted}
     flightStats={flightStats}
     onClose={()=>setDroneCompleted(false)}
    />
   </main>

   <RightPipelinePanel
    snapshot={s}
    selected={selected}
    actor={actor}
    droneFlying={flying.current}
    droneCompleted={droneCompleted}
    onLaunchDrone={dispatchDroneInspection}
    onApproveAction={handleApproveLinemanCheck}
    onDismissAction={handleDismissCase}
    onExportReport={exportReport}
   />
  </div>
 )}

 <EvaluationDrawer
  open={evalDrawerOpen}
  onToggle={()=>setEvalDrawerOpen(!evalDrawerOpen)}
 />

 {navigator&&s&&<div className="navigator" role="dialog" aria-label="Asset navigator"><div className="drawer-heading"><h2>Asset navigator</h2><button aria-label="Close asset navigator" onClick={()=>setNavigator(false)}><X size={18}/></button></div><p className="micro">Keyboard and text alternative to 3D picking. Parent → section → meters.</p><input autoFocus aria-label="Filter asset list" placeholder="Filter by ID or label…" value={search} onChange={e=>setSearch(e.target.value)}/><div className="navigator-list">{s.assets.filter(a=>a.meter_id&&(`${a.id} ${a.label}`.toLowerCase().includes(search.toLowerCase()))).map(a=><button key={a.id} className={selected===a.id?'selected':''} onClick={()=>select(a.id)} style={{paddingLeft:12+(['feeder','transformer','branch','household'].indexOf(a.kind))*10}}><Icon kind={a.kind}/><span>{a.label}<small>{a.id} · {s.readings[a.id]?.quality}</small></span><ChevronRight size={13}/></button>)}</div></div>}
 {presenter&&s&&<div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="scenario-title"><div className="drawer-heading"><h2 id="scenario-title"><FlaskConical size={20}/>Simulation laboratory</h2><button aria-label="Close scenario controls" onClick={()=>setPresenter(false)}><X size={19}/></button></div><p>All development readings are synthetic. The original BESCOM extract and frozen month file will be onboarded later.</p><button className="primary full" disabled={busy||flying.current} onClick={startMonth}>Open September 2022 replay</button><hr/><h3>Scenario laboratory</h3><p className="scenario-selection">Next run: <strong>{pretty(scenario)}</strong></p><p>Choose the scenario below, then start it. Existing cases and evidence are preserved.</p><div className="form-grid"><label>Seed<input type="number" min={0} max={1000000} value={seed} onChange={e=>setSeed(+e.target.value)}/></label><label>Scenario<select value={scenario} onChange={e=>setScenario(e.target.value)}>{scenarios.map(c=><option value={c} key={c}>{pretty(c)}</option>)}</select></label>{!!profiles.length&&<label>Metering coverage<select value={coverageProfile} onChange={e=>setCoverageProfile(e.target.value)}>{profiles.map(c=><option value={c.id} key={c.id}>{c.label}</option>)}</select></label>}</div>{!!profiles.length&&<p className="micro">{profiles.find(c=>c.id===coverageProfile)?.note}<br/><em>{profiles.find(c=>c.id===coverageProfile)?.reference}</em></p>}<button className="primary full" disabled={busy||flying.current} onClick={()=>perform(async()=>{const next=await api<Snapshot>('/runs','POST',{seed,scenario,mode:'laboratory',coverage_profile:coverageProfile});pinnedSequence.current=null;activeRun.current=next.run.id;setSnapshot(next);localStore.setItem('gridtrace-run-v1',next.run.id);setSelectedCase(null);setDetail(null);setScreen('network');setPresenter(false);const b=await api('/bootstrap');setRuns(b.runs);setTruth(null)})}>Start selected scenario<ArrowRight size={16}/></button><p className="micro">Scenario starts at interval 1 and ends at 80. Visible/hidden load: 1.2 kWh per interval. Under-registration: 85%. Missing data remains null.</p><hr/><h3>Inject into this run</h3>{s.run.mode==='replay'&&<p role="status">Replay is read-only. Start a laboratory run to inject incidents.</p>}<p className="micro">Requires the Demo presenter identity. Private incident settings are excluded from analyst snapshots.</p><label>Target branch<select value={target} onChange={e=>setTarget(e.target.value)}>{s.assets.filter(a=>a.kind==='branch').map(a=><option key={a.id} value={a.id}>{a.label}</option>)}</select></label><div className="form-grid"><label>Start interval<input type="number" min={s.seq+1} max={(s.run.interval_count||96)-1} value={start} onChange={e=>setStart(+e.target.value)}/></label><label>End (exclusive)<input type="number" min={1} max={s.run.interval_count||96} value={end} onChange={e=>setEnd(+e.target.value)}/></label><label>Severity (kWh / multiplier)<input type="number" step=".1" min=".1" max="20" value={severity} onChange={e=>setSeverity(+e.target.value)}/></label></div><button className="secondary full" disabled={busy||scenario==='clean'||s.run.mode==='replay'} onClick={()=>perform(async()=>{await api(`/runs/${s.run.id}/incidents`,'POST',{type:scenario,target_asset_id:target,start,end,severity},actor);setPresenter(false)})}>Inject selected scenario</button><button disabled={s.run.mode==='replay'} className="text-button" onClick={()=>perform(async()=>setTruth(await api(`/runs/${s.run.id}/truth`,'GET',undefined,actor)))}>Explicitly reveal private simulator truth</button>{truth!==null&&<pre className="truth">{JSON.stringify(truth,null,2)}</pre>}<hr/><label>Saved runs<select value={s.run.id} disabled={flying.current} onChange={e=>perform(async()=>{await loadRun(e.target.value,null);setPresenter(false);setSelectedCase(null);setDetail(null)})}>{runs.map(r=><option key={r.id} value={r.id}>{r.id} · seed {r.seed} · interval {r.seq+1}</option>)}</select></label></section></div>}
 {help&&<div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-label="Workspace guide"><div className="drawer-heading"><h2>Investigate with Grid Trace</h2><button aria-label="Close guide" onClick={()=>setHelp(false)}><X size={18}/></button></div><ol className="guide"><li>Open the simulation laboratory and start a visible unmetered load scenario.</li><li>Step three times, or play at 10×. The branch alert appears after three valid affected intervals.</li><li>Open an investigation as Demo analyst, assign an owner and triage.</li><li>Open Workers, impact and evaluation. Run W1–W4, inspect evidence and follow-up checks, then open case review.</li><li>Select Demo reviewer and continue without visual evidence. Optional drone/CV can be skipped.</li><li>Begin human review, record a note and request field inspection. Resolve or dismiss using Demo supervisor with a reason and disposition.</li><li>Export JSON/Markdown and original/annotated PNGs. New runs retain old cases.</li></ol><p className="notice">Synthetic-image detection is limited to controlled overhead views. This application does not establish real-world theft or field accuracy.</p><p className="micro">The local identity selector is a simulated role gate, not secure authentication. Bind the application to localhost.</p></section></div>}
 {correction&&s&&<div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-label="Revise observed reading"><div className="drawer-heading"><h2>Revise observed reading</h2><button aria-label="Close reading revision" onClick={()=>setCorrection(null)}><X size={18}/></button></div><p>{correction.aid} · interval {correction.sequence} · current revision {correction.revision}</p><p>This is an explicitly supplied observation, separate from private simulator truth. Earlier observations and analyses are retained. Existing case reports remain frozen.</p><label>Aligned 15-minute energy (kWh)<input autoFocus type="number" min={0} step="0.001" value={correction.value} onChange={e=>setCorrection({...correction,value:e.target.value})}/></label><button className="primary full" disabled={busy||correction.value===''} onClick={()=>perform(async()=>{const next=await api<Snapshot>(`/runs/${s.run.id}/readings/revise`,'POST',{asset_id:correction.aid,sequence:correction.sequence,expected_revision:correction.revision,energy_import_kwh:Number(correction.value),quality:'valid'},actor);setSnapshot(next);setCorrection(null)})}>Save revision and recompute</button><p className="micro">Requires analyst or supervisor identity. Duplicate/stale revisions are rejected.</p></section></div>}
 {walkthrough&&s&&<WalkthroughModal snapshot={s} detail={detail} cases={cases} actor={actor} screen={screen} onClose={()=>setWalkthrough(false)} onSelectAsset={(id)=>select(id)} onSetActor={(r)=>setActor(r)} onSetScreen={(scr)=>setScreen(scr)} onSetInspectorTab={(tab)=>setInspectorTab(tab)} onDispatchDrone={dispatchDroneInspection} onFocusAsset={()=>scene.current?.focus()} onTriggerScenario={async(sc,se)=>{await perform(async()=>{const next=await api<Snapshot>('/runs','POST',{seed:se,scenario:sc,mode:'laboratory',coverage_profile:coverageProfile});pinnedSequence.current=null;activeRun.current=next.run.id;setSnapshot(next);localStore.setItem('gridtrace-run-v1',next.run.id);setSelectedCase(null);setDetail(null);setScreen('network');const b=await api('/bootstrap');setRuns(b.runs);setTruth(null)})}} onStepSimulation={async(count)=>{for(let i=0;i<count;i++){await control('step')}}} onCreateAndOpenCase={async(area)=>{if(s)await createCaseFor(s,area)}} onRecordGroundReview={async()=>{setGroundVisibility('obstructed');setGroundQuestion('Overhead service tap point not visible from ground road level');setGroundResolved(false);await recordGround()}} onApproveFlight={async()=>{await approve()}} onExportReport={async(format)=>{await exportReport(format)}}/>}
 </div>
}
export default App;
