import {Canvas,useFrame,useThree} from '@react-three/fiber';
import {OrbitControls,Html,Line} from '@react-three/drei';
import {useEffect,useMemo,useRef,useState,forwardRef,useImperativeHandle} from 'react';
import * as THREE from 'three';
import type {Asset,Snapshot,V3,Pose,Mission} from './types';
import {sampleFlight,type FlightTelemetry} from './flight';
export type SceneHandle={focus:()=>void;reset:()=>void;capture:(pose:Pose)=>Promise<string>;fly:(mission:Mission)=>Promise<void>};
type Props={snapshot:Snapshot;selected:string;onSelect:(id:string)=>void;handle:React.RefObject<SceneHandle|null>;onFps?:(v:number)=>void;reviewedIds:string[];reduced:boolean;inspection?:boolean;onFlightProgress?:(value:FlightTelemetry)=>void;onReady?:()=>void;onUnavailable?:()=>void;paused?:boolean};
const cyan='#58dce9',violet='#a294ff',amber='#ffbc44';

function Box({p,s,color,...rest}:{p:V3;s:V3;color:string;[key:string]:any}){return <mesh position={p} {...rest}><boxGeometry args={s}/><meshStandardMaterial color={color} roughness={.85}/></mesh>}
function Wire({points,r=.065,color='#a9bfc4'}:{points:V3[];r?:number;color?:string}){
 const curve=useMemo(()=>new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),[points]);
 return <mesh><tubeGeometry args={[curve,12,r,5,false]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={.28}/></mesh>
}
function House({a,onSelect}:{a:Asset;onSelect:(id:string)=>void}){
 const [x,,z]=a.position_m; const i=Number(a.id.slice(-2));
 return <group onClick={e=>{e.stopPropagation();onSelect(a.id)}}>
  <Box p={[x,.1,z]} s={[7,.2,8]} color="#405052"/>
  <Box p={[x,1.9,z]} s={[5.8,3.6,6]} color={['#718082','#536976','#92918a'][i%3]}/>
  <mesh position={[x,4.35,z]} rotation={[0,Math.PI/4,0]}><coneGeometry args={[4.9,1.8,4]}/><meshStandardMaterial color={['#344454','#35404b','#4f515a'][i%3]}/></mesh>
  <Box p={[x-.8,1.3,z-3.04]} s={[.8,2.1,.1]} color="#1d303d"/>
  {[-1.9,1.9].map(dx=><mesh key={dx} position={[x+dx,2.3,z+3.03]}><planeGeometry args={[.8,1.1]}/><meshStandardMaterial color="#f4d69a" emissive="#d5953f" emissiveIntensity={i%4===0?.35:1.3} side={THREE.DoubleSide}/></mesh>)}
  <Box p={[x+2.8,1.6,z-2]} s={[.3,.5,.18]} color="#9bc8d1"/>
  <Box p={[x,-.01,z-6]} s={[2.3,.1,6]} color="#4b555a"/>
 </group>
}
function Pole({p}:{p:V3}){const [x,,z]=p;return <group>
 <mesh position={[x,4,z]}><cylinderGeometry args={[.15,.22,8,7]}/><meshStandardMaterial color="#687275"/></mesh>
 <Box p={[x,7.7,z]} s={[2.4,.15,.2]} color="#a1acaf"/>
 {[-.85,0,.85].map(dx=><mesh key={dx} position={[x+dx,7.95,z]}><cylinderGeometry args={[.12,.12,.3,6]}/><meshStandardMaterial color="#768a95"/></mesh>)}
 <Box p={[x+.3,5.6,z]} s={[.65,1,.5]} color="#8b999d"/>
 </group>}
