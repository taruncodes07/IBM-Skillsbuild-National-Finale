import {X} from 'lucide-react';
import type {Snapshot,Detail,Case} from './types';
export interface WalkthroughModalProps {
  snapshot: Snapshot | null;
  detail: Detail | null;
  cases: Case[];
  actor: string;
  screen?: 'network' | 'inspection';
  onClose: () => void;
  onSelectAsset: (id: string) => void;
  onSetActor: (actor: string) => void;
  onSetScreen?: (screen: 'network' | 'inspection') => void;
  onSetInspectorTab?: (tab: 'balance' | 'meters' | 'queue') => void;
  onDispatchDrone?: () => Promise<void>;
  onFocusAsset?: () => void;
  onTriggerScenario?: (scenario: string, seed: number) => Promise<void>;
  onStepSimulation?: (count: number) => Promise<void>;
  onCreateAndOpenCase: (area: string) => Promise<void>;
  onRecordGroundReview: () => Promise<void>;
  onApproveFlight?: () => Promise<void>;
  onExportReport: (format: string) => Promise<void>;
}

export default function WalkthroughModal({onClose}:WalkthroughModalProps){
 return <div className="modal-backdrop"><section className="modal compact-guide" role="dialog" aria-modal="true" aria-labelledby="guide-title"><div className="drawer-heading"><h2 id="guide-title">विद्युत drishti — Guided Walkthrough</h2><button autoFocus aria-label="Close guide" onClick={onClose}><X size={18}/></button></div>
  <ol><li><strong>Choose a scenario</strong><p>Baseline balances. Missing data blocks loss alerts. Unexplained loss opens a विद्युत drishti investigation.</p></li><li><strong>Analyze the section</strong><p>Run the multi-agent workers to review evidence and suggested checks.</p></li><li><strong>Review a case</strong><p>Open and triage a case. Switch to reviewer and record a ground observation.</p></li><li><strong>Inspect and record</strong><p>If an overhead question remains, approve the drone. Review captures, request a field check, and export.</p></li></ol><button className="primary full" onClick={onClose}>Start Walkthrough</button>
 </section></div>;
}
