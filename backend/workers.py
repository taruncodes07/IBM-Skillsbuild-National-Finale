"""Pure analytical workers. No simulator, private truth or network access."""
import hashlib
import json
import statistics
import time
from typing import get_args

from .contracts import Action, WorkerResult
from .topology import BY_ID, CHILDREN

VERSION='workers-1.0'


def execute(snapshot,area_id,past_frames):
    started=time.perf_counter()
    balance=next(b for b in snapshot['balances'] if b['boundary_asset_id']==area_id)
    source=snapshot['run'].get('source',{})
    digest=source.get('source_hash') or hashlib.sha256(json.dumps(snapshot['readings'],sort_keys=True).encode()).hexdigest()
    prefix=f"{snapshot['run']['id']}-{snapshot['seq']}-{area_id}"
    results=[]
    def result(worker,status,findings,missing=(),assumptions=(),uncertainty=None):
        item=WorkerResult(worker=worker,status=status,findings=findings,
                          evidence_ids=[f'ev-{prefix}-{worker}'],input_hashes=[digest],
                          missing_inputs=list(missing),assumptions=list(assumptions),
                          uncertainty=uncertainty or {},model_or_rule_version=VERSION,
                          elapsed_ms=(time.perf_counter()-started)*1000).model_dump()
        results.append(item)
        return item

    valid=balance['validity']=='valid'
    raw=None if balance['input_kwh'] is None or balance['output_sum_kwh'] is None else balance['input_kwh']-balance['output_sum_kwh']
    result('W1','OK' if valid else 'INSUFFICIENT_DATA',
           dict(balance_id=balance['id'],area_id=area_id,input_kwh=balance['input_kwh'],
                output_kwh=balance['output_sum_kwh'],raw_gap_kwh=raw,
                authorized_unmetered_kwh=balance['authorized_unmetered_kwh'],
                coverage_fraction=balance['completeness_ratio'],quality_flags=balance['invalid_reasons'],
                input_meter_id=balance['input_meter_id'],output_meter_ids=balance['output_meter_ids']),
           missing=balance['invalid_reasons'])

    central=balance['expected_loss_kwh']
    low=high=residual_low=residual_high=None
    if valid and central is not None:
        low=max(0,central*.5);high=central*1.5
        meter_bound=3*balance['sigma_kwh']
        residual_low=raw-balance['authorized_unmetered_kwh']-high-meter_bound
        residual_high=raw-balance['authorized_unmetered_kwh']-low+meter_bound
    result('W2','WARNING' if valid else 'INSUFFICIENT_DATA',
           dict(technical_loss_kwh_low=low,technical_loss_kwh_central=central if valid else None,
                technical_loss_kwh_high=high,residual_kwh_low=residual_low,
                residual_kwh_central=balance['residual_kwh'] if valid else None,
                residual_kwh_high=residual_high,threshold_kwh=balance['threshold_kwh'],
                model_validity='ASSUMED_REDUCED_ORDER' if valid else 'DATA_INCOMPLETE'),
           missing=['measured_voltage','power_factor','line_impedance','transformer_specs'],
           assumptions=['Technical-loss range is 0.5-1.5 times the configured reduced-order estimate.',
                        'Meter residual bound uses 3 times the development residual sigma; it is not a calibrated 95% confidence interval.'],
           uncertainty=dict(kind='ASSUMPTION_BOUNDS',physical_calibration='NOT_AVAILABLE'))

    household_ids=[a for a in snapshot['readings'] if BY_ID[a]['kind']=='household' and is_descendant(a,area_id)]
    shifts=[];enough=0
    for hid in household_ids:
        reading=snapshot['readings'][hid]
        prior=[frame['readings'][hid]['energy_import_kwh'] for frame in past_frames
               if frame['seq']<snapshot['seq'] and (snapshot['seq']-frame['seq'])%96==0
               and hid in frame['readings'] and frame['readings'][hid]['quality']=='valid'
               and frame['readings'][hid]['energy_import_kwh'] is not None]
        if len(prior)<3 or reading['quality']!='valid' or reading['energy_import_kwh'] is None:continue
        enough+=1;baseline=statistics.median(prior)
        if baseline>=.15 and reading['energy_import_kwh']<baseline*.5:
            shifts.append(dict(meter_id=reading['meter_id'],reason='Consumption drop against earlier same-time observations',baseline_kwh=baseline))
    result('W3','OK' if enough else 'INSUFFICIENT_DATA',
           dict(consumption_shifts=shifts,baseline_ready_meters=enough,
                billing_mismatch_kwh=None,billing_status='NOT_AVAILABLE',collection_status='COLLECTION_UNKNOWN',
                history_status='READY' if enough else 'INSUFFICIENT_HISTORY'),
           missing=['matched_billing_records','payment_records']+([] if enough else ['three_prior_same_time_valid_intervals']),
           assumptions=['Baseline uses only earlier days at the same 15-minute slot. Consumption changes do not establish bypass or intent.'])

    significant=valid and residual_low is not None and residual_low>balance['threshold_kwh']
    candidates=[area_id] if significant else []
    # Only measured descendant boundaries may justify a smaller region.
    finer=[b['boundary_asset_id'] for b in snapshot['balances'] if b['validity']=='valid'
           and b['qualifies'] and is_descendant(b['boundary_asset_id'],area_id)]
    branches=[sid for sid in finer if BY_ID[sid]['kind']=='branch']
    if significant and branches:candidates=branches
    level={'feeder':'FEEDER','transformer':'DT_AREA','branch':'BRANCH'}[BY_ID[area_id]['kind']]
    result('W4','OK' if valid else 'INSUFFICIENT_DATA',
           dict(localization_level='BRANCH' if branches and significant else level if significant else 'NONE',
                candidate_area_ids=candidates,inspection_eligible=False,visual_status='DEFERRED',
                reason='Optional drone/CV is deferred. Meter, topology or human field review remains available.',
                household_attribution='UNSUPPORTED'),
           missing=['verified_overhead_inspection_capability'],
           assumptions=['Localization stops at measured boundaries; no pole or household guilt is inferred.'])

    persistent=any(a['status']=='active' and a['boundary_asset_id']==area_id for a in snapshot['alerts'])
    status=('DATA_INCOMPLETE' if not valid else 'UNEXPLAINED_ENERGY' if significant and persistent
            else 'REVIEW_MODEL_OR_TOPOLOGY' if balance['negative_review'] else
            'PERSISTENCE_PENDING' if significant else 'WITHIN_MODEL_RANGE')
    evidence_ids=[eid for worker in results for eid in worker['evidence_ids']]
    candidates_causes=[]
    if status=='UNEXPLAINED_ENERGY':
        candidates_causes=[dict(cause=c,supporting_evidence_ids=evidence_ids[:2],
                                information_gaps=['Independent field or meter verification'])
                           for c in ['METER_FAULT','UNMETERED_LOAD','TECHNICAL_MODEL_ERROR','TOPOLOGY_MISMATCH','AUTHORIZED_UNMETERED_LOAD']]
    fusion=dict(diagnostic_status=status,candidates=candidates_causes,evidence_ids=evidence_ids,
                unresolved_conflicts=['Accounting does not identify a unique cause.'] if candidates_causes else [],
                allowed_inference='Investigation recommendation only; no theft verdict.',version=VERSION)
    return results,fusion


