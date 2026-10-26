"""Registered, read-only analytical follow-ups over frozen observations."""
import hashlib
import json
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .topology import BY_ID, CHILDREN, VERSION, validate_cut
from .workers import is_descendant

VERSION_ID='followups-1.0'
LOCAL_CHECKS=('REQUEST_ELECTRICAL_RECHECK','REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION')


class CheckResult(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id: str
    investigation_id: str
    action: Literal['REQUEST_ELECTRICAL_RECHECK','REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION']
    target_area_id: str
    status: Literal['OK','WARNING','INSUFFICIENT_DATA','FAILED']
    evidence_id: str
    input_hash: str
    signature: str
    source_kind: str
    findings: dict
    limitations: list[str]
    derived_from_evidence_ids: list[str]
    model_or_rule_version: str
    elapsed_ms: float


def signature(action,area_id,inv):
    material=dict(action=action,area_id=area_id,version=VERSION_ID,
                  frames=inv['followup_inputs']['window'],topology_version=VERSION,
                  localization=inv['workers'][3]['findings'])
    return hashlib.sha256(json.dumps(material,sort_keys=True,allow_nan=False).encode()).hexdigest()


def _electrical(area_id,inv):
    balances=[next((b for b in f['balances'] if b['boundary_asset_id']==area_id),None)
              for f in inv['followup_inputs']['window']]
    balances=[b for b in balances if b is not None]
    valid=[b for b in balances if b['validity']=='valid' and b['residual_kwh'] is not None]
    streak=0
    for b in reversed(balances):
        if b['validity']!='valid' or not b['qualifies']:break
        streak+=1
    return ('WARNING' if len(valid)!=len(balances) else 'OK',
            dict(window_intervals=len(balances),valid_intervals=len(valid),
                 incomplete_intervals=len(balances)-len(valid),
                 signed_residual_valid_sum_kwh=sum(b['residual_kwh'] for b in valid) if valid else None,
                 above_threshold_intervals=sum(bool(b['qualifies']) for b in valid),
                 trailing_qualifying_intervals=streak,
                 aggregation_status='COMPLETE_WINDOW' if len(valid)==len(balances) else 'VALID_INTERVALS_ONLY',
                 first_interval_start=balances[0]['interval_start'],last_interval_end=balances[-1]['interval_end']),
            ['Uses configured reduced-order losses; this is not a calibrated power-flow calculation.',
             'Window summaries derive from the same meters and are not independent evidence of cause.'])


def _topology(area_id,inv):
    snapshot=inv['observations'];cut=CHILDREN[area_id]
    validate_cut(area_id,cut)
    readings=[snapshot['readings'][sid] for sid in [area_id,*cut]]
    reference=readings[0]
    mismatches=[r['meter_id'] for r in readings if r['topology_version']!=VERSION]
    misaligned=[r['meter_id'] for r in readings if (r['interval_start'],r['interval_end'])!=(reference['interval_start'],reference['interval_end'])]
    return ('WARNING' if mismatches or misaligned else 'OK',
            dict(registered_cut_valid=True,registered_output_count=len(cut),
                 mismatched_meter_ids=mismatches,misaligned_meter_ids=misaligned,
                 registered_graph_status='MISMATCH_REQUIRES_REVIEW' if mismatches or misaligned else 'CONSISTENT_WITH_REGISTERED_GRAPH',
                 physical_mapping_verified=False,topology_version=VERSION),
            ['Only the registered graph and observed metadata were checked; actual field wiring remains unverified.',
             'A consistent registered cut does not rule out an incorrect real-world meter-parent mapping.'])


def _localization(area_id,inv):
    # W4's admissible measured regions constrain geometry; no renderer truth is used.
    w4_findings=inv['workers'][3]['findings'] if len(inv.get('workers',[]))>3 else {}
    regions=[sid for sid in w4_findings.get('candidate_area_ids',[])
             if sid==area_id or is_descendant(sid,area_id)]
    if not regions:
        return ('INSUFFICIENT_DATA',dict(localization_level='NONE',candidate_regions=[],
                spatial_bounds=None,reason='No significant measured region supports finer localization.'),
                ['Spatial context cannot replace missing measurements.'])
    measured=[a for a in BY_ID.values() if a['meter_id'] and any(a['id']==sid or is_descendant(a['id'],sid) for sid in regions)]
    points=[a['position_m'] for a in measured]
    bounds=dict(min_m=[min(p[i] for p in points) for i in range(3)],
                max_m=[max(p[i] for p in points) for i in range(3)],coordinate_system='LOCAL_FICTIONAL_METERS')
    levels={'feeder':'FEEDER','transformer':'DT_AREA','branch':'BRANCH'}
    return ('OK',dict(localization_level=levels[BY_ID[regions[0]]['kind']],candidate_regions=regions,
                     measured_asset_count=len(measured),spatial_bounds=bounds,
                     household_attribution='UNSUPPORTED',virtual_inspection='DEFERRED'),
            ['Bounds describe coverage of a fictional measured area, not an exact fault location.',
             'This analytical check does not launch a drone or capture new visual evidence.'])


REGISTRY=dict(zip(LOCAL_CHECKS,(_electrical,_topology,_localization)))


def execute_check(inv,action,area_id):
    started=time.perf_counter()
    sig=signature(action,area_id,inv)
    status,findings,limitations=REGISTRY[action](area_id,inv)
    return CheckResult(id=f"check-{inv['id']}-{sig[:16]}",investigation_id=inv['id'],
        action=action,target_area_id=area_id,status=status,evidence_id=f"ev-{inv['id']}-{sig[:16]}",
        input_hash=sig,signature=sig,source_kind=inv['source'].get('source_kind','SYNTHETIC_CHALLENGE'),
        findings=findings,limitations=limitations,
        derived_from_evidence_ids=[eid for worker in inv['workers'] for eid in worker['evidence_ids']],
        model_or_rule_version=VERSION_ID,elapsed_ms=(time.perf_counter()-started)*1000).model_dump()


def fuse(original,result):
    fused=json.loads(json.dumps(original))
    fused['evidence_ids']=list(dict.fromkeys([*fused['evidence_ids'],result['evidence_id']]))
    fused.setdefault('followup_observations',[]).append(dict(evidence_id=result['evidence_id'],
         action=result['action'],status=result['status'],findings=result['findings'],
         derived_from_evidence_ids=result['derived_from_evidence_ids'],
         independence='DERIVED_FROM_SAME_OBSERVATIONS',limitations=result['limitations']))
    # A recomputed summary never upgrades a hypothesis into a field-confirmed cause.
    return fused
