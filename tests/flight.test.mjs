import test from 'node:test';
import assert from 'node:assert/strict';
import {sampleFlight,FLIGHT_DURATION_MS} from '../frontend/flight.ts';

const route=[[20,12,26],[-20,12,26],[10,14,30]];
test('flight visits the approved path and ends at the final waypoint',()=>{
 assert.deepEqual(sampleFlight(route,0).position,route[0]);
 assert.deepEqual(sampleFlight(route,FLIGHT_DURATION_MS/2).position,route[1]);
 assert.deepEqual(sampleFlight(route,FLIGHT_DURATION_MS).position,route[2]);
 assert.deepEqual(sampleFlight(route,FLIGHT_DURATION_MS/4).position,[0,12,26]);
 assert.equal(sampleFlight(route,99999).progress,1);
 assert.equal(sampleFlight(route,-10).progress,0);
});
test('reduced motion advances discretely and still reaches the capture position',()=>{
 assert.deepEqual(sampleFlight(route,5000,true).position,route[0]);
 assert.deepEqual(sampleFlight(route,10000,true).position,route[1]);
 assert.deepEqual(sampleFlight(route,15000,true).position,route[2]);
});
test('an invalid route cannot start a misleading inspection animation',()=>{
 assert.throws(()=>sampleFlight([],0));
 assert.throws(()=>sampleFlight([[0,0,0],[NaN,0,0]],0));
});