def is_descendant(asset_id,area_id):
    parent=BY_ID[asset_id]['parent_id']
    while parent:
        if parent==area_id:return True
        parent=BY_ID[parent]['parent_id']
    return False


def rule_plan(area_id,workers,fusion):
    status=fusion['diagnostic_status']
    action=('REQUEST_MISSING_DATA' if status=='DATA_INCOMPLETE' else
            'REQUEST_TOPOLOGY_CHECK' if status=='REVIEW_MODEL_OR_TOPOLOGY' else
            'REQUEST_METER_REVIEW' if status=='UNEXPLAINED_ENERGY' else 'ABSTAIN_NO_ACTION')
    reasons=dict(REQUEST_MISSING_DATA='Restore missing or invalid measurements before interpreting the cut.',
                 REQUEST_TOPOLOGY_CHECK='Check mapping and model assumptions behind the signed residual.',
                 REQUEST_METER_REVIEW='Persistent unexplained energy has several possible causes. Obtain an independent meter/field check.',
                 ABSTAIN_NO_ACTION='Available evidence does not support a persistent significant unexplained residual.')
    return dict(next_action=action,target_area_id=area_id,evidence_ids=fusion['evidence_ids'],
                competing_causes=[c['cause'] for c in fusion['candidates']],
                justification=reasons[action],requires_human_approval=action not in ('ABSTAIN_NO_ACTION',))


def validate_policy(proposal,area_id,workers,fusion):
    known=set(fusion['evidence_ids'])
    areas={area_id}|set(workers[3]['findings']['candidate_area_ids'])
    if not set(proposal.evidence_ids)<=known:return dict(allowed=False,reason='Unknown evidence reference')
    if proposal.target_area_id not in areas:return dict(allowed=False,reason='Target exceeds supported localization')
    if fusion['diagnostic_status'] in ('WITHIN_MODEL_RANGE','PERSISTENCE_PENDING'):
        if proposal.next_action not in ('ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY'):
            return dict(allowed=False,reason='NO_PERSISTENT_SIGNAL: normal or nonpersistent measurements do not justify additional diagnostic checks')
        return dict(allowed=True,reason='Only abstention or a summary of existing evidence is authorized. No diagnostic check is authorized for normal or nonpersistent measurements.')
    if fusion['diagnostic_status']=='DATA_INCOMPLETE' and proposal.next_action not in ('REQUEST_MISSING_DATA','REQUEST_TOPOLOGY_CHECK','GENERATE_CASE_SUMMARY','ABSTAIN_NO_ACTION'):
        return dict(allowed=False,reason='Incomplete measurements block diagnostic escalation')
    if proposal.next_action=='REQUEST_BILLING_AUDIT' and workers[2]['findings']['billing_status']=='NOT_AVAILABLE':
        return dict(allowed=False,reason='Billing records are unavailable; request data instead')
    return dict(allowed=True,reason='Registered action and evidence validated; external checks remain human tasks')


def permitted_actions(workers,fusion):
    """Planner affordances mirror policy, while independent policy checks remain mandatory."""
    if fusion['diagnostic_status'] in ('WITHIN_MODEL_RANGE','PERSISTENCE_PENDING'):
        return ['ABSTAIN_NO_ACTION','GENERATE_CASE_SUMMARY']
    if fusion['diagnostic_status']=='DATA_INCOMPLETE':
        return ['REQUEST_MISSING_DATA','REQUEST_TOPOLOGY_CHECK','GENERATE_CASE_SUMMARY','ABSTAIN_NO_ACTION']
    actions=list(get_args(Action))
    if workers[2]['findings']['billing_status']=='NOT_AVAILABLE':actions.remove('REQUEST_BILLING_AUDIT')
    return actions
