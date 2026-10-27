import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,Play,Radio,X} from 'lucide-react';

export const CHAPTERS = [
 {title:'Follow the energy',target:'.zone-c-center',view:'overview',preset:1,body:'विद्युत drishti follows electricity from feeders to homes. Moving dots show network direction; select a building or branch to inspect its energy balance.',action:'Try a closer view',command:'focus'},
 {title:'Start with a healthy grid',target:'.energy-section',view:'section',preset:1,body:'In this baseline, input energy matches metered demand plus expected technical loss. A small residual alone is not a loss alert.',action:'Advance 15 minutes',command:'step'},
 {title:'Explore the digital twin',target:'.zone-b-left',view:'section',body:'Choose a feeder, branch or home in the tree or directly in 3D. The balance and investigation panels follow your selection.',action:'Select another branch',command:'branch'},
 {title:'Missing data is not theft',target:'.energy-section',view:'section',preset:2,body:'This example removes telemetry. विद्युत drishti marks the balance incomplete and blocks unsupported loss alerts. Missing readings remain missing.',action:'Advance 15 minutes',command:'step'},
 {title:'Find a persistent loss',target:'.zone-d-right',view:'section',preset:3,body:'An unmetered load creates repeated excess loss. After three valid affected intervals, the branch is flagged. The alert is a reason to investigate, not a verdict.',action:'Inspect energy balance',command:'focus'},
 {title:'Turn an alert into a check',target:'.review-summary',view:'section',preset:3,body:'Analyze section opens the evidence workers and suggested checks. Open case starts an auditable human review. A reviewer records ground observations before any inspection is approved.',action:'Open section analysis',command:'analyze'},
 {title:'Get a view from above',target:'.zone-c-center',view:'drone',body:'Launch the virtual drone for a 15-second camera flight. This tour is a visual preview. Actual case inspections require reviewer approval and capture two RGB views.',action:'Launch drone preview',command:'drone'},
 {title:'Show the energy saved',target:'.compare-launch',view:'overview',body:'Compare the same simulated day with and without intervention. विद्युत drishti detects the loss; a crew repairs it one hour later, removing 90% of that incident’s loss.',action:'Run the loss comparison',command:'compare'},
 {title:'Make the demo your own',target:'.guided-demo-stepper',view:'overview',body:'Switch among baseline, missing data and unexplained loss. Play, pause or step through 15-minute intervals. Use the laboratory for other incidents and coverage settings. This runtime is simulated; the team’s source data is partly synthesized.',action:'Open scenario laboratory',command:'lab'},
] as const;
export type TourCommand=typeof CHAPTERS[number]['command'];
type Props={onStage:(index:number)=>Promise<void>;onAction:(command:TourCommand)=>Promise<void>;onClose:()=>void;blocked:boolean;obscured:boolean};

