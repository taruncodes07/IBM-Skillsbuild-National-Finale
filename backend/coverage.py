"""Metering coverage inventory (PRD FR-03/Table 2, AC-13, Scenario H).

coverage_mode describes which meters are INSTALLED. completeness describes which
expected readings actually arrived for a cut. They are reported separately: an
uninstalled meter is a permanent observability limit, while a missing reading is a
repairable data fault. Neither is ever filled with zero.

The named profiles parameterise this fictional network using metering counts published
by the Central Electricity Authority in 'Status of Metering in the Country', reference
date 31 March 2025. Those counts describe installation at one date for a real utility.
They do not establish communication health, correct customer mapping, or that any
particular feeder is metered, and they are applied here to a synthetic topology. No
profile claims GridTrace was tested on that utility's data.
"""
import math

INVENTORY_VERSION_PREFIX = 'inventory'
KINDS = ('feeder', 'transformer', 'branch', 'household')

# fraction of assets of each kind carrying a usable meter.
PROFILES = {
    'full_sectional': dict(
        label='Full sectional (reference)',
        reference='Synthetic best case; not a published utility profile.',
        reference_date=None,
        fractions=dict(feeder=1.0, transformer=1.0, branch=1.0, household=1.0),
        note='Every boundary is instrumented. The smallest monitored branch is reconcilable.'),
    'tpddl_like': dict(
        label='Well-instrumented urban (TPDDL-like)',
        reference=('CEA metering status 31 Mar 2025: 1,286 HV + 16,929 LT feeders metered and '
                   'communicable; 4,342 of 4,986 DTs communicable (87%).'),
        reference_date='2025-03-31',
        fractions=dict(feeder=1.0, transformer=0.87, branch=1.0, household=1.0),
        note='Close to full sectional. Branch localization is usually supported.'),
    'bescom_like': dict(
        label='Urban DT gap (BESCOM-like)',
        reference=('CEA metering status 31 Mar 2025: 6,389 of 6,389 11 kV feeders metered; '
                   '114,377 of 455,604 DTs metered (25.10%, urban 65.18%); '
                   '11,745,006 consumers metered (100%).'),
        reference_date='2025-03-31',
        fractions=dict(feeder=1.0, transformer=0.65, branch=0.0, household=1.0),
        note=('Uses the published URBAN DT figure (65.18%), not the 25.10% all-network figure, '
              'because this fictional district is urban. Feeders and consumers are instrumented '
              'but no LV branch metering is published, so localization stops at the DT area.')),
    'tgspdcl_like': dict(
        label='Sparse DT coverage (TGSPDCL-like)',
        reference=('CEA metering status 31 Mar 2025: 8,713 of 8,713 11 kV feeders metered, '
                   '1,616 on NFMS (18.55%); 197,266 of 614,590 DTs metered (32.10%).'),
        reference_date='2025-03-31',
        fractions=dict(feeder=1.0, transformer=0.32, branch=0.0, household=1.0),
        note='Scenario H. Feeder-and-consumer accounting only across most of the network.'),
    'pgvcl_like': dict(
        label='No DT telemetry (PGVCL-like)',
        reference=('PGVCL BEE energy audit FY2023-24: 4,860 of 9,920 feeders communicable; '
                   '0 of 1,126,220 DTs communicable, DT meter modules inoperative since 2018. '
                   'That report states DT-wise loss computation is not possible.'),
        reference_date='2024-03-31',
        fractions=dict(feeder=0.49, transformer=0.0, branch=0.0, household=0.0),
        note=('No DT or downstream telemetry. No reconciled localization is possible; only a '
              'feeder trend or an explicit observability gap can be reported.')),
}

DEFAULT_PROFILE = 'full_sectional'


def _ordered(assets, kind):
    return sorted(a['id'] for a in assets if a['kind'] == kind and a.get('meter_id'))


def installed_meters(profile_id, assets):
    """Deterministic installed-meter set for a profile. Same profile, same assets, same set."""
    spec = PROFILES[profile_id]
    installed = set()
    for kind in KINDS:
        ids = _ordered(assets, kind)
        if not ids:
            continue
        count = int(math.floor(len(ids) * spec['fractions'][kind] + 1e-9))
        installed.update(ids[:count])
    return installed


def summary(profile_id, assets):
    spec = PROFILES[profile_id]
    installed = installed_meters(profile_id, assets)
    counts = {}
    for kind in KINDS:
        ids = _ordered(assets, kind)
        present = [i for i in ids if i in installed]
        counts[kind] = dict(total=len(ids), metered=len(present),
                            fraction=(len(present) / len(ids)) if ids else 0.0,
                            published_fraction=spec['fractions'][kind])
    return dict(profile_id=profile_id, label=spec['label'], reference=spec['reference'],
                reference_date=spec['reference_date'], note=spec['note'],
                counts=counts, installed_meter_count=len(installed),
                inventory_version=inventory_version(profile_id),
                disclosure=('Published metering counts parameterise a fictional network. They '
                            'describe installation at one date, not communication health, '
                            'mapping correctness, or any tested utility deployment.'))


def inventory_version(profile_id):
    return f'{INVENTORY_VERSION_PREFIX}-{profile_id}-1'


def observability(boundary_id, cut_ids, installed):
    """Classify a cut against the installed inventory.

    Returns (status, missing_meter_asset_ids). status is 'INSTRUMENTED' when every meter in
    the cut exists, otherwise 'INSUFFICIENT_OBSERVABILITY'.
    """
    if installed is None:
        return 'INSTRUMENTED', []
    absent = [aid for aid in [boundary_id, *cut_ids] if aid not in installed]
    return ('INSTRUMENTED', []) if not absent else ('INSUFFICIENT_OBSERVABILITY', absent)


def describe_profiles():
    return [dict(id=pid, label=spec['label'], reference=spec['reference'],
                 reference_date=spec['reference_date'], note=spec['note'],
                 fractions=spec['fractions'])
            for pid, spec in PROFILES.items()]
