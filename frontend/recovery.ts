// Browser recovery state contains local demo context, never API credentials.
export type Store=Pick<Storage,'getItem'|'setItem'|'removeItem'>;
export function resilientStore(getStore:()=>Store):Store{
 const memory=new Map<string,string>();let unavailable=false;
 return {getItem(key){if(!unavailable){try{return getStore().getItem(key)}catch{unavailable=true}}return memory.get(key)??null},
 setItem(key,value){memory.set(key,value);if(!unavailable){try{getStore().setItem(key,value)}catch{unavailable=true}}},
 removeItem(key){memory.delete(key);if(!unavailable){try{getStore().removeItem(key)}catch{unavailable=true}}}};
}
export const localStore=resilientStore(()=>window.localStorage);
export const sessionStore=resilientStore(()=>window.sessionStorage);
export function readJson<T>(store:Store,key:string):T|null{try{return JSON.parse(store.getItem(key)||'null') as T|null}catch{return null}}
export type Workspace={runId:string;assetId:string;sequence:number|null;screen:'network'|'inspection';caseId:string|null;actor:string;analysis?:{area:string;sequence:number}|null};
export const WORKSPACE_KEY='gridtrace-workspace-v2';
export function restoreWorkspace(raw:unknown,runs:{id:string}[],cases:{id:string;run_id:string;boundary_asset_id:string;analysis_sequence:number}[]):Workspace|null{
 if(!raw||typeof raw!=='object')return null;
 const v=raw as Partial<Workspace>;
 const actor=['analyst','reviewer','supervisor','presenter'].includes(v.actor||'')?v.actor!:'analyst';
 const chosen=v.screen==='inspection'?cases.find(c=>c.id===v.caseId):null;
 if(chosen&&runs.some(r=>r.id===chosen.run_id))return {runId:chosen.run_id,assetId:chosen.boundary_asset_id,sequence:chosen.analysis_sequence,screen:'inspection',caseId:chosen.id,actor,analysis:v.analysis?.sequence===chosen.analysis_sequence?{area:chosen.boundary_asset_id,sequence:chosen.analysis_sequence}:null};
 if(!runs.some(r=>r.id===v.runId))return null;
 const sequence=Number.isInteger(v.sequence)&&v.sequence!=null&&v.sequence>=0&&v.sequence<2880?v.sequence:null;
 const analysis=v.analysis&&typeof v.analysis.area==='string'&&Number.isInteger(v.analysis.sequence)&&v.analysis.sequence>=0&&v.analysis.sequence<2880?v.analysis:null;
 return {runId:v.runId!,assetId:typeof v.assetId==='string'?v.assetId:'branch-03',sequence,screen:'network',caseId:null,actor,analysis};
}
export type InvestigationRequest={run_id:string;area_id:string;sequence:number;initial_check?:string};
type Pending={body:InvestigationRequest&{idempotency_key:string};actor:string};
export function pendingInvestigation(store:Store,key:string):Pending|null{
 const v=readJson<Pending>(store,key+':pending');return v&&typeof v.body?.idempotency_key==='string'&&typeof v.actor==='string'?v:null;
}
const submissions=new Map<string,Promise<{id:string}>>();
export function submitInvestigation<T extends {id:string}>(store:Store,key:string,input:InvestigationRequest,actor:string,post:(body:Pending['body'],actor:string)=>Promise<T>,makeKey=()=>crypto.randomUUID()):Promise<T>{
 const ongoing=submissions.get(key);if(ongoing)return ongoing as Promise<T>;
 const previous=pendingInvestigation(store,key);
 const pending=previous&&previous.body.run_id===input.run_id&&previous.body.area_id===input.area_id&&previous.body.sequence===input.sequence?previous:{body:{...input,idempotency_key:makeKey()},actor};
 store.setItem(key+':pending',JSON.stringify(pending));
 const job=(async()=>{try{const result=await post(pending.body,pending.actor);if(typeof result.id!=='string')throw new Error('Invalid investigation response; resume the submitted request.');store.setItem(key,result.id);store.removeItem(key+':pending');return result}catch(error){const status=(error as {status?:number}).status;if(status&&status>=400&&status<500&&status!==408&&status!==429)store.removeItem(key+':pending');throw error}finally{submissions.delete(key)}})();
 submissions.set(key,job);return job;
}
