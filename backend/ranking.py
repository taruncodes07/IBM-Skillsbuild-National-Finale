"""Deterministic next-check ranking (PRD FR-06 quantitative half, AC-14).

Illustrative economics only. Costs, reliabilities, access probabilities and outcome
likelihoods are authored assumptions frozen after calibration. They are NOT measured
Indian inspection prices, measured success rates or achieved product results. Nothing
here reads scenario truth: inputs are the public fusion/worker outputs plus the
recorded ground-observation state.
"""
import math

POLICY_VERSION = 'ranking-1.0'
OUTCOME_TABLE_VERSION = 'outcomes-1.0'

# PRD section 5 normalisation. Frozen after calibration; vary only with a version bump.
COST_NORMALISER_INR = 2000.0
TIME_NORMALISER_MIN = 120.0
COST_WEIGHT = 0.35
TIME_WEIGHT = 0.15
MIN_USEFUL_SCORE = 0.05
TIE_BAND = 0.05
SENSITIVITY_FRACTION = 0.20

CURRENCY = 'INR'

# Hypothesis space mirrors the fusion candidate causes. Priors are uniform unless an
# external calibrated prior is supplied; a uniform prior is an explicit assumption,
# not a measured base rate.
CAUSES = ('METER_FAULT', 'UNMETERED_LOAD', 'TECHNICAL_MODEL_ERROR',
          'TOPOLOGY_MISMATCH', 'AUTHORIZED_UNMETERED_LOAD')


def _cost(travel=0.0, staff=0.0, equipment=0.0, processing=0.0):
    return dict(travel_inr=travel, staff_inr=staff, equipment_inr=equipment,
                processing_inr=processing, currency=CURRENCY,
                total_inr=travel + staff + equipment + processing)


