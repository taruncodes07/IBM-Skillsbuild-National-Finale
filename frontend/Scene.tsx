import {Canvas,useFrame,useThree} from '@react-three/fiber';
import {OrbitControls,Html,Line} from '@react-three/drei';
import {useEffect,useMemo,useRef,useState,forwardRef,useImperativeHandle} from 'react';
import * as THREE from 'three';
import type {Asset,Snapshot,V3,Pose,Mission} from './types';
import {sampleFlight,type FlightTelemetry} from './flight';
export type SceneHandle={focus:()=>void;reset:()=>void;capture:(pose:Pose)=>Promise<string>;fly:(mission:Mission)=>Promise<void>};
type Props={snapshot:Snapshot;selected:string;onSelect:(id:string)=>void;handle:React.RefObject<SceneHandle|null>;onFps?:(v:number)=>void;reviewedIds:string[];reduced:boolean;inspection?:boolean;onFlightProgress?:(value:FlightTelemetry)=>void;onReady?:()=>void;onUnavailable?:()=>void;paused?:boolean};
const blue='#3b82f6',royalBlue='#2563eb',amber='#f59e0b',slate='#475569';

function Box({p,s,color,...rest}:{p:V3;s:V3;color:string;[key:string]:any}){return <mesh position={p} {...rest}><boxGeometry args={s}/><meshStandardMaterial color={color} roughness={.85}/></mesh>}
function Wire({points,r=.065,color='#a9bfc4'}:{points:V3[];r?:number;color?:string}){
 const curve=useMemo(()=>new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p))),[points]);
 return <mesh><tubeGeometry args={[curve,12,r,5,false]}/><meshStandardMaterial color={color} emissive={color} emissiveIntensity={.28}/></mesh>
}
function House({a,onSelect}:{a:Asset;onSelect:(id:string)=>void}){
 const [x,,z]=a.position_m; const i=Number(a.id.slice(-2))||1;
 const floors=2+(i%2); const h=floors*2.7; const w=6.4+(i%3)*.5; const d=6.8+((i*2)%3)*.6;
 const wallCol=['#222a33','#29333e','#322e2a','#252d37','#2e353e'][i%5];
 const trimCol=['#182029','#1f2732','#25201c'][i%3];
 const tankCol=i%3===0?'#172554':'#0f172a';
 const rotY=((i*19)%7-3)*.018;
 return <group position={[x,0,z]} rotation={[0,rotY,0]} onClick={e=>{e.stopPropagation();onSelect(a.id)}}>
  <Box p={[0,.2,0]} s={[w+.4,.4,d+.4]} color="#1a222c"/>
  <Box p={[0,h/2+.4,0]} s={[w,h,d]} color={wallCol}/>
  {Array.from({length:floors}).map((_,fl)=><group key={fl}>
   <Box p={[0,(fl+1)*2.7+.35,d/2+.22]} s={[w+.2,.1,.65]} color={trimCol}/>
   {[-w*.26,w*.26].map((wx,wi)=><group key={wi} position={[wx,fl*2.7+1.5,d/2+.02]}>
    <mesh><planeGeometry args={[1.05,1.15]}/><meshStandardMaterial color="#fef08a" emissive="#ca8a04" emissiveIntensity={(i+fl+wi)%3===0?.25:1.1} side={THREE.DoubleSide}/></mesh>
    <Box p={[0,0,.03]} s={[1.12,.05,.04]} color="#0b111a"/>
    <Box p={[0,0,.03]} s={[.05,1.2,.04]} color="#0b111a"/>
   </group>)}
  </group>)}
  {i%2===0?<group position={[0,1.25,d/2+.03]}>
   <Box p={[0,0,0]} s={[2.3,2.1,.08]} color="#2d3748"/>
   {Array.from({length:5}).map((_,si)=><Box key={si} p={[0,-.8+si*.36,.05]} s={[2.2,.05,.03]} color="#1a202c"/>)}
   <Box p={[0,1.18,.08]} s={[2.5,.35,.12]} color="#0f172a"/>
  </group>:<group position={[-w*.2,1.2,d/2+.03]}>
   <Box p={[0,0,0]} s={[1.2,2.1,.08]} color="#17202a"/>
   <Box p={[0,1.15,.08]} s={[1.4,.14,.25]} color="#222c36"/>
  </group>}
  <group position={[w*.35,1.5,d/2+.06]}>
   <Box p={[0,0,0]} s={[.42,.58,.2]} color="#1e293b"/>
   <mesh position={[0,.08,.11]}><planeGeometry args={[.24,.14]}/><meshStandardMaterial color="#0284c7" emissive="#0284c7" emissiveIntensity={.8}/></mesh>
   <mesh position={[.1,-.14,.11]}><sphereGeometry args={[.03,8,8]}/><meshBasicMaterial color="#22c55e"/></mesh>
   <mesh position={[0,(h-1.5)/2,.05]}><cylinderGeometry args={[.02,.02,h-1.5,6]}/><meshStandardMaterial color="#475569"/></mesh>
  </group>
  <group position={[0,h-1.1,d/2+.4]}>
   <Box p={[0,0,0]} s={[w*.6,.14,.8]} color="#1a222c"/>
   <Box p={[0,.42,.38]} s={[w*.6,.05,.05]} color="#475569"/>
   {[-w*.26,-w*.09,w*.09,w*.26].map((rx,ri)=><Box key={ri} p={[rx,.21,.38]} s={[.04,.42,.04]} color="#334155"/>)}
  </group>
  <group position={[0,h+.4,0]}>
   <Box p={[0,.08,0]} s={[w+.2,.16,d+.2]} color="#17202a"/>
   <Box p={[0,.42,d/2+.04]} s={[w+.2,.68,.14]} color={wallCol}/>
   <Box p={[0,.42,-d/2-.04]} s={[w+.2,.68,.14]} color={wallCol}/>
   <Box p={[-w/2-.04,.42,0]} s={[.14,.68,d]} color={wallCol}/>
   <Box p={[w/2+.04,.42,0]} s={[.14,.68,d]} color={wallCol}/>
   <group position={[-w*.28,1.05,-d*.25]}>
    <Box p={[0,0,0]} s={[2.1,1.9,2.2]} color={wallCol}/>
    <Box p={[0,1.02,0]} s={[2.3,.12,2.4]} color="#17202a"/>
    <Box p={[0,-.1,1.11]} s={[.75,1.55,.05]} color="#0c1219"/>
   </group>
   <group position={[w*.26,0,d*.2]}>
    <Box p={[0,.32,0]} s={[1.3,.64,1.3]} color="#1a222c"/>
    <mesh position={[0,1.25,0]}><cylinderGeometry args={[.52,.52,1.2,16]}/><meshStandardMaterial color={tankCol} roughness={.5}/></mesh>
    <mesh position={[0,1.92,0]}><cylinderGeometry args={[.28,.3,.12,16]}/><meshStandardMaterial color={tankCol}/></mesh>
   </group>
   {i%2===0?<group position={[w*.36,.65,-d*.3]}>
    <mesh position={[0,.28,0]} rotation={[.4,.5,0]}><cylinderGeometry args={[.03,.03,.65,6]}/><meshStandardMaterial color="#64748b"/></mesh>
    <mesh position={[.12,.6,-.08]} rotation={[.6,.5,0]}><coneGeometry args={[.42,.12,16,1,true]}/><meshStandardMaterial color="#94a3b8" side={THREE.DoubleSide}/></mesh>
   </group>:<group position={[-w*.08,.45,d*.28]}>
    <Box p={[0,.35,-.7]} s={[.05,.7,.05]} color="#475569"/><Box p={[0,.35,.7]} s={[.05,.7,.05]} color="#475569"/><Box p={[0,.68,0]} s={[.02,.02,1.4]} color="#94a3b8"/>
   </group>}
  </group>
 </group>;
}
function AutoRickshaw({p,rotY=0}:{p:V3;rotY?:number}){
 const [x,y,z]=p;
 return <group position={[x,y+.05,z]} rotation={[0,rotY,0]}>
  <Box p={[0,.42,0]} s={[1.25,.45,2.1]} color="#0f172a"/>
  <mesh position={[0,.28,.8]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.24,.24,.15,12]}/><meshStandardMaterial color="#05080e"/></mesh>
  {[-.6,.6].map(dx=><mesh key={dx} position={[dx,.28,-.6]} rotation={[0,0,Math.PI/2]}><cylinderGeometry args={[.25,.25,.16,12]}/><meshStandardMaterial color="#05080e"/></mesh>)}
  <Box p={[0,.85,-.08]} s={[1.28,.6,1.9]} color="#14532d"/>
  <Box p={[0,1.4,-.18]} s={[1.24,.52,1.6]} color="#ca8a04"/>
  <mesh position={[0,1.2,.64]} rotation={[-.32,0,0]}><planeGeometry args={[1.05,.6]}/><meshStandardMaterial color="#38bdf8" transparent opacity={.65} side={THREE.DoubleSide}/></mesh>
  <mesh position={[0,.6,.92]}><sphereGeometry args={[.09,8,8]}/><meshBasicMaterial color="#fef08a"/></mesh>
 </group>;
}
function InfillBuilding({p,w,h,d,rotY=0,color,seed=1}:{p:V3;w:number;h:number;d:number;rotY?:number;color:string;seed?:number}){
 const [x,y,z]=p; const tankCol=seed%2===0?'#172554':'#0f172a';
 return <group position={[x,y,z]} rotation={[0,rotY,0]}>
  <Box p={[0,.2,0]} s={[w+.3,.4,d+.3]} color="#161e27"/>
  <Box p={[0,h/2+.4,0]} s={[w,h,d]} color={color}/>
  {Array.from({length:Math.floor(h/2.7)}).map((_,fl)=><group key={fl}>
   <Box p={[0,(fl+1)*2.7+.35,d/2+.16]} s={[w+.15,.09,.5]} color="#161e26"/>
   {[-w*.25,w*.25].map((wx,wi)=><mesh key={wi} position={[wx,fl*2.7+1.5,d/2+.02]}><planeGeometry args={[.9,1.05]}/><meshStandardMaterial color="#fef08a" emissive="#ca8a04" emissiveIntensity={(seed+fl+wi)%4===0?.2:1} side={THREE.DoubleSide}/></mesh>)}
  </group>)}
  <group position={[0,h+.4,0]}>
   <Box p={[0,.06,0]} s={[w+.15,.12,d+.15]} color="#141c24"/>
   <Box p={[0,.38,d/2+.03]} s={[w+.15,.64,.12]} color={color}/>
   <Box p={[0,.38,-d/2-.03]} s={[w+.15,.64,.12]} color={color}/>
   <Box p={[-w/2-.03,.38,0]} s={[.12,.64,d]} color={color}/>
   <Box p={[w/2+.03,.38,0]} s={[.12,.64,d]} color={color}/>
   <group position={[-w*.25,.95,-d*.22]}>
    <Box p={[0,0,0]} s={[1.9,1.7,2]} color={color}/>
    <Box p={[0,.9,0]} s={[2.1,.1,2.2]} color="#141c24"/>
   </group>
   <group position={[w*.24,0,d*.18]}>
    <Box p={[0,.28,0]} s={[1.2,.56,1.2]} color="#172029"/>
    <mesh position={[0,1.1,0]}><cylinderGeometry args={[.48,.48,1.1,14]}/><meshStandardMaterial color={tankCol} roughness={.5}/></mesh>
   </group>
  </group>
 </group>;
}
function Pole({p}:{p:V3}){const [x,,z]=p;return <group>
 <mesh position={[x,4,z]}><cylinderGeometry args={[.14,.2,8,7]}/><meshStandardMaterial color="#505a62"/></mesh>
 <Box p={[x,7.7,z]} s={[2.8,.14,.18]} color="#7a878c"/>
 {[-1.1,-.35,.35,1.1].map(dx=><mesh key={dx} position={[x+dx,7.95,z]}><cylinderGeometry args={[.1,.1,.3,6]}/><meshStandardMaterial color="#889da8"/></mesh>)}
 <Box p={[x+.28,5.4,z]} s={[.6,1.1,.45]} color="#64748b"/>
 <mesh position={[x-.15,6.2,z+.1]} rotation={[0,0,.3]}><torusGeometry args={[.32,.04,6,12]}/><meshStandardMaterial color="#1e293b"/></mesh>
 <group position={[x-.65,7.3,z]}>
  <Box p={[0,0,0]} s={[1.2,.07,.07]} rotation={[0,0,-.2]} color="#475569"/>
  <mesh position={[-.55,-.12,0]}><cylinderGeometry args={[.16,.22,.12,8]}/><meshStandardMaterial color="#cbd5e1" emissive="#fef08a" emissiveIntensity={.6}/></mesh>
  <mesh position={[-.55,-.2,0]}><sphereGeometry args={[.08,8,8]}/><meshBasicMaterial color="#fef08a"/></mesh>
 </group>
</group>}
function Transformer({a,onSelect}:{a:Asset;onSelect:(id:string)=>void}){const [x,,z]=a.position_m;return <group onClick={e=>{e.stopPropagation();onSelect(a.id)}}>
 <Box p={[x,.15,z]} s={[6.4,.3,5.4]} color="#36404b"/>
 <Box p={[x,1.6,z]} s={[2.7,2.8,2]} color="#64748b"/>
 {[-1,1].map(k=><group key={k}>{Array.from({length:7},(_,i)=><Box key={i} p={[x+k*1.55,1.5,z-.9+i*.3]} s={[.4,2.3,.12]} color="#475569"/>)}</group>)}
 {[-.8,0,.8].map(dx=><mesh key={dx} position={[x+dx,3.4,z]}><cylinderGeometry args={[.12,.16,.8,7]}/><meshStandardMaterial color="#94a3b8"/></mesh>)}
 <Box p={[x,1.4,z-2.4]} s={[1.8,1.2,.06]} color="#dc2626"/>
 <Box p={[x,1.4,z-2.38]} s={[1.6,1,.06]} color="#fef08a"/>
 <Pole p={[x+2.5,0,z]}/>
</group>}
function Scenery(){
 const infill=useMemo(()=>{
  const list:{p:V3;w:number;h:number;d:number;rotY:number;color:string;seed:number}[]=[];
  const cols=['#1e2630','#262e38','#2e2a26','#222b35','#2a313b','#1c232d','#2b333e'];
  // Clustered dense infill along Indian urban layout
  const blocks=[
   {x:-46,z:-38,nx:4,nz:2,w:6.2,d:7,spX:7.8,spZ:8.5},
   {x:18,z:-38,nx:4,nz:2,w:6.2,d:7,spX:7.8,spZ:8.5},
   {x:-52,z:32,nx:5,nz:2,w:6.5,d:7.2,spX:8.2,spZ:9},
   {x:14,z:32,nx:5,nz:2,w:6.5,d:7.2,spX:8.2,spZ:9},
   {x:-12,z:-42,nx:3,nz:2,w:5.8,d:6.5,spX:7.5,spZ:8},
   {x:-12,z:38,nx:3,nz:2,w:5.8,d:6.5,spX:7.5,spZ:8},
   {x:-56,z:-4,nx:2,nz:3,w:6.8,d:6.4,spX:8.5,spZ:7.8},
   {x:44,z:-4,nx:2,nz:3,w:6.8,d:6.4,spX:8.5,spZ:7.8}
  ];
  let seed=1;
  blocks.forEach(b=>{
   for(let ix=0;ix<b.nx;ix++){
    for(let iz=0;iz<b.nz;iz++){
     seed++;
     const px=b.x+ix*b.spX+((seed%5)-2)*.5;
     const pz=b.z+iz*b.spZ+((seed%7)-3)*.5;
     const h=5.4+(seed%3)*2.7; // G+1, G+2, G+3
     const w=b.w+((seed%3)-1)*.6;
     const d=b.d+((seed%4)-2)*.5;
     const rotY=((seed%11)-5)*.025; // organic slight rotation
     list.push({p:[px,0,pz],w,h,d,rotY,color:cols[seed%cols.length],seed});
    }
   }
  });
  return list;
 },[]);
 const trees=useMemo(()=>Array.from({length:55},(_,i)=>{
  const x=(Math.sin(i*217.3)*.5+.5)*130-65;const z=(Math.cos(i*89.7)*.5+.5)*132-62;
  return [x,z] as const;
 }).filter(([x,z])=>Math.abs(x)>54||Math.abs(z)>48||Math.abs(z-6)<4),[]);
 return <group>
  {/* Ground plane */}
  <Box p={[0,-.7,0]} s={[155,1,155]} color="#06090f"/>
  {/* Main asphalt street */}
  <Box p={[0,-.14,-8]} s={[148,.16,7]} color="#0b111a"/>
  {/* Roadside drainage slabs / gutters */}
  {[-11.6,-4.4].map(z=><group key={z}>{Array.from({length:24},(_,i)=><Box key={i} p={[-68+i*6,-.04,z]} s={[5.6,.08,.6]} color="#1a2432"/>)}</group>)}
  {/* Narrow cross gullies / lanes */}
  {[-60,-34,0,34,60].map(x=><group key={x}>
   <Box p={[x,-.14,0]} s={[5.4,.16,138]} color="#0c121c"/>
   {Array.from({length:18},(_,i)=><Box key={i} p={[x-.04,-.03,-60+i*7]} s={[.6,.08,5.8]} color="#1a2432"/>)}
  </group>)}
  {/* Interconnecting alleys */}
  {[-26,14,50].map(z=><Box key={z} p={[0,-.15,z]} s={[136,.14,4.6]} color="#0e1522"/>)}
  {/* Dense infill buildings */}
  {infill.map((b,i)=><InfillBuilding key={i} {...b}/>)}
  {/* Parked Indian Auto-Rickshaws */}
  <AutoRickshaw p={[-18,0,-6]} rotY={.35}/>
  <AutoRickshaw p={[12,0,-10]} rotY={-.25}/>
  <AutoRickshaw p={[-28,0,16]} rotY={1.4}/>
  <AutoRickshaw p={[24,0,18]} rotY={-1.2}/>
  {/* Foliage between buildings */}
  {trees.map(([x,z],i)=><group position={[x,0,z]} key={i}>
   <mesh position={[0,1.5,0]}><cylinderGeometry args={[.22,.3,3,6]}/><meshStandardMaterial color="#1a221e"/></mesh>
   <mesh position={[0,3.8,0]}><icosahedronGeometry args={[2.2+i%3*.4,1]}/><meshStandardMaterial color={i%2?'#13241b':'#182d22'}/></mesh>
  </group>)}
 </group>;
}
const LAUNCH_STATION_POS:V3=[0,0,-22];
function LaunchStation({p}:{p:V3}){
 const [x,y,z]=p;
 return <group position={[x,y,z]}>
  <mesh rotation={[-Math.PI/2,0,0]} position={[0,.04,0]}>
   <cylinderGeometry args={[5,5.3,.2,32]}/>
   <meshStandardMaterial color="#0c131d" roughness={.9}/>
  </mesh>
  <mesh rotation={[-Math.PI/2,0,0]} position={[0,.15,0]}>
   <ringGeometry args={[4.4,4.75,32]}/>
   <meshBasicMaterial color="#1e293b" side={THREE.DoubleSide}/>
  </mesh>
  <mesh rotation={[-Math.PI/2,0,0]} position={[0,.16,0]}>
   <ringGeometry args={[2.5,2.7,32]}/>
   <meshBasicMaterial color={royalBlue} transparent opacity={.85} side={THREE.DoubleSide}/>
  </mesh>
  <Box p={[-1.1,.17,0]} s={[.3,.02,2.4]} color={royalBlue}/>
  <Box p={[1.1,.17,0]} s={[.3,.02,2.4]} color={royalBlue}/>
  <Box p={[0,.17,0]} s={[2.2,.02,.3]} color={royalBlue}/>
  {[-3.4,3.4].flatMap(dx=>[-3.4,3.4].map(dz=><group key={`${dx}:${dz}`} position={[dx,.2,dz]}>
   <mesh position={[0,.25,0]}><cylinderGeometry args={[.14,.18,.5,8]}/><meshStandardMaterial color="#162232"/></mesh>
   <mesh position={[0,.55,0]}><sphereGeometry args={[.16,8,8]}/><meshStandardMaterial color={blue} emissive={blue} emissiveIntensity={1.5}/></mesh>
  </group>))}
  <group position={[-3.8,0,0]}>
   <Box p={[0,1.1,0]} s={[1.2,2.2,1.8]} color="#0c1420"/>
   <mesh position={[0,2.8,0]}><cylinderGeometry args={[.06,.08,1.8,8]}/><meshStandardMaterial color="#334155"/></mesh>
   <mesh position={[0,3.8,0]}><sphereGeometry args={[.18,8,8]}/><meshStandardMaterial color={amber} emissive={amber} emissiveIntensity={1.8}/></mesh>
  </group>
  <Html position={[0,2.6,0]} center distanceFactor={110} zIndexRange={[5,0]}>
   <div className="launchpad-label"><span className="live-dot"/><strong>BESCOM AERIAL BASE · DOCK-01</strong></div>
  </Html>
 </group>;
}
function Drone({active,reduced}:{active:boolean;reduced:boolean}){
 const rotors=useRef<(THREE.Group|null)[]>([]);
 useFrame((_,delta)=>{if(active&&!reduced)rotors.current.forEach((r,i)=>{if(r)r.rotation.y+=delta*(i%2?40:-40)})});
 return <group scale={1.7}>
  <Box p={[0,0,0]} s={[1.25,.42,1.6]} color="#111827"/>
  <Box p={[0,.25,0]} s={[.8,.16,1.1]} color="#1e293b"/>
  {[-1,1].map(k=><Box key={k} p={[0,0,0]} s={[4.4,.18,.22]} rotation={[0,k*Math.PI/4,0]} color="#1e293b"/>)}
  {[-1,1].flatMap((x,i)=>[-1,1].map((z,j)=><group key={x+':'+z} position={[x*1.55,.2,z*1.55]}>
   <mesh><cylinderGeometry args={[.22,.24,.3,12]}/><meshStandardMaterial color="#0b111a"/></mesh>
   <group ref={r=>{rotors.current[i*2+j]=r}}><Box p={[0,.2,0]} s={[1.8,.04,.13]} color="#475569"/><Box p={[0,.2,0]} s={[.13,.04,1.8]} color="#475569"/></group>
   <mesh rotation={[-Math.PI/2,0,0]} position={[0,.16,0]}><ringGeometry args={[.85,.91,24]}/><meshBasicMaterial color={royalBlue} transparent opacity={active?.45:.15} side={THREE.DoubleSide}/></mesh>
   <mesh position={[0,0,0]}><sphereGeometry args={[.12,8,8]}/><meshBasicMaterial color={x===1?blue:'#475569'}/></mesh>
  </group>))}
  <mesh position={[0,-.48,.45]}><sphereGeometry args={[.3,12,12]}/><meshStandardMaterial color="#080d14"/></mesh>
  <mesh position={[0,-.48,.7]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.16,.16,.12,12]}/><meshStandardMaterial color={royalBlue} emissive={royalBlue} emissiveIntensity={.6}/></mesh>
  {[-.7,.7].map(x=><Box key={x} p={[x,-.55,0]} s={[.08,.5,1.6]} color="#334155"/>)}
 </group>;
}
const World=forwardRef<SceneHandle,Omit<Props,'handle'>>(function World({snapshot,selected,onSelect,onFps,reviewedIds,reduced,inspection,onFlightProgress,onReady,onUnavailable},ref){
 const {gl,scene,camera}=useThree(); const controls=useRef<any>(null);const overlay=useRef<THREE.Group>(null);const drone=useRef<THREE.Group>(null);const [mission,setMission]=useState<Mission|null>(null);
 const flight=useRef<{start:number;resolve:()=>void;reject:(error:Error)=>void;mission:Mission;timer:ReturnType<typeof setTimeout>;lastUpdate:number;route?:V3[]}|null>(null); const fps=useRef({t:0,n:0});
 const [flightActive,setFlightActive]=useState(false);const [routeComplete,setRouteComplete]=useState(false);
 const dronePos=useRef<V3>([0,.45,-22]);
 const asset=snapshot.assets.find(a=>a.id===selected)!;const targetBranch=asset.kind==='household'?asset.parent_id!:selected;
 const status=snapshot.balances.find(b=>b.boundary_asset_id===targetBranch);const anomalous=snapshot.alerts.filter(a=>a.status==='active').map(a=>a.boundary_asset_id);
 const selectedColor=anomalous.includes(targetBranch)?amber:blue;
 useFrame((_,delta)=>{
   fps.current.n++;fps.current.t+=delta;if(fps.current.t>2){onFps?.(Math.round(fps.current.n/fps.current.t));fps.current={n:0,t:0}}
   if(flight.current&&drone.current){
    const f=flight.current,now=performance.now(),sample=sampleFlight(f.route||f.mission.waypoints_m,(now-f.start)*3,reduced);
    dronePos.current=sample.position;
    drone.current.position.set(...sample.position);
    if(!reduced){
     camera.position.lerp(new THREE.Vector3(...sample.position).add(new THREE.Vector3(16,10,18)),Math.min(1,delta*3.5));
     controls.current?.target.lerp(new THREE.Vector3(...sample.position),Math.min(1,delta*4.5));
     controls.current?.update();
    }
    if(now-f.lastUpdate>200||sample.progress===1){onFlightProgress?.(sample);f.lastUpdate=now}
    if(sample.progress===1){
     clearTimeout(f.timer);
     flight.current=null;
     setFlightActive(false);
     setRouteComplete(true);
     f.resolve();
    }
   }else if(routeComplete&&drone.current&&dronePos.current){
    const bob=Math.sin(performance.now()*0.003)*0.12;
    drone.current.position.set(dronePos.current[0],dronePos.current[1]+bob,dronePos.current[2]);
    if(!reduced){
     camera.position.lerp(new THREE.Vector3(dronePos.current[0]+15,dronePos.current[1]+8,dronePos.current[2]+18),Math.min(1,delta*2));
     controls.current?.target.lerp(new THREE.Vector3(dronePos.current[0],dronePos.current[1]-2,dronePos.current[2]),Math.min(1,delta*3));
     controls.current?.update();
    }
   }
 });
 useEffect(()=>{const abort=()=>{const f=flight.current;if(f){clearTimeout(f.timer);flight.current=null;f.reject(new Error('The flight view was interrupted. Retry the inspection to capture evidence.'))}};const lost=()=>{setFlightActive(false);onUnavailable?.();abort()};const restored=()=>onReady?.();gl.domElement.addEventListener('webglcontextlost',lost);gl.domElement.addEventListener('webglcontextrestored',restored);return()=>{gl.domElement.removeEventListener('webglcontextlost',lost);gl.domElement.removeEventListener('webglcontextrestored',restored);abort()}},[gl]);
 useEffect(()=>{if(inspection&&!flight.current){const p=new THREE.Vector3(...asset.position_m);camera.position.copy(p.clone().add(new THREE.Vector3(44,35,54)));controls.current?.target.copy(p.clone().add(new THREE.Vector3(0,5,10)));controls.current?.update()}},[inspection,asset.id,camera]);
 useImperativeHandle(ref,()=>({
  focus(){const p=new THREE.Vector3(...asset.position_m);camera.position.copy(p.clone().add(new THREE.Vector3(32,30,40)));controls.current.target.copy(p);controls.current.update()},
  reset(){camera.position.set(100,95,120);controls.current.target.set(0,0,0);controls.current.update()},
  fly(m){
   if(flight.current){clearTimeout(flight.current.timer);flight.current=null}
   const takeoff:V3=[0,.45,-22]; const climb:V3=[0,15,-22];
   const targetId=m.target_asset_ids?.[0]||asset.id;
   const poleAsset=snapshot.assets.find(a=>a.id===targetId||a.id==='pole-'+targetId)||asset;
   const [px,,pz]=poleAsset.position_m;
   const conn=snapshot.connections.find(c=>c.to_asset_id===poleAsset.id||c.from_asset_id===poleAsset.id||c.to_asset_id===targetId||c.from_asset_id===targetId);
   let lineRoute:V3[];
   if(conn&&conn.geometry_points_m&&conn.geometry_points_m.length>=2){
    const p0=conn.geometry_points_m[0];
    const p1=conn.geometry_points_m[conn.geometry_points_m.length-1];
    const isRev=Math.hypot(p0[0]-px,p0[2]-pz)<Math.hypot(p1[0]-px,p1[2]-pz);
    const sPt=isRev?p1:p0,ePt=isRev?p0:p1;
    const approach:V3=[sPt[0]*.5,14,(sPt[2]-22)*.5];
    const wireStart:V3=[sPt[0],11.5,sPt[2]];
    const wireMid:V3=[(sPt[0]+ePt[0])/2,10.4,(sPt[2]+ePt[2])/2];
    const poleTop:V3=[ePt[0],10.5,ePt[2]];
    const poleHover:V3=[ePt[0],10.2,ePt[2]];
    lineRoute=[approach,wireStart,wireMid,poleTop,poleHover];
   }else{
    lineRoute=[[px*.5,14,pz*.5],[px,11.5,pz],[px,10.2,pz]];
   }
   const completeRoute:V3[]=[takeoff,climb,...lineRoute];
   dronePos.current=[0,.45,-22];
   const initial=sampleFlight(completeRoute,0);onFlightProgress?.(initial);setMission(m);setFlightActive(true);setRouteComplete(false);
   camera.position.set(20,24,-5);controls.current?.target.set(0,8,-16);controls.current?.update();
   return new Promise<void>((resolve,reject)=>{const timer=setTimeout(()=>{if(flight.current){flight.current=null;setFlightActive(false);reject(new Error('The flight view stopped updating. Keep the tab visible and retry the inspection.'))}},25000);flight.current={start:performance.now(),resolve,reject,mission:m,route:completeRoute,timer,lastUpdate:0}})
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
  <color attach="background" args={['#060a10']}/><fog attach="fog" args={['#06090e',100,260]}/>
  {/* Key: cool-white overhead sun */}
  <ambientLight intensity={0.75} color="#b8c8e0"/>
  <directionalLight position={[15,60,45]} intensity={2.8} color="#dde8f5"/>
  {/* Fill: deep blue from opposite corner */}
  <directionalLight position={[-25,18,-35]} intensity={1.4} color="#2a5bbf"/>
  {/* Warm accent: faint orange bounce from ground level */}
  <directionalLight position={[0,-8,30]} intensity={0.35} color="#f59e4a"/>
  {/* Street / pole lamp point lights scattered through scene */}
  <pointLight position={[-12,8,-8]} intensity={18} distance={28} decay={2} color="#fef3c7"/>
  <pointLight position={[14,8,10]} intensity={18} distance={28} decay={2} color="#fef3c7"/>
  <pointLight position={[0,8,20]} intensity={14} distance={24} decay={2} color="#fde68a"/>
  <pointLight position={[-30,8,-6]} intensity={12} distance={22} decay={2} color="#fef3c7"/>
  <pointLight position={[28,8,-6]} intensity={12} distance={22} decay={2} color="#fef3c7"/>
  {/* Blue accent at launch station */}
  <pointLight position={[0,3,-22]} intensity={22} distance={18} decay={2} color="#3b82f6"/>
  <Scenery/>
  <LaunchStation p={LAUNCH_STATION_POS}/>
  {!flightActive&&!mission&&!routeComplete&&<group position={[0,.45,-22]}><Drone active={false} reduced={reduced}/><Html position={[0,2.6,0]} center zIndexRange={[5,0]}><div className="drone-caption"><span style={{background:blue}}/>GT–01 <small>DOCKED · STANDBY</small></div></Html></group>}
  {snapshot.assets.filter(a=>a.kind==='household').map(a=><House a={a} key={a.id} onSelect={onSelect}/>)}
  {snapshot.assets.filter(a=>a.kind==='transformer').map(a=><Transformer a={a} key={a.id} onSelect={onSelect}/>)}
  {snapshot.assets.filter(a=>a.kind==='branch'||a.kind==='feeder').map(a=><group key={a.id} onClick={e=>{e.stopPropagation();onSelect(a.id)}}><Pole p={a.position_m}/><mesh position={a.position_m}><sphereGeometry args={[.65,12,8]}/><meshStandardMaterial color="#94a3b8"/></mesh></group>)}
  {snapshot.connections.map(c=><Wire key={c.id} points={c.geometry_points_m}/>)}
  {snapshot.physical_connections_m.map((p,i)=><Wire key={'extra'+i} points={p}/>)}
  {snapshot.physical_occluders?.map((o,i)=><Box key={'occluder'+i} p={o.position_m} s={o.size_m} color="#1e293b"/>)}
  <group ref={overlay}>
   {snapshot.connections.map(c=>{
    const problem=anomalous.includes(c.from_asset_id)||anomalous.includes(c.to_asset_id);const active=c.from_asset_id===targetBranch||c.to_asset_id===targetBranch;
    return <Line key={c.id} points={c.geometry_points_m} color={problem?amber:active?royalBlue:slate} lineWidth={problem||active?2.5:1} transparent opacity={(problem || active) ? .95 : .35}/>
   })}
   <mesh position={[asset.position_m[0],.1,asset.position_m[2]]} rotation={[-Math.PI/2,0,0]}><ringGeometry args={[3,3.3,40]}/><meshBasicMaterial color={selectedColor} transparent opacity={.8}/></mesh>
   {!inspection&&!routeComplete&&<Html position={[asset.position_m[0],asset.kind==='household'?7:11,asset.position_m[2]]} center distanceFactor={110} zIndexRange={[5,0]}><button className="scene-label" style={{borderColor:selectedColor}} onClick={()=>onSelect(asset.id)}><span style={{color:selectedColor}}>◇</span> <strong>{asset.label}</strong><small>{!!status&&status.validity!=='valid'?'⚠ Data incomplete':reviewedIds.includes(targetBranch)?'◉ Under review':anomalous.includes(targetBranch)?'△ Unexplained loss':'✓ Within threshold'}</small></button></Html>}
   {!inspection&&snapshot.assets.filter(a=>a.kind==='feeder'&&a.id!==selected).map(a=><Html position={[a.position_m[0],12,a.position_m[2]]} key={a.id} center distanceFactor={140} zIndexRange={[5,0]}><button className="scene-label feeder" onClick={()=>onSelect(a.id)}>{a.label}</button></Html>)}
   {(mission||routeComplete)&&<><Line points={flight.current?.route||mission?.waypoints_m||[]} color={royalBlue} lineWidth={2} dashed dashSize={1} gapSize={.7}/>{(mission?.waypoints_m||[]).map((p,i)=><group key={i} position={p}><mesh rotation={[-Math.PI/2,0,0]}><ringGeometry args={[1.6,1.8,32]}/><meshBasicMaterial color={blue} transparent opacity={.75} side={THREE.DoubleSide}/></mesh></group>)}<group ref={drone} position={dronePos.current}><Drone active={flightActive||routeComplete} reduced={reduced}/><Html position={[0,4,0]} center zIndexRange={[6,0]}><div className="drone-caption"><span style={{background:routeComplete?'#f59e0b':blue}}/>GT–01 <small>{flightActive?'IN FLIGHT':routeComplete?'AT VIEWPOINT':'STANDBY'}</small></div></Html><mesh rotation={[Math.PI,0,0]} position={[0,-4,0]}><coneGeometry args={[3.2,7.5,24,1,true]}/><meshBasicMaterial color={routeComplete?amber:royalBlue} wireframe transparent opacity={flightActive?.22:routeComplete?.38:.08}/></mesh>{(flightActive||routeComplete)&&<mesh rotation={[-Math.PI/2,0,0]} position={[0,-2.5,0]}><ringGeometry args={[1.6,1.85,24]}/><meshBasicMaterial color={routeComplete?amber:blue} transparent opacity={.85} side={THREE.DoubleSide}/></mesh>}</group></>}
   {(()=>{
     const flg=snapshot.assets.find(a=>a.id===mission?.target_asset_ids[0]);
     if(!flg)return null;
     const [fx,,fz]=flg.position_m;
     if(routeComplete){
      return <group position={[fx,0,fz]}>
       <mesh rotation={[-Math.PI/2,0,0]} position={[0,.18,0]}><ringGeometry args={[2.8,3.6,32]}/><meshBasicMaterial color={amber} transparent opacity={.9} side={THREE.DoubleSide}/></mesh>
       <mesh rotation={[-Math.PI/2,0,0]} position={[0,.2,0]}><ringGeometry args={[1.2,1.5,24]}/><meshBasicMaterial color="#d97706" transparent opacity={.7} side={THREE.DoubleSide}/></mesh>
       <Html position={[0,15.2,0]} center distanceFactor={26} zIndexRange={[7,0]}>
        <div className="pole-inspection-flag">
         <strong><span className="live-dot" style={{background:'#f59e0b'}}/>Inspection viewpoint</strong>
         <small>Review saved captures</small>
        </div>
       </Html>
      </group>;
     }
     if(flightActive){
      return <group position={[fx,0,fz]}>
       <mesh rotation={[-Math.PI/2,0,0]} position={[0,.22,0]}><ringGeometry args={[2.2,2.8,32]}/><meshBasicMaterial color={royalBlue} transparent opacity={.85} side={THREE.DoubleSide}/></mesh>
       <Html position={[0,12.5,0]} center distanceFactor={85} zIndexRange={[7,0]}>
        <div className="pole-scanning-badge">
         <strong><span className="live-dot" style={{background:blue}}/>AERIAL SCAN IN PROGRESS</strong>
         <small>MULTISPECTRAL CONTOUR EXTRACTION</small>
        </div>
       </Html>
      </group>;
     }
     if(anomalous.length>0){
      return <group position={[fx,0,fz]}>
       <mesh rotation={[-Math.PI/2,0,0]} position={[0,.15,0]}><ringGeometry args={[2,2.4,32]}/><meshBasicMaterial color={amber} transparent opacity={.55} side={THREE.DoubleSide}/></mesh>
       <Html position={[0,12,0]} center distanceFactor={90} zIndexRange={[6,0]}>
        <div className="pole-target-badge">
         <strong><span className="live-dot" style={{background:'#d97706'}}/>INSPECTION TARGET</strong>
         <small>UNEXPLAINED ENERGY DEFICIT · PENDING FLIGHT</small>
        </div>
       </Html>
      </group>;
     }
     return null;
   })()}
  </group>
  <OrbitControls ref={controls} makeDefault enabled={!flightActive} maxPolarAngle={Math.PI*.47} minDistance={10} maxDistance={240} enableDamping dampingFactor={.12}/>
 </>
});
export default function Scene({handle,onReady,paused,...props}:Props){return <Canvas frameloop={paused?'never':'always'} onCreated={()=>onReady?.()} camera={{position:[100,95,120],fov:40,near:.1,far:500}} dpr={[1,2]} gl={{antialias:true,powerPreference:'high-performance',alpha:false,stencil:false}}><World ref={handle} {...props} onReady={onReady}/></Canvas>}
