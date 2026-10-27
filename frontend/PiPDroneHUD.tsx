import {useState} from 'react';
import {Camera,X} from 'lucide-react';
import type {FlightTelemetry} from './flight';
import type {Evidence} from './types';
import {pretty} from './api';
export default function PiPDroneHUD({active,completed,flightStats,evidence,onClose}:{active:boolean;completed:boolean;flightStats:FlightTelemetry|null;evidence?:Evidence;onClose:()=>void}){
 const [annotated,setAnnotated]=useState(true);
 if(!active&&!completed)return null;
 return <section className="pip-drone-hud" aria-label="Drone inspection"><div className="pip-header"><div className="pip-title"><Camera size={15}/><strong>{active?'Inspection in progress':'Inspection captures'}</strong></div>{!active&&<button aria-label="Close drone captures" onClick={onClose}><X size={15}/></button>}</div>
  {active?<div className="flight-progress"><strong>{Math.round((flightStats?.progress||0)*100)}%</strong><progress max={1} value={flightStats?.progress||0}/><small>{flightStats?`${flightStats.position[1].toFixed(1)} m altitude`:'Preparing camera'}</small></div>:evidence?<><img className="inspection-capture" src={annotated&&evidence.annotated_image_path?evidence.annotated_image_path:evidence.original_image_path} alt={annotated?'Processed inspection capture':'Original drone capture'}/><div className="pip-footer"><button onClick={()=>setAnnotated(!annotated)}>{annotated?'View original':'View processed'}</button><small>{pretty(evidence.observation_status)}</small></div></>:<p className="micro">No saved capture is available.</p>}
 </section>;
}
