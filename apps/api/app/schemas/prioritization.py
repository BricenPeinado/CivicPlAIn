"""Explicit policy assumptions; source observations cannot be submitted through this API."""
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import Field,model_validator,field_validator
from app.schemas.municipal_planning import Model,Evidence,Number

class Weights(Model):
    condition_need:str
    inspection_age:str
    evidence_gap:str

    @model_validator(mode='after')
    def valid(self):
        import re
        values=list(self.model_dump().values())
        if any(not re.fullmatch(r'(0|1)(\.[0-9]{1,6})?',v) for v in values):raise ValueError('Weights are plain decimal strings in 0..1, max six decimal places')
        if any(not 0<=Decimal(v)<=1 for v in values) or sum(map(Decimal,values))!=1:raise ValueError('Weights must sum exactly to one')
        return self

class PriorityPolicy(Model):
    id:str=Field(min_length=1,max_length=100,pattern=r'^[a-zA-Z0-9._-]+$')
    version:str=Field(min_length=1,max_length=50,pattern=r'^[a-zA-Z0-9._-]+$')
    objective:Literal['maintenance_review','inspection_review']
    weights:Weights
    age_horizon_days:int=Field(strict=True,ge=1,le=36500)
    max_condition_age_days:int=Field(strict=True,ge=0,le=36500)
    stale_behavior:Literal['exclude','allow_qualified']
    evidence:Evidence

    @model_validator(mode='after')
    def objectives(self):
        if self.objective=='maintenance_review' and Decimal(self.weights.evidence_gap)!=0:raise ValueError('Completeness cannot be scored as maintenance need')
        if self.objective=='inspection_review' and Decimal(self.weights.condition_need)!=0:raise ValueError('Inspection review must not score maintenance need')
        return self

class EstimateChoice(Model):
    road_id:str=Field(min_length=1,max_length=200)
    estimate_id:str=Field(pattern=r'^estimate-[0-9a-f]{64}$')
    treatment:Literal['patch','resurface']

class PriorityRequest(Model):
    contract_version:Literal['maintenance-priority-v1']
    snapshot_id:str=Field(pattern=r'^nyc-[0-9a-f]{32}$')
    road_ids:list[str]=Field(min_length=1,max_length=100)
    as_of_date:date
    condition_release_id:str|None=Field(default=None,pattern=r'^intel-[0-9a-f]{32}$')
    permit_release_id:str|None=Field(default=None,pattern=r'^intel-[0-9a-f]{32}$')
    policy:PriorityPolicy
    sensitivity_policies:list[PriorityPolicy]=Field(default_factory=list,max_length=3)
    estimates:list[EstimateChoice]=Field(default_factory=list,max_length=100)
    max_estimate_usd:Number|None=None

    @field_validator('as_of_date',mode='before')
    @classmethod
    def explicit_date(cls,value):
        if not isinstance(value,str) or date.fromisoformat(value).isoformat()!=value:raise ValueError('Explicit YYYY-MM-DD required')
        return value

    @model_validator(mode='after')
    def context(self):
        if len(self.road_ids)!=len(set(self.road_ids)) or any(not r.strip() or len(r)>200 for r in self.road_ids):raise ValueError('Unique bounded road IDs required')
        if len({c.road_id for c in self.estimates})!=len(self.estimates) or any(c.road_id not in self.road_ids for c in self.estimates):raise ValueError('One selected estimate per scoped road')
        policies=[self.policy,*self.sensitivity_policies]
        if len({(p.id,p.version) for p in policies})!=len(policies):raise ValueError('Distinct policy identities required')
        if any(p.objective!=self.policy.objective for p in policies):raise ValueError('Sensitivity policies must retain the objective')
        if self.max_estimate_usd and (self.max_estimate_usd.unit!='USD' or self.max_estimate_usd.number>1000000000000):raise ValueError('Per-declared-scope cost ceiling requires USD <= 1 trillion')
        return self

class PriorityFactor(Model):
    value:str|None
    unit:Literal['dimensionless']
    weight:str
    contribution:str|None
    reason:str|None
    definition:str

class PriorityRoad(Model):
    road_id:str
    name:str
    rank:int|None=Field(ge=1)
    score:str|None
    status:Literal['ranked','unranked']
    objective:Literal['maintenance_review','inspection_review']
    missing_weighted_factors:list[str]
    ineligible_reasons:list[str]
    factors:dict[Literal['condition_need','inspection_age','evidence_gap'],PriorityFactor]
    completeness:dict
    maintenance_need:dict
    recency:dict
    road_classification:dict
    implementation_cost:dict|None
    cost_constraint:str
    coordination:dict
    traffic_disruption:dict
    unknowns:list[str]
    human_review_required:Literal[True]
    why:str
    lineage:dict

    @model_validator(mode='after')
    def numerical_state(self):
        if (self.status=='ranked')!=(self.rank is not None and self.score is not None):raise ValueError('Inconsistent ranking state')
        if self.score is not None and not 0<=Decimal(self.score)<=1:raise ValueError('Score outside 0..1')
        return self

class PriorityEvaluation(Model):
    policy_id:str
    policy_version:str
    policy_hash:str
    objective:str
    rows:list[PriorityRoad]
    ranked:int
    unranked:int
    rank_changes:list[dict]|None=None
    result_hash:str|None=None

class PriorityResult(Model):
    method_version:Literal['maintenance-priority-v1']
    snapshot_id:str
    as_of_date:str
    base:PriorityEvaluation
    sensitivity:list[PriorityEvaluation]
    coverage:dict
    definitions:dict[str,str]
    warnings:list[str]
    contains_synthetic:Literal[False]
    classification:Literal['derived_calculation']
    utility_coverage:Literal['unknown']
