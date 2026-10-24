export async function api<T=any>(path:string,method='GET',body?:unknown,actor='analyst'):Promise<T>{
 let response:Response;
 try{response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json','X-Actor':actor},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(20000)})}
 catch(e){if((e as Error).name==='TimeoutError')throw new Error('The local API timed out after 20 seconds. Retry, or continue without visual evidence.');throw e}
 if(!response.ok){let text='Request failed';try{const data=await response.json();text=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail);}catch{}throw new Error(text)}
 return response.json();
}
export const date=(value:string,short=false)=>new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',...(short?{hour:'2-digit',minute:'2-digit'}:{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'}),hour12:false}).format(new Date(value));
export const n=(v:number|null|undefined,d=3)=>v==null?'—':v.toFixed(d);
export const words=(s:string)=>s.replaceAll('_',' ');
