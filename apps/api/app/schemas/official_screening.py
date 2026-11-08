"""Source-neutral work declarations; permits never supply work geometry or schedules."""
from datetime import date
from typing import Literal
from pydantic import Field, model_validator, field_validator
from app.schemas.municipal_planning import Model, Evidence, Citation, Number
from app.schemas.conflicts import WorkPolygon
from app.schemas.roads import Geometry

class Basis(Model):
    classification:Literal['planning_assumption','supplied_document']
    author:str=Field(min_length=1,max_length=200)
    entered_on:date
    note:str=Field(min_length=1,max_length=2000)
    citations:list[Citation]=Field(default_factory=list,max_length=10)

    @model_validator(mode='after')
    def provenance(self):
        if not self.author.strip() or not self.note.strip():raise ValueError('Nonblank provenance required')
        if self.classification=='supplied_document' and not self.citations:raise ValueError('Documentary declaration requires citations; independently unverified')
        return self

class Schedule(Model):
    start:date
    end:date
    basis:Basis

    @field_validator('start','end',mode='before')
    @classmethod
    def strict_date(cls,value):
        if not isinstance(value,str) or date.fromisoformat(value).isoformat()!=value:raise ValueError('YYYY-MM-DD required')
        return value

    @model_validator(mode='after')
    def interval(self):
        if self.start>=self.end:raise ValueError('Half-open interval requires start < end')
        return self

class Location(Model):
    geometry:WorkPolygon|Geometry
    crs:Literal['EPSG:4326']
    certainty:Literal['declared','approximate']
    basis:Basis

class WorkInput(Model):
    id:str=Field(pattern=r'^[a-zA-Z0-9._-]{1,100}$')
    title:str=Field(min_length=1,max_length=200)
    work_type:Literal['resurfacing','excavation','maintenance','inspection','other']
    basis:Basis
    road_ids:list[str]=Field(default_factory=list,max_length=30)
    permit_ids:list[str]=Field(default_factory=list,max_length=30)
    location:Location|None=None
    schedule:Schedule|None=None
    grade:Literal['unknown','surface','elevated','underground']='unknown'
    grade_basis:Basis|None=None
    excavation_required:bool|None=Field(default=None,strict=True)
    excavation_basis:Basis|None=None
    excavation_depth_m:str|None=Field(default=None,pattern=r'^(0|[1-9][0-9]{0,3})(\.[0-9]{1,6})?$')
    depth_basis:Basis|None=None
    closure:Schedule|None=None

    @model_validator(mode='after')
    def evidence(self):
        if not self.title.strip():raise ValueError('Nonblank work title required')
        for refs in [self.road_ids,self.permit_ids]:
            if len(refs)!=len(set(refs)) or any(not r.strip() or len(r)>200 for r in refs):raise ValueError('Distinct bounded references required')
        for present,basis in [(self.grade!='unknown',self.grade_basis),(self.excavation_required is not None,self.excavation_basis),(self.excavation_depth_m is not None,self.depth_basis)]:
            if present != (basis is not None):raise ValueError('Every populated grade/excavation/depth declaration requires its own provenance')
        if self.excavation_depth_m is not None and self.excavation_required is not True:raise ValueError('Depth requires explicit excavation declaration')
        if self.closure and (not self.schedule or not self.schedule.start<=self.closure.start<self.closure.end<=self.schedule.end):raise ValueError('Closure must be within explicit work schedule')
        return self

class ScheduleOverride(Model):
    work_id:str
    schedule:Schedule
    closure:Schedule|None=None

class Alternative(Model):
    id:str=Field(pattern=r'^[a-zA-Z0-9._-]{1,100}$')
    overrides:list[ScheduleOverride]=Field(min_length=1,max_length=30)
    evidence:Evidence

class CostComparison(Model):
    work_id:str
    estimate_id:str=Field(pattern=r'^estimate-[0-9a-f]{64}$')
    treatment:Literal['patch','resurface']
    base_schedule_addition:Number
    alternative_schedule_additions:dict[str,Number]
    comparable_scope_and_nonoverlap:Literal['declared_same_scope_nonoverlapping_additions']
    evidence:Evidence

    @model_validator(mode='after')
    def money(self):
        if len(self.alternative_schedule_additions)>3 or any(v.unit!='USD' or v.number>1000000000 for v in [self.base_schedule_addition,*self.alternative_schedule_additions.values()]):raise ValueError('Explicit nonnegative USD schedule additions <= 1 billion required')
        return self

class ScreeningRequest(Model):
    contract_version:Literal['official-screen-v1']
    snapshot_id:str=Field(pattern=r'^nyc-[a-f0-9]{32}$')
    works:list[WorkInput]=Field(default_factory=list,max_length=30)
    permit_ids:list[str]=Field(default_factory=list,max_length=30)
    permit_release_id:str|None=Field(default=None,pattern=r'^intel-[a-f0-9]{32}$')
    proximity_m:float=Field(ge=0,le=100,strict=True)
    reopening_horizon_days:int=Field(ge=0,le=365,strict=True)
    policy_evidence:Evidence
    alternatives:list[Alternative]=Field(default_factory=list,max_length=3)
    cost_comparison:CostComparison|None=None

    @model_validator(mode='after')
    def references(self):
        ids=[w.id for w in self.works];permits=self.permit_ids
        if len(ids)!=len(set(ids)) or len(permits)!=len(set(permits)) or any(not x.strip() or len(x)>200 for x in permits):raise ValueError('Distinct bounded work/permit IDs required')
        if len(set(permits)|{p for w in self.works for p in w.permit_ids})>30:raise ValueError('At most 30 distinct administrative records')
        if not self.works and not permits:raise ValueError('Select work declarations or administrative records')
        if len({a.id for a in self.alternatives})!=len(self.alternatives):raise ValueError('Unique alternative IDs required')
        for a in self.alternatives:
            if len({o.work_id for o in a.overrides})!=len(a.overrides) or any(o.work_id not in ids for o in a.overrides):raise ValueError('Distinct known override work IDs required')
            for o in a.overrides:
                work=next(w for w in self.works if w.id==o.work_id)
                WorkInput.model_validate(work.model_dump(mode='json')|{'schedule':o.schedule.model_dump(mode='json'),'closure':o.closure.model_dump(mode='json') if o.closure else None})
        if self.cost_comparison:
            c=self.cost_comparison
            if c.work_id not in ids or not next(w for w in self.works if w.id==c.work_id).schedule:raise ValueError('Cost comparison requires scheduled known work')
            if set(c.alternative_schedule_additions)!={a.id for a in self.alternatives} or not self.alternatives:raise ValueError('Explicit addition for every alternative required')
            if any(c.work_id not in {o.work_id for o in a.overrides} for a in self.alternatives):raise ValueError('Costed work schedule must be explicitly overridden in every alternative')
        return self

class ReviewNote(Model):
    finding_id:str|None=Field(default=None,pattern=r'^finding-[a-f0-9]{64}$')
    author:str=Field(min_length=1,max_length=200)
    note:str=Field(min_length=1,max_length=2000)
    disposition:Literal['needs_review','reviewed_with_limitations','dismissed_for_planning']

    @model_validator(mode='after')
    def nonblank(self):
        if not self.author.strip() or not self.note.strip():raise ValueError('Nonblank review text required')
        return self
