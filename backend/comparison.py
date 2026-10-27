"""Paired presentation simulation. Detection is observed; repair is an assumption.

No cases, operational runs, provider calls or source datasets are modified here.
Simulator truth is used only to score physical losses, never to trigger detection.
"""
import statistics

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from . import analytics, coverage
from .simulation import generate, stamp
from .topology import ASSETS


class ComparisonInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    seed: int = Field(default=42, ge=0, le=1000000)
    scenario: Literal['visible_unmetered_load', 'hidden_bypass', 'clean'] = 'visible_unmetered_load'
    repair_delay_minutes: int = Field(default=60, ge=0, le=1440, multiple_of=15)
    repair_effectiveness: float = Field(default=.9, ge=0, le=1, allow_inf_nan=False)
    coverage_profile: Literal[tuple(coverage.PROFILES)] = coverage.DEFAULT_PROFILE


def compare(body: ComparisonInput):
    installed = coverage.installed_meters(body.coverage_profile, ASSETS)
    # The same seven-day calibration as operational runs; only clean prior readings.
    residuals = {}
    slots = {a['id']: [[] for _ in range(96)] for a in ASSETS if a['kind'] == 'household'}
    for seq in range(-672, 0):
        readings = generate(body.seed, seq, [])['readings']
        for key, values in slots.items():
            values[seq % 96].append(readings[key]['energy_import_kwh'])
        for balance in analytics.reconcile('comparison', seq, readings, installed=installed):
            if balance['residual_kwh'] is not None:
                residuals.setdefault(balance['boundary_asset_id'], []).append(balance['residual_kwh'])
    sigmas = {key: max(.015, statistics.stdev(values)) for key, values in residuals.items()}
    baseline = {key: [statistics.mean(slot) for slot in values] for key, values in slots.items()}
    incident_start = 8  # 02:00 IST, after a visible clean opening.
    event = dict(type=body.scenario, target_asset_id='branch-03', start=incident_start, end=96, severity=1.2)
    incidents = [] if body.scenario == 'clean' else [event]
    feeders = [a['id'] for a in ASSETS if a['kind'] == 'feeder']
    streaks, previous = {}, []
    detection = repair = None
    cumulative_without = cumulative_with = 0.0
    points = []
    for seq in range(96):
        untreated = generate(body.seed, seq, incidents)
        balances = analytics.reconcile('comparison', seq, untreated['readings'], sigmas, installed)
        # No truth/incident labels are supplied to the real detector.
        alerts, _, streaks = analytics.detect('comparison', seq, balances, untreated['readings'], previous, streaks, baseline)
        previous = alerts
        if detection is None and any(a['boundary_asset_id'] == 'branch-03' and a['status'] == 'active' for a in alerts):
            detection = seq
            # Detection happens at interval END. Even a zero-delay intervention starts next interval.
            repair = seq + 1 + body.repair_delay_minutes // 15
        repaired = repair is not None and seq >= repair
        treated_events = [dict(event, severity=event['severity'] * (1 - body.repair_effectiveness))] if repaired and incidents else incidents
        treated = generate(body.seed, seq, treated_events)
        delivered = sum(untreated['truth']['actual_demand_kwh'].values())
        without = sum(untreated['truth']['physical_kwh'][key] for key in feeders) - delivered
        with_system = sum(treated['truth']['physical_kwh'][key] for key in feeders) - delivered
        extra = event['severity'] if incidents and seq >= incident_start else 0.0
        extra_with = extra * (1 - body.repair_effectiveness) if repaired else extra
        cumulative_without += without
        cumulative_with += with_system
        branch_balance = next(b for b in balances if b['boundary_asset_id'] == 'branch-03')
        points.append(dict(sequence=seq, elapsed_minutes=(seq + 1) * 15, timestamp=stamp(seq + 1),
                           without_kwh=without, with_kwh=with_system,
                           unmetered_without_kwh=extra, unmetered_with_kwh=extra_with,
                           technical_without_kwh=without-extra, technical_with_kwh=with_system-extra_with,
                           delivered_kwh=delivered, cumulative_without_kwh=cumulative_without,
                           cumulative_with_kwh=cumulative_with, saved_kwh=cumulative_without-cumulative_with,
                           residual_kwh=branch_balance['residual_kwh'], threshold_kwh=branch_balance['threshold_kwh'],
                           status='repair_active' if repaired else 'detected' if detection is not None else 'monitoring'))
    return dict(version='paired-comparison-1', assumptions=body.model_dump(), interval_minutes=15,
                target_asset_id='branch-03', incident_start_sequence=incident_start if incidents else None,
                detection_sequence=detection, repair_sequence=repair if repair is not None and repair < 96 else None,
                repair_within_horizon=repair is not None and repair < 96,
                detection_timestamp=stamp(detection+1) if detection is not None else None,
                repair_timestamp=stamp(repair) if repair is not None and repair < 96 else None,
                source=dict(kind='PAIRED_GENERATED_SIMULATION', seed=body.seed,
                            project_dataset='Real-world-derived data with partially synthesized columns (team-provided provenance).',
                            runtime='This comparison uses the deterministic network simulator, not a replay of the supplied CSV.'),
                methodology='Total network loss = disjoint feeder physical input minus delivered household energy. Technical losses remain. The observed three-interval detector triggers a simulated crew repair; Grid Trace alone does not remove energy loss.',
                points=points)
