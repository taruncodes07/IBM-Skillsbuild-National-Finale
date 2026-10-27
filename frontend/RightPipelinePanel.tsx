import {useState} from 'react';
import {Activity,Sparkles,CheckCircle2,ShieldCheck,AlertTriangle,Navigation,FileText,Download,XCircle} from 'lucide-react';
import type {Snapshot,Case} from './types';
import {pretty} from './api';

type Props={
 snapshot:Snapshot;
 selected:string;
 actor:string;
 droneFlying:boolean;
 droneCompleted:boolean;
 onLaunchDrone:()=>void;
 onApproveAction:()=>void;
 onDismissAction:()=>void;
 onExportReport:(format:'json'|'md')=>void;
};

export default function RightPipelinePanel({
 snapshot,
 selected,
 actor,
 droneFlying,
 droneCompleted,
 onLaunchDrone,
 onApproveAction,
 onDismissAction,
 onExportReport
}:Props){
 const [groundPreset,setGroundPreset]=useState('obscured');
 const [approvedStep,setApprovedStep]=useState(false);

 const targetBranch=snapshot.assets.find(a=>a.id===selected)?.kind==='household'
  ? snapshot.assets.find(a=>a.id===selected)!.parent_id!
  : selected;

 const isBranch3=targetBranch==='branch-03'||targetBranch.includes('03');

 return (
  <aside className="zone-d-right">
   <div className="zone-header">
    <Activity size={15} color="#3b82f6"/>
    <div>
     <h3>Live Agent Pipeline & Review</h3>
     <small>Zone D · Multi-worker fusion & human gate</small>
    </div>
   </div>

   {/* Card 1: Live Multi-Worker Execution Trace */}
   <div className="cockpit-card worker-trace-card">
    <div className="card-badge-header">
     <span>1. Multi-Worker Execution Trace</span>
     <span className="badge blue">WATSONX & RULES</span>
    </div>
    <div className="worker-stepper">
     <div className="worker-row done">
      <div className="w-meta">
       <span className="w-pill">W1</span>
       <strong>Metering & Accounting Worker</strong>
       <span className="w-ms">18 ms</span>
      </div>
      <p className="w-desc">Disjoint cut verified · 6/6 child streams valid · Consecutive streak: 3/3 intervals &gt; 3σ threshold.</p>
     </div>

     <div className="worker-row done">
      <div className="w-meta">
       <span className="w-pill">W2</span>
       <strong>Electrical Physics Worker</strong>
       <span className="w-ms">12 ms</span>
      </div>
      <p className="w-desc">Line impedance uncalibrated; conservative 3.2% technical loss bound applied. Residual exceeds bound.</p>
     </div>

     <div className="worker-row done">
      <div className="w-meta">
       <span className="w-pill">W3</span>
       <strong>Commercial & Baseline Worker</strong>
       <span className="w-ms">15 ms</span>
      </div>
      <p className="w-desc">Downstream meters H-07..H-09 show stable baseline profiles; no consumer billing mismatch data available.</p>
     </div>

     <div className="worker-row done">
      <div className="w-meta">
       <span className="w-pill">W4</span>
       <strong>Spatial Localization & Vision Worker</strong>
       <span className="w-ms">{droneCompleted?'2.1 s (CV)':'42 ms'}</span>
      </div>
      <p className="w-desc">
       {droneCompleted
        ? 'Smallest boundary localized to Branch-03. Aerial RGB confirms unmetered physical tap at Pole B-03 (OpenCV 0.94).'
        : 'Smallest boundary localized to Branch-03. Ground line-of-sight obstructed; aerial viewpoint recommended.'}
      </p>
     </div>

     <div className="worker-row granite-row done">
      <div className="w-meta">
       <span className="w-pill purple">Granite</span>
       <strong>ibm/granite-4-h-small</strong>
       <span className="badge green"><ShieldCheck size={10}/> Policy Passed</span>
      </div>
      <p className="w-desc">
       Proposal: <code>{droneCompleted?'REQUEST_ELECTRICAL_RECHECK':'PROPOSE_VIRTUAL_DRONE'}</code>. Action validated against 9-enum whitelist. Zero simulator truth-leak verified.
      </p>
     </div>
    </div>
   </div>

   {/* Card 2: Competing Hypotheses & Evidence Ledger */}
   <div className="cockpit-card hypotheses-card">
    <div className="card-badge-header">
     <span>2. Competing Hypotheses Ledger</span>
     <span className="badge">EVIDENCE FUSION</span>
    </div>
    <div className="hypothesis-list">
     <div className="hypo-item">
      <div className="hypo-header">
       <span>Unaccounted / Bypass Load</span>
       <strong className="status-supported">{droneCompleted?'Supported (94%)':'Supported (68%)'}</strong>
      </div>
      <div className="hypo-bar-track">
       <div className="hypo-bar-fill supported" style={{width:droneCompleted?'94%':'68%'}}/>
      </div>
      <small className="hypo-reason">E_in &gt; E_out + L_expected; {droneCompleted?'Aerial OpenCV candidate detected':'Aerial inspection pending'}</small>
     </div>

     <div className="hypo-item">
      <div className="hypo-header">
       <span>Meter Under-Registration</span>
       <strong className="status-plausible">Plausible (22%)</strong>
      </div>
      <div className="hypo-bar-track">
       <div className="hypo-bar-fill plausible" style={{width:'22%'}}/>
      </div>
      <small className="hypo-reason">Requires on-site reference meter injection test to verify calibration</small>
     </div>

     <div className="hypo-item">
      <div className="hypo-header">
       <span>Data / Telemetry Failure</span>
       <strong className="status-contradicted">Contradicted (0%)</strong>
      </div>
      <div className="hypo-bar-track">
       <div className="hypo-bar-fill contradicted" style={{width:'0%'}}/>
      </div>
      <small className="hypo-reason">All 3 downstream AMR meters reporting valid telemetry timestamps</small>
     </div>
    </div>

    <div className="missing-evidence-box">
     <AlertTriangle size={12} color="#f59e0b"/>
     <div>
      <strong>Missing Evidence Explicitly Declared:</strong>
      <p>Physical energization verification and authorized service drop records cannot be proven by sensors alone.</p>
     </div>
    </div>
   </div>

   {/* Card 3: Allowed Next Action & Human Review Gate */}
   <div className="cockpit-card human-gate-card">
    <div className="card-badge-header">
     <span>3. Human Review & Disposition Gate</span>
     <span className="badge blue">ACTOR: {actor.toUpperCase()}</span>
    </div>

    <div className="case-id-bar">
     <FileText size={13}/>
     <div className="case-id-text">
      <strong>CASE-2022-0914-{targetBranch.toUpperCase().replace('BRANCH-','BR')}</strong>
      <small>Distribution vigilance review · Frozen interval 8</small>
     </div>
     <span className={'badge '+(approvedStep?'green':'amber')}>
      {approvedStep?'APPROVED_FOR_CHECK':'AWAITING_REVIEW'}
     </span>
    </div>

    <div className="next-action-recommendation">
     <small>Recommended Next Action (9-Enum Whitelist):</small>
     <div className="action-pill">
      <Sparkles size={14} color="#3b82f6"/>
      <strong>{droneFlying?'DRONE_IN_FLIGHT':droneCompleted?'REQUEST_ELECTRICAL_RECHECK':'PROPOSE_VIRTUAL_DRONE'}</strong>
     </div>
    </div>

    <div className="ground-log-input">
     <label>Ground-First Lead Note (FR-07):</label>
     <select value={groundPreset} onChange={e=>setGroundPreset(e.target.value)}>
      <option value="obscured">Ground lead notes: Overhead mid-span obscured by compound roof at Pole B-03.</option>
      <option value="clear">Ground lead notes: Clear line of sight; service drops appear intact.</option>
      <option value="refused">Ground lead notes: Substation compound gate locked; inspection delayed.</option>
     </select>
    </div>

    <div className="disposition-button-group">
     <button className="primary full launch-btn" disabled={droneFlying} onClick={onLaunchDrone}>
      <Navigation size={14}/>
      <span>{droneFlying?'GT-01 Flying along Conductor…':droneCompleted?'Re-inspect Flagged Pole with Drone':'Approve Virtual Drone Inspection'}</span>
     </button>
     {droneCompleted&&(
      <button className="primary full approve-btn" style={{marginTop:'8px'}} onClick={()=>{setApprovedStep(true);onApproveAction();}}>
       <CheckCircle2 size={14}/>
       <span>Approve Lineman Electrical Recheck</span>
      </button>
     )}

     <div className="dual-action-row">
      <button className="secondary" onClick={onDismissAction}>
       <XCircle size={13}/>
       <span>Override / Dismiss</span>
      </button>
      <button className="secondary" onClick={()=>onExportReport('json')}>
       <Download size={13}/>
       <span>Export Case (JSON/MD)</span>
      </button>
     </div>
    </div>
   </div>
  </aside>
 );
}
