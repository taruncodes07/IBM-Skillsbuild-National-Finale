import React, { useState, useEffect, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  X,
  Play,
  Pause,
  Building2,
  Camera,
  FileText,
  HelpCircle,
  Maximize2,
  Minimize2,
  CheckCircle2,
  AlertTriangle,
  Compass,
  ArrowRight,
  Sparkles,
  Zap,
  Activity,
  Navigation,
  ShieldCheck,
  Download
} from 'lucide-react';
import type { Snapshot, Detail, Case } from './types';

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

export interface TutorialStep {
  id: number;
  shortLabel: string;
  badge: string;
  title: string;
  subtitle: string;
  summary: string;
  metrics: { label: string; value: string; color?: string }[];
  actionLabel: string;
  actionIcon: React.ReactNode;
  trigger: (props: WalkthroughModalProps, setStatus: (s: string) => void) => Promise<void>;
  juryDefense: {
    question: string;
    answer: string;
  };
}

const TUTORIAL_STEPS: TutorialStep[] = [
  {
    id: 1,
    shortLabel: '1. Balance',
    badge: 'STEP 1 · TELEMETRY RECONCILIATION',
    title: 'Physical Energy Conservation & Deficit Detection',
    subtitle: '15-Minute Boundary Balance vs Consumer ML Guesswork',
    summary:
      'Grid Trace continuously monitors 11kV/415V distribution transformers. By subtracting metered consumer loads and calculated technical conductor loss from sectional branch input, unexplained non-technical theft is mathematically confirmed when exceeding 3σ statistical gating.',
    metrics: [
      { label: 'Branch Input', value: '1.818 kWh' },
      { label: 'Metered Sum', value: '0.597 kWh' },
      { label: 'Unexplained Deficit', value: '1.210 kWh (66.6%)', color: '#f59e0b' }
    ],
    actionLabel: 'Trigger: Focus Energy Deficit',
    actionIcon: <Activity size={15} />,
    trigger: async (props, setStatus) => {
      setStatus('Switching to network view and isolating Branch 03 DT boundary...');
      props.onSetScreen?.('network');
      props.onSelectAsset('branch-03');
      props.onSetInspectorTab?.('balance');
      props.onFocusAsset?.();
      setStatus('Isolated Transformer 02 / Branch 03: Active unexplained residual deficit of 1.210 kWh (66.6% loss).');
    },
    juryDefense: {
      question: 'Why not simply use consumer-level smart meter drop algorithms?',
      answer:
        'Consumer drops alone cannot distinguish between rooftop solar net-metering, vacations, or theft. Grid Trace balances the physical branch input: by conservation of energy, power that enters the branch but never reaches any consumer meter is undeniable commercial loss.'
    }
  },
  {
    id: 2,
    shortLabel: '2. Drone Dispatch',
    badge: 'STEP 2 · TARGETED PHYSICAL RECONNAISSANCE',
    title: 'Autonomous Drone Mission from Dock Station',
    subtitle: 'Conductor Corridor Navigation from Base DOCK-01',
    summary:
      'Instead of sending unguided foot-patrols into dense neighborhoods, BESCOM vigilance operators dispatch drone GT-01 from Aerial Dock-01. The drone navigates along calibrated conductor coordinates directly to the flagged branch pole.',
    metrics: [
      { label: 'Launch Base', value: 'BESCOM DOCK-01' },
      { label: 'Corridor', value: '24m Conductor Line' },
      { label: 'Cruise Altitude', value: '10.4m (2.4m over wires)', color: '#60a5fa' }
    ],
    actionLabel: 'Trigger: Launch Drone GT-01',
    actionIcon: <Navigation size={15} />,
    trigger: async (props, setStatus) => {
      props.onSetScreen?.('network');
      setStatus('Dispatched Drone GT-01 from Dock-01. Cruising along 415V conductor corridor...');
      if (props.onDispatchDrone) {
        await props.onDispatchDrone();
      }
      setStatus('Drone GT-01 reached target pole Branch-03 and established stationary hover.');
    },
    juryDefense: {
      question: 'Is aerial inspection assumed for every single loss alert?',
      answer:
        'No. Drone flight is strictly targeted (PRD FR-07) and justified only after statistical persistence confirms an unresolved deficit that cannot be inspected clearly from street roadway level.'
    }
  },
  {
    id: 3,
    shortLabel: '3. AI Tap Detection',
    badge: 'STEP 3 · EDGE COMPUTER VISION',
    title: 'Overhead OpenCV Wire Contour Verification',
    subtitle: 'Physical Splice Detection vs Solar Rooftop False Positives',
    summary:
      'Holding stationary hover above the pole crossarm, onboard edge computer vision extracts wire contours. It identifies an unmetered bypass tap spliced directly into the secondary distribution line prior to consumer smart metering.',
    metrics: [
      { label: 'Vision Engine', value: 'OpenCV Contour Extraction' },
      { label: 'AI Confidence', value: '0.94 (Confirmed)', color: '#60a5fa' },
      { label: 'Physical Finding', value: 'Unmetered Tap Splice', color: '#f59e0b' }
    ],
    actionLabel: 'Trigger: Verify Edge AI Tap Detection',
    actionIcon: <Zap size={15} />,
    trigger: async (props, setStatus) => {
      props.onSetScreen?.('network');
      props.onSelectAsset('branch-03');
      props.onFocusAsset?.();
      setStatus('Edge AI multispectral contour extraction active: unmetered bypass tap confirmed (OpenCV 0.94 confidence).');
    },
    juryDefense: {
      question: 'How does computer vision differentiate legitimate drops from theft taps?',
      answer:
        'Insulated utility service lines connect to official revenue meter terminals with standardized drip loops. The OpenCV model detects irregular non-insulated splices tapped directly to the secondary phase before the meter box.'
    }
  },
  {
    id: 4,
    shortLabel: '4. Case Dossier',
    badge: 'STEP 4 · FORENSIC INVESTIGATION DOSSIER',
    title: 'Human Review Dossier & Ground Certification',
    subtitle: 'High-Resolution Aerial RGB Evidence with Annotated Bounding Boxes',
    summary:
      'The case review workspace presents captured aerial evidence with original vs OpenCV annotated pixel comparisons. The operator records ground line-of-sight obstruction, establishing legal proof of why aerial inspection was mandatory.',
    metrics: [
      { label: 'Scene Evidence', value: 'IMG-001 & IMG-002' },
      { label: 'Visual Modes', value: 'Original vs Annotated' },
      { label: 'Ground Line-of-Sight', value: 'Obstructed (Certified)', color: '#60a5fa' }
    ],
    actionLabel: 'Trigger: Open Investigation Dossier',
    actionIcon: <Camera size={15} />,
    trigger: async (props, setStatus) => {
      setStatus('Opening forensic case dossier for Branch-03...');
      await props.onCreateAndOpenCase('branch-03');
      props.onSetScreen?.('inspection');
      await props.onRecordGroundReview();
      setStatus('Forensic investigation dossier active: Annotated overhead evidence, timestamped telemetry, and certified ground obstruction note.');
    },
    juryDefense: {
      question: 'Can the system automatically disconnect or penalize consumers?',
      answer:
        'Zero automated punitive actions are permitted. Grid Trace strictly enforces a human-in-the-loop review workflow, producing certified forensic evidence packages for authorized BESCOM vigilance squads.'
    }
  },
  {
    id: 5,
    shortLabel: '5. Enforcement',
    badge: 'STEP 5 · BESCOM REGULATORY ENFORCEMENT',
    title: 'Lineman Work Order, Loss Recovery & Audit Trail',
    subtitle: 'KERC / BEE Compliance & Tamper Dossier Export',
    summary:
      'Grid Trace compiles the final enforcement package: formal lineman repair dispatch, commercial loss recovery calculation (₹ / kWh), and an immutable SHA-256 audit log protecting consumer rights while recovering utility revenue.',
    metrics: [
      { label: 'Lineman Action', value: 'Disconnection Work Order' },
      { label: 'Loss Recovery', value: '₹ Computed & Verified' },
      { label: 'Audit Log', value: 'SHA-256 Immutable Trace', color: '#60a5fa' }
    ],
    actionLabel: 'Trigger: Generate Vigilance Order & Export Report',
    actionIcon: <Download size={15} />,
    trigger: async (props, setStatus) => {
      setStatus('Generating BESCOM vigilance dispatch work order and downloading case report...');
      await props.onExportReport('markdown');
      setStatus('Enforcement package ready: Work order issued, loss recovery verified, and audit report downloaded.');
    },
    juryDefense: {
      question: 'How does this align with National RDSS and BEE regulatory mandates?',
      answer:
        'It fulfills the Revamped Distribution Sector Scheme (RDSS) DT metering mandate and BEE Periodic Energy Accounting norms by transforming raw AMR smart meter streams into verifiable physical accountability.'
    }
  }
];

