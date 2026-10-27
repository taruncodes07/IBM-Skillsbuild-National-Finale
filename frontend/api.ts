export class ApiError extends Error{status:number;constructor(message:string,status:number){super(message);this.name='ApiError';this.status=status}}
export async function api<T=any>(path:string,method='GET',body?:unknown,actor='analyst'):Promise<T>{
 let response:Response;
 try{response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json','X-Actor':actor},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(20000)})}
 catch(e){if((e as Error).name==='TimeoutError')throw new Error('The local API timed out after 20 seconds. Retry the request. Submitted investigations can be resumed without starting another job.');if(e instanceof TypeError)throw new Error('Cannot reach the local VidyutDrishti server. Keep this tab open, restart the server, and retry. Your local note draft is kept.');throw e}
 if(!response.ok){let text='Request failed';try{const data=await response.json();text=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail);}catch{}throw new ApiError(text,response.status)}
 return response.json();
}
export const date=(value:string,short=false)=>new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',...(short?{hour:'2-digit',minute:'2-digit'}:{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}),hour12:false}).format(new Date(value));
export const n=(v:number|null|undefined,d=3)=>v==null?'—':v.toFixed(d);
export const words=(s:string)=>s.replaceAll('_',' ');
export const pct=(v:number|null|undefined)=>v==null?'—':(v*100).toFixed(1)+'%';
export const pretty=(s:string)=>words(s).replace(/^./,c=>c.toUpperCase());