# Authored outcome likelihoods P(observable outcome | cause, action).
# AUTHORED means the row was written on calibration cases; UNKNOWN produces an IG range
# instead of a fabricated point value (PRD section 5).
ACTIONS = {
    'REQUEST_MISSING_DATA': dict(
        label='Retry telemetry / restore missing readings',
        question='Can the incomplete boundary be reconciled once the missing readings arrive?',
        reliability=0.90, access=0.98,
        cost=_cost(processing=60.0), minutes=20,
        likelihood_confidence='AUTHORED',
        outcomes=('READINGS_RESTORED', 'STILL_MISSING'),
        likelihoods={
            'METER_FAULT': (0.35, 0.65),
            'UNMETERED_LOAD': (0.80, 0.20),
            'TECHNICAL_MODEL_ERROR': (0.85, 0.15),
            'TOPOLOGY_MISMATCH': (0.70, 0.30),
            'AUTHORIZED_UNMETERED_LOAD': (0.85, 0.15)},
        external=False),
    'REQUEST_TOPOLOGY_CHECK': dict(
        label='Validate registered mapping and model assumptions',
        question='Does the registered cut and loss model explain the signed residual?',
        reliability=0.92, access=1.00,
        cost=_cost(processing=80.0), minutes=15,
        likelihood_confidence='AUTHORED',
        outcomes=('MAPPING_OR_MODEL_FAULT_FOUND', 'REGISTERED_GRAPH_CONSISTENT'),
        likelihoods={
            'METER_FAULT': (0.10, 0.90),
            'UNMETERED_LOAD': (0.08, 0.92),
            'TECHNICAL_MODEL_ERROR': (0.70, 0.30),
            'TOPOLOGY_MISMATCH': (0.85, 0.15),
            'AUTHORIZED_UNMETERED_LOAD': (0.45, 0.55)},
        external=False),
    'REQUEST_ELECTRICAL_RECHECK': dict(
        label='Recheck frozen interval balances and persistence',
        question='Is the excess persistent and above its uncertainty allowance across valid intervals?',
        reliability=0.95, access=1.00,
        cost=_cost(processing=40.0), minutes=10,
        likelihood_confidence='AUTHORED',
        outcomes=('PERSISTENT_EXCESS_CONFIRMED', 'NOT_PERSISTENT'),
        likelihoods={
            'METER_FAULT': (0.75, 0.25),
            'UNMETERED_LOAD': (0.88, 0.12),
            'TECHNICAL_MODEL_ERROR': (0.60, 0.40),
            'TOPOLOGY_MISMATCH': (0.55, 0.45),
            'AUTHORIZED_UNMETERED_LOAD': (0.50, 0.50)},
        external=False),
    'REQUEST_LOCALIZATION': dict(
        label='Refine measured-region bounds',
        question='Can the unexplained energy be bounded to a smaller measured region?',
        reliability=0.90, access=1.00,
        cost=_cost(processing=50.0), minutes=12,
        likelihood_confidence='AUTHORED',
        outcomes=('NARROWED_TO_SMALLER_REGION', 'NO_NARROWING_POSSIBLE'),
        likelihoods={
            'METER_FAULT': (0.45, 0.55),
            'UNMETERED_LOAD': (0.60, 0.40),
            'TECHNICAL_MODEL_ERROR': (0.30, 0.70),
            'TOPOLOGY_MISMATCH': (0.35, 0.65),
            'AUTHORIZED_UNMETERED_LOAD': (0.40, 0.60)},
        external=False),
    'RECORD_CROSS_CHECK': dict(
        label='Meter record cross-check',
        question='Do connection, authorisation and meter-change records explain the excess?',
        reliability=0.95, access=1.00,
        cost=_cost(staff=80.0, processing=20.0), minutes=10,
        likelihood_confidence='AUTHORED',
        outcomes=('RECORD_EXPLAINS_EXCESS', 'NO_RECORD_EXPLANATION'),
        likelihoods={
            'METER_FAULT': (0.40, 0.60),
            'UNMETERED_LOAD': (0.12, 0.88),
            'TECHNICAL_MODEL_ERROR': (0.20, 0.80),
            'TOPOLOGY_MISMATCH': (0.65, 0.35),
            'AUTHORIZED_UNMETERED_LOAD': (0.90, 0.10)},
        external=True),
    'REQUEST_METER_REVIEW': dict(
        label='Independent meter inspection / test',
        question='Does the boundary meter register correctly under an independent test?',
        reliability=0.88, access=0.85,
        cost=_cost(travel=200.0, staff=300.0, equipment=100.0), minutes=60,
        likelihood_confidence='AUTHORED',
        outcomes=('METER_DEFECT_FOUND', 'METER_WITHIN_TOLERANCE'),
        likelihoods={
            'METER_FAULT': (0.88, 0.12),
            'UNMETERED_LOAD': (0.08, 0.92),
            'TECHNICAL_MODEL_ERROR': (0.10, 0.90),
            'TOPOLOGY_MISMATCH': (0.15, 0.85),
            'AUTHORIZED_UNMETERED_LOAD': (0.10, 0.90)},
        external=True),
    'GROUND_OBSERVATION': dict(
        label='Targeted ground observation',
        question='What is physically present on the monitored section from ground view?',
        reliability=0.85, access=0.90,
        cost=_cost(travel=200.0, staff=250.0, processing=50.0), minutes=35,
        likelihood_confidence='AUTHORED',
        outcomes=('PHYSICAL_FINDING_OBSERVED', 'NOTHING_VISIBLE_FROM_GROUND'),
        likelihoods={
            'METER_FAULT': (0.25, 0.75),
            'UNMETERED_LOAD': (0.72, 0.28),
            'TECHNICAL_MODEL_ERROR': (0.12, 0.88),
            'TOPOLOGY_MISMATCH': (0.40, 0.60),
            'AUTHORIZED_UNMETERED_LOAD': (0.55, 0.45)},
        external=True),
    'AERIAL_OBSERVATION': dict(
        label='Targeted aerial RGB viewpoint',
        question='Is there an unmatched overhead connection that ground view could not resolve?',
        reliability=0.80, access=0.95,
        cost=_cost(travel=300.0, staff=600.0, equipment=500.0, processing=100.0), minutes=45,
        likelihood_confidence='AUTHORED',
        outcomes=('UNMATCHED_OVERHEAD_CANDIDATE', 'NO_VISIBLE_CANDIDATE'),
        likelihoods={
            'METER_FAULT': (0.08, 0.92),
            'UNMETERED_LOAD': (0.70, 0.30),
            'TECHNICAL_MODEL_ERROR': (0.05, 0.95),
            'TOPOLOGY_MISMATCH': (0.20, 0.80),
            'AUTHORIZED_UNMETERED_LOAD': (0.45, 0.55)},
        external=True,
        # Access is only this high once ground review has specified the gap; before that
        # the action is rejected outright rather than scored (PRD section 5 hard gates).
        requires_ground_question=True),
    'REQUEST_BILLING_AUDIT': dict(
        label='Commercial / billing audit',
        question='Do billing and collection records account for the delivered energy?',
        reliability=0.90, access=0.60,
        cost=_cost(staff=400.0, processing=150.0), minutes=90,
        likelihood_confidence='UNKNOWN',
        outcomes=('BILLING_GAP_FOUND', 'BILLING_CONSISTENT'),
        likelihoods={cause: (0.5, 0.5) for cause in CAUSES},
        external=True),
}