function Transformer({a,onSelect}:{a:Asset;onSelect:(id:string)=>void}){const [x,,z]=a.position_m;return <group onClick={e=>{e.stopPropagation();onSelect(a.id)}}>
 <Box p={[x,.15,z]} s={[6,.3,5]} color="#48535e"/>
 <Box p={[x,1.6,z]} s={[2.7,2.8,2]} color="#7a8c9d"/>
 {[-1,1].map(k=><group key={k}>{Array.from({length:7},(_,i)=><Box key={i} p={[x+k*1.55,1.5,z-.9+i*.3]} s={[.4,2.3,.12]} color="#596d83"/>)}</group>)}
 {[-.8,0,.8].map(dx=><mesh key={dx} position={[x+dx,3.4,z]}><cylinderGeometry args={[.12,.16,.8,7]}/><meshStandardMaterial color="#bfd2da"/></mesh>)}
 <Pole p={[x+2.5,0,z]}/>
 </group>}
function Scenery(){
 const trees=useMemo(()=>Array.from({length:94},(_,i)=>{const x=(Math.sin(i*217.3)*.5+.5)*124-62;const z=(Math.cos(i*89.7)*.5+.5)*128-60;return [x,z] as const}).filter(([x,z])=>Math.abs(x)>57||Math.abs(z)>46||Math.abs(z+3)<6),[]);
 return <group>
 <Box p={[0,-.7,0]} s={[144,1,145]} color="#203137"/>
 <Box p={[0,-.12,-8]} s={[138,.16,6]} color="#303c47"/>
 {[-60,0,60].map(x=><group key={x}><Box p={[x,-.12,0]} s={[5,.16,132]} color="#303d48"/>{Array.from({length:15},(_,i)=><Box key={i} p={[x,-.015,-61+i*8]} s={[.12,.02,3]} color="#7f8a88"/>)}</group>)}
 {[-33,17,54].map(z=><group key={z}><Box p={[0,-.12,z]} s={[126,.15,4]} color="#33404a"/>{Array.from({length:18},(_,i)=><Box key={i} p={[-61+i*7,-.02,z]} s={[3,.02,.12]} color="#687574"/>)}</group>)}
 {trees.map(([x,z],i)=><group position={[x,0,z]} key={i}><mesh position={[0,1.4,0]}><cylinderGeometry args={[.2,.27,2.8,5]}/><meshStandardMaterial color="#424a40"/></mesh><mesh position={[0,3.6,0]}><icosahedronGeometry args={[2+i%3*.3,1]}/><meshStandardMaterial color={i%2?'#304941':'#3d5549'}/></mesh></group>)}
 {[-55,55].map(x=>[-33,17].map(z=><group key={x+':'+z}><Pole p={[x,0,z]}/><mesh position={[x,7.9,z]}><sphereGeometry args={[.3,8,6]}/><meshStandardMaterial color="#fed39b" emissive="#ffbf67" emissiveIntensity={2}/></mesh></group>))}
 </group>
}
function Drone({active,reduced}:{active:boolean;reduced:boolean}){
 const rotors=useRef<(THREE.Group|null)[]>([]);
 useFrame((_,delta)=>{if(active&&!reduced)rotors.current.forEach((r,i)=>{if(r)r.rotation.y+=delta*(i%2?40:-40)})});
 return <group scale={1.7}>
  <Box p={[0,0,0]} s={[1.25,.42,1.6]} color="#d4e5ef"/>
  <Box p={[0,.25,0]} s={[.8,.16,1.1]} color="#1c3445"/>
  {[-1,1].map(k=><Box key={k} p={[0,0,0]} s={[4.4,.18,.22]} rotation={[0,k*Math.PI/4,0]} color="#344f62"/>)}
  {[-1,1].flatMap((x,i)=>[-1,1].map((z,j)=><group key={x+':'+z} position={[x*1.55,.2,z*1.55]}>
   <mesh><cylinderGeometry args={[.22,.24,.3,12]}/><meshStandardMaterial color="#182b39"/></mesh>
   <group ref={r=>{rotors.current[i*2+j]=r}}><Box p={[0,.2,0]} s={[1.8,.04,.13]} color="#a8d8e6"/><Box p={[0,.2,0]} s={[.13,.04,1.8]} color="#a8d8e6"/></group>
   <mesh rotation={[-Math.PI/2,0,0]} position={[0,.16,0]}><ringGeometry args={[.85,.91,24]}/><meshBasicMaterial color={cyan} transparent opacity={active?.45:.18} side={THREE.DoubleSide}/></mesh>
   <mesh position={[0,0,0]}><sphereGeometry args={[.12,8,8]}/><meshBasicMaterial color={x===1?'#54ffd0':'#ff876b'}/></mesh>
  </group>))}
  <mesh position={[0,-.48,.45]}><sphereGeometry args={[.3,12,12]}/><meshStandardMaterial color="#182e3c"/></mesh>
  <mesh position={[0,-.48,.7]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.16,.16,.12,12]}/><meshStandardMaterial color={cyan} emissive={cyan} emissiveIntensity={.7}/></mesh>
  {[-.7,.7].map(x=><Box key={x} p={[x,-.55,0]} s={[.08,.5,1.6]} color="#7895a5"/>)}
 </group>
}
const World=forwardRef<SceneHandle,Omit<Props,'handle'>>(function World({snapshot,selected,onSelect,onFps,reviewedIds,reduced,inspection,onFlightProgress,onReady,onUnavailable},ref){
 const {gl,scene,camera}=useThree(); const controls=useRef<any>(null);const overlay=useRef<THREE.Group>(null);const drone=useRef<THREE.Group>(null);const [mission,setMission]=useState<Mission|null>(null);
 const flight=useRef<{start:number;resolve:()=>void;reject:(error:Error)=>void;mission:Mission;timer:ReturnType<typeof setTimeout>;lastUpdate:number}|null>(null); const fps=useRef({t:0,n:0});
 const [flightActive,setFlightActive]=useState(false);const [routeComplete,setRouteComplete]=useState(false);
 const asset=snapshot.assets.find(a=>a.id===selected)!;const targetBranch=asset.kind==='household'?asset.parent_id!:selected;
 const status=snapshot.balances.find(b=>b.boundary_asset_id===targetBranch);const anomalous=snapshot.alerts.filter(a=>a.status==='active').map(a=>a.boundary_asset_id);
 const selectedColor=anomalous.includes(targetBranch)?amber:violet;
 useFrame((_,delta)=>{
   fps.current.n++;fps.current.t+=delta;if(fps.current.t>2){onFps?.(Math.round(fps.current.n/fps.current.t));fps.current={n:0,t:0}}
   if(flight.current&&drone.current){
    const f=flight.current,now=performance.now(),sample=sampleFlight(f.mission.waypoints_m,now-f.start,reduced);
    drone.current.position.set(...sample.position);
    if(!reduced){camera.position.lerp(new THREE.Vector3(...sample.position).add(new THREE.Vector3(18,13,22)),Math.min(1,delta*3));controls.current?.target.lerp(new THREE.Vector3(...sample.position),Math.min(1,delta*4));controls.current?.update()}
    if(now-f.lastUpdate>250||sample.progress===1){onFlightProgress?.(sample);f.lastUpdate=now}
    if(sample.progress===1){clearTimeout(f.timer);flight.current=null;setFlightActive(false);setRouteComplete(true);f.resolve()}
   }
 });
 useEffect(()=>{const abort=()=>{const f=flight.current;if(f){clearTimeout(f.timer);flight.current=null;f.reject(new Error('The flight view was interrupted. Retry the inspection to capture evidence.'))}};const lost=()=>{setFlightActive(false);onUnavailable?.();abort()};const restored=()=>onReady?.();gl.domElement.addEventListener('webglcontextlost',lost);gl.domElement.addEventListener('webglcontextrestored',restored);return()=>{gl.domElement.removeEventListener('webglcontextlost',lost);gl.domElement.removeEventListener('webglcontextrestored',restored);abort()}},[gl]);
 useEffect(()=>{if(inspection&&!flight.current){const p=new THREE.Vector3(...asset.position_m);camera.position.copy(p.clone().add(new THREE.Vector3(44,35,54)));controls.current?.target.copy(p.clone().add(new THREE.Vector3(0,5,10)));controls.current?.update()}},[inspection,asset.id,camera]);
 useImperativeHandle(ref,()=>({
  focus(){const p=new THREE.Vector3(...asset.position_m);camera.position.copy(p.clone().add(new THREE.Vector3(32,30,40)));controls.current.target.copy(p);controls.current.update()},
  reset(){camera.position.set(100,95,120);controls.current.target.set(0,0,0);controls.current.update()},
  fly(m){
   if(flight.current)return Promise.reject(new Error('A drone flight is already active.'));
   const initial=sampleFlight(m.waypoints_m,0);onFlightProgress?.(initial);setMission(m);setFlightActive(true);setRouteComplete(false);
   const center=new THREE.Vector3();m.waypoints_m.forEach(p=>center.add(new THREE.Vector3(...p)));center.divideScalar(m.waypoints_m.length);
   camera.position.copy(center.clone().add(new THREE.Vector3(reduced?45:20,reduced?35:16,reduced?52:26)));controls.current?.target.copy(center);controls.current?.update();
   return new Promise<void>((resolve,reject)=>{const timer=setTimeout(()=>{if(flight.current){flight.current=null;setFlightActive(false);reject(new Error('The flight view stopped updating. Keep the tab visible and retry the inspection.'))}},30000);flight.current={start:performance.now(),resolve,reject,mission:m,timer,lastUpdate:0}})
  },
  async capture(pose){
   if(gl.getContext().isContextLost())throw new Error('WebGL is unavailable. Reload the scene before retrying capture.');
   const view=new THREE.PerspectiveCamera(pose.fov,640/480,.1,500);view.position.set(...pose.position);view.lookAt(new THREE.Vector3(...pose.target));view.updateMatrixWorld();
   const renderTarget=new THREE.WebGLRenderTarget(640,480);renderTarget.texture.colorSpace=THREE.SRGBColorSpace;
   const prior=gl.getRenderTarget();const priorBackground=scene.background;const visible=overlay.current?.visible;
   try{
    if(overlay.current)overlay.current.visible=false;
    gl.setRenderTarget(renderTarget);gl.render(scene,view);
    const pixels=new Uint8Array(640*480*4);gl.readRenderTargetPixels(renderTarget,0,0,640,480,pixels);
    const canvas=document.createElement('canvas');canvas.width=640;canvas.height=480;const ctx=canvas.getContext('2d')!;const out=ctx.createImageData(640,480);
    for(let y=0;y<480;y++)out.data.set(pixels.subarray((479-y)*640*4,(480-y)*640*4),y*640*4);
    ctx.putImageData(out,0,0);return canvas.toDataURL('image/png').split(',')[1];
   }finally{gl.setRenderTarget(prior);scene.background=priorBackground;if(overlay.current)overlay.current.visible=visible??true;renderTarget.dispose()}
  }
 }),[asset,gl,scene,camera,reduced,onFlightProgress]);
 return <>
  <color attach="background" args={['#0b1623']}/><fog attach="fog" args={['#0b1623',140,320]}/>
  <ambientLight intensity={1.3}/><directionalLight position={[10,55,40]} intensity={2.3} color="#c5d9ff"/><directionalLight position={[-20,25,-30]} intensity={1.2} color="#5c97cc"/>
  <Scenery/>
  {snapshot.assets.filter(a=>a.kind==='household').map(a=><House a={a} key={a.id} onSelect={onSelect}/>)}
  {snapshot.assets.filter(a=>a.kind==='transformer').map(a=><Transformer a={a} key={a.id} onSelect={onSelect}/>)}
  {snapshot.assets.filter(a=>a.kind==='branch'||a.kind==='feeder').map(a=><group key={a.id} onClick={e=>{e.stopPropagation();onSelect(a.id)}}><Pole p={a.position_m}/><mesh position={a.position_m}><sphereGeometry args={[.65,12,8]}/><meshStandardMaterial color="#a7b7c7"/></mesh></group>)}
  {snapshot.connections.map(c=><Wire key={c.id} points={c.geometry_points_m}/>)}
  {snapshot.physical_connections_m.map((p,i)=><Wire key={'extra'+i} points={p}/>)}
  {snapshot.physical_occluders?.map((o,i)=><Box key={'occluder'+i} p={o.position_m} s={o.size_m} color="#40555e"/>)}
  <group ref={overlay}>
   {snapshot.connections.map(c=>{
    const problem=anomalous.includes(c.from_asset_id)||anomalous.includes(c.to_asset_id);const active=c.from_asset_id===targetBranch||c.to_asset_id===targetBranch;
    return <Line key={c.id} points={c.geometry_points_m} color={problem?amber:active?violet:cyan} lineWidth={problem||active?2.6:1.1} transparent opacity={(problem || active) ? .9 : .4}/>
   })}
   <mesh position={[asset.position_m[0],.1,asset.position_m[2]]} rotation={[-Math.PI/2,0,0]}><ringGeometry args={[3,3.3,40]}/><meshBasicMaterial color={selectedColor} transparent opacity={.8}/></mesh>
   {!inspection&&<Html position={[asset.position_m[0],asset.kind==='household'?7:11,asset.position_m[2]]} center distanceFactor={110} zIndexRange={[5,0]}><button className="scene-label" style={{borderColor:selectedColor}} onClick={()=>onSelect(asset.id)}><span style={{color:selectedColor}}>◇</span> <strong>{asset.label}</strong><small>{status?.validity==='data_incomplete'?'⚠ Data incomplete':reviewedIds.includes(targetBranch)?'◉ Under review':anomalous.includes(targetBranch)?'△ Unexplained loss':'✓ Within threshold'}</small></button></Html>}
   {!inspection&&snapshot.assets.filter(a=>a.kind==='feeder'&&a.id!==selected).map(a=><Html position={[a.position_m[0],12,a.position_m[2]]} key={a.id} center distanceFactor={140} zIndexRange={[5,0]}><button className="scene-label feeder" onClick={()=>onSelect(a.id)}>{a.label}</button></Html>)}
   {mission&&<><Line points={mission.waypoints_m} color={cyan} lineWidth={2} dashed dashSize={1} gapSize={.7}/>{mission.waypoints_m.map((p,i)=><group key={i} position={p}><mesh rotation={[-Math.PI/2,0,0]}><ringGeometry args={[1.6,1.8,32]}/><meshBasicMaterial color={cyan} transparent opacity={.65} side={THREE.DoubleSide}/></mesh></group>)}<group ref={drone} position={mission.waypoints_m[0]}><Drone active={flightActive} reduced={reduced}/><Html position={[0,4,0]} center zIndexRange={[6,0]}><div className="drone-caption"><span/>GT–01 <small>{flightActive?'IN FLIGHT':routeComplete?'ROUTE COMPLETE':'FLIGHT INTERRUPTED'}</small></div></Html><mesh rotation={[Math.PI,0,0]} position={[0,-4,0]}><coneGeometry args={[3,7,24,1,true]}/><meshBasicMaterial color={cyan} wireframe transparent opacity={.12}/></mesh></group></>}
  </group>
  <OrbitControls ref={controls} makeDefault enabled={!flightActive} maxPolarAngle={Math.PI*.47} minDistance={10} maxDistance={240} enableDamping dampingFactor={.12}/>
 </>
});
export default function Scene({handle,onReady,paused,...props}:Props){return <Canvas frameloop={paused?'never':'always'} onCreated={()=>onReady?.()} camera={{position:[100,95,120],fov:43,near:.1,far:500}} dpr={[1,1.5]} gl={{antialias:true,powerPreference:'high-performance'}}><World ref={handle} {...props} onReady={onReady}/></Canvas>}
