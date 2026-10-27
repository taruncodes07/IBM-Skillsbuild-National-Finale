import {useState,useEffect,useRef,useCallback,Component,lazy,Suspense,type ReactNode} from 'react';
import {Activity,ArrowRight,Box,Building2,Check,CheckCircle2,ChevronRight,ClipboardList,Compass,Download,FileText,FlaskConical,Focus,GitBranch,House,Info,Layers,Map,Maximize2,Pause,Play,Radio,RotateCcw,Search,Settings2,ShieldCheck,SkipForward,TriangleAlert,UserRound,X,ZoomIn,ZoomOut,Camera,Navigation,ScanLine} from 'lucide-react';
import type {SceneHandle} from './Scene';
const Scene=lazy(()=>import('./Scene'));
import {loadDemo} from './demo';
import ComparisonPanel from './ComparisonPanel';
import PresentationTour,{PresentationWelcome,CHAPTERS,type TourCommand} from './PresentationTour';
import './presentation.css';
import type {FlightTelemetry} from './flight';
import InvestigationPanel from './InvestigationPanel';
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

function App(){
 const [welcomeOpen,setWelcomeOpen]=useState(true),[presentationActive,setPresentationActive]=useState(false),[presentationShot,setPresentationShot]=useState(0);
 const [comparisonOpen,setComparisonOpen]=useState(false),[rotating,setRotating]=useState(false),[motion,setMotion]=useState(true),[tourActive,setTourActive]=useState(false);
 const [analysisContext,setAnalysisContext]=useState<{snapshot:Snapshot;area:string}|null>(null);
 const [snapshot,setSnapshot]=useState<Snapshot|null>(null),[selected,setSelected]=useState('branch-03'),[screen,setScreen]=useState<'network'|'inspection'>('network');
 const [actor,setActor]=useState('analyst'),[cases,setCases]=useState<Case[]>([]),[detail,setDetail]=useState<Detail|null>(null),[selectedCase,setSelectedCase]=useState<string|null>(null);
 const [notice,setNotice]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[search,setSearch]=useState(''),[navigator,setNavigator]=useState(false),[presenter,setPresenter]=useState(false),[help,setHelp]=useState(false),[walkthrough,setWalkthrough]=useState(false),[queueTab,setQueueTab]=useState('alerts'),[inspectorTab,setInspectorTab]=useState<'balance'|'meters'|'queue'>('balance');
 const [demoPreset,setDemoPreset]=useState<number>(0),[streakMissing,setStreakMissing]=useState(false),[evalDrawerOpen,setEvalDrawerOpen]=useState(false),[droneCompleted,setDroneCompleted]=useState(false);
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
   if(saved.caseId){const d=await refreshDetail(saved.caseId);if(!mounted.current)return;setSelectedCase(d.case.id);setOwner(d.case.assigned_to||'');setDisposition(d.case.disposition||'inconclusive');setNote(sessionStore.getItem('gridtrace-note-'+d.case.id)||'');setInspectionView(d.evidence.length?'evidence':'flight');setDroneCompleted(d.evidence.length>0);setScreen('inspection')}
   if(saved.analysis){try{const frozen=await api<Snapshot>(`/runs/${rid}/snapshot?seq=${saved.analysis.sequence}`);if(mounted.current&&frozen.assets.some(a=>a.id===saved.analysis!.area))setAnalysisContext({snapshot:frozen,area:saved.analysis.area})}catch{if(mounted.current)setNotice('The saved investigation view could not be restored. Open it again from the activity icon.')}}
  }
 }catch(e){if(mounted.current)setError((e as Error).message)}finally{initialized.current=true}})();const interval=setInterval(()=>setWall(new Date().toISOString()),1000);return()=>{mounted.current=false;clearInterval(interval)}},[loadRun,refreshDetail]);
 useEffect(()=>{if(!initialized.current||!snapshot)return;const saved:Workspace={runId:snapshot.run.id,assetId:selected,sequence:screen==='inspection'&&detail?detail.case.analysis_sequence:snapshot.seq,screen,caseId:screen==='inspection'?selectedCase:null,actor,analysis:analysisContext?{area:analysisContext.area,sequence:analysisContext.snapshot.seq}:null};localStore.setItem(WORKSPACE_KEY,JSON.stringify(saved))},[snapshot?.run.id,snapshot?.seq,selected,screen,selectedCase,actor,analysisContext,detail?.case.id]);
 useEffect(()=>{
  if(!snapshot?.run.id)return;const rid=snapshot.run.id;let last=-1;const stream=new EventSource(`/api/runs/${rid}/events?after_seq=-1`);
  stream.addEventListener('snapshot',(e)=>{const event=JSON.parse((e as MessageEvent).data);if(event.event_seq>last&&activeRun.current===rid){last=event.event_seq;setConnection('Live');loadRun(rid).catch(e=>setError((e as Error).message));refreshCases().catch(e=>console.error('[App] refreshCases error',e))}});
  stream.onopen=()=>setConnection('Live');stream.onerror=()=>setConnection('Reconnecting');return()=>stream.close();
 },[snapshot?.run.id,loadRun,refreshCases]);
 useEffect(()=>{if(analysisContext||!navigator&&!presenter&&!help&&!walkthrough&&!correction&&!groundOpen)return;
  const dialog=Array.from(document.querySelectorAll<HTMLElement>('[role="dialog"]')).at(-1);if(!dialog)return;
  const previous=document.activeElement as HTMLElement|null;
  const elements=()=>Array.from(dialog.querySelectorAll<HTMLElement>('button:not(:disabled),select:not(:disabled),input:not(:disabled),textarea:not(:disabled),a[href],summary')).filter(el=>el.getClientRects().length);
  (dialog.querySelector<HTMLElement>('[autofocus]')||elements()[0])?.focus();
  const keydown=(e:KeyboardEvent)=>{if(e.key==='Escape'){e.preventDefault();if(groundOpen)setGroundOpen(false);else if(walkthrough)setWalkthrough(false);else if(correction)setCorrection(null);else if(help)setHelp(false);else if(presenter)setPresenter(false);else setNavigator(false)}else if(e.key==='Tab'){const items=elements(),first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};
  document.addEventListener('keydown',keydown);return()=>{document.removeEventListener('keydown',keydown);previous?.focus()}
 },[navigator,presenter,help,walkthrough,groundOpen,!!correction,!!analysisContext]);
 const s=snapshot;const asset=s?.assets.find(a=>a.id===selected);const boundary=asset?.kind==='household'?asset.parent_id:asset?.id;
 const balance=s?.balances.find(b=>b.boundary_asset_id===boundary);const alert=s?.alerts.find(a=>a.boundary_asset_id===boundary&&a.status==='active');
 const activeAlerts=s?.alerts.filter(a=>a.status==='active').sort((a,b)=>b.unexplained_kwh-a.unexplained_kwh)||[];
 const children=s?.assets.filter(a=>a.parent_id===asset?.id&&a.meter_id)||[];
 const selectedEvidence=detail?.evidence.find(e=>e.id===evidenceId)||detail?.evidence[0];
 const select=(id:string)=>{if(flying.current)return;if(screen==='inspection'){setScreen('network');setDetail(null);setSelectedCase(null);setDroneCompleted(false);pinnedSequence.current=null;}setSelected(id);setNavigator(false);setSearch('')};
 const openCase=async(c:Case)=>{if(flying.current)throw new Error('Finish or cancel the active mission before switching run context');setSelectedCase(c.id);setSelected(c.boundary_asset_id);await loadRun(c.run_id,c.analysis_sequence);const d=await refreshDetail(c.id);setOwner(d.case.assigned_to||'');setDisposition(d.case.disposition||'inconclusive');setNote(sessionStore.getItem('gridtrace-note-'+d.case.id)||'');setScreen('inspection');setEvidenceId('');setInspectionView(d.evidence.length?'evidence':'flight');setFlightStats(null);setDroneCompleted(d.evidence.length>0)};
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
  flying.current=true;localStore.removeItem('gridtrace-mission-approval-'+m.case_id);setInspectionView('flight');setFlightStats(null);setMissionProgress('Preparing approved route');setDroneCompleted(false);
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
   await api('/missions/'+m.id,'PATCH',{status:'completed'},missionActor);await refreshDetail(m.case_id);await refreshCases();setInspectionView('evidence');setDroneCompleted(true);setNotice('Inspection complete. Two RGB views are ready for human review.');
  }catch(e){await api('/missions/'+m.id,'PATCH',{status:'failed',reason:(e as Error).message},missionActor).catch(()=>{});await refreshDetail(m.case_id).catch(()=>{});throw e}
  finally{flying.current=false;setMissionProgress('')}
 };
 const applyPreset=async(preset:number)=>{
  if(flying.current)throw new Error('End the drone flight before changing scenarios.');
  const next=await loadDemo(preset,api);
  ++loadSeq.current;pinnedSequence.current=null;activeRun.current=next.run.id;
  setSnapshot(next);setDemoPreset(preset);setSelected('branch-03');setSelectedCase(null);setDetail(null);
  setAnalysisContext(null);setScreen('network');setDroneCompleted(false);setFlightStats(null);setTruth(null);setActor('analyst');
  localStore.setItem('gridtrace-run-v1',next.run.id);
  const bootstrap=await api('/bootstrap');setRuns(bootstrap.runs);
  setNotice(['Baseline ready.','Missing telemetry loaded.','Persistent loss ready for investigation.'][preset-1]);
 };
 const handleSelectPreset=(preset:number)=>perform(()=>applyPreset(preset));
 const dispatchDroneInspection=async()=>{await approve()};
 const openComparison=()=>perform(async()=>{
  if(!s||flying.current)return;
  if(s.run.playing){await api(`/runs/${s.run.id}/control`,'POST',{command:'pause'},actor);await loadRun(s.run.id)}
  setComparisonOpen(true);
 });
 const previewDrone=()=>perform(async()=>{
  if(!scene.current||!s||flying.current||screen==='inspection')return;
  if(s.run.playing){await api(`/runs/${s.run.id}/control`,'POST',{command:'pause'},actor);await loadRun(s.run.id)}
  const renderer=scene.current;flying.current=true;setTourActive(true);setRotating(false);setFlightStats(null);
  try{
   // Renderer-only tour: no mission, case, approval or evidence is written to the API.
   await renderer.fly({id:'presentation-tour',case_id:'',run_id:s.run.id,target_asset_ids:[boundary||'branch-03'],status:'flying',waypoints_m:[],capture_sequence:s.seq,failure_reason:null,frame_keys:{}});
   setNotice('Drone tour complete. For RGB evidence capture, open a loss case, triage it and record a ground observation as Reviewer.');
  }finally{renderer.reset();flying.current=false;setTourActive(false);setFlightStats(null)}
 });
 const latestGround=detail?.ground?.at(-1);
 const openQuestion=latestGround&&!latestGround.resolved_from_ground&&latestGround.outstanding_question.trim()?latestGround:null;
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
  if(!detail){setError('Open a case before exporting.');return;}
  try{
   const response=await fetch(`/api/cases/${detail.case.id}/export?format=${format}`,{signal:AbortSignal.timeout(20000)});
   if(!response.ok)throw new Error('Export failed. Retry the download.');
   const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');
   link.href=url;link.download=`${detail.case.id}.${format}`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   setNotice('Case report downloaded.');
  }catch(e){setError((e as Error).message)}
 };

 const startPresentation=async()=>{
  let prepared=false;
  await perform(async()=>{
  if(!s||flying.current)return;
  if(s.run.playing){await api(`/runs/${s.run.id}/control`,'POST',{command:'pause'},actor);await loadRun(s.run.id)}
  setWelcomeOpen(false);setWalkthrough(false);setPresenter(false);setNavigator(false);setHelp(false);setAnalysisContext(null);setEvalDrawerOpen(false);setComparisonOpen(false);setPresentationShot(0);setRotating(false);prepared=true;
  });
  if(prepared)setPresentationActive(true);
 };
 const endPresentation=()=>{scene.current?.cancelTour();setPresentationActive(false);setRotating(false)};
 const preparePresentationChapter=async(index:number)=>{
  if(operation.current)throw new Error('Wait for the current operation, then retry this chapter.');
  operation.current=true;setBusy(true);
  try{
   setRotating(false);setScreen('network');setDetail(null);setSelectedCase(null);setAnalysisContext(null);setComparisonOpen(false);setEvalDrawerOpen(false);setPresenter(false);setSelected('branch-03');
   pinnedSequence.current=null;
   const chapter=CHAPTERS[index];
   if('preset' in chapter)await applyPreset(chapter.preset);
   else if(s?.run.playing){await api(`/runs/${s.run.id}/control`,'POST',{command:'pause'},actor);await loadRun(s.run.id,null)}
   setPresentationShot(index);
  }finally{operation.current=false;setBusy(false)}
 };
 const presentationAction=async(command:TourCommand)=>{
  if(command==='step')await control('step');
  else if(command==='branch'){const branches=s?.assets.filter(a=>a.kind==='branch')||[];const next=branches[(branches.findIndex(a=>a.id===selected)+1)%branches.length];if(next){select(next.id);scene.current?.focus(next.id)}}
  else if(command==='focus'){setRotating(false);scene.current?.focus()}
  else if(command==='analyze'&&s&&boundary)setAnalysisContext({snapshot:s,area:boundary});
  else if(command==='drone')await previewDrone();
  else if(command==='compare')await openComparison();
  else if(command==='lab')setPresenter(true);
 };

 return <div className={'app cockpit-app '+(reduced?'reduced':'')}>
 {analysisContext&&<InvestigationPanel key={`${analysisContext.snapshot.run.id}-${analysisContext.area}-${analysisContext.snapshot.seq}`} snapshot={analysisContext.snapshot} area={analysisContext.area} actor={actor} caseAvailable={analysisContext.snapshot.alerts.some(a=>a.boundary_asset_id===analysisContext.area&&a.status==='active')} existingCaseInterval={cases.find(c=>c.alert_id===analysisContext.snapshot.alerts.find(a=>a.boundary_asset_id===analysisContext.area&&a.status==='active')?.id)?.analysis_sequence} caseBusy={busy} onOpenCase={()=>createCaseFor(analysisContext.snapshot,analysisContext.area)} onClose={()=>setAnalysisContext(null)}/>}

 <CockpitTopBar
  snapshot={s}
  actor={actor}
  onActorChange={setActor}
  demoPreset={s?.run.mode==='laboratory'?({'clean':1,'missing_telemetry':2,'visible_unmetered_load':3}[s.run.scenario||'']||0):0}
  onSelectPreset={handleSelectPreset}
  busy={busy}
  locked={flying.current}
  reviewLocked={screen==='inspection'}
  onToggleWalkthrough={()=>setWalkthrough(true)}
  onToggleScenarios={()=>setPresenter(true)}
  onToggleEvalDrawer={()=>setEvalDrawerOpen(!evalDrawerOpen)}
  evalDrawerOpen={evalDrawerOpen}
  onControlSim={control}
  onCompare={openComparison}
  onPresentation={startPresentation}

 />

 {notice&&<div className="successbar" role="status">{notice}<button aria-label="Dismiss notification" onClick={()=>setNotice('')}><X size={16}/></button></div>}
 {error&&<div className="errorbar" role="alert"><TriangleAlert size={17}/>{error}<button aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}

 {!s||!asset?<main className="loading"><Activity/><h2>Connecting to Grid Trace</h2><p>Loading network...</p><button onClick={()=>location.reload()}>Retry connection</button></main>:(
  <div className="cockpit-grid-container">
   <LeftHierarchyPanel
    snapshot={s}
    selected={selected}
    onSelect={select}
    disabled={busy||flying.current}
   />

   <main className="zone-c-center">
    <div className="zone-c-floating-hud">
     <button className="hud-pill asset-badge" onClick={()=>setNavigator(true)} title="Asset Explorer — click to browse all assets">
      <span className="live-dot"/>
      <strong>{asset.label}</strong>
      <small>{asset.parent_id?pretty(asset.parent_id):'Root Feeder'}</small>
     </button>
     {balance&&<div className={'hud-pill metric-badge '+(balance.qualifies?'amber':'')}>
      {balance.qualifies&&<TriangleAlert size={11}/>}
      <span>Residual:</span>
      <strong>{n(balance.residual_kwh)} kWh</strong>
      <small>({pct(balance.residual_ratio)})</small>
     </div>}
     {alert&&<div className="hud-pill alert-badge">
      <TriangleAlert size={11}/>
      <strong>ALERT</strong>
      <small>{n(alert.unexplained_kwh)} kWh unaccounted</small>
     </div>}

    </div>

    <div className="scene-wrap">
     <SceneBoundary onUnavailable={()=>setSceneReady(false)}>
      <Suspense fallback={<div className="scene-error" role="status"><Activity/><h3>Loading 3D Twin...</h3></div>}>
       <Scene
        key={s.run.id}
        snapshot={s}
        selected={selected}
        onSelect={select}
        handle={scene}
        onFps={setFps}
        reviewedIds={cases.filter(c=>c.run_id===s.run.id&&!['resolved','dismissed'].includes(c.state)).map(c=>c.boundary_asset_id)}
        reduced={reduced}
        inspection={screen==='inspection'}
        paused={comparisonOpen}
        presentationView={presentationActive?CHAPTERS[presentationShot].view:undefined}
        presentationShot={presentationShot}
        rotating={rotating}
        motion={motion}
        onManualCamera={()=>setRotating(false)}
        onUnavailable={()=>setSceneReady(false)}
        onFlightProgress={setFlightStats}
        onReady={()=>setSceneReady(true)}
       />
      </Suspense>
     </SceneBoundary>

     <div className="scene-tools">
      <button disabled={busy} aria-label="Focus selected asset" title="Focus selected asset" onClick={()=>{setRotating(false);scene.current?.focus()}}><Focus size={17}/></button>
      <button disabled={busy} aria-label="Reset camera" title="Reset camera" onClick={()=>{setRotating(false);scene.current?.reset()}}><RotateCcw size={17}/></button>
      {sceneReady&&<button disabled={busy} aria-label="Search assets" title="Search assets" onClick={()=>setNavigator(true)}><Search size={16}/></button>}
     </div>

     <div className="scene-legend">
      <span><i/>Network</span>
      <span><i className="blue-legend"/>Selected</span>
      <span><i className="amber"/>Alert</span>
      <small className={fps<30&&fps>0?'fps-warn':''}>{fps} FPS</small>
     </div>
     <div className="presentation-scene-tools" aria-label="Presentation controls">
      <button disabled={!sceneReady||busy||reduced||screen==='inspection'} aria-pressed={rotating&&!reduced&&screen!=='inspection'} onClick={()=>{if(!rotating)scene.current?.reset();setRotating(!rotating)}} title={reduced?'Rotation is off for reduced motion':'Slowly orbit the network; dragging stops rotation'}><RotateCcw size={15}/>{rotating?'Stop rotation':'Rotate POV'}</button>
      <button disabled={reduced} aria-pressed={motion&&!reduced} onClick={()=>{if(motion)setRotating(false);setMotion(!motion)}}>{motion&&!reduced?<Pause size={15}/>:<Play size={15}/>}Scene motion {motion&&!reduced?'on':'off'}</button>
      <button disabled={!sceneReady||(!tourActive&&(busy||screen==='inspection'))} onClick={()=>tourActive?scene.current?.cancelTour():previewDrone()}><Navigation size={15}/>{tourActive?'End drone tour':'Drone tour'}</button>
     </div>
     {tourActive&&<div className="drone-tour-status" role="status"><strong>DRONE TOUR / {Math.round((flightStats?.progress||0)*100)}%</strong><span>Presentation preview · no evidence captured</span><progress max={1} value={flightStats?.progress||0}/></div>}
    </div>

    <PiPDroneHUD
     active={flying.current&&!tourActive}
     completed={droneCompleted}
     flightStats={flightStats}
     evidence={detail?.evidence.at(-1)}
     onClose={()=>setDroneCompleted(false)}
    />
   </main>

   <RightPipelinePanel snapshot={s} selected={selected} actor={actor} busy={busy||flying.current}
    detail={screen==='inspection'?detail:null} cases={cases} note={note}
    onNote={value=>{setNote(value);if(detail)sessionStore.setItem('gridtrace-note-'+detail.case.id,value)}}
    onInvestigate={()=>{if(boundary)setAnalysisContext({snapshot:s,area:boundary})}}
    onOpenCase={createCase} onResumeCase={c=>perform(()=>openCase(c))}
    onTransition={state=>perform(()=>patchCase(state))} onGround={()=>setGroundOpen(true)}
    onLaunchDrone={approve} onResumeMission={m=>perform(()=>runMission(m))} onExportReport={exportReport} onSetActor={setActor}
    onSaveNote={()=>perform(()=>patchCase(undefined,{note}))}
    disposition={disposition} dispositions={dispositions} onDisposition={setDisposition}
    onCloseCase={()=>{setScreen('network');setDetail(null);setSelectedCase(null);setDroneCompleted(false);pinnedSequence.current=null;loadRun(s.run.id,null).catch(e=>setError(e.message))}}
    canFly={!!openQuestion&&openQuestion.visibility!=='clear'&&!!detail&&['ground_review','inspection_requested','evidence_ready','under_review'].includes(detail.case.state)} sceneReady={sceneReady}
   />
  </div>
 )}

 <EvaluationDrawer
  open={evalDrawerOpen}
  onToggle={()=>setEvalDrawerOpen(!evalDrawerOpen)}
 />
 {comparisonOpen&&<ComparisonPanel reduced={reduced} onClose={()=>setComparisonOpen(false)}/>}

 {groundOpen&&detail&&<div className="modal-backdrop"><section className="modal compact-modal" role="dialog" aria-modal="true" aria-labelledby="ground-title"><div className="drawer-heading"><h2 id="ground-title">Ground observation</h2><button aria-label="Close ground observation" onClick={()=>setGroundOpen(false)}><X size={18}/></button></div><label>Access<select value={groundAccess} onChange={e=>setGroundAccess(e.target.value)}><option value="obtained">Obtained</option><option value="refused">Refused</option><option value="unsafe">Unsafe</option><option value="not_attempted">Not attempted</option></select></label><label>Visibility<select value={groundVisibility} onChange={e=>setGroundVisibility(e.target.value)}><option value="obstructed">Obstructed</option><option value="partial">Partial</option><option value="clear">Clear</option><option value="not_visible">Not visible</option></select></label><label className="check-row"><input type="checkbox" checked={groundResolved} onChange={e=>setGroundResolved(e.target.checked)}/>Question resolved from ground</label>{!groundResolved&&<label>Unanswered question<textarea rows={3} placeholder="Which overhead connection needs a closer view?" value={groundQuestion} onChange={e=>setGroundQuestion(e.target.value)}/></label>}<button className="primary full" disabled={busy||!groundResolved&&!groundQuestion.trim()} onClick={recordGround}>Save observation</button></section></div>}
 {navigator&&s&&<div className="navigator" role="dialog" aria-label="Asset navigator"><div className="drawer-heading"><h2>Asset navigator</h2><button aria-label="Close asset navigator" onClick={()=>setNavigator(false)}><X size={18}/></button></div><p className="micro">Keyboard and text alternative to 3D picking. Parent → section → meters.</p><input autoFocus aria-label="Filter asset list" placeholder="Filter by ID or label…" value={search} onChange={e=>setSearch(e.target.value)}/><div className="navigator-list">{s.assets.filter(a=>a.meter_id&&(`${a.id} ${a.label}`.toLowerCase().includes(search.toLowerCase()))).map(a=><button key={a.id} className={selected===a.id?'selected':''} onClick={()=>select(a.id)} style={{paddingLeft:12+(['feeder','transformer','branch','household'].indexOf(a.kind))*10}}><Icon kind={a.kind}/><span>{a.label}<small>{a.id} · {s.readings[a.id]?.quality}</small></span><ChevronRight size={13}/></button>)}</div></div>}
 {presenter&&s&&<div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="scenario-title"><div className="drawer-heading"><h2 id="scenario-title"><FlaskConical size={20}/>Simulation laboratory</h2><button aria-label="Close scenario controls" onClick={()=>setPresenter(false)}><X size={19}/></button></div><button className="primary full" disabled={busy||flying.current} onClick={startMonth}>Open September 2022 replay</button><hr/><h3>Scenario laboratory</h3><p className="scenario-selection">Next run: <strong>{pretty(scenario)}</strong></p><div className="form-grid"><label>Seed<input type="number" min={0} max={1000000} value={seed} onChange={e=>setSeed(+e.target.value)}/></label><label>Scenario<select value={scenario} onChange={e=>setScenario(e.target.value)}>{scenarios.map(c=><option value={c} key={c}>{pretty(c)}</option>)}</select></label>{!!profiles.length&&<label>Metering coverage<select value={coverageProfile} onChange={e=>setCoverageProfile(e.target.value)}>{profiles.map(c=><option value={c.id} key={c.id}>{c.label}</option>)}</select></label>}</div>{!!profiles.length&&<p className="micro">{profiles.find(c=>c.id===coverageProfile)?.note}<br/><em>{profiles.find(c=>c.id===coverageProfile)?.reference}</em></p>}<button className="primary full" disabled={busy||flying.current} onClick={()=>perform(async()=>{const next=await api<Snapshot>('/runs','POST',{seed,scenario,mode:'laboratory',coverage_profile:coverageProfile});pinnedSequence.current=null;activeRun.current=next.run.id;setSnapshot(next);localStore.setItem('gridtrace-run-v1',next.run.id);setSelectedCase(null);setDetail(null);setScreen('network');setPresenter(false);const b=await api('/bootstrap');setRuns(b.runs);setTruth(null)})}>Start selected scenario<ArrowRight size={16}/></button><p className="micro">Scenario starts at interval 1 and ends at 80. Visible/hidden load: 1.2 kWh per interval. Under-registration: 85%. Missing data remains null.</p><hr/><h3>Inject into this run</h3>{s.run.mode==='replay'&&<p role="status">Replay is read-only. Start a laboratory run to inject incidents.</p>}<p className="micro">Requires the Demo presenter identity. Private incident settings are excluded from analyst snapshots.</p><label>Target branch<select value={target} onChange={e=>setTarget(e.target.value)}>{s.assets.filter(a=>a.kind==='branch').map(a=><option key={a.id} value={a.id}>{a.label}</option>)}</select></label><div className="form-grid"><label>Start interval<input type="number" min={s.seq+1} max={(s.run.interval_count||96)-1} value={start} onChange={e=>setStart(+e.target.value)}/></label><label>End (exclusive)<input type="number" min={1} max={s.run.interval_count||96} value={end} onChange={e=>setEnd(+e.target.value)}/></label><label>Severity (kWh / multiplier)<input type="number" step=".1" min=".1" max="20" value={severity} onChange={e=>setSeverity(+e.target.value)}/></label></div><button className="secondary full" disabled={busy||scenario==='clean'||s.run.mode==='replay'} onClick={()=>perform(async()=>{await api(`/runs/${s.run.id}/incidents`,'POST',{type:scenario,target_asset_id:target,start,end,severity},actor);setPresenter(false)})}>Inject selected scenario</button><button disabled={s.run.mode==='replay'} className="text-button" onClick={()=>perform(async()=>setTruth(await api(`/runs/${s.run.id}/truth`,'GET',undefined,actor)))}>Explicitly reveal private simulator truth</button>{truth!==null&&<pre className="truth">{JSON.stringify(truth,null,2)}</pre>}<hr/><label>Saved runs<select value={s.run.id} disabled={flying.current} onChange={e=>perform(async()=>{await loadRun(e.target.value,null);setPresenter(false);setSelectedCase(null);setDetail(null)})}>{runs.map(r=><option key={r.id} value={r.id}>{r.id} · seed {r.seed} · interval {r.seq+1}</option>)}</select></label></section></div>}
 {help&&<div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-label="Workspace guide"><div className="drawer-heading"><h2>Investigate with Grid Trace</h2><button aria-label="Close guide" onClick={()=>setHelp(false)}><X size={18}/></button></div><ol className="guide"><li>Open the simulation laboratory and start a visible unmetered load scenario.</li><li>Step three times, or play at 10×. The branch alert appears after three valid affected intervals.</li><li>Open an investigation as Demo analyst, assign an owner and triage.</li><li>Open Workers, impact and evaluation. Run W1–W4, inspect evidence and follow-up checks, then open case review.</li><li>Select Demo reviewer and continue without visual evidence. Optional drone/CV can be skipped.</li><li>Begin human review, record a note and request field inspection. Resolve or dismiss using Demo supervisor with a reason and disposition.</li><li>Export JSON/Markdown and original/annotated PNGs. New runs retain old cases.</li></ol><p className="notice">Synthetic-image detection is limited to controlled overhead views. This application does not establish real-world theft or field accuracy.</p><p className="micro">The local identity selector is a simulated role gate, not secure authentication. Bind the application to localhost.</p></section></div>}
 {correction&&s&&<div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-label="Revise observed reading"><div className="drawer-heading"><h2>Revise observed reading</h2><button aria-label="Close reading revision" onClick={()=>setCorrection(null)}><X size={18}/></button></div><p>{correction.aid} · interval {correction.sequence} · current revision {correction.revision}</p><p>This is an explicitly supplied observation, separate from private simulator truth. Earlier observations and analyses are retained. Existing case reports remain frozen.</p><label>Aligned 15-minute energy (kWh)<input autoFocus type="number" min={0} step="0.001" value={correction.value} onChange={e=>setCorrection({...correction,value:e.target.value})}/></label><button className="primary full" disabled={busy||correction.value===''} onClick={()=>perform(async()=>{const next=await api<Snapshot>(`/runs/${s.run.id}/readings/revise`,'POST',{asset_id:correction.aid,sequence:correction.sequence,expected_revision:correction.revision,energy_import_kwh:Number(correction.value),quality:'valid'},actor);setSnapshot(next);setCorrection(null)})}>Save revision and recompute</button><p className="micro">Requires analyst or supervisor identity. Duplicate/stale revisions are rejected.</p></section></div>}
 {welcomeOpen&&<PresentationWelcome ready={!!s&&!busy&&!flying.current} onPresent={startPresentation} onExplore={()=>setWelcomeOpen(false)}/>}
 {presentationActive&&s&&<PresentationTour onStage={preparePresentationChapter} onAction={presentationAction} onClose={endPresentation} blocked={busy} obscured={comparisonOpen||!!analysisContext||presenter||navigator||evalDrawerOpen||groundOpen||walkthrough||help}/>}
 {walkthrough&&s&&<WalkthroughModal snapshot={s} detail={detail} cases={cases} actor={actor} screen={screen} onClose={()=>setWalkthrough(false)} onSelectAsset={(id)=>select(id)} onSetActor={(r)=>setActor(r)} onSetScreen={(scr)=>setScreen(scr)} onSetInspectorTab={(tab)=>setInspectorTab(tab)} onDispatchDrone={dispatchDroneInspection} onFocusAsset={()=>scene.current?.focus()} onTriggerScenario={async(sc,se)=>{await perform(async()=>{const next=await api<Snapshot>('/runs','POST',{seed:se,scenario:sc,mode:'laboratory',coverage_profile:coverageProfile});pinnedSequence.current=null;activeRun.current=next.run.id;setSnapshot(next);localStore.setItem('gridtrace-run-v1',next.run.id);setSelectedCase(null);setDetail(null);setScreen('network');const b=await api('/bootstrap');setRuns(b.runs);setTruth(null)})}} onStepSimulation={async(count)=>{for(let i=0;i<count;i++){await control('step')}}} onCreateAndOpenCase={async(area)=>{if(s)await createCaseFor(s,area)}} onRecordGroundReview={async()=>{setGroundVisibility('obstructed');setGroundQuestion('Overhead service tap point not visible from ground road level');setGroundResolved(false);await recordGround()}} onApproveFlight={async()=>{await approve()}} onExportReport={async(format)=>{await exportReport(format)}}/>}
 </div>
}
export default App;
