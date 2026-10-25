"""Typed contracts shared by workers, planners and the policy boundary."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Action = Literal['REQUEST_ELECTRICAL_RECHECK','REQUEST_METER_REVIEW','REQUEST_BILLING_AUDIT',
                 'REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION','REQUEST_MISSING_DATA',
                 'GENERATE_CASE_SUMMARY','ABSTAIN_NO_ACTION']


class WorkerResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    worker: Literal['W1','W2','W3','W4']
    status: Literal['OK','WARNING','INSUFFICIENT_DATA','FAILED']
    findings: dict
    evidence_ids: list[str]
    input_hashes: list[str]
    missing_inputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    uncertainty: dict = Field(default_factory=dict)
    model_or_rule_version: str
    elapsed_ms: float
    retryable: bool = False


class PlannerProposal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    next_action: Action
    target_area_id: str
    evidence_ids: list[str] = Field(min_length=1,max_length=20)
    competing_causes: list[str] = Field(max_length=10)
    justification: str = Field(min_length=1,max_length=1500)
    requires_human_approval: bool


class InvestigationInput(BaseModel):
    run_id: str
    area_id: str
    sequence: int = Field(ge=0,le=2879)
    idempotency_key: str = Field(min_length=1,max_length=100)
    initial_check: Literal['REQUEST_ELECTRICAL_RECHECK','REQUEST_TOPOLOGY_CHECK','REQUEST_LOCALIZATION']|None=None


class FinanceInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    physical_saved_kwh: float = Field(default=0,ge=0,le=1e7,allow_inf_nan=False)
    newly_billable_kwh: float = Field(default=0,ge=0,le=1e7,allow_inf_nan=False)
    assumed_tariff_inr: float = Field(default=6,ge=0,le=100,allow_inf_nan=False)
    assumed_collection_fraction: float = Field(default=.7,ge=0,le=1,allow_inf_nan=False)
    assumed_supply_cost_inr: float = Field(default=3,ge=0,le=100,allow_inf_nan=False)
    inspection_cost_inr: float = Field(default=500,ge=0,le=1e8,allow_inf_nan=False)
    repair_cost_inr: float = Field(default=0,ge=0,le=1e8,allow_inf_nan=False)
    api_cost_inr: float = Field(default=0,ge=0,le=1e8,allow_inf_nan=False)
    action_kind: Literal['investigation_only','meter_correction','physical_repair','combined']='investigation_only'
    scope_asset: str='branch-03'
    period_start: str='2022-09-01'
    period_end: str='2022-10-01'
