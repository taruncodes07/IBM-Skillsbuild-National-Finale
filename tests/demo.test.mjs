import test from 'node:test';
import assert from 'node:assert/strict';
import {loadDemo} from '../frontend/demo.ts';

test('each demo creates the matching real scenario and steps with current revisions',async()=>{
 for(const [preset,scenario] of [[1,'clean'],[2,'missing_telemetry'],[3,'visible_unmetered_load']]){
  const requests=[];
  const snapshot=await loadDemo(preset,async(path,method,body)=>{
   requests.push({path,method,body});
   if(requests.length===1){assert.equal(body.scenario,scenario);assert.equal(body.coverage_profile,'full_sectional');}
   else{assert.equal(body.command,'step');assert.equal(body.expected_revision,requests.length-1);assert.equal(path,'/runs/demo/control');}
   return {run:{id:'demo',revision:requests.length,playing:false},seq:requests.length-1};
  });
  assert.equal(snapshot.seq,3);assert.equal(snapshot.run.playing,false);assert.equal(requests.length,4);
 }
});

test('a failed scenario never reports a completed demo',async()=>{
 let calls=0;
 await assert.rejects(loadDemo(3,async()=>{if(++calls===3)throw new Error('API unavailable');return {run:{id:'demo',revision:calls}};}),/API unavailable/);
 assert.equal(calls,3);
 await assert.rejects(loadDemo(99,async()=>assert.fail('invalid preset made a request')),/Choose a demo/);
});
