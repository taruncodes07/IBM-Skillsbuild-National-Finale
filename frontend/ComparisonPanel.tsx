import {useEffect,useId,useRef,useState} from 'react';
import {Download,Pause,Play,RotateCcw,X} from 'lucide-react';
import {api,date} from './api';

type Point={sequence:number;elapsed_minutes:number;timestamp:string;without_kwh:number;with_kwh:number;unmetered_without_kwh:number;unmetered_with_kwh:number;technical_without_kwh:number;technical_with_kwh:number;delivered_kwh:number;cumulative_without_kwh:number;cumulative_with_kwh:number;saved_kwh:number;status:string};
type Report={version:string;assumptions:{seed:number;scenario:string;repair_delay_minutes:number;repair_effectiveness:number;coverage_profile:string};points:Point[];detection_sequence:number|null;repair_sequence:number|null;incident_start_sequence:number|null;repair_within_horizon:boolean;detection_timestamp:string|null;repair_timestamp:string|null;source:{kind:string;project_dataset:string;runtime:string};methodology:string};
const amount=(v:number)=>v.toLocaleString('en-IN',{minimumFractionDigits:1,maximumFractionDigits:1});
const clock=(minutes:number)=>`${String(Math.floor(minutes/60)).padStart(2,'0')}:${String(minutes%60).padStart(2,'0')}`;

