import {useEffect,useState} from 'react';
import {api} from './api';
import type {Snapshot} from './types';

type Day={date:string;first_sequence:number;missing_readings:number;coverage_fraction:number;feeder_input_kwh:number;household_valid_kwh:number;household_sum_complete:boolean};
type Month={days:Day[];aggregation_note:string};

export default function MonthReplay({snapshot,busy,onSeek}:{snapshot:Snapshot;busy:boolean;onSeek:(sequence:number)=>void}){
 const [month,setMonth]=useState<Month|null>(null),[error,setError]=useState(''),[attempt,setAttempt]=useState(0);
 useEffect(()=>{let active=true;setMonth(null);setError('');api<Month>(`/runs/${snapshot.run.id}/month`).then(m=>{if(active)setMonth(m)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[snapshot.run.id,attempt]);
 const day=Math.floor(snapshot.seq/96),selected=month?.days[day];
 // Derive the year-month prefix from the source manifest rather than hardcoding 2022-09.
 const periodStart=snapshot.run.source?.period_start??month?.days[0]?.date??'2022-09-01';
 const yearMonth=periodStart.slice(0,7);
 const totalDays=month?.days.length??30;
 const minDate=`${yearMonth}-01`,maxDate=`${yearMonth}-${String(totalDays).padStart(2,'0')}`;
 const datePattern=new RegExp(`^${yearMonth}-\\d{2}$`);
 return <details className="month-replay" open>
  <summary>{yearMonth} replay <small>{totalDays} days · IST</small></summary>
  <p>Development fixture · BESCOM and frozen source onboarding pending</p>
  <div className="replay-date-controls"><label>Replay date<input aria-label="Replay date" type="date" min={minDate} max={maxDate} value={`${yearMonth}-${String(day+1).padStart(2,'0')}`} disabled={busy} onChange={e=>{const value=e.target.value;if(datePattern.test(value)){const d=Number(value.slice(-2));if(d>=1&&d<=totalDays)onSeek((d-1)*96)}}}/></label></div>
  {error?<p role="alert">{error} <button onClick={()=>setAttempt(a=>a+1)}>Retry summary</button></p>:!month?<p role="status">Calculating daily coverage…</p>:<>
   <div className="day-grid" role="group" aria-label="September replay days">{month.days.map((d,i)=><button key={d.date} aria-label={`September ${i+1}, ${d.missing_readings} missing readings`} aria-pressed={i===day} className={(i===day?'selected ':'')+(d.missing_readings?'partial':'')} disabled={busy} onClick={()=>onSeek(d.first_sequence)}>{i+1}{d.missing_readings>0&&<span aria-hidden="true">*</span>}</button>)}</div>
   {selected&&<dl className="day-summary"><dt>Feeder input</dt><dd>{selected.feeder_input_kwh.toFixed(2)} kWh</dd><dt>Valid household sum</dt><dd>{selected.household_valid_kwh.toFixed(2)} kWh{!selected.household_sum_complete?' (partial)':''}</dd><dt>Reading coverage</dt><dd>{(selected.coverage_fraction*100).toFixed(2)}% · {selected.missing_readings} missing</dd></dl>}
   <p className="micro">* Partial day. Missing readings are excluded from sums; feeder and household totals are separate meter cuts.</p>
  </>}
 </details>
}
