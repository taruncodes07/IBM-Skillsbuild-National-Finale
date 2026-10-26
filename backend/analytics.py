"""Observed inputs only. This module must never import the simulator or truth store.
Implements energy balance, 3-interval persistence, and PRD v5.0 Section 7 Next-Best-Check engine.
"""
import math
from . import coverage
from .topology import BY_ID, CHILDREN, SECTIONS, VERSION, validate_cut

RULE_VERSION = 'section-1.0'
ANALYSIS_VERSION = 'accounting-1.0'
COEFFICIENTS = {'branch':(0.035,0.0012),'transformer':(0.045,0.00012),'feeder':(0.08,0.00004)}

COVERAGE_MODES = ('full', 'partial', 'feeder_and_dt_only', 'feeder_only')
BALANCE_QUALITIES = (
    'valid', 'incomplete', 'misaligned', 'stale', 'mapping_unknown',
    'model_uncertain', 'insufficient_observability'
)

# PRD v5.0 Section 7 Next-Best-Check Action Catalog
NEXT_CHECK_CATALOG = {
    'meter_record_cross_check': {
        'id': 'meter_record_cross_check',
        'action_name': 'REQUEST_METER_REVIEW',
        'label': 'Meter record cross-check',
        'ig_bits': 0.55,
        'reliability': 0.95,
        'access': 1.0,
        'cost_inr': 100.0,
        'time_min': 10.0,
        'eligible': True,
        'why': 'Cheapest check that can change the decision; records disagree with meter data'
    },
    'ground_observation': {
        'id': 'ground_observation',
        'action_name': 'REQUEST_FIELD_INSPECTION',
        'label': 'Targeted ground inspection',
        'ig_bits': 0.90,
        'reliability': 0.85,
        'access': 0.90,
        'cost_inr': 500.0,
        'time_min': 35.0,
        'eligible': True,
        'why': 'Smallest observable abnormal section is actionable'
    },
    'aerial_view': {
        'id': 'aerial_view',
        'action_name': 'REQUEST_DRONE_MISSION',
        'label': 'Aerial inspection flight',
        'ig_bits': 0.80,
        'reliability': 0.80,
        'access': 0.95,
        'cost_inr': 800.0,
        'time_min': 20.0,
        'eligible': False,  # Feature-flagged off by default in PRD v5.0 Section 11
        'why': 'Optional module (O1) - feature flagged off by default'
    }
}


def score_action(ig, r, a, cost_inr, time_min):
    """
    PRD v5.0 Section 7 deterministic scoring:
    S(a) = IG(a) * R * A - 0.35 * Cn - 0.15 * Tn
    where Cn = min(cost_inr / 2000, 1), Tn = min(time_min / 120, 1).
    """
    cn = min(max(0.0, cost_inr) / 2000.0, 1.0)
    tn = min(max(0.0, time_min) / 120.0, 1.0)
    score = (ig * r * a) - (0.35 * cn) - (0.15 * tn)
    return round(score, 4)


