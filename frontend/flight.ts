import type {V3} from './types';

export const FLIGHT_DURATION_MS=15000;
export type FlightTelemetry={progress:number;waypoint:number;position:V3};

export function sampleFlight(route:V3[],elapsedMs:number,reduced=false):FlightTelemetry{
 if(route.length<2||route.some(p=>p.length!==3||p.some(v=>!Number.isFinite(v))))throw new Error('A flight needs at least two valid waypoints.');
 const progress=Math.max(0,Math.min(1,elapsedMs/FLIGHT_DURATION_MS));
 const offset=progress*(route.length-1),segment=Math.min(route.length-2,Math.floor(offset));
 const fraction=reduced?(progress===1?1:0):offset-segment;
 const position=route[segment].map((v,i)=>v+(route[segment+1][i]-v)*fraction) as V3;
 return {progress,waypoint:progress===1?route.length:segment+1,position};
}
