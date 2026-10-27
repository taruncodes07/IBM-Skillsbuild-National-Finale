import {Radio,ShieldCheck,Play,Pause,SkipForward,Sparkles,Compass} from 'lucide-react';
import type {Snapshot} from './types';
import {date} from './api';

type Props={
 snapshot:Snapshot|null;
 playing?:boolean;
 speed?:number;
 actor:string;
 preset?:number;
 demoPreset?:number;
 busy?:boolean;
 evalDrawerOpen?:boolean;
 onControl?:(command:string,speed?:number,sequence?:number)=>void;
 onControlSim?:(command:string,speed?:number,sequence?:number)=>void;
 onSelectPreset:(preset:number)=>void;
 onSetActor?:(actor:string)=>void;
 onActorChange?:(actor:string)=>void;
 onOpenTutorial?:()=>void;
 onToggleWalkthrough?:()=>void;
 onToggleScenarios?:()=>void;
 onToggleEvalDrawer?:()=>void;
};

export default function CockpitTopBar({
 snapshot,
 playing=false,
 speed=1,
 actor,
 preset,
 demoPreset,
 busy=false,
 evalDrawerOpen,
 onControl,
 onControlSim,
 onSelectPreset,
 onSetActor,
 onActorChange,
 onOpenTutorial,
 onToggleWalkthrough,
 onToggleScenarios,
 onToggleEvalDrawer
}:Props){
 const currentPreset = preset ?? demoPreset ?? 1;
 const handleActorChange = onActorChange || onSetActor || (()=>{});
 const handleControl = onControlSim || onControl || (()=>{});
 const handleTutorial = onToggleWalkthrough || onOpenTutorial || (()=>{});
 const isPlaying = snapshot?.run?.playing ?? playing;
 const currentSpeed = snapshot?.run?.speed ?? speed;
 const intervalTime = snapshot?.readings['feeder-01']?.interval_start || snapshot?.simulation_time || '2022-09-14T14:45:00Z';

 return (
  <header className="cockpit-topbar">
   {/* Brand */}
   <div className="brand-section">
    <div className="brand-icon"><Radio size={16}/></div>
    <div className="brand-names">
     <strong>VIDYUT-TRACE</strong>
     <small>GridTrace × VoltGuard</small>
    </div>
   </div>

   {/* Persistent Provenance Banner (FR-11) */}
   <div className="provenance-banner">
    <ShieldCheck size={12} color="#3b82f6"/>
    <span className="prov-tag">SYNTHETIC REPLAY: <strong>VIDYUT_TRACE_v4</strong> (109,440 rows)</span>
    <span className="prov-dot">•</span>
    <span className="prov-ref">Ref: <strong>BESCOM Hebbal F11-Sanjay Nagar</strong> (9.31% gap)</span>
   </div>

   {/* Time-Series Replay Scrubber (FR-03) */}
   <div className="replay-scrubber">
    <button className="scrub-btn play-pause" disabled={busy} onClick={()=>handleControl(isPlaying?'pause':'play')} title={isPlaying?'Pause':'Play'}>
     {isPlaying?<Pause size={13}/>:<Play size={13}/>}
    </button>
    <button className="scrub-btn step-btn" disabled={busy||isPlaying} onClick={()=>handleControl('step')} title="Step one 15-minute interval">
     <SkipForward size={12}/>
     <span>+15m</span>
    </button>
    <select className="speed-select" value={currentSpeed} onChange={e=>handleControl('speed',+e.target.value)} disabled={busy}>
     <option value={1}>1×</option>
     <option value={10}>10×</option>
     <option value={60}>60×</option>
    </select>
    <div className="time-display">
     <strong>{date(intervalTime)}</strong>
     <small>Seq {(snapshot?.seq??0)+1}/96 · 15m</small>
    </div>
   </div>

   {/* Guided Demo Stepper (4-Preset Bar) */}
   <div className="guided-demo-stepper">
    <button className={'preset-btn '+(currentPreset===1?'active':'')} onClick={()=>onSelectPreset(1)} title="Scenario: Normal balanced baseline">
     <span className="p-num">1</span>
     <span>Clean Baseline</span>
    </button>
    <button className={'preset-btn '+(currentPreset===2?'active':'')} onClick={()=>onSelectPreset(2)} title="Scenario: Missing meter telemetry (NULL) - streak broken">
     <span className="p-num">2</span>
     <span>Missing Meter (NULL)</span>
    </button>
    <button className={'preset-btn '+(currentPreset===3?'active':'')} onClick={()=>onSelectPreset(3)} title="Scenario: Branch residual deficit + Drone inspection">
     <span className="p-num">3</span>
     <span>Branch Deficit + Drone</span>
    </button>
    <button className={'preset-btn '+(currentPreset===4?'active':'')} onClick={()=>onSelectPreset(4)} title="View IBM Bob proof log and B0/B1/B2 metrics">
     <span className="p-num">4</span>
     <span>IBM Bob Proof & Eval</span>
    </button>
   </div>

   {/* Right tools: Tutorial button, Scenarios, and simulated identity */}
   <div className="right-tools">
    {onToggleScenarios&&<button className="tool-btn" onClick={onToggleScenarios} title="Laboratory Scenarios">
     <span>Scenarios</span>
    </button>}
    <button className="tutorial-btn" onClick={handleTutorial} title="Open Guided Step-by-Step Walkthrough">
     <Compass size={13}/>
     <span>Tutorial</span>
    </button>
    <select className="actor-dropdown" value={actor} onChange={e=>handleActorChange(e.target.value)}>
     <option value="analyst">Demo Analyst</option>
     <option value="reviewer">Demo Reviewer</option>
     <option value="supervisor">Demo Supervisor</option>
     <option value="presenter">Demo Presenter</option>
    </select>
   </div>
  </header>
 );
}