def rank_next_checks(balance, candidate_actions=None, drone_enabled=False):
    """
    Legacy Developer 1 scoring fixture, retained for compatibility.
    Runtime recommendations use backend.ranking and its persistence/ground gates.
    Includes hard gates, score calculation, sensitivity analysis (+/-20%), and abstention rule.
    """
    # Hard gate 1: Data-quality issue or unobserved boundary blocks loss dispatch
    if balance.get('validity') != 'valid':
        reasons = balance.get('invalid_reasons', [])
        return {
            'recommendation': 'REPAIR_OR_VALIDATE_DATA',
            'action_name': 'REQUEST_MISSING_DATA',
            'reason': f"Boundary cannot be reconciled: {'; '.join(reasons) if reasons else 'data incomplete'}. Withhold loss dispatch.",
            'candidates': [],
            'sensitivity': {'stable': True, 'competing': []},
            'abstain': True,
            'missing_evidence_question': 'Which meters are missing, misaligned, or unverified?'
        }

    # Hard gate 2: Within model range or negative residual
    if not balance.get('qualifies'):
        if balance.get('negative_review'):
            return {
                'recommendation': 'MODEL_EQUIPMENT_OR_TOPOLOGY_CHECK',
                'action_name': 'REQUEST_TOPOLOGY_CHECK',
                'reason': 'Residual is negative beyond uncertainty threshold; mapping, export or meter review required.',
                'candidates': [],
                'sensitivity': {'stable': True, 'competing': []},
                'abstain': False,
                'missing_evidence_question': 'Is consumer-to-transformer mapping or metering polarity incorrect?'
            }
        return {
            'recommendation': 'NO_INVESTIGATION',
            'action_name': 'ABSTAIN_NO_ACTION',
            'reason': 'Input and metered outputs reconcile within configured loss and uncertainty thresholds.',
            'candidates': [],
            'sensitivity': {'stable': True, 'competing': []},
            'abstain': True,
            'missing_evidence_question': None
        }

    # Active abnormal section: rank available candidate actions
    actions = NEXT_CHECK_CATALOG if candidate_actions is None else candidate_actions
    candidates = []

    for key, spec in actions.items():
        is_eligible = spec.get('eligible', True)
        if key == 'aerial_view' and drone_enabled:
            is_eligible = True
        if not is_eligible:
            candidates.append({
                'id': key,
                'label': spec['label'],
                'action_name': spec.get('action_name', key),
                'score': None,
                'eligible': False,
                'ineligible_reason': 'Module not enabled (feature-flag off)'
            })
            continue

        base_score = score_action(
            spec['ig_bits'], spec['reliability'], spec['access'],
            spec['cost_inr'], spec['time_min']
        )

        # Sensitivity bounds: vary IG, R, A, C, T by +/- 20%
        score_low = score_action(
            spec['ig_bits'] * 0.8,
            max(0.0, spec['reliability'] * 0.8),
            max(0.0, spec['access'] * 0.8),
            spec['cost_inr'] * 1.2,
            spec['time_min'] * 1.2
        )
        score_high = score_action(
            min(1.0, spec['ig_bits'] * 1.2),
            min(1.0, spec['reliability'] * 1.2),
            min(1.0, spec['access'] * 1.2),
            spec['cost_inr'] * 0.8,
            spec['time_min'] * 0.8
        )

        candidates.append({
            'id': key,
            'label': spec['label'],
            'action_name': spec.get('action_name', key),
            'score': base_score,
            'score_range': [score_low, score_high],
            'eligible': True,
            'ig_bits': spec['ig_bits'],
            'reliability': spec['reliability'],
            'access': spec['access'],
            'cost_inr': spec['cost_inr'],
            'time_min': spec['time_min'],
            'why': spec['why']
        })

    eligible_cands = [c for c in candidates if c['eligible'] and c['score'] is not None]
    eligible_cands.sort(key=lambda x: x['score'], reverse=True)

    # Policy threshold: best score > 0.05, otherwise abstain
    if not eligible_cands or eligible_cands[0]['score'] <= 0.05:
        return {
            'recommendation': 'ABSTAIN_NO_ACTION',
            'action_name': 'ABSTAIN_NO_ACTION',
            'reason': 'No feasible check improves the decision with score > 0.05 threshold.',
            'candidates': candidates,
            'sensitivity': {'stable': True, 'competing': []},
            'abstain': True,
            'missing_evidence_question': 'What high-information low-cost observation can be obtained?'
        }

    winner = eligible_cands[0]
    # Check if competitor is within 0.05 (tie / competing actions go to human choice)
    competing = [c['label'] for c in eligible_cands[1:]
                 if c['score_range'][1] >= winner['score_range'][0] - 0.05]

    return {
        'recommendation': winner['action_name'],
        'action_name': winner['action_name'],
        'label': winner['label'],
        'reason': winner['why'],
        'winner_score': winner['score'],
        'candidates': candidates,
        'sensitivity': {
            'stable': len(competing) == 0,
            'competing': competing
        },
        'abstain': False,
        'missing_evidence_question': 'Does physical inspection confirm unmetered connection or overhead bypass?'
    }


