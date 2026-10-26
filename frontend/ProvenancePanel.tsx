import {useState, useEffect} from 'react';
import {Layers, RotateCcw, ShieldCheck, TriangleAlert} from 'lucide-react';
import {api, date, words} from './api';
import type {Sources, AnalysisRevisions} from './types';

const pretty = (s: string) => words(s).replace(/^./, c => c.toUpperCase());

/** Data provenance and recomputation history.
 *  Surfaces /api/sources and /api/runs/{id}/analysis-revisions, which prove two claims the
 *  product makes: that the fixture is openly labelled development data rather than utility
 *  telemetry, and that revising an observation preserves every earlier analysis (AC-10). */
export default function ProvenancePanel({runId}: {runId: string}) {
  const [sources, setSources] = useState<Sources | null>(null);
  const [history, setHistory] = useState<AnalysisRevisions | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let live = true;
    api<Sources>('/sources').then(r => { if (live) setSources(r); }).catch(() => {});
    return () => { live = false; };
  }, []);

  useEffect(() => {
    let live = true;
    api<AnalysisRevisions>(`/runs/${runId}/analysis-revisions`)
      .then(r => { if (live) setHistory(r); }).catch(() => {});
    return () => { live = false; };
  }, [runId]);

  if (!sources) return null;
  const dev = sources.development;
  const pendingCount = [sources.bescom, sources.frozen_replay].filter(s => s.status === 'PENDING').length;
  const recomputations = history ? history.recomputations : [];

  return <div className="provenance-panel">
    <button className="provenance-chip" aria-expanded={open} onClick={() => setOpen(v => !v)}>
      <Layers size={13}/>
      <span>{dev.source_kind}</span>
      <code>{dev.source_hash.slice(0, 10)}</code>
      {pendingCount > 0 && <em>{pendingCount} source{pendingCount === 1 ? '' : 's'} pending</em>}
    </button>

    {open && <div className="provenance-detail">
      <h4>Where these readings come from</h4>
      <dl>
        <dt>Kind</dt><dd>{dev.source_kind} &middot; {dev.source_status}</dd>
        <dt>Label</dt><dd>{dev.label}</dd>
        <dt>Period</dt><dd>{date(dev.period_start)} to {date(dev.period_end)} &middot; {dev.interval_minutes} min intervals</dd>
        <dt>Expected</dt><dd>{dev.expected_reading_count.toLocaleString('en-IN')} readings across {dev.meter_count} meters</dd>
        <dt>Deliberate gaps</dt><dd>{dev.fixture_missing_readings} missing readings, left null</dd>
        <dt>Hash</dt><dd><code title={dev.source_hash}>{dev.source_hash.slice(0, 24)}…</code> <small>({dev.hash_kind})</small></dd>
      </dl>
      <p className="provenance-disclosure"><TriangleAlert size={13}/> {dev.disclosure}</p>

      <h4>Official sources</h4>
      <div className="source-row">
        <strong>BESCOM extract</strong>
        <span className={'source-status ' + sources.bescom.status.toLowerCase()}>{sources.bescom.status}</span>
        <small>{sources.bescom.reason}</small>
      </div>
      <div className="source-row">
        <strong>Frozen September replay</strong>
        <span className={'source-status ' + sources.frozen_replay.status.toLowerCase()}>{sources.frozen_replay.status}</span>
        <small>{sources.frozen_replay.reason}</small>
      </div>

      <h4><RotateCcw size={14}/> Recomputation history</h4>
      {recomputations.length === 0
        ? <p className="micro">No observation has been revised on this run. Revising a household reading
          creates a new analysis version and keeps every earlier one.</p>
        : <>
            <p className="micro">{recomputations.length} recomputation{recomputations.length === 1 ? '' : 's'}.
            Earlier analyses are retained, and case reports already exported stay frozen.</p>
            {recomputations.map(r => <div key={r.id} className="revision-row">
              <ShieldCheck size={13}/>
              <div>
                <strong>Revision {r.analysis_revision} &middot; {pretty(r.asset_id)}</strong>
                <small>interval {r.sequence} &middot; {r.actor} &middot; {date(r.wall_timestamp, true)} IST</small>
                <small>{r.reason}</small>
              </div>
            </div>)}
          </>}
    </div>}
  </div>;
}
