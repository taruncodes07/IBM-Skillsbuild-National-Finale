"""Observation adapters. Development fixtures never impersonate utility data."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import json

from .simulation import generate
from .topology import ASSETS, VERSION

IST = timezone(timedelta(hours=5, minutes=30))
MONTH_START = datetime(2022, 9, 1, tzinfo=IST)
INTERVALS_PER_DAY = 96
MONTH_INTERVALS = 30 * INTERVALS_PER_DAY
FIXTURE_VERSION = 'september-development-1'
# Deliberate development quality controls, unrelated to the unavailable frozen CSV.
FIXTURE_GAPS = {95: 'household-07', 96: 'household-08', 2111: 'household-18'}


def manifest(seed=42):
    config = dict(version=FIXTURE_VERSION, seed=seed, topology_version=VERSION,
                  start=MONTH_START.isoformat(), interval_count=MONTH_INTERVALS,
                  gaps=FIXTURE_GAPS)
    # Hash the generator implementation too, so changing it invalidates cached results.
    from pathlib import Path
    implementation = Path(__file__).read_bytes() + Path(__file__).with_name('simulation.py').read_bytes()
    digest = hashlib.sha256(implementation + json.dumps(config, sort_keys=True).encode()).hexdigest()
    return dict(id=f'dev-september-2022-{seed}', source_kind='DEV_FIXTURE',
                label='September 2022 development fixture', source_hash=digest,
                hash_kind='GENERATOR_AND_CONFIG', source_status='DEVELOPMENT_ONLY',
                official_source_status='PENDING', interval_count=MONTH_INTERVALS,
                meter_count=38, expected_reading_count=MONTH_INTERVALS * 38,
                fixture_missing_readings=len(FIXTURE_GAPS), interval_minutes=15,
                period_start=MONTH_START.isoformat(),
                period_end=(MONTH_START + timedelta(days=30)).isoformat(),
                timezone='Asia/Kolkata', generator_version=FIXTURE_VERSION,
                baseline='Seven generated prior days; development fixture only',
                disclosure='Generated test readings, not BESCOM telemetry or the frozen PRD CSV.')


class DevelopmentMonthSource:
    def __init__(self, seed=42):
        self.seed = seed
        self.manifest = manifest(seed)

    def read_interval(self, sequence):
        if not 0 <= sequence < MONTH_INTERVALS:
            raise ValueError('Interval is outside September 2022')
        frame = generate(self.seed, sequence, [])
        for reading in frame['readings'].values():
            reading['source_kind'] = 'DEV_FIXTURE'
        if sequence in FIXTURE_GAPS:
            reading = frame['readings'][FIXTURE_GAPS[sequence]]
            reading.update(energy_import_kwh=None, quality='missing')
        return frame


@lru_cache(maxsize=8)
def month_summary(seed):
    """Per-day input and delivered energy use disjoint feeder/household cuts."""
    source = DevelopmentMonthSource(seed)
    feeder_ids = [a['id'] for a in ASSETS if a['kind'] == 'feeder']
    household_ids = [a['id'] for a in ASSETS if a['kind'] == 'household']
    days = []
    for day in range(30):
        valid = 0
        feeder_sum = household_sum = 0.0
        for seq in range(day * 96, (day + 1) * 96):
            readings = source.read_interval(seq)['readings']
            valid += sum(r['quality'] == 'valid' and r['energy_import_kwh'] is not None for r in readings.values())
            feeder_sum += sum(readings[k]['energy_import_kwh'] for k in feeder_ids)
            household_sum += sum(readings[k]['energy_import_kwh'] or 0 for k in household_ids)
        expected = 96 * 38
        days.append(dict(date=(MONTH_START + timedelta(days=day)).date().isoformat(),
                         first_sequence=day * 96, interval_count=96,
                         valid_readings=valid, expected_readings=expected,
                         missing_readings=expected-valid, coverage_fraction=valid/expected,
                         household_sum_complete=valid == expected,
                         feeder_input_kwh=feeder_sum,
                         household_valid_kwh=household_sum))
    return dict(source=source.manifest, days=days,
                aggregation_note='Feeder input and valid household energy are separate cuts; missing values are excluded, never imputed.')
