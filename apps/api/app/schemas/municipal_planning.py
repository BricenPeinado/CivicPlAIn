"""Official-road planning inputs; never accepted as synthetic RepairOption/Road DTOs."""
from datetime import date
from decimal import Decimal
import re
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator

class Model(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)

class Citation(Model):
    title:str=Field(min_length=1,max_length=300)
    url:str=Field(pattern=r'^https://[^\s]+$',max_length=2000)
    accessed_on:date
    published_on:date|None=None
    locator:str=Field(min_length=1,max_length=500)
    geography:str=Field(min_length=1,max_length=300)
    limitations:str=Field(min_length=1,max_length=1000)

class Evidence(Model):
    classification:Literal['planning_assumption']
    author:str=Field(min_length=1,max_length=200)
    entered_on:date
    note:str=Field(min_length=1,max_length=2000)
    citations:list[Citation]=Field(default_factory=list,max_length=10)

    @field_validator('author','note')
    @classmethod
    def nonblank(cls,value):
        if not value.strip():raise ValueError('Nonblank provenance required')
        return value

class Number(Model):
    value:str=Field(max_length=26)
    unit:Literal['m','ft','m2','yd2','ft2','USD/m2','USD/yd2','USD/ft2','USD','fraction','m2/active_workday','yd2/active_workday','ft2/active_workday','days']
    evidence:Evidence

    @field_validator('value')
    @classmethod
    def decimal_string(cls,value):
        if not re.fullmatch(r'(0|[1-9][0-9]{0,11})(\.[0-9]{1,6})?',value):
            raise ValueError('Nonnegative plain decimal string, max 12 integer/6 fractional digits required')
        return value

    @property
    def number(self):return Decimal(self.value)

class Scope(Model):
    description:str=Field(min_length=1,max_length=2000)
    extent:Literal['partial','entire_road_reference']
    area:Number|None=None
    length:Number|None=None
    width:Number|None=None

    @model_validator(mode='after')
    def units(self):
        if not self.description.strip():raise ValueError('Explicit scope description required')
        if self.area and (self.length or self.width):raise ValueError('Supply area or dimensions, not both')
        for key,units in [('area',{'m2','yd2','ft2'}),('length',{'m','ft'}),('width',{'m','ft'})]:
            value=getattr(self,key)
            if value and (value.unit not in units or value.number<=0):raise ValueError(f'Invalid {key} unit/value')
        return self

class Allowance(Model):
    key:Literal['mobilization','traffic_control','other']
    label:str=Field(min_length=1,max_length=200)
    disposition:Literal['priced','included','excluded','unknown']
    amount:Number|None=None
    evidence:Evidence

    @model_validator(mode='after')
    def amount_rule(self):
        if not self.label.strip():raise ValueError('Nonblank allowance label required')
        if self.disposition=='priced' and (not self.amount or self.amount.unit!='USD' or self.amount.number>1000000000):raise ValueError('Priced allowance requires USD amount <= 1 billion')
        if self.disposition!='priced' and self.amount:raise ValueError('Nonpriced disposition cannot contain an amount')
        return self

class Sensitivity(Model):
    low:Number
    high:Number
    evidence:Evidence

