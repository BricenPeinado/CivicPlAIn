"""Pure, network-free domain calculations. No database or HTTP dependencies."""
import hashlib
import json
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, localcontext

from app.schemas.planning import (Assessment, Calculation, CostScenario, Duration,
    LineItem, PlanningAssumptions, RepairOption, Suitability)
from app.schemas.roads import Road

VERSION = 'repair-estimate-v1'


class MissingInputs(ValueError):
    pass


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def money(value: Decimal):
    return format(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP), '.2f')


def suitability(road: Road, assessment: Assessment | None, option: RepairOption):
    if assessment is None or assessment.rating is None or assessment.assessed_on is None or road.surface_material != 'asphalt':
        return Suitability(status='requires_review', rule_id='suitability-v1:incomplete',
            rationale='A dated demo assessment and asphalt surface information are required for condition screening. Engineering review is always required.')
    indicated = {'good': 'preventive', 'fair': 'resurface', 'poor': 'reconstruct'}.get(assessment.category)
    return Suitability(status='candidate_requires_review' if option.treatment == indicated else 'not_indicated',
        rule_id=f'suitability-v1:{assessment.category}:{option.treatment}',
        rationale=f'Demo condition category {assessment.category} screens for {indicated}. Condition score alone cannot establish structural feasibility, safety or suitability. Verify age, drainage, pavement structure and site conditions.')


def duration(quantity: Decimal, option: RepairOption):
    if quantity <= 0 or not quantity.is_finite():
        raise ValueError('repair quantity must be positive and finite')
    days = int((quantity / option.productivity_per_day).to_integral_value(rounding=ROUND_CEILING))
    return Duration(active_workdays=days, setup_days=option.setup_days, curing_days=option.curing_days,
        total_preliminary_days=days + option.setup_days + option.curing_days,
        productivity_per_day=option.productivity_per_day,
        basis='Sequential active workdays + setup + curing allowance; no weekends/weather/calendar dates modeled. Not a contractor schedule.')


def calculate(road: Road, assessment: Assessment | None, option: RepairOption,
              assumptions: PlanningAssumptions | None = None):
    with localcontext() as ctx:
        ctx.prec = 40
        dimensions = {}
        provenance = {}
        for field in ('length_m', 'width_m'):
            override = getattr(assumptions, field) if assumptions else None
            value = override if override is not None else getattr(road, field)
            if value is None:
                raise MissingInputs(f'{field} is unknown; explicitly enter a labeled planning assumption before estimating.')
            dimensions[field] = value
            provenance[field] = {'value': str(value), 'unit': 'm',
                'basis': 'user_planning_assumption' if override is not None else road.dimension_basis.get(field, 'source_supplied'),
                'evidence_ids': ['user-planning-assumption'] if override is not None else road.field_evidence.get(field, []),
                'note': assumptions.note if override is not None else 'Not a geometric measurement or field survey.'}
        quantity = dimensions['length_m'] * dimensions['width_m']
        if quantity <= 0:
            raise MissingInputs('repairable area must be positive')
        scenarios = cost_scenarios(quantity, option)
        return Calculation(road_segment_id=road.id, repair_option_id=option.id, repair_category=option.treatment,
            quantity=quantity, dimension_provenance=provenance, scenarios=scenarios, duration=duration(quantity, option),
            suitability=suitability(road, assessment, option),
            assumptions=[option.sensitivity_basis, option.rate_inclusions, 'Area = explicit length_m × width_m; full rectangular repair scope.',
                'USD; each line and contingency rounded to cents using ROUND_HALF_UP.',
                *([f'User planning assumption: {assumptions.note}'] if assumptions else [])],
            warnings=['SYNTHETIC DEMONSTRATION ESTIMATE: not official NYC prices or a certified engineering estimate.',
                'Human engineering review required for every alternative; utility coverage is unknown. No excavation clearance.',
                *(['Legacy dimension basis is unknown; validate or explicitly override these synthetic planning inputs.'] if 'legacy_synthetic_basis_unknown' in road.dimension_basis.values() else []),
                *option.exclusions, *option.limitations],
            evidence_ids=sorted(set(road.evidence_ids + option.evidence_ids + (assessment.evidence_ids if assessment else []) +
                (['user-planning-assumption'] if assumptions else []))))


def cost_scenarios(quantity: Decimal, option: RepairOption):
    """Single M2/M4 cost assembly; uncertainty changes bundled rates only."""
    if not quantity.is_finite() or quantity <= 0 or quantity > 10000000:
        raise ValueError("quantity must be positive, finite and at most 10,000,000 m2")
    with localcontext() as ctx:
        ctx.prec = 40
        scenarios = {}
        for name in ('low', 'base', 'high'):
            rate = getattr(option.unit_rates_usd, name)
            items = [LineItem(label='Bundled roadwork: materials + labor + equipment', quantity=quantity,
                unit='m2', unit_rate_usd=str(rate), amount_usd=money(quantity * rate), evidence_ids=option.evidence_ids)]
            for label, value in [('Mobilization', option.mobilization_usd), ('Traffic management allowance', option.traffic_management_usd)]:
                items.append(LineItem(label=label, quantity=Decimal(1), unit='allowance', unit_rate_usd=str(value),
                    amount_usd=money(value), evidence_ids=option.evidence_ids))
            subtotal = sum((Decimal(item.amount_usd) for item in items), Decimal(0))
            contingency = Decimal(money(subtotal * option.contingency_fraction))
            scenarios[name] = CostScenario(line_items=items, subtotal_usd=money(subtotal),
                contingency_fraction=option.contingency_fraction, contingency_usd=money(contingency), total_usd=money(subtotal + contingency))
        return scenarios