def expected_loss(kind, output):
    # a [kW] and b [1/kW]; interval = 0.25 h; output / .25 gives kW.
    a,b=COEFFICIENTS[kind]
    return a*.25+b*(output/.25)**2*.25


def balance_terms(input_kwh,output_kwh,authorized_kwh,loss_kwh):
    if input_kwh is None or output_kwh is None or loss_kwh is None: return None,None
    residual=input_kwh-output_kwh-authorized_kwh-loss_kwh
    return residual,residual/max(input_kwh,1e-6)

def reconcile(run_id, seq, readings, sigmas=None, installed=None, coverage_mode='full'):
    """Reconcile the installed cut; legacy coverage modes remain supported.

    Explicit installed-meter inventories always constrain observability. Legacy modes
    additionally restrict eligible boundaries; they cannot restore absent meters.

    """
    if coverage_mode not in COVERAGE_MODES:
        raise ValueError('Unknown coverage mode')
    result=[]
    for s in SECTIONS:
        sid=s['id']; cut=CHILDREN[sid]; validate_cut(sid,cut)
        observability,absent=coverage.observability(sid,cut,installed)
        if observability=='INSUFFICIENT_OBSERVABILITY':
            result.append(dict(id=f'balance-{run_id}-{seq}-{sid}',run_id=run_id,boundary_asset_id=sid,
                interval_start=readings[sid]['interval_start'] if sid in readings else None,
                interval_end=readings[sid]['interval_end'] if sid in readings else None,
                input_meter_id=s['meter_id'],output_meter_ids=[BY_ID[x]['meter_id'] for x in cut],
                input_kwh=None,output_sum_kwh=None,authorized_unmetered_kwh=0.0,expected_loss_kwh=None,
                residual_kwh=None,residual_ratio=None,sigma_kwh=None,threshold_kwh=None,
                completeness_ratio=0.0,validity='insufficient_observability',
                invalid_reasons=[f'{BY_ID[a]["id"]}: meter not installed under this coverage profile' for a in absent],
                uninstrumented_asset_ids=absent,topology_version=VERSION,analysis_version=ANALYSIS_VERSION,
                coverage_mode=coverage_mode,negative_review=False,qualifies=False))
            continue
        rs=[readings[x] for x in [sid]+cut]
        reasons=[]

        # Coverage mode gate
        if coverage_mode == 'feeder_only' and s['kind'] != 'feeder':
            reasons.append('insufficient_observability: feeder-only coverage mode')
        elif coverage_mode == 'feeder_and_dt_only' and s['kind'] == 'branch':
            reasons.append('insufficient_observability: feeder-and-DT-only coverage mode')

        for r in rs:
            if r['quality']!='valid' or r['energy_import_kwh'] is None:
                reasons.append(r['meter_id']+': '+r['quality'])
            elif not math.isfinite(r['energy_import_kwh']) or r['energy_import_kwh']<0:
                reasons.append(r['meter_id']+': invalid energy')
            if r['topology_version']!=VERSION:
                reasons.append(r['meter_id']+': topology mismatch')
            if r['interval_start']!=rs[0]['interval_start'] or r['interval_end']!=rs[0]['interval_end']:
                reasons.append(r['meter_id']+': interval mismatch')
            if r.get('energy_export_kwh',0)!=0:
                reasons.append(r['meter_id']+': unsupported export flow')

        complete=sum(r['quality']=='valid' and r['energy_import_kwh'] is not None for r in rs)/len(rs)
        ein=rs[0]['energy_import_kwh']

        if any(r in reasons for r in ['insufficient_observability: feeder-only coverage mode', 'insufficient_observability: feeder-and-DT-only coverage mode']):
            out=None; loss=None; residual=None; ratio=None
            validity='insufficient_observability'
        elif reasons:
            out=None; loss=None; residual=None; ratio=None
            validity='data_incomplete'
        else:
            out=sum(r['energy_import_kwh'] for r in rs[1:])
            loss=expected_loss(s['kind'],out)
            residual,ratio=balance_terms(ein,out,0,loss)
            validity='valid'

        sigma=max(.015,(sigmas or {}).get(sid,.015))
        threshold=max(.25,.08*(ein or 0),3*sigma)
        qualifies=validity=='valid' and residual is not None and residual>threshold

        result.append(dict(
            id=f'balance-{run_id}-{seq}-{sid}',
            run_id=run_id,
            boundary_asset_id=sid,
            interval_start=rs[0]['interval_start'],
            interval_end=rs[0]['interval_end'],
            input_meter_id=s['meter_id'],
            output_meter_ids=[BY_ID[x]['meter_id'] for x in cut],
            input_kwh=ein,
            output_sum_kwh=out,
            authorized_unmetered_kwh=0.0,
            expected_loss_kwh=loss,
            residual_kwh=residual,
            residual_ratio=ratio,
            sigma_kwh=sigma,
            threshold_kwh=threshold,
            completeness_ratio=complete if validity != 'insufficient_observability' else 0.0,
            validity=validity,
            invalid_reasons=reasons,
            coverage_mode=coverage_mode,
            topology_version=VERSION,
            analysis_version=ANALYSIS_VERSION,
            negative_review=bool(residual is not None and residual < -threshold),
            qualifies=qualifies
        ))
    return result


