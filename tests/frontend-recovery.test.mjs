import test from 'node:test';
import assert from 'node:assert/strict';
import {resilientStore,readJson,restoreWorkspace,submitInvestigation,pendingInvestigation} from '../frontend/recovery.ts';
const store=()=>{const data=new Map();return {getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)}};
const input={run_id:'run-1',area_id:'branch-03',sequence:3,initial_check:'REQUEST_TOPOLOGY_CHECK'};

test('lost response retries the original request and actor after reopening',async()=>{
 const s=store();const seen=[];const jobs=new Map();
 const post=async(body,actor)=>{seen.push({body:{...body},actor});if(!jobs.has(body.idempotency_key))jobs.set(body.idempotency_key,{id:'investigation-1'});if(seen.length===1)throw new Error('Response lost after server accepted request');return jobs.get(body.idempotency_key)};
 await assert.rejects(submitInvestigation(s,'lost-response',input,'reviewer',post,()=> 'stable-key'));
 assert.ok(pendingInvestigation(s,'lost-response'));
 const result=await submitInvestigation(s,'lost-response',{...input,initial_check:undefined},'analyst',post,()=> 'must-not-be-used');
 assert.equal(jobs.size,1);assert.equal(result.id,'investigation-1');assert.deepEqual(seen[0],seen[1]);
 assert.equal(s.getItem('lost-response'),'investigation-1');assert.equal(pendingInvestigation(s,'lost-response'),null);
});

test('rapid submissions share one in-flight request',async()=>{
 const s=store();let release;let calls=0;
 const post=()=>{calls++;return new Promise(resolve=>release=resolve)};
 const first=submitInvestigation(s,'double-click',input,'analyst',post,()=> 'one-key');
 const second=submitInvestigation(s,'double-click',input,'analyst',post,()=> 'another-key');
 assert.equal(first,second);assert.equal(calls,1);release({id:'inv-shared'});await first;
});

test('definitive validation failure allows editing a fresh request',async()=>{
 const s=store();await assert.rejects(submitInvestigation(s,'bad-input',input,'analyst',async()=>{throw Object.assign(new Error('Invalid input'),{status:400})},()=> 'invalid-key'));
 assert.equal(pendingInvestigation(s,'bad-input'),null);
});

test('transient HTTP failure preserves the resumable key',async()=>{
 const s=store();await assert.rejects(submitInvestigation(s,'rate-limit',input,'analyst',async()=>{throw Object.assign(new Error('Retry later'),{status:429})},()=> 'retained-key'));
 assert.equal(pendingInvestigation(s,'rate-limit').body.idempotency_key,'retained-key');
});

test('a pending request for another interval is never reused',async()=>{
 const s=store();s.setItem('binding:pending',JSON.stringify({body:{...input,sequence:2,idempotency_key:'old'},actor:'reviewer'}));
 let request;await submitInvestigation(s,'binding',input,'analyst',async body=>{request=body;return {id:'new-inv'}},()=> 'new-key');
 assert.equal(request.idempotency_key,'new-key');assert.equal(request.sequence,3);
});

test('case restoration uses the case frozen interval instead of a stale saved run',()=>{
 const runs=[{id:'case-run'},{id:'other-run'}];const cases=[{id:'case-1',run_id:'case-run',boundary_asset_id:'branch-03',analysis_sequence:3}];
 const restored=restoreWorkspace({runId:'other-run',assetId:'household-01',sequence:900,screen:'inspection',caseId:'case-1',actor:'reviewer'},runs,cases);
 assert.equal(restored.runId,'case-run');assert.equal(restored.sequence,3);assert.equal(restored.assetId,'branch-03');assert.equal(restored.actor,'reviewer');
});

test('missing cases and malformed recovery data fall back safely',()=>{
 const runs=[{id:'run-1'}];assert.equal(restoreWorkspace(null,runs,[]),null);assert.equal(restoreWorkspace({runId:'missing'},runs,[]),null);
 const restored=restoreWorkspace({runId:'run-1',screen:'inspection',caseId:'removed',sequence:-1,actor:'invented',analysis:{area:'branch-03',sequence:99999}},runs,[]);
 assert.equal(restored.screen,'network');assert.equal(restored.caseId,null);assert.equal(restored.sequence,null);assert.equal(restored.analysis,null);assert.equal(restored.actor,'analyst');
 const s=store();s.setItem('broken','{bad');assert.equal(readJson(s,'broken'),null);
});

test('browser storage failure retains in-session recovery without crashing',()=>{
 const s=resilientStore(()=>{throw new Error('Browser storage blocked')});s.setItem('case-note-1','Draft');assert.equal(s.getItem('case-note-1'),'Draft');assert.equal(s.getItem('case-note-2'),null);s.removeItem('case-note-1');assert.equal(s.getItem('case-note-1'),null);
});


test('API errors preserve status for safe conflict recovery',async()=>{
 const {api,ApiError}=await import('../frontend/api.ts');const original=globalThis.fetch;
 try{globalThis.fetch=async()=>new Response(JSON.stringify({detail:'Case changed'}),{status:409,headers:{'Content-Type':'application/json'}});
 await assert.rejects(api('/cases/case-1','PATCH',{expected_revision:1}),e=>e instanceof ApiError&&e.status===409&&e.message==='Case changed');
 }finally{globalThis.fetch=original}
});

test('API timeout and offline errors explain recovery without discarding drafts',async()=>{
 const {api}=await import('../frontend/api.ts');const original=globalThis.fetch;
 try{globalThis.fetch=async()=>{throw new DOMException('Timed out','TimeoutError')};await assert.rejects(api('/investigations'),/resumed without starting another job/);
 globalThis.fetch=async()=>{throw new TypeError('Failed to fetch')};await assert.rejects(api('/cases'),/local note draft is kept/);
 }finally{globalThis.fetch=original}
});