def entropy(distribution):
    """Shannon entropy in bits of an iterable of probabilities."""
    total = 0.0
    for p in distribution:
        if p > 0:
            total -= p * math.log2(p)
    return total


def information_gain(prior, likelihoods, outcomes):
    """Expected reduction in hypothesis entropy, in bits.

    prior: {cause: probability}; likelihoods: {cause: (P(o|cause), ...)} aligned to outcomes.
    """
    causes = [c for c in prior if prior[c] > 0]
    before = entropy([prior[c] for c in causes])
    after = 0.0
    for index in range(len(outcomes)):
        joint = [prior[c] * likelihoods[c][index] for c in causes]
        marginal = sum(joint)
        if marginal <= 0:
            continue
        after += marginal * entropy([j / marginal for j in joint])
    return max(0.0, before - after)


def normalise_cost(total_inr):
    return min(total_inr / COST_NORMALISER_INR, 1.0)


def normalise_time(minutes):
    return min(minutes / TIME_NORMALISER_MIN, 1.0)


def score_from_components(ig_bits, reliability, access, cost_inr, minutes):
    """S(a) = IG x R x A - 0.35 x Cn - 0.15 x Tn (PRD section 5).

    Reliability and access are separate operational discounts; IG is conditional on
    obtaining a usable observation, so a failed attempt is not discounted twice.
    """
    return (ig_bits * reliability * access
            - COST_WEIGHT * normalise_cost(cost_inr)
            - TIME_WEIGHT * normalise_time(minutes))


def uniform_prior(causes=CAUSES):
    share = 1.0 / len(causes)
    return {cause: share for cause in causes}


def _eligibility(action_id, spec, context):
    """Infeasible or unsafe actions are rejected before ranking, never scored low."""
    status = context.get('diagnostic_status')
    if status in ('WITHIN_MODEL_RANGE', 'PERSISTENCE_PENDING'):
        return False, ('NO_PERSISTENT_SIGNAL: normal or nonpersistent measurements do not '
                       'justify a diagnostic check')
    if status == 'DATA_INCOMPLETE':
        # Repair the specific defect first; a mapping check cannot interpret absent readings.
        kind = context.get('incomplete_kind', 'MISSING_READINGS')
        allowed = set()
        if kind in ('MISSING_READINGS', 'BOTH'):
            allowed.add('REQUEST_MISSING_DATA')
        if kind in ('TOPOLOGY_MISMATCH', 'BOTH'):
            allowed.add('REQUEST_TOPOLOGY_CHECK')
        if not allowed:
            allowed = {'REQUEST_MISSING_DATA', 'REQUEST_TOPOLOGY_CHECK'}
        if action_id not in allowed:
            return False, f'DATA_INCOMPLETE ({kind}): repair the measurement defect before any other check'
    elif action_id == 'REQUEST_MISSING_DATA':
        return False, 'NOTHING_MISSING: the boundary cut is complete, so there is nothing to restore'
    if action_id == 'REQUEST_BILLING_AUDIT' and context.get('billing_status') == 'NOT_AVAILABLE':
        return False, 'BILLING_UNAVAILABLE: records are not obtainable; request data instead'
    if spec.get('requires_ground_question') and not context.get('ground_question_open'):
        return False, ('NO_GROUND_GAP: aerial review requires a recorded unresolved overhead '
                       'question from ground review')
    if action_id == 'GROUND_OBSERVATION' and context.get('ground_question_open'):
        return False, 'GROUND_REVIEW_DONE: a ground observation for this case is already recorded'
    if action_id in context.get('completed_actions', ()):  # already answered on frozen inputs
        return False, 'ALREADY_COMPLETED: identical check already ran against these inputs'
    return True, None


def _sensitivity(entry, context, prior):
    """Vary illustrative inputs by +/- 20%, clipped to valid domains (PRD section 5)."""
    spec = ACTIONS[entry['action_id']]
    lo, hi = 1 - SENSITIVITY_FRACTION, 1 + SENSITIVITY_FRACTION
    variants = []
    for ig_scale in (lo, hi):
        for cost_scale in (lo, hi):
            for time_scale in (lo, hi):
                for quality_scale in (lo, hi):
                    variants.append(score_from_components(
                        entry['information_gain_bits'] * ig_scale,
                        min(1.0, spec['reliability'] * quality_scale),
                        min(1.0, spec['access'] * quality_scale),
                        entry['cost']['total_inr'] * cost_scale,
                        entry['expected_minutes'] * time_scale))
    return dict(low=min(variants), high=max(variants), fraction=SENSITIVITY_FRACTION,
                samples=len(variants))