def detect(run_id, seq, balances, readings, previous, streaks, baseline):
    alerts={a['boundary_asset_id']:dict(a) for a in previous}
    quality=[]
    for b in balances:
        sid=b['boundary_asset_id']; streaks[sid]=streaks.get(sid,0)+1 if b['qualifies'] else 0
        if b['validity']=='insufficient_observability':
            # A permanent instrumentation limit, not a repairable reading fault.
            quality.append(dict(asset_id=sid,kind='observability',
                reason='; '.join(b['invalid_reasons']),
                recommended='Install sectional measurement or reconcile at a complete ancestor cut.'))
        elif b['validity']!='valid' or b['negative_review']:
            quality.append(dict(asset_id=sid,kind='data_quality',reason='; '.join(b['invalid_reasons']) or 'Negative residual: mapping, export or meter review required'))
        if streaks[sid]>=3:
            a=alerts.get(sid) or dict(id=f'alert-{run_id}-{sid}',run_id=run_id,boundary_asset_id=sid,first_interval=seq-2,rule_id='persistent_excess_residual',rule_version=RULE_VERSION,priority='high',reason_codes=['residual_above_uncertainty_threshold','three_consecutive_valid_intervals'],balance_ids=[],candidate_meter_ids=[])
            a.update(last_interval=seq,consecutive_intervals=streaks[sid],status='active',unexplained_kwh=b['residual_kwh'],residual_ratio=b['residual_ratio'])
            if not a['balance_ids']: a['balance_ids']=[f'balance-{run_id}-{i}-{sid}' for i in range(seq-2,seq)]
            a['balance_ids']=a['balance_ids']+[b['id']]
            a['candidate_meter_ids']=[]
            if BY_ID[sid]['kind']=='branch':
                for hid in CHILDREN[sid]:
                    expected=baseline[hid][seq%96]; r=readings[hid]
                    if expected>=.15 and r['quality']=='valid' and r['energy_import_kwh']<.5*expected:
                        # only a watch reason; caller supplies consecutive meter streak separately if needed
                        a['candidate_meter_ids'].append(BY_ID[hid]['meter_id'])
            alerts[sid]=a
        elif sid in alerts:
            alerts[sid]['status']=('insufficient_observability' if b['validity']=='insufficient_observability'
                                   else 'data_incomplete' if b['validity']!='valid' else 'cleared')
    return list(alerts.values()),quality,streaks
