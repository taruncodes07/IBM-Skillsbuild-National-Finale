import {Radio,Play,Pause,SkipForward,FlaskConical,Compass} from 'lucide-react';
import type {Snapshot} from './types';
import {date} from './api';
type Props={snapshot:Snapshot|null;actor:string;demoPreset?:number;busy?:boolean;locked?:boolean;reviewLocked?:boolean;onControlSim:(command:string,speed?:number)=>void;onSelectPreset:(preset:number)=>void;onActorChange:(actor:string)=>void;onToggleWalkthrough:()=>void;onToggleScenarios:()=>void;onToggleEvalDrawer:()=>void;onCompare:()=>void;evalDrawerOpen?:boolean};
export default function CockpitTopBar(p:Props){
 const s=p.snapshot,playing=s?.run.playing,atEnd=!!s&&s.seq>=(s.run.interval_count||96)-1;
 return <header className="cockpit-topbar">
  <div className="brand-section"><div className="brand-icon"><Radio size={19}/></div><strong>Grid Trace</strong><span className="source-chip">Simulation lab</span></div>
  <button className="compare-launch" disabled={p.busy||p.locked||!s} onClick={p.onCompare}>Compare loss <span>↗</span></button>
  <nav className="guided-demo-stepper" aria-label="Demo scenarios">{['Baseline','Missing data','Unexplained loss'].map((label,i)=><button key={label} className={'preset-btn '+(p.demoPreset===i+1?'active':'')} disabled={p.busy||p.locked||!s} aria-pressed={p.demoPreset===i+1} onClick={()=>p.onSelectPreset(i+1)}>{label}</button>)}</nav>
  <div className="replay-scrubber">
   <button disabled={p.busy||p.locked||p.reviewLocked||!s||atEnd&&!playing} onClick={()=>p.onControlSim(playing?'pause':'play')} aria-label={playing?'Pause replay':'Play replay'}>{playing?<Pause size={15}/>:<Play size={15}/>}</button>
   <button disabled={p.busy||p.locked||p.reviewLocked||!s||playing||atEnd} onClick={()=>p.onControlSim('step')} aria-label="Step 15 minutes"><SkipForward size={15}/></button>
   <select aria-label="Replay speed" value={s?.run.speed||10} onChange={e=>p.onControlSim('speed',+e.target.value)} disabled={p.busy||p.locked||p.reviewLocked||!s}><option value={1}>1x</option><option value={10}>10x</option><option value={60}>60x</option></select>
   <div className="time-display"><strong>{s?date(s.simulation_time,true):'--'} <small>IST</small></strong><small>Interval {s?s.seq+1:0} / {s?.run.interval_count||96}</small></div>
  </div>
  <div className="right-tools"><button onClick={p.onToggleScenarios} disabled={p.busy||p.locked} aria-label="Open scenario laboratory" title="Scenario laboratory"><FlaskConical size={16}/></button><button onClick={p.onToggleWalkthrough} title="Guide" aria-label="Open guide"><Compass size={16}/></button><button onClick={p.onToggleEvalDrawer} aria-expanded={p.evalDrawerOpen}>Evidence</button><select aria-label="Simulated role" value={p.actor} disabled={p.busy||p.locked} onChange={e=>p.onActorChange(e.target.value)}><option value="analyst">Analyst</option><option value="reviewer">Reviewer</option><option value="supervisor">Supervisor</option><option value="presenter">Presenter</option></select></div>
 </header>;
}
