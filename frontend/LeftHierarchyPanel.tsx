import {GitBranch,Radio,Box,House} from 'lucide-react';
import type {Snapshot} from './types';
import {n,pct} from './api';
export default function LeftHierarchyPanel({snapshot,selected,onSelect,disabled}:{snapshot:Snapshot;selected:string;onSelect:(id:string)=>void;disabled?:boolean}){
 const asset=snapshot.assets.find(a=>a.id===selected)!;
 const boundary=asset.kind==='household'?asset.parent_id:selected;
 const balance=snapshot.balances.find(b=>b.boundary_asset_id===boundary);
 const active=snapshot.alerts.some(a=>a.boundary_asset_id===boundary&&a.status==='active');
 const status=(id:string)=>snapshot.alerts.some(a=>a.boundary_asset_id===id&&a.status==='active')?'Alert':snapshot.balances.some(b=>b.boundary_asset_id===id&&b.validity!=='valid')?'Incomplete':'Balanced';
 const recent=snapshot.history.filter(h=>h.seq<=snapshot.seq).slice(-3);
 const renderNode=(id:string,depth=0):React.ReactNode=>{
  const node=snapshot.assets.find(a=>a.id===id)!;
  const Icon=node.kind==='feeder'?Radio:node.kind==='transformer'?Box:node.kind==='household'?House:GitBranch;
  const descendants=snapshot.assets.filter(a=>a.parent_id===id&&a.meter_id);
  const expanded=node.kind!=='branch'||selected===id||descendants.some(a=>a.id===selected);
  const quality=status(id);
  return <div key={id}><button className={'tree-node '+(selected===id?'selected':'')} style={{paddingLeft:10+depth*13}} disabled={disabled} aria-pressed={selected===id} onClick={()=>onSelect(id)}><Icon size={14}/><span className="node-label">{node.label}</span>{node.kind==='household'?<small>{n(snapshot.readings[id]?.energy_import_kwh)} kWh</small>:<span className={'status-dot '+(quality==='Alert'?'red':quality==='Incomplete'?'yellow':'green')} role="img" aria-label={quality}/>}</button>{expanded&&descendants.map(a=>renderNode(a.id,depth+1))}</div>;
 };
 return <aside className="zone-b-left" aria-label="Network and energy"><div className="zone-header"><h2>Network</h2><small>2 feeders / 24 homes</small></div><div className="tree-scroll-container">{snapshot.assets.filter(a=>a.kind==='feeder').map(a=>renderNode(a.id))}</div>
  <section className="energy-section"><div className="section-title"><h3>Energy balance</h3><small>kWh / 15 min</small></div>{balance?<><dl className="energy-values"><div><dt>Input</dt><dd>{n(balance.input_kwh)}</dd></div><div><dt>Metered</dt><dd>{n(balance.output_sum_kwh)}</dd></div><div><dt>Expected loss</dt><dd>{n(balance.expected_loss_kwh)}</dd></div><div className={'energy-residual '+(active?'amber-text':'')}><dt>Unexplained</dt><dd>{n(balance.residual_kwh)} <small>{pct(balance.residual_ratio)}</small></dd></div></dl>
   <div className="interval-strip" aria-label="Recent interval residuals">{recent.map(h=>{const b=h.balances.find(b=>b.boundary_asset_id===boundary);return <div key={h.seq} className={b?.validity!=='valid'?'incomplete':b.qualifies?'excess':''}><small>#{h.seq+1}</small><strong>{pct(b?.residual_ratio)}</strong></div>})}</div>
   <p className={'balance-state '+(balance.validity!=='valid'||active?'amber-text':'')}>{balance.validity!=='valid'?'Data incomplete':active?'Persistent excess':balance.qualifies?'Awaiting persistence':'Within model range'}</p>
   <details className="calculation"><summary>Calculation details</summary><p>Input - metered - expected loss = unexplained energy.</p><p>Threshold: {n(balance.threshold_kwh)} kWh. Alerts require three valid consecutive intervals.</p>{balance.invalid_reasons.map(r=><p key={r}>{r}</p>)}</details></>:<p className="micro">Select a measured section.</p>}</section>
 </aside>;
}