export function PresentationWelcome({ready,onPresent,onExplore}:{ready:boolean;onPresent:()=>void;onExplore:()=>void}){
 const root=useRef<HTMLElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;root.current?.focus();return()=>previous?.focus()},[]);
 return <div className="presentation-welcome-backdrop" onKeyDown={e=>{if(e.key==='Escape')onExplore();if(e.key==='Tab'){const buttons=root.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)');if(!buttons)return;if(e.shiftKey&&document.activeElement===buttons[0]){e.preventDefault();buttons[buttons.length-1].focus()}else if(!e.shiftKey&&document.activeElement===buttons[buttons.length-1]){e.preventDefault();buttons[0].focus()}}}}>
  <section ref={root} tabIndex={-1} className="presentation-welcome" role="dialog" aria-modal="true" aria-labelledby="presentation-welcome-title">
   <Radio size={36}/><p className="welcome-brand">विद्युत drishti · Digital Twin & Loss Investigation Platform</p>
   <h1 id="presentation-welcome-title">विद्युत drishti</h1>
   <p>See where the energy goes. A physical energy balance digital twin, simulated aerial computer vision, and explainable multi-agent loss investigation platform.</p>
   <div className="welcome-route" aria-hidden="true"><span>Measure</span><i/><span>Investigate</span><i/><span>Recover</span></div>
   <button className="primary" disabled={!ready} onClick={onPresent}><Play size={16}/>{ready?'Start Walkthrough':'Connecting to simulation…'}</button>
   <button className="welcome-explore" onClick={onExplore}>Explore Dashboard</button>
   <small>9 interactive chapters · presenter-paced walkthrough · live digital twin</small>
  </section>
 </div>;
}

export default function PresentationTour({onStage,onAction,onClose,blocked,obscured}:Props){
 const [index,setIndex]=useState(0),[pending,setPending]=useState(true),[pendingAction,setPendingAction]=useState(false),[failure,setFailure]=useState('');
 const [rect,setRect]=useState<{left:number;top:number;width:number;height:number}|null>(null);
 const card=useRef<HTMLElement>(null),stageCallback=useRef(onStage),actionLock=useRef(false);
 stageCallback.current=onStage;
 const chapter=CHAPTERS[index];
 useEffect(()=>{let active=true;setPending(true);setFailure('');stageCallback.current(index).catch(e=>{if(active)setFailure((e as Error).message)}).finally(()=>{if(active)setPending(false)});return()=>{active=false}},[index]);
 useEffect(()=>{if(!obscured&&(!pending||index===0))card.current?.focus()},[index,pending,obscured]);
 useLayoutEffect(()=>{
  if(obscured){setRect(null);return}
  const update=()=>{const el=document.querySelector<HTMLElement>(chapter.target);if(!el){setRect(null);return}const r=el.getBoundingClientRect();const left=Math.max(6,r.left-6),top=Math.max(6,r.top-6),right=Math.min(innerWidth-6,r.right+6),bottom=Math.min(innerHeight-6,r.bottom+6);setRect(right>left&&bottom>top?{left,top,width:right-left,height:bottom-top}:null)};
  const target=document.querySelector<HTMLElement>(chapter.target);if(innerWidth<=900)target?.scrollIntoView({block:'center',behavior:'instant'});
  update();const element=document.querySelector(chapter.target),observer=new ResizeObserver(update);if(element)observer.observe(element);window.addEventListener('resize',update);window.addEventListener('scroll',update,true);
  return()=>{observer.disconnect();window.removeEventListener('resize',update);window.removeEventListener('scroll',update,true)};
 },[chapter.target,obscured,pending]);
 const action=async()=>{if(actionLock.current||pending||blocked)return;actionLock.current=true;setPendingAction(true);setPending(true);setFailure('');try{await onAction(chapter.command)}catch(e){setFailure((e as Error).message)}finally{actionLock.current=false;setPendingAction(false);setPending(false)}};
 const advance=(next:number)=>{if(!pending&&!blocked)setIndex(next)};
 useEffect(()=>{if(obscured)return;const key=(e:KeyboardEvent)=>{const target=e.target as HTMLElement;if(target.closest('input,select,textarea,[role="dialog"]'))return;if(e.key==='Escape'){e.preventDefault();onClose()}if(target.closest('.presentation-tour-card')&&e.key==='ArrowRight'&&index<CHAPTERS.length-1){e.preventDefault();advance(index+1)}if(target.closest('.presentation-tour-card')&&e.key==='ArrowLeft'&&index>0){e.preventDefault();advance(index-1)}};document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key)},[index,pending,blocked,obscured,onClose]);
 if(obscured)return null;
 return <div className="presentation-tour-layer">
  {rect&&<div className="presentation-spotlight" aria-hidden="true" style={rect}/>}
  <div className="presentation-mode-tag"><Radio size={14}/>विद्युत drishti Walkthrough <span>Explore the highlighted feature</span></div>
  <section ref={card} tabIndex={-1} className="presentation-tour-card" aria-label="विद्युत drishti walkthrough">
   <div className="tour-card-heading"><span>विद्युत drishti · Chapter {index+1} of {CHAPTERS.length}</span><button aria-label="End walkthrough" onClick={onClose}><X size={16}/></button></div>
   <div aria-live="polite" aria-atomic="true"><h2>{chapter.title}</h2><p>{chapter.body}</p></div>
   <button className="tour-try" disabled={pending||blocked} onClick={action}>{pending?'Preparing scene…':chapter.action}<Play size={13}/></button>
   {failure&&<p role="alert" className="tour-failure">{failure} <button disabled={pending||blocked} onClick={()=>{setPending(true);stageCallback.current(index).then(()=>setFailure('')).catch(e=>setFailure((e as Error).message)).finally(()=>setPending(false))}}>Retry chapter</button></p>}
   <nav className="tour-chapters" aria-label="Walkthrough chapters">{CHAPTERS.map((c,i)=><button key={c.title} aria-label={`Chapter ${i+1}: ${c.title}`} aria-current={i===index?'step':undefined} disabled={pending||blocked} onClick={()=>advance(i)}/>)}</nav>
   <div className="tour-navigation"><button disabled={index===0||pending||blocked} onClick={()=>advance(index-1)}><ArrowLeft size={15}/>Back</button><small>← → to navigate · Esc to exit</small><button className="primary" disabled={pending||blocked} onClick={()=>index===CHAPTERS.length-1?onClose():advance(index+1)}>{index===CHAPTERS.length-1?'Finish':'Next'}<ArrowRight size={15}/></button></div>
  </section>
 </div>;
}