export const WalkthroughModal: React.FC<WalkthroughModalProps> = (props) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);
  const [actionStatus, setActionStatus] = useState<string>('');
  const [isBusy, setIsBusy] = useState(false);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [showDefense, setShowDefense] = useState(false);
  const autoPlayTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const step = TUTORIAL_STEPS[currentStepIndex];

  // Auto-play tour sequencing
  useEffect(() => {
    if (!isAutoPlaying) {
      if (autoPlayTimer.current) clearTimeout(autoPlayTimer.current);
      return;
    }

    const runAutoStep = async () => {
      setIsBusy(true);
      try {
        await step.trigger(props, setActionStatus);
      } catch (err) {
        setActionStatus(`Step error: ${(err as Error).message}`);
      } finally {
        setIsBusy(false);
      }

      // Schedule next step in auto tour
      autoPlayTimer.current = setTimeout(() => {
        if (currentStepIndex < TUTORIAL_STEPS.length - 1) {
          setCurrentStepIndex((prev) => prev + 1);
        } else {
          setIsAutoPlaying(false);
          setActionStatus('Full interactive tutorial completed successfully!');
        }
      }, step.id === 2 ? 10000 : 5000);
    };

    runAutoStep();

    return () => {
      if (autoPlayTimer.current) clearTimeout(autoPlayTimer.current);
    };
  }, [isAutoPlaying, currentStepIndex]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && currentStepIndex < TUTORIAL_STEPS.length - 1 && !isBusy) {
        handleNext();
      } else if (e.key === 'ArrowLeft' && currentStepIndex > 0 && !isBusy) {
        handlePrev();
      } else if (e.key === 'Escape') {
        setIsAutoPlaying(false);
        props.onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStepIndex, isBusy, props]);

  const handleNext = () => {
    if (currentStepIndex < TUTORIAL_STEPS.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
      setActionStatus('');
      setShowDefense(false);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
      setActionStatus('');
      setShowDefense(false);
    }
  };

  const handleExecuteTrigger = async () => {
    if (isBusy) return;
    setIsBusy(true);
    setActionStatus(`Executing Step ${step.id} action live on Grid Trace...`);
    try {
      await step.trigger(props, setActionStatus);
    } catch (err) {
      setActionStatus(`Action failed: ${(err as Error).message}`);
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <div className={`tutorial-dock-card ${isExpanded ? 'expanded' : ''}`} role="region" aria-label="Interactive Project Tutorial">
      {/* Top Header Row */}
      <div className="tutorial-dock-header">
        <div className="tutorial-title-area">
          <div className="tutorial-live-badge">
            <span className="live-dot" style={{ background: '#3b82f6' }} />
            <strong>INTERACTIVE TUTORIAL · STEP {step.id} OF {TUTORIAL_STEPS.length}</strong>
          </div>
          <span className="tutorial-badge-pill">{step.badge}</span>
        </div>

        <div className="tutorial-dock-actions">
          <button
            className={`tutorial-autoplay-btn ${isAutoPlaying ? 'active' : ''}`}
            onClick={() => setIsAutoPlaying((prev) => !prev)}
            title={isAutoPlaying ? 'Pause Auto-Play' : 'Auto-Run Complete Tour'}
          >
            {isAutoPlaying ? <Pause size={13} /> : <Play size={13} />}
            <span>{isAutoPlaying ? 'Pause Tour' : 'Auto-Play'}</span>
          </button>

          <button
            className="tutorial-icon-btn"
            onClick={() => setIsExpanded((prev) => !prev)}
            title={isExpanded ? 'Collapse to compact widget' : 'Expand technical details & jury defense'}
          >
            {isExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>

          <button
            className="tutorial-icon-btn"
            onClick={() => {
              setIsAutoPlaying(false);
              props.onClose();
            }}
            title="Close Tutorial (Esc)"
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Step Selector Pills */}
      <div className="tutorial-step-pills">
        {TUTORIAL_STEPS.map((s, idx) => (
          <button
            key={s.id}
            className={`step-pill ${idx === currentStepIndex ? 'active' : ''} ${idx < currentStepIndex ? 'completed' : ''}`}
            onClick={() => {
              setIsAutoPlaying(false);
              setCurrentStepIndex(idx);
              setActionStatus('');
              setShowDefense(false);
            }}
          >
            <span>{s.shortLabel}</span>
          </button>
        ))}
      </div>

      {/* Main Card Content */}
      <div className="tutorial-body">
        <h3 className="tutorial-step-title">{step.title}</h3>
        <p className="tutorial-step-subtitle">{step.subtitle}</p>
        <p className="tutorial-step-desc">{step.summary}</p>

        {/* Live Metrics Row */}
        <div className="tutorial-metrics-row">
          {step.metrics.map((m, i) => (
            <div key={i} className="tutorial-metric-chip">
              <small>{m.label}</small>
              <strong style={{ color: m.color || '#f1f5f9' }}>{m.value}</strong>
            </div>
          ))}
        </div>

        {/* Live Action Trigger Button */}
        <div className="tutorial-action-section">
          <button
            className="tutorial-trigger-action-btn"
            disabled={isBusy}
            onClick={handleExecuteTrigger}
          >
            {step.actionIcon}
            <span>{step.actionLabel}</span>
          </button>
        </div>

        {/* Status / Telemetry Feedback */}
        {actionStatus && (
          <div className="tutorial-status-feedback">
            <span className="live-dot" style={{ background: '#3b82f6' }} />
            <span>{actionStatus}</span>
          </div>
        )}

        {/* Expandable Technical Defense Section */}
        {isExpanded && (
          <div className="tutorial-expanded-drawer">
            <button
              className="tutorial-defense-toggle"
              onClick={() => setShowDefense((prev) => !prev)}
            >
              <HelpCircle size={14} />
              <span>BESCOM Hackathon Jury Q&A Defense</span>
              <span className="drawer-indicator">{showDefense ? '▲' : '▼'}</span>
            </button>

            {showDefense && (
              <div className="tutorial-defense-content">
                <p><strong>Question:</strong> {step.juryDefense.question}</p>
                <p><strong>Defense:</strong> {step.juryDefense.answer}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Navigation Bar */}
      <div className="tutorial-footer">
        <button
          className="tutorial-nav-btn prev"
          disabled={currentStepIndex === 0 || isBusy}
          onClick={handlePrev}
        >
          <ChevronLeft size={14} />
          <span>Previous</span>
        </button>

        <div className="tutorial-keyboard-tip">
          Use <kbd>←</kbd> <kbd>→</kbd> keys or Auto-Play
        </div>

        <button
          className="tutorial-nav-btn next"
          disabled={currentStepIndex === TUTORIAL_STEPS.length - 1 || isBusy}
          onClick={handleNext}
        >
          <span>Next Step</span>
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default WalkthroughModal;
