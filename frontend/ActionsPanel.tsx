import {useState, useEffect} from 'react';
import {Activity, ArrowRight, Layers, ShieldCheck, TriangleAlert} from 'lucide-react';
import {api, words} from './api';
import type {Actions, RankedAction} from './types';

const pretty = (s: string) => words(s).replace(/^./, c => c.toUpperCase());
const rupees = (v: number) => '₹' + Math.round(v).toLocaleString('en-IN');

/** Ranked next checks for one boundary (PRD FR-06 / AC-14).
 *  Every number shown is an authored planning assumption, never a measured price or
 *  success rate, and the panel recommends a check for a human - it never authorises one. */
export default function ActionsPanel({runId, boundaryId, caseId, sequence}:
  {runId: string; boundaryId: string; caseId?: string | null; sequence: number}) {
  const [data, setData] = useState<Actions | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setLoading(true); setError(''); setData(null);
    const query = `/balances/${boundaryId}/actions?run_id=${encodeURIComponent(runId)}` +
      (caseId ? `&case_id=${encodeURIComponent(caseId)}` : '');
    api<Actions>(query)
      .then(result => { if (live) setData(result); })
      .catch(e => { if (live) setError((e as Error).message); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [runId, boundaryId, caseId, sequence]);

  if (loading) return <div className="actions-panel"><h3>Next useful check</h3><p className="empty">Ranking available checks…</p></div>;
  if (error) return <div className="actions-panel"><h3>Next useful check</h3><p className="empty">{error}</p></div>;
  if (!data) return null;

  const ranked: RankedAction[] = data.ranked || [];
  const scale = Math.max(0.0001, ...ranked.map(a => Math.abs(a.score)));
  const abstained = data.recommended_action === 'ABSTAIN_NO_ACTION';

  return <div className="actions-panel">
    <h3>Next useful check <span className="muted">{data.policy_version}</span></h3>

    {data.diagnostic_status === 'INSUFFICIENT_OBSERVABILITY' ? <>
      <div className="action-verdict blocked">
        <TriangleAlert size={17}/>
        <div><strong>Not instrumented</strong>
        <p>{data.abstain_reason}</p></div>
      </div>
      {!!data.uninstrumented_asset_ids?.length &&
        <p className="micro">No meter installed on: {data.uninstrumented_asset_ids.join(', ')}.</p>}
    </> : <>
      <div className={'action-verdict ' + (abstained ? 'abstain' : 'recommend')}>
        {abstained ? <ShieldCheck size={17}/> : <ArrowRight size={17}/>}
        <div>
          <strong>{abstained ? 'Abstain — no check justifies its cost' : pretty(data.recommended_action)}</strong>
          <p>{abstained ? data.abstain_reason : data.missing_evidence_question}</p>
        </div>
      </div>

      {data.human_choice_required && <div className="action-tie">
        <Layers size={16}/>
        <div><strong>Statistically tied — your call.</strong>
        <p>{data.tied_actions.map(pretty).join(' and ')} stay within {data.tie_band} of the leader once inputs
        vary by &plusmn;20%. The system will not pick between them for you.</p></div>
      </div>}

      {ranked.map(action => {
        const expanded = open === action.action_id;
        const width = Math.max(2, Math.abs(action.score) / scale * 100);
        return <div key={action.action_id} className={'action-card' + (action.rank === 1 && !abstained ? ' leading' : '')}>
          <button className="action-head" aria-expanded={expanded}
                  onClick={() => setOpen(expanded ? null : action.action_id)}>
            <span className="action-rank">{action.rank}</span>
            <span className="action-name">{action.label}
              {action.requires_external_action && <em> · needs a person on site</em>}
            </span>
            <span className={'action-score ' + (action.score < 0 ? 'negative' : '')}>{action.score.toFixed(3)}</span>
          </button>
          <div className="score-track"><i className={action.score < 0 ? 'negative' : ''} style={{width: width + '%'}}/></div>
          <div className="action-facts">
            <span title="Expected reduction in uncertainty"><Activity size={13}/>{action.information_gain_bits.toFixed(2)} bits</span>
            <span title="Illustrative total incremental cost">{rupees(action.cost.total_inr)}</span>
            <span title="Minutes to answer the question">{action.expected_minutes} min</span>
          </div>
          {expanded && <div className="action-detail">
            <p className="action-question">{action.question}</p>
            <dl>
              <dt>Score</dt><dd><code>IG &times; R &times; A &minus; 0.35&middot;Cn &minus; 0.15&middot;Tn</code></dd>
              <dt>Substituted</dt><dd><code>
                {action.information_gain_bits.toFixed(3)} &times; {action.reliability} &times; {action.access} &minus; 0.35&middot;
                {(Math.min(action.cost.total_inr / 2000, 1)).toFixed(3)} &minus; 0.15&middot;
                {(Math.min(action.expected_minutes / 120, 1)).toFixed(3)} = {action.score.toFixed(3)}
              </code></dd>
              <dt>Reliability</dt><dd>{action.reliability} observation is usable</dd>
              <dt>Access</dt><dd>{action.access} chance of obtaining it</dd>
              <dt>Cost split</dt><dd>travel {rupees(action.cost.travel_inr)} · staff {rupees(action.cost.staff_inr)} ·
                equipment {rupees(action.cost.equipment_inr)} · processing {rupees(action.cost.processing_inr)}</dd>
              <dt>Sensitivity</dt><dd>{action.sensitivity.low.toFixed(3)} to {action.sensitivity.high.toFixed(3)} at
                &plusmn;{Math.round(action.sensitivity.fraction * 100)}% on every input</dd>
              <dt>Likelihoods</dt><dd>{action.likelihood_confidence === 'AUTHORED'
                ? 'Authored on calibration cases'
                : 'Unknown — information gain is reported as a range, not a point value'}</dd>
            </dl>
          </div>}
        </div>;
      })}

      {!!data.rejected?.length && <details className="rejected-actions">
        <summary>{data.rejected.length} action{data.rejected.length === 1 ? '' : 's'} rejected before scoring</summary>
        {data.rejected.map(r => <div key={r.action_id} className="rejected-row">
          <TriangleAlert size={13}/>
          <div><strong>{r.label}</strong><small>{r.rejection_reason}</small></div>
        </div>)}
      </details>}
    </>}

    <p className="micro">Costs, reliabilities and likelihoods are authored planning assumptions, not measured
    Indian inspection economics. A ranked check is a recommendation for a human, never an authorisation.</p>
  </div>;
}
