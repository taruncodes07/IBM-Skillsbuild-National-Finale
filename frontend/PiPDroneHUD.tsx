import {useState} from 'react';
import {Camera,ScanLine,ShieldCheck,AlertTriangle,X} from 'lucide-react';
import type {FlightTelemetry} from './flight';

type Props={
 active:boolean;
 completed:boolean;
 flightStats:FlightTelemetry|null;
 onClose?:()=>void;
};

export default function PiPDroneHUD({active,completed,flightStats,onClose}:Props){
 const [tab,setTab]=useState<'rgb'|'opencv'>('opencv');
 if(!active&&!completed)return null;

 return (
  <div className="pip-drone-hud">
   <div className="pip-header">
    <div className="pip-title">
     <Camera size={13} color="#3b82f6"/>
     <strong>AERIAL DRONE HUD · GT-01</strong>
     <span className="badge blue">{active?'LIVE TELEMETRY':'INSPECTION EVIDENCE'}</span>
    </div>
    <div className="pip-controls">
     <button className={tab==='rgb'?'active':''} onClick={()=>setTab('rgb')}>Raw RGB</button>
     <button className={tab==='opencv'?'active':''} onClick={()=>setTab('opencv')}>OpenCV CV</button>
     {onClose&&<button className="close-btn" onClick={onClose}><X size={13}/></button>}
    </div>
   </div>

   <div className="pip-viewport">
    {tab==='rgb'?(
     <div className="pip-frame rgb-frame">
      <svg viewBox="0 0 320 200" className="hud-svg">
       <rect width="320" height="200" fill="#090f19"/>
       <polygon points="40,160 140,90 280,130 180,195" fill="#172230" stroke="#253549" strokeWidth="1.5"/>
       <rect x="70" y="80" width="35" height="30" fill="#0f1924" stroke="#253549"/>
       <line x1="160" y1="20" x2="160" y2="180" stroke="#64748b" strokeWidth="3"/>
       <line x1="120" y1="40" x2="200" y2="40" stroke="#94a3b8" strokeWidth="2.5"/>
       <line x1="20" y1="35" x2="120" y2="40" stroke="#cbd5e1" strokeWidth="1.5"/>
       <line x1="200" y1="40" x2="300" y2="45" stroke="#cbd5e1" strokeWidth="1.5"/>
       <line x1="160" y1="40" x2="90" y2="90" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3,2"/>
       <circle cx="160" cy="100" r="28" stroke="#3b82f6" strokeWidth="1" fill="none" opacity="0.6"/>
       <line x1="160" y1="65" x2="160" y2="135" stroke="#3b82f6" strokeWidth="1" strokeDasharray="2,2"/>
       <line x1="125" y1="100" x2="195" y2="100" stroke="#3b82f6" strokeWidth="1" strokeDasharray="2,2"/>
      </svg>
      <div className="pip-stamp">
       <span>POSE: [X: 16.2, Y: 10.4, Z: 24.1] · FOV 45°</span>
       <span className="hash"><ShieldCheck size={10}/> sha256:7f9a8b1c4e2d3f...</span>
      </div>
     </div>
    ):(
     <div className="pip-frame opencv-frame">
      <svg viewBox="0 0 320 200" className="hud-svg">
       <rect width="320" height="200" fill="#05080f"/>
       <line x1="20" y1="35" x2="120" y2="40" stroke="#22c55e" strokeWidth="2"/>
       <line x1="200" y1="40" x2="300" y2="45" stroke="#22c55e" strokeWidth="2"/>
       <line x1="120" y1="40" x2="200" y2="40" stroke="#22c55e" strokeWidth="2"/>
       <line x1="160" y1="40" x2="90" y2="90" stroke="#ec4899" strokeWidth="3"/>
       <rect x="80" y="32" width="90" height="65" fill="none" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="4,2"/>
       <text x="85" y="28" fill="#f43f5e" fontSize="9" fontFamily="monospace" fontWeight="bold">UNMATCHED TAP · IOU: 0.94</text>
       <polygon points="30,170 150,110 270,140 170,195" fill="none" stroke="#475569" strokeWidth="1" strokeDasharray="3,3"/>
       <text x="180" y="165" fill="#64748b" fontSize="8" fontFamily="monospace">ROOF OBSTRUCTION</text>
      </svg>
      <div className="pip-stamp">
       <span className="cand-tag">OPENCV 4.8 HOUGH/CANNY · CONFIDENCE 0.94</span>
       <span className="hash">ALIGNED TOPOLOGY-1 MATCH</span>
      </div>
     </div>
    )}

    {flightStats&&active&&(
     <div className="pip-telemetry-bar">
      <span>ALT: <strong>{flightStats.position[1].toFixed(1)}m</strong></span>
      <span>WP: <strong>{flightStats.waypoint}/3</strong></span>
      <span>SPD: <strong>4.2 m/s</strong></span>
      <span>MODE: <strong>CORRIDOR TRACK</strong></span>
     </div>
    )}
   </div>

   <div className="pip-footer">
    <div className="pip-badge-row">
     <span className="badge green"><ShieldCheck size={11}/> CANDIDATE_FOUND (Score: 0.94)</span>
     <span className="badge cyan">640×480 RGB</span>
    </div>
    <div className="pip-disclaimer">
     <AlertTriangle size={11} color="#f59e0b"/>
     <p><strong>Mandatory Disclaimer:</strong> Visual geometry candidate only. Does not prove current flow, energization, or theft.</p>
    </div>
   </div>
  </div>
 );
}