class Alternative(Model):
    treatment:Literal['patch','resurface']
    scope:Scope|None=None
    rate:Number|None=None
    price_basis_date:date|None=None
    geography:str|None=Field(default=None,min_length=1,max_length=300)
    inclusions:str|None=Field(default=None,min_length=1,max_length=2000)
    exclusions:list[str]=Field(default_factory=list,max_length=20)
    allowances:list[Allowance]=Field(default_factory=list,max_length=12)
    contingency:Number|None=None
    cost_overlap_review:Literal['declared_nonoverlapping']|None=None
    sensitivity:Sensitivity|None=None
    productivity:Number|None=None
    setup_days:Number|None=None
    curing_days:Number|None=None

    @model_validator(mode='after')
    def consistent(self):
        for text in [self.geography,self.inclusions,*self.exclusions]:
            if text is not None and (not text.strip() or len(text)>2000):raise ValueError('Nonblank bounded declarations required')
        labels=[a.label.casefold().strip() for a in self.allowances]
        if len(labels)!=len(set(labels)):raise ValueError('Duplicate allowance label')
        for key in ['mobilization','traffic_control']:
            if sum(a.key==key for a in self.allowances)>1:raise ValueError('Duplicate allowance category')
        if self.rate and (self.rate.unit not in {'USD/m2','USD/yd2','USD/ft2'} or not 0<self.rate.number<=1000000):raise ValueError('Positive area rate <= 1 million required')
        if self.contingency and (self.contingency.unit!='fraction' or self.contingency.number>1):raise ValueError('Contingency fraction must be 0..1')
        if self.sensitivity:
            if not self.rate or any(n.unit!=self.rate.unit for n in [self.sensitivity.low,self.sensitivity.high]):raise ValueError('Sensitivity requires same units as base rate')
            if not 0<=self.sensitivity.low.number<=self.rate.number<=self.sensitivity.high.number<=1000000:raise ValueError('Ordered low <= base <= high rates required')
        if self.productivity and (self.productivity.unit not in {'m2/active_workday','yd2/active_workday','ft2/active_workday'} or not 0<self.productivity.number<=10000000):raise ValueError('Invalid productivity')
        for n in [self.setup_days,self.curing_days]:
            if n and (n.unit!='days' or n.number>365 or n.number!=n.number.to_integral_value()):raise ValueError('Days must be integer 0..365')
        return self

class EstimateRequest(Model):
    contract_version:Literal['municipal-estimate-v1']
    snapshot_id:str=Field(pattern=r'^nyc-[a-f0-9]{32}$')
    road_id:str=Field(min_length=1,max_length=200)
    alternatives:list[Alternative]=Field(min_length=1,max_length=2)

    @model_validator(mode='after')
    def unique(self):
        if len({a.treatment for a in self.alternatives})!=len(self.alternatives):raise ValueError('Duplicate treatment')
        return self

class CostLine(Model):
    label:str
    quantity:str
    unit:Literal['m2','yd2','ft2','allowance']
    rate_usd:str
    amount_usd:str=Field(pattern=r'^[0-9]+\.[0-9]{2}$')
    amount_cents:int=Field(ge=0)
    evidence_path:str

class CostCase(Model):
    line_items:list[CostLine]
    subtotal_usd:str
    contingency_usd:str
    total_usd:str
    contingency_fraction:str
    total_cents:int=Field(ge=0)

class WorkDuration(Model):
    active_workdays:int=Field(ge=1)
    setup_days:int=Field(ge=0)
    curing_days:int=Field(ge=0)
    total_preliminary_days:int=Field(ge=1)
    basis:str

class AlternativeResult(Model):
    treatment:Literal['patch','resurface']
    status:Literal['available','unavailable']
    input_path:str
    missing_fields:list[str]
    scope:Scope|None
    quantity_m2:str|None
    cases:dict[Literal['low','base','high'],CostCase]|None
    duration:WorkDuration|None
    price_basis_date:str|None
    geography:str|None
    inclusions:str|None
    exclusions:list[str]
    allowance_declarations:list[Allowance]
    unknowns:list[str]
    suitability:Literal['requires_engineering_review']
    classification:Literal['derived_calculation']

class EstimateResult(Model):
    contract_version:Literal['municipal-estimate-v1']
    method_version:Literal['municipal-area-cost-v1']
    arithmetic_version:Literal['area-cost-decimal-v1']
    snapshot_id:str
    road_id:str
    currency:Literal['USD']
    alternatives:list[AlternativeResult]
    warnings:list[str]
    utility_coverage:Literal['unknown']
    classification:Literal['derived_calculation']
    contains_assumptions:Literal[True]
    contains_synthetic:Literal[False]
    comparison_basis:str
