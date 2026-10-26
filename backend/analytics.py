"""Observed inputs only. This module must never import the simulator or truth store."""
import math
from . import coverage
from .topology import BY_ID, CHILDREN, SECTIONS, VERSION, validate_cut

RULE_VERSION = 'section-1.0'
ANALYSIS_VERSION = 'accounting-1.0'
COEFFICIENTS = {'branch':(0.035,0.0012),'transformer':(0.045,0.00012),'feeder':(0.08,0.00004)}

def expected_loss(kind, output):
    # a [kW] and b [1/kW]; interval = 0.25 h; output / .25 gives kW.
    a,b=COEFFICIENTS[kind]
    return a*.25+b*(output/.25)**2*.25

def balance_terms(input_kwh,output_kwh,authorized_kwh,loss_kwh):
    if input_kwh is None or output_kwh is None or loss_kwh is None: return None,None
    residual=input_kwh-output_kwh-authorized_kwh-loss_kwh
    return residual,residual/max(input_kwh,1e-6)

def reconcile(run_id, seq, readings, sigmas=None, installed=None):
    """installed: set of asset ids whose meters exist, or None for a fully instrumented network.

    An absent meter is an observability limit, not a repairable data fault, so such a cut
    returns residual=None with validity 'insufficient_observability' and never qualifies.
    """
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
                negative_review=False,qualifies=False))
            continue
        rs=[readings[x] for x in [sid]+cut]
        reasons=[]
        for r in rs:
            if r['quality']!='valid' or r['energy_import_kwh'] is None: reasons.append(r['meter_id']+': '+r['quality'])
            elif not math.isfinite(r['energy_import_kwh']) or r['energy_import_kwh']<0: reasons.append(r['meter_id']+': invalid energy')
            if r['topology_version']!=VERSION: reasons.append(r['meter_id']+': topology mismatch')
            if r['interval_start']!=rs[0]['interval_start'] or r['interval_end']!=rs[0]['interval_end']: reasons.append(r['meter_id']+': interval mismatch')
            if r.get('energy_export_kwh',0)!=0: reasons.append(r['meter_id']+': unsupported export flow')
        complete=sum(r['quality']=='valid' and r['energy_import_kwh'] is not None for r in rs)/len(rs)
        ein=rs[0]['energy_import_kwh']; out=None if any(r['energy_import_kwh'] is None for r in rs[1:]) else sum(r['energy_import_kwh'] for r in rs[1:])
        loss=expected_loss(s['kind'],out) if out is not None else None
        residual,ratio=balance_terms(ein,out,0,loss)
        sigma=max(.015,(sigmas or {}).get(sid,.015)); threshold=max(.25,.08*(ein or 0),3*sigma)
        result.append(dict(id=f'balance-{run_id}-{seq}-{sid}',run_id=run_id,boundary_asset_id=sid,interval_start=rs[0]['interval_start'],interval_end=rs[0]['interval_end'],input_meter_id=s['meter_id'],output_meter_ids=[BY_ID[x]['meter_id'] for x in cut],input_kwh=ein,output_sum_kwh=out,authorized_unmetered_kwh=0.0,expected_loss_kwh=loss,residual_kwh=residual,residual_ratio=ratio,sigma_kwh=sigma,threshold_kwh=threshold,completeness_ratio=complete,validity='data_incomplete' if reasons else 'valid',invalid_reasons=reasons,topology_version=VERSION,analysis_version=ANALYSIS_VERSION,negative_review=bool(residual is not None and residual < -threshold),qualifies=not reasons and residual is not None and residual>threshold))
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