def rank(context, prior=None):
    """Return the ranked eligible checks, rejected actions and the recommendation.

    context keys: diagnostic_status, billing_status, ground_question_open,
    completed_actions, area_id, balance_id, evidence_ids.
    """
    prior = prior or uniform_prior()
    prior_source = context.get('prior_source', 'UNIFORM_ASSUMPTION')
    ranked, rejected = [], []
    for action_id, spec in ACTIONS.items():
        eligible, reason = _eligibility(action_id, spec, context)
        if not eligible:
            rejected.append(dict(action_id=action_id, label=spec['label'],
                                 prerequisite_status='REJECTED', rejection_reason=reason))
            continue
        ig = information_gain(prior, spec['likelihoods'], spec['outcomes'])
        unknown = spec['likelihood_confidence'] == 'UNKNOWN'
        entry = dict(
            action_id=action_id, label=spec['label'], question=spec['question'],
            prerequisite_status='ELIGIBLE',
            information_gain_bits=ig,
            information_gain_range=[0.0, ig] if unknown else [ig, ig],
            likelihood_confidence=spec['likelihood_confidence'],
            outcomes=list(spec['outcomes']),
            reliability=spec['reliability'], access=spec['access'],
            cost=dict(spec['cost']), expected_minutes=spec['minutes'],
            requires_external_action=spec['external'],
            normalisation=dict(cost_normaliser_inr=COST_NORMALISER_INR,
                               time_normaliser_minutes=TIME_NORMALISER_MIN,
                               cost_weight=COST_WEIGHT, time_weight=TIME_WEIGHT))
        entry['score'] = score_from_components(ig, spec['reliability'], spec['access'],
                                               spec['cost']['total_inr'], spec['minutes'])
        entry['sensitivity'] = _sensitivity(entry, context, prior)
        ranked.append(entry)

    ranked.sort(key=lambda e: e['score'], reverse=True)
    for position, entry in enumerate(ranked, start=1):
        entry['rank'] = position

    best = ranked[0] if ranked else None
    tied = [e for e in ranked[1:] if best and abs(best['score'] - e['score']) <= TIE_BAND]
    stable = True
    if best and tied:
        stable = all(best['sensitivity']['low'] >= e['sensitivity']['high'] for e in tied)

    if best is None:
        recommendation, abstain_reason = 'ABSTAIN_NO_ACTION', 'No feasible check can improve this decision.'
    elif best['score'] <= MIN_USEFUL_SCORE:
        recommendation, abstain_reason = 'ABSTAIN_NO_ACTION', (
            f"Best eligible score {best['score']:.3f} does not exceed the {MIN_USEFUL_SCORE} "
            'policy floor; no check justifies its cost.')
    else:
        recommendation, abstain_reason = best['action_id'], None

    return dict(
        policy_version=POLICY_VERSION, outcome_table_version=OUTCOME_TABLE_VERSION,
        prior=dict(prior), prior_source=prior_source,
        prior_entropy_bits=entropy(prior.values()),
        ranked=ranked, rejected=rejected,
        recommended_action=recommendation,
        abstain_reason=abstain_reason,
        missing_evidence_question=(best['question'] if best and abstain_reason is None
                                   else 'Which independent observation would change this decision?'),
        tie_band=TIE_BAND, tied_actions=[e['action_id'] for e in tied],
        winner_stable_under_sensitivity=stable,
        human_choice_required=bool(tied) and not stable,
        disclosure=('Illustrative authored economics and likelihoods. Not measured prices, '
                    'success rates or field results. Ranking informs a human decision and '
                    'never authorises execution.'))


# Calibration fixture reproducing PRD section 5 Table 4 exactly from logged components.
# AC-14 recomputes each row to within 0.001 of the published score.
CALIBRATION_FIXTURE = [
    dict(label='Meter record cross-check', ig=0.55, reliability=0.95, access=1.0,
         cost_inr=100.0, minutes=10, expected_score=0.493, eligible=True),
    dict(label='Ground observation', ig=0.90, reliability=0.85, access=0.90,
         cost_inr=500.0, minutes=35, expected_score=0.557, eligible=True),
    dict(label='Drone view before ground review', ig=1.10, reliability=0.80, access=0.60,
         cost_inr=1500.0, minutes=45, expected_score=None, eligible=False),
    dict(label='Drone after specified ground gap', ig=1.10, reliability=0.80, access=0.95,
         cost_inr=1500.0, minutes=45, expected_score=0.517, eligible=True),
]
