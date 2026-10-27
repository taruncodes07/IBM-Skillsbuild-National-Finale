import {useEffect,useState} from 'react';
import {ChevronUp,ChevronDown} from 'lucide-react';
import {api} from './api';
export default function EvaluationDrawer({open,onToggle}:{open:boolean;onToggle:()=>void}){
 const [report,setReport]=useState<Record<string,unknown>|null>(null),[error,setError]=useState('');
 useEffect(()=>{if(!open)return;let active=true;api<Record<string,unknown>>('/benchmark').then(r=>{if(active){setReport(r);setError('')}}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[open]);
 return <section className={'evaluation-drawer '+(open?'open':'')}><button className="drawer-header-bar" aria-expanded={open} onClick={onToggle}><strong>Project evidence</strong><span>Evaluation & provenance {open?<ChevronDown size={15}/>:<ChevronUp size={15}/>}</span></button>
  {open&&<div className="drawer-body evidence-body"><div><h3>Evaluation</h3><p>{error||(!report?'Loading saved results...':report.status==='STALE'?'Saved evaluation is stale. Rerun the evaluator.':'Saved synthetic evaluation; field performance is unverified.')}</p>{report&&<details><summary>Saved report</summary><pre>{JSON.stringify(report,null,2)}</pre></details>}</div><div><h3>Source</h3><p>Generated meter readings. Official utility extract pending.</p><a href="/api/sources" target="_blank" rel="noreferrer">Source manifest</a></div><div><h3>IBM Bob</h3><p>Build evidence is maintained in docs/BOB_EVIDENCE.md.</p></div></div>}
 </section>;
}
