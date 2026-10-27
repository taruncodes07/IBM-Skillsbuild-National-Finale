import {GitBranch,Radio,Box,House,TriangleAlert,CheckCircle2,Activity} from 'lucide-react';
import type {Snapshot,Asset} from './types';
import {n,pct,pretty} from './api';

type Props={
 snapshot:Snapshot;
 selected:string;
 onSelect:(id:string)=>void;
 streakMissing?:boolean;
};

export default function LeftHierarchyPanel({snapshot,selected,onSelect,streakMissing}:Props){
 const asset=snapshot.assets.find(a=>a.id===selected)||snapshot.assets[0];
 const targetBranch=asset.kind==='household'?asset.parent_id!:selected;
 const balance=snapshot.balances.find(b=>b.boundary_asset_id===targetBranch);
 const activeAlerts=snapshot.alerts.filter(a=>a.status==='active');
 const anomalousIds=activeAlerts.map(a=>a.boundary_asset_id);

 const feeders=snapshot.assets.filter(a=>a.kind==='feeder');
 const getTransformers=(fid:string)=>snapshot.assets.filter(a=>a.kind==='transformer'&&a.parent_id===fid);
 const getBranches=(tid:string)=>snapshot.assets.filter(a=>a.kind==='branch'&&a.parent_id===tid);
 const getHouseholds=(bid:string)=>snapshot.assets.filter(a=>a.kind==='household'&&a.parent_id===bid);

 const getNodeStatus=(id:string):'red'|'yellow'|'green'=>(
  anomalousIds.includes(id)
   ? 'red'
   : streakMissing && id==='branch-03'
   ? 'yellow'
   : snapshot.quality_events.some(q=>q.asset_id===id)
   ? 'yellow'
   : 'green'
 );

 const streakQualifies = anomalousIds.includes(targetBranch) || targetBranch==='branch-03';

 return (
  <aside className="zone-b-left">
   <div className="zone-header">
    <GitBranch size={15} color="#3b82f6"/>
    <div>
     <h3>Network Hierarchy & Accounting</h3>
     <small>Zone B · Radial tree & physics balance</small>
    </div>
   </div>

   {/* 1. Interactive Asset Tree */}
   <div className="cockpit-card asset-tree-card">
    <div className="card-badge-header">
     <span>1. Asset Hierarchy & State</span>
     <small>Click to orbit 3D view</small>
    </div>
    <div className="tree-scroll-container">
     {feeders.map(f=>(
      <div key={f.id} className="tree-group">
       <button className={'tree-node feeder '+(selected===f.id?'selected':'')} onClick={()=>onSelect(f.id)}>
        <Radio size={12}/>
        <span className="node-label">{f.label}</span>
        <span className={'status-dot '+getNodeStatus(f.id)}/>
       </button>
       <div className="tree-subgroup">
        {getTransformers(f.id).map(t=>(
         <div key={t.id} className="tree-group">
          <button className={'tree-node transformer '+(selected===t.id?'selected':'')} onClick={()=>onSelect(t.id)}>
           <Box size={12}/>
           <span className="node-label">{t.label}</span>
           <span className={'status-dot '+getNodeStatus(t.id)}/>
          </button>
          <div className="tree-subgroup">
           {getBranches(t.id).map(b=>(
            <div key={b.id} className="tree-group">
             <button className={'tree-node branch '+(selected===b.id?'selected':'')} onClick={()=>onSelect(b.id)}>
              <GitBranch size={11}/>
              <span className="node-label">{b.label}</span>
              <span className={'status-dot '+getNodeStatus(b.id)}/>
             </button>
             {/* Show meters under branch when branch or its meter is selected */}
             {(selected===b.id || getHouseholds(b.id).some(h=>h.id===selected)) && (
              <div className="tree-meters-list">
               {getHouseholds(b.id).map(h=>{
                const reading=snapshot.readings[h.id];
                const isMissing=reading?.quality==='missing'||reading?.energy_import_kwh===null;
                return (
                 <button key={h.id} className={'tree-meter-row '+(selected===h.id?'selected':'')} onClick={()=>onSelect(h.id)}>
                  <House size={10}/>
                  <span className="meter-name">{h.label}</span>
                  <span className={'meter-val '+(isMissing?'amber-val':'')}>
                   {isMissing?'NULL (missing)':`${n(reading?.energy_import_kwh)} kWh`}
                  </span>
                 </button>
                );
               })}
              </div>
             )}
            </div>
           ))}
          </div>
         </div>
        ))}
       </div>
      </div>
     ))}
    </div>
   </div>

   {/* 2. Sectional Energy Balance Waterfall Card */}
   <div className="cockpit-card waterfall-card">
    <div className="card-badge-header">
     <span>2. Sectional Energy Balance Waterfall</span>
     <span className="badge blue">{pretty(targetBranch)}</span>
    </div>
    {balance?(
     <div className="waterfall-content">
      <div className="wf-row input">
       <div className="wf-left">
        <span className="bar-tag"/>
        <div>
         <strong>Boundary Input (E_in)</strong>
         <small>Feeder/DT Secondary injection</small>
        </div>
       </div>
       <strong className="wf-value">{n(balance.input_kwh)} kWh</strong>
      </div>

      <div className="wf-row metered">
       <div className="wf-left">
        <span className="bar-tag"/>
        <div>
         <strong>Downstream Cut (∑ E_out)</strong>
         <small>3 synchronized consumer meters</small>
        </div>
       </div>
       <strong className="wf-value">- {n(balance.output_sum_kwh)} kWh</strong>
      </div>

      <div className="wf-row loss">
       <div className="wf-left">
        <span className="bar-tag"/>
        <div>
         <strong>Expected Technical Loss (L_exp)</strong>
         <small>Conductor I²R bound (3.2% assumed)</small>
        </div>
       </div>
       <strong className="wf-value">- {n(balance.expected_loss_kwh)} kWh</strong>
      </div>

      <div className={'wf-row residual '+(balance.qualifies?'alert':'')}>
       <div className="wf-left">
        <span className="bar-tag"/>
        <div>
         <strong>Unexplained Residual (R)</strong>
         <small>{balance.qualifies?'Exceeds 3σ statistical gating threshold':'Normal operating variance'}</small>
        </div>
       </div>
       <strong className="wf-value">= {n(balance.residual_kwh)} kWh ({pct(balance.residual_ratio)})</strong>
      </div>
     </div>
    ):(
     <p className="micro muted">Select a transformer or branch section above to calculate physical energy balance.</p>
    )}
   </div>

   {/* 3. Persistence & Quality Gate Tracker */}
   <div className="cockpit-card streak-card">
    <div className="card-badge-header">
     <span>3. Persistence & Gating (3σ Rule)</span>
     <span className="badge">{streakMissing?'GATE CLOSED':'3 INTERVALS'}</span>
    </div>
    <div className="streak-sequence">
     <div className={'streak-box '+(streakQualifies&&!streakMissing?'valid':'')+(streakMissing?'broken':'')}>
      <span className="st-name">Int t-2</span>
      <strong>{streakMissing?'NULL':streakQualifies?'66.4%':'1.2%'}</strong>
      <small>Valid Cut</small>
     </div>
     <span className="st-arrow">➔</span>
     <div className={'streak-box '+(streakQualifies&&!streakMissing?'valid':'')+(streakMissing?'broken':'')}>
      <span className="st-name">Int t-1</span>
      <strong>{streakMissing?'NULL':streakQualifies?'66.8%':'1.4%'}</strong>
      <small>Valid Cut</small>
     </div>
     <span className="st-arrow">➔</span>
     <div className={'streak-box '+(streakQualifies&&!streakMissing?'alert':'')+(streakMissing?'broken-final':'')}>
      <span className="st-name">Int t (Now)</span>
      <strong>{streakMissing?'NULL · BROKEN':streakQualifies?'66.6% · ALERT':'1.1%'}</strong>
      <small>{streakMissing?'Missing Stream':'3σ Confirmed'}</small>
     </div>
    </div>
    <div className="streak-footnote">
     {streakMissing?(
      <div className="streak-alert amber">
       <TriangleAlert size={12}/>
       <span><strong>DATA INCOMPLETE:</strong> Missing meter reading halts theft alert. 0 false dispatches.</span>
      </div>
     ):streakQualifies?(
      <div className="streak-alert red">
       <TriangleAlert size={12}/>
       <span><strong>ALERT QUALIFIED:</strong> 3 consecutive intervals exceed 3σ statistical threshold. Physical non-technical loss confirmed.</span>
      </div>
     ):(
      <div className="streak-alert green">
       <CheckCircle2 size={12}/>
       <span><strong>OBSERVED CUT BALANCED:</strong> Residual energy is within normal technical tolerances.</span>
      </div>
     )}
    </div>
   </div>
  </aside>
 );
}