export default function ComparisonPanel({onClose,reduced}:{onClose:()=>void;reduced:boolean}){
 const [report,setReport]=useState<Report|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 const [seed,setSeed]=useState(42),[scenario,setScenario]=useState('visible_unmetered_load'),[delay,setDelay]=useState(60),[effectiveness,setEffectiveness]=useState(90),[coverage,setCoverage]=useState('full_sectional');
 const [frame,setFrame]=useState(-1),[playing,setPlaying]=useState(false);
 const dialog=useRef<HTMLElement>(null),request=useRef(0),inFlight=useRef(false),close=useRef(onClose);
 close.current=onClose;
 const id=useId();
 useEffect(()=>{
  const previous=document.activeElement as HTMLElement|null;
  const elements=()=>Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),summary')||[]).filter(e=>e.getClientRects().length);
  elements()[0]?.focus();
  const keydown=(e:KeyboardEvent)=>{if(e.key==='Escape'){e.preventDefault();close.current()}if(e.key==='Tab'){const items=elements(),first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}};
  document.addEventListener('keydown',keydown);return()=>{request.current++;document.removeEventListener('keydown',keydown);previous?.focus()};
 },[]);
 useEffect(()=>{if(!playing||!report)return;const timer=setInterval(()=>setFrame(v=>Math.min(report.points.length-1,v+1)),180);return()=>clearInterval(timer)},[playing,report]);
 useEffect(()=>{if(report&&frame===report.points.length-1)setPlaying(false)},[frame,report]);
 async function run(){
  if(inFlight.current)return;
  inFlight.current=true;const current=++request.current;setPlaying(false);setLoading(true);setError('');
  try{const result=await api<Report>('/comparison','POST',{seed,scenario,repair_delay_minutes:delay,repair_effectiveness:effectiveness/100,coverage_profile:coverage});if(current!==request.current)return;setReport(result);setFrame(reduced?95:-1);setPlaying(!reduced)}
  catch(e){if(current===request.current)setError((e as Error).message)}finally{inFlight.current=false;if(current===request.current)setLoading(false)}
 }
 const point=report&&frame>=0?report.points[frame]:null;
 const without=point?.cumulative_without_kwh||0,withSystem=point?.cumulative_with_kwh||0,saved=point?.saved_kwh||0;
 const totalWithout=report?.points.at(-1)?.cumulative_without_kwh||1;
 const changed=!!report&&(seed!==report.assumptions.seed||scenario!==report.assumptions.scenario||delay!==report.assumptions.repair_delay_minutes||effectiveness/100!==report.assumptions.repair_effectiveness||coverage!==report.assumptions.coverage_profile);
 const detected=!!report&&report.detection_sequence!==null&&frame>=report.detection_sequence;
 const repaired=!!report&&report.repair_sequence!==null&&frame>=report.repair_sequence;
 const visible=report?.points.slice(0,frame+1)||[];
 const y=(v:number)=>250-v/totalWithout*210;
 const x=(seq:number)=>60+(seq+1)/96*780;
 const path=(key:'cumulative_without_kwh'|'cumulative_with_kwh')=>'M60,250'+visible.map(p=>` L${x(p.sequence)},${y(p[key])}`).join('');
 const exportReport=()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=`grid-trace-comparison-seed-${report.assumptions.seed}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 return <div className="modal-backdrop comparison-backdrop"><section ref={dialog} className="comparison-panel" role="dialog" aria-modal="true" aria-labelledby={id}>
  <div className="comparison-heading"><div><span className="comparison-eyebrow">HACKATHON / PAIRED SIMULATION</span><h2 id={id}>The same grid. A different outcome.</h2><p>24 hours of electricity loss, with and without VidyutDrishti.</p></div><button onClick={onClose} aria-label="Close loss comparison"><X size={20}/></button></div>
  <div className="comparison-assumptions">
   <label>Scenario<select value={scenario} disabled={loading} onChange={e=>setScenario(e.target.value)}><option value="visible_unmetered_load">Visible unmetered load</option><option value="hidden_bypass">Hidden bypass</option><option value="clean">Clean network / control</option></select></label>
   <label>Seed<input type="number" min={0} max={1000000} value={seed} disabled={loading} onChange={e=>setSeed(+e.target.value)}/></label>
   <label>Repair after detection<select value={delay} disabled={loading} onChange={e=>setDelay(+e.target.value)}><option value={0}>Immediately after alert</option><option value={30}>30 minutes</option><option value={60}>1 hour</option><option value={120}>2 hours</option><option value={1440}>Next day / no repair today</option></select></label>
   <label>Loss removed<select value={effectiveness} disabled={loading} onChange={e=>setEffectiveness(+e.target.value)}><option value={0}>0% / investigation only</option><option value={50}>50%</option><option value={90}>90%</option><option value={100}>100%</option></select></label>
   <label>Meter coverage<select value={coverage} disabled={loading} onChange={e=>setCoverage(e.target.value)}><option value="full_sectional">Full sectional meters</option><option value="pgvcl_like">Sparse / branch unobservable</option></select></label>
   <button className="primary" disabled={loading||!Number.isInteger(seed)||seed<0||seed>1000000} onClick={run}><Play size={16}/>{loading?'Calculating…':report?'Run again':'Run comparison'}</button>
  </div>
  {error&&<p role="alert" className="comparison-error">{error}</p>}
  {changed&&<p className="comparison-change" role="status">Settings changed. Run again to apply them; the chart still shows the previous run.</p>}
  <div className="comparison-metrics" aria-label="Cumulative physical network loss">
   <div className="without"><span>Without VidyutDrishti</span><strong>{amount(without)} <small>kWh lost</small></strong><p>Loss continues without intervention.</p></div>
   <div className="with"><span>With VidyutDrishti + crew repair</span><strong>{amount(withSystem)} <small>kWh lost</small></strong><p>Detection → {report?.assumptions.repair_delay_minutes??delay} min response → {Math.round((report?.assumptions.repair_effectiveness??effectiveness/100)*100)}% removal.</p></div>
   <div className="saved"><span>Energy saved in this simulation</span><strong>{amount(saved)} <small>kWh</small></strong><p>{without?amount(saved/without*100):'0.0'}% less total network loss so far.</p></div>
  </div>
  <div className="comparison-chart-heading"><strong>Cumulative network loss <small>/ kWh</small></strong><div><span className="chart-without">— Without system</span><span className="chart-with">┄ With system + repair</span></div></div>
  <svg className="comparison-chart" viewBox="0 0 900 290" role="img" aria-labelledby={`${id}-chart`}><title id={`${id}-chart`}>Cumulative electricity loss: without VidyutDrishti {amount(without)} kWh; with VidyutDrishti and simulated repair {amount(withSystem)} kWh, saving {amount(saved)} kWh. Use the timeline slider to inspect each interval.</title>
   {[0,.25,.5,.75,1].map(f=><g key={f}><line x1="60" x2="840" y1={y(totalWithout*f)} y2={y(totalWithout*f)} stroke="#304455" strokeDasharray="3 5"/><text x="48" y={y(totalWithout*f)+4} textAnchor="end">{Math.round(totalWithout*f)}</text></g>)}
   {[0,6,12,18,24].map(h=><text key={h} x={60+h/24*780} y="278" textAnchor="middle">{clock(h*60)}</text>)}
   {report?.incident_start_sequence!=null&&frame>=report.incident_start_sequence&&<line x1={x(report.incident_start_sequence-1)} x2={x(report.incident_start_sequence-1)} y1="36" y2="250" stroke="#f3ba77" opacity=".4"/>}
   {detected&&report&&<line x1={x(report.detection_sequence!)} x2={x(report.detection_sequence!)} y1="36" y2="250" stroke="#9dbdfa" strokeDasharray="3 4"/>}
   {repaired&&report&&<line x1={x(report.repair_sequence!-1)} x2={x(report.repair_sequence!-1)} y1="36" y2="250" stroke="#63dec0" strokeDasharray="3 4"/>}
   <path d={path('cumulative_without_kwh')} fill="none" stroke="#f3ba77" strokeWidth="3"/>
   <path d={path('cumulative_with_kwh')} fill="none" stroke="#63dec0" strokeWidth="3" strokeDasharray="9 5"/>
   {point&&<><circle cx={x(frame)} cy={y(without)} r="4" fill="#f3ba77"/><circle cx={x(frame)} cy={y(withSystem)} r="4" fill="#63dec0"/></>}
   {!report&&<text x="450" y="145" textAnchor="middle" className="chart-empty">Run the simulation to compare both paths.</text>}
  </svg>
  <div className="comparison-playback"><button disabled={!report||loading} aria-label={playing?'Pause comparison':'Play comparison'} onClick={()=>{if(frame===95)setFrame(-1);setPlaying(!playing)}}>{playing?<Pause size={16}/>:<Play size={16}/>}</button><button disabled={!report||loading} aria-label="Restart comparison playback" onClick={()=>{setFrame(-1);setPlaying(false)}}><RotateCcw size={16}/></button><input type="range" aria-label="Comparison time" min={-1} max={95} value={frame} disabled={!report||loading} onChange={e=>{setPlaying(false);setFrame(+e.target.value)}}/><strong>{clock((frame+1)*15)} <small>IST</small></strong><button disabled={!report||loading} onClick={()=>{setPlaying(false);setFrame(95)}}>Show outcome</button><button disabled={!report||loading} onClick={exportReport} aria-label="Download comparison report"><Download size={16}/></button></div>
  <ol className="comparison-story" aria-label="Simulation milestones">
   <li className={report?.incident_start_sequence!=null&&frame>=report.incident_start_sequence?'reached':''}><span>01 / INCIDENT</span><strong>{report?.assumptions.scenario==='clean'?'Clean control':'02:00 · unmetered load begins'}</strong><p>Identical demand and incident in both paths.</p></li>
   <li className={detected?'reached':''}><span>02 / DETECT</span><strong>{detected&&report?.detection_timestamp?`${date(report.detection_timestamp,true)} · branch localized`:report&&frame===95?'No observable branch alert':'Waiting for 3 valid intervals'}</strong><p>Uses the operational residual and persistence rules.</p></li>
   <li className={repaired?'reached':''}><span>03 / RESPOND</span><strong>{repaired&&report?.repair_timestamp?`${date(report.repair_timestamp,true)} · simulated repair`:report&&frame===95?'No repair during this day':'Crew response pending'}</strong><p>Human response is assumed; technical losses remain.</p></li>
  </ol>
  <p className="comparison-caption" role="status">{!report?'Choose assumptions and run the paired simulation.':frame===95?`Day complete. ${amount(saved)} kWh saved under the displayed assumptions.`:repaired?'Simulated repair is active. The two loss curves now diverge.':detected?'Persistent loss detected on Branch 03. Waiting for the assumed crew response.':'Monitoring both paths with identical demand.'}</p>
  <details className="comparison-method"><summary>Data, assumptions & accounting</summary><p>Project dataset: real-world-derived data with partially synthesized columns, as described by the team. This comparison runs the deterministic network simulator; it does not replay the supplied CSV.</p><p>{report?.methodology||'Loss is feeder physical input minus energy delivered to households, counted once across the network. Both paths share the same seed, demand and incident. A simulated crew repair removes the selected fraction of unmetered load after detection and the selected delay.'}</p><p>Detector inputs contain meter observations only. Simulator ground truth scores physical savings. No repair, no detection, or a clean control produces no claimed savings. These are simulated outcomes, not measured field results.</p>{point&&<p>Current interval: {amount(point.without_kwh)} / {amount(point.with_kwh)} kWh lost (without / with). Technical loss: {amount(point.technical_without_kwh)} / {amount(point.technical_with_kwh)} kWh; unmetered load: {amount(point.unmetered_without_kwh)} / {amount(point.unmetered_with_kwh)} kWh.</p>}</details>
 </section></div>;
}
