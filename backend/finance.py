from datetime import date


def calculate(body):
    try:
        start=date.fromisoformat(body.period_start)
        end=date.fromisoformat(body.period_end)
    except ValueError as exc:
        raise ValueError(f'Invalid date format: {exc}') from exc
    if start>=end:
        raise ValueError('Period end must follow period start')
    if body.action_kind=='investigation_only' and (body.physical_saved_kwh or body.newly_billable_kwh):
        raise ValueError('Investigation alone has no recovery; select an explicit hypothetical intervention')
    if body.action_kind=='meter_correction' and body.physical_saved_kwh:
        raise ValueError('A meter correction does not imply physical energy saved')
    if body.action_kind=='physical_repair' and body.newly_billable_kwh:
        raise ValueError('Physical repair alone does not imply newly billable energy')
    invoice=body.newly_billable_kwh*body.assumed_tariff_inr
    cash=invoice*body.assumed_collection_fraction
    avoidance=body.physical_saved_kwh*body.assumed_supply_cost_inr
    cost=body.inspection_cost_inr+body.repair_cost_inr+body.api_cost_inr
    return dict(source_kind='MODELED_SCENARIO',status='MODELED_ONLY',currency='INR',
                assumptions=body.model_dump(),physical_saved_kwh=body.physical_saved_kwh,
                newly_billable_kwh=body.newly_billable_kwh,invoice_value_inr=invoice,
                modeled_cash_inr=cash,avoided_supply_cost_inr=avoidance,total_cost_inr=cost,
                net_modeled_benefit_inr=cash+avoidance-cost,
                actual_collection_status='COLLECTION_UNKNOWN',actual_bescom_savings_inr=None,
                caveat='Hypothetical intervention assumptions; not verified BESCOM recovery. Invoice value is not added again to modeled cash.')
