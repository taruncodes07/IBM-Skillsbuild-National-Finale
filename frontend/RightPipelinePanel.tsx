import {ArrowRight,FileText} from 'lucide-react';
import type {Snapshot,Case,Detail,Mission} from './types';
import {pretty,n} from './api';
type Props={snapshot:Snapshot;selected:string;actor:string;busy:boolean;detail:Detail|null;cases:Case[];note:string;onNote:(s:string)=>void;onInvestigate:()=>void;onOpenCase:()=>void;onResumeCase:(c:Case)=>void;onTransition:(state:string)=>void;onGround:()=>void;onLaunchDrone:()=>void;onExportReport:(format:'json'|'md')=>void;onCloseCase:()=>void;canFly:boolean;sceneReady:boolean;onSaveNote:()=>void;onSetActor:(actor:string)=>void;onResumeMission:(mission:Mission)=>void;disposition:string;dispositions:string[];onDisposition:(value:string)=>void};
export default function RightPipelinePanel(p:Props){
 const asset=p.snapshot.assets.find(a=>a.id===p.selected)!;
 const area=asset.kind==='household'?asset.parent_id!:p.selected;
 const balance=p.snapshot.balances.find(b=>b.boundary_asset_id===area);
 const alert=p.snapshot.alerts.find(a=>a.boundary_asset_id===area&&a.status==='active');
 const c=p.detail?.case,reviewer=['reviewer','supervisor'].includes(p.actor),analyst=['analyst','supervisor'].includes(p.actor);
 const interrupted=p.detail?.missions.find(m=>!['completed','cancelled'].includes(m.status));
 const status=balance?.validity!=='valid'?'Data incomplete':alert?'Persistent excess':balance.qualifies?'Awaiting persistence':'Within model range';
 return <aside className="zone-d-right" aria-label="Investigation and review">
  <div className="zone-header"><h2>{c?'Case review':'Investigation'}</h2><span className={'badge '+(alert?'amber':'')}>{c?pretty(c.state):alert?'Alert':'Monitoring'}</span></div>
  <section className="review-summary"><small>{asset.label}</small><h3>{status}</h3><p>{balance?.validity!=='valid'?'Restore readings before investigating loss.':alert?'Review the evidence and choose the next check.':balance?.qualifies?'Three consecutive intervals are required.':'No persistent alert in this section.'}</p>
   {!c&&<><button className="primary full" disabled={p.busy||!analyst} onClick={p.onInvestigate}>Analyze section<ArrowRight size={15}/></button>{alert&&<button className="secondary full" disabled={p.busy||!analyst} onClick={p.onOpenCase}>Open case</button>}{!analyst&&<button className="text-button" disabled={p.busy} onClick={()=>p.onSetActor('analyst')}>Switch to analyst</button>}</>}
  </section>
  {c&&p.detail&&<section className="case-controls"><div className="section-title"><h3>Human review</h3><button className="text-button" disabled={p.busy} onClick={p.onCloseCase}>Close</button></div><small className="case-reference">{c.id} / Interval {c.analysis_sequence+1}</small>
   {['open','reopened'].includes(c.state)&&<button className="primary full" disabled={p.busy||!analyst} onClick={()=>p.onTransition('triaged')}>Triage case</button>}
   {c.state!=='open'&&!reviewer&&!['resolved','dismissed'].includes(c.state)&&<button className="secondary full" disabled={p.busy} onClick={()=>p.onSetActor('reviewer')}>Switch to reviewer</button>}
   {c.state==='triaged'&&<button className="primary full" disabled={p.busy||!reviewer} onClick={()=>p.onTransition('ground_review')}>Begin ground review</button>}
   {['ground_review','inspection_requested','evidence_ready','under_review','field_check_required'].includes(c.state)&&<><button className="secondary full" disabled={p.busy||!reviewer} onClick={p.onGround}>Record ground observation</button>{p.canFly&&!interrupted&&<button className="primary full" disabled={p.busy||!reviewer||!p.sceneReady} onClick={p.onLaunchDrone}>{p.sceneReady?'Approve drone inspection':'Loading scene...'}</button>}</>}
   {interrupted&&<button className="primary full" disabled={p.busy||!reviewer||!p.sceneReady} onClick={()=>p.onResumeMission(interrupted)}>Retry interrupted inspection</button>}
   {p.detail.transitions.includes('under_review')&&<button className="secondary full" disabled={p.busy||!reviewer} onClick={()=>p.onTransition('under_review')}>Begin review</button>}
   {['resolved','dismissed'].includes(c.state)&&<button className="secondary full" disabled={p.busy||p.actor!=='supervisor'} onClick={()=>p.onTransition('reopened')}>Reopen case</button>}
   <label>Review note<textarea rows={3} placeholder="Record an observation or decision..." value={p.note} disabled={p.busy} onChange={e=>p.onNote(e.target.value)}/></label><button className="secondary full" disabled={p.busy||!p.note.trim()||p.actor==='presenter'} onClick={p.onSaveNote}>Save note</button>
   {c.state==='under_review'&&<><button className="primary full" disabled={p.busy||!reviewer} onClick={()=>p.onTransition('field_check_required')}>Request field check</button><details><summary>Close case</summary><label>Disposition<select value={p.disposition} disabled={p.busy||p.actor!=='supervisor'} onChange={e=>p.onDisposition(e.target.value)}>{p.dispositions.map(d=><option key={d} value={d}>{d}</option>)}</select></label><button className="secondary full" disabled={p.busy||p.actor!=='supervisor'||!p.note.trim()} onClick={()=>p.onTransition('resolved')}>Resolve with reason</button><button className="secondary full" disabled={p.busy||p.actor!=='supervisor'||!p.note.trim()} onClick={()=>p.onTransition('dismissed')}>Dismiss with reason</button></details>{p.actor!=='supervisor'&&<button className="text-button" disabled={p.busy} onClick={()=>p.onSetActor('supervisor')}>Switch to supervisor</button>}</>}
   <div className="dual-action-row"><button disabled={p.busy} onClick={()=>p.onExportReport('json')}>Export JSON</button><button disabled={p.busy} onClick={()=>p.onExportReport('md')}>Markdown</button></div>
   {!!p.detail.evidence.length&&<details><summary>Captures / {p.detail.evidence.length}</summary>{p.detail.evidence.map(e=><a className="capture-link" key={e.id} href={e.annotated_image_path||e.original_image_path} target="_blank" rel="noreferrer"><img src={e.annotated_image_path||e.original_image_path} alt={'Inspection: '+pretty(e.observation_status)}/><small>{pretty(e.observation_status)} / {n(e.processing_ms,0)} ms</small></a>)}</details>}
   <details><summary>Activity / {p.detail.audit.length}</summary>{p.detail.audit.map(a=><p className="micro" key={a.id}>{pretty(a.action)} / {a.actor_id}</p>)}</details>
  </section>}
  {!c&&<section className="recent-cases"><h3>Saved cases <small>{p.cases.length}</small></h3>{p.cases.length?p.cases.slice(0,5).map(c=><button key={c.id} disabled={p.busy} onClick={()=>p.onResumeCase(c)}><FileText size={15}/><span>{pretty(c.boundary_asset_id)}<small>{pretty(c.state)} / Interval {c.analysis_sequence+1}</small></span><ArrowRight size={13}/></button>):<p className="micro">Cases appear after reviewing an alert.</p>}</section>}
  <p className="review-disclosure">Synthetic observations. Human verification required.</p>
 </aside>;
}
