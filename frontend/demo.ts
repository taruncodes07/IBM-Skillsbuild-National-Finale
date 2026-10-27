import type {Snapshot} from './types';

export const DEMO_SCENARIOS = ['clean', 'missing_telemetry', 'visible_unmetered_load'] as const;

type Request = <T>(path:string, method:string, body:unknown, actor?:string)=>Promise<T>;

// Return one paused, fully prepared snapshot; never publish partial demo state.
export async function loadDemo(preset:number, request:Request):Promise<Snapshot>{
 const scenario=DEMO_SCENARIOS[preset-1];
 if(!scenario)throw new Error('Choose a demo scenario.');
 let snapshot=await request<Snapshot>('/runs','POST',{seed:42,scenario,mode:'laboratory',coverage_profile:'full_sectional'});
 for(let i=0;i<3;i++)snapshot=await request<Snapshot>(`/runs/${snapshot.run.id}/control`,'POST',{command:'step',expected_revision:snapshot.run.revision});
 return snapshot;
}
