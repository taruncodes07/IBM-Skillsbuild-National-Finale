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


def ingest_readings_csv(csv_content_or_path):
    """
    Ingests and validates CSV readings per Shared Contract and PRD v5.0 Section 9:
    Required columns: stream_id, timestamp, value, unit, quality
    Optional columns: asset_id, source_file, source_row, is_synthetic

    Preserves missing values as None, validates units, and detects duplicate readings.
    """
    import csv
    import io
    import math
    from pathlib import Path

    if isinstance(csv_content_or_path, Path):
        text = csv_content_or_path.read_text(encoding='utf-8-sig')
    else:
        text = str(csv_content_or_path)
        # CSV text may exceed Windows path limits or contain invalid path characters.
        if '\n' not in text and '\r' not in text and ',' not in text:
            text = Path(text).read_text(encoding='utf-8-sig')
    text = text.lstrip('\ufeff')

    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames:
        raise ValueError('Empty or invalid CSV: missing header row')

    field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
    stream_col = field_map.get('stream_id') or field_map.get('meter_id')
    time_col = field_map.get('timestamp') or field_map.get('interval_start')
    val_col = field_map.get('value') or field_map.get('energy_import_kwh') or field_map.get('energy_kwh')
    unit_col = field_map.get('unit')
    quality_col = field_map.get('quality')

    if not stream_col or not time_col or not val_col:
        raise ValueError(f"Missing required columns in CSV header. Found: {reader.fieldnames}")

    records = []
    seen_keys = set()
    duplicates = []
    errors = []

    for row_idx, row in enumerate(reader, start=2):
        stream_id = (row.get(stream_col) or '').strip()
        timestamp = (row.get(time_col) or '').strip()
        val_str = (row.get(val_col) or '').strip()
        unit = (row.get(unit_col) or 'kwh').strip().lower() if unit_col else 'kwh'
        quality = (row.get(quality_col) or 'valid').strip().lower() if quality_col else 'valid'

        if not stream_id or not timestamp:
            errors.append(f"Row {row_idx}: stream_id and timestamp must not be empty")
            continue

        try:
            parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if parsed_time.tzinfo is None:
                raise ValueError('Timestamp needs an explicit timezone')
            normalized_time = parsed_time.astimezone(timezone.utc).isoformat()
        except ValueError:
            errors.append(f"Row {row_idx}: invalid or timezone-naive timestamp '{timestamp}'")
            continue

        # Duplicate detection within the observation stream
        key = (stream_id, normalized_time)
        duplicate = key in seen_keys
        if key in seen_keys:
            duplicates.append(dict(row=row_idx, stream_id=stream_id, timestamp=timestamp))
        seen_keys.add(key)

        # Unit verification
        if unit not in ('kwh', 'wh'):
            errors.append(f"Row {row_idx}: unsupported unit '{unit}', expected 'kWh' or 'Wh'")
            continue

        # Missing value preservation
        if val_str.lower() in ('', 'null', 'none', 'nan', 'na'):
            value = None
            if quality == 'valid':
                quality = 'missing'
        else:
            try:
                raw_val = float(val_str)
                if not math.isfinite(raw_val) or raw_val < 0:
                    value = None
                    quality = 'invalid'
                else:
                    value = raw_val * 0.001 if unit == 'wh' else raw_val
            except ValueError:
                value = None
                quality = 'invalid'

        if duplicate:
            quality = 'duplicate'

        records.append(dict(
            stream_id=stream_id,
            timestamp=timestamp,
            value=value,
            unit='kWh',
            quality=quality,
            source_row=row_idx,
            is_synthetic=True
        ))

    return dict(
        records=records,
        total_rows=len(records),
        valid_count=sum(1 for r in records if r['quality'] == 'valid' and r['value'] is not None),
        missing_count=sum(1 for r in records if r['value'] is None),
        duplicates_detected=duplicates,
        validation_errors=errors,
        unique_streams=sorted(list({r['stream_id'] for r in records}))
    )
