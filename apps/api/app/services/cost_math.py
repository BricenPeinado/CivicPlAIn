"""Source-neutral Decimal arithmetic, shared by v1 synthetic and v2 planning wrappers."""
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, localcontext

VERSION='area-cost-decimal-v1'

def money(value:Decimal):
    return format(value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP),'.2f')

def workdays(quantity:Decimal,productivity:Decimal):
    if not quantity.is_finite() or not productivity.is_finite() or quantity<=0 or productivity<=0:
        raise ValueError('Positive finite quantity and productivity required')
    with localcontext() as ctx:
        ctx.prec=40
        return int((quantity/productivity).to_integral_value(rounding=ROUND_CEILING))

def assemble(quantity:Decimal,rate:Decimal,allowances:list[Decimal],contingency:Decimal):
    with localcontext() as ctx:
        ctx.prec=40
        amounts=[money(quantity*rate),*[money(a) for a in allowances]]
        subtotal=sum(map(Decimal,amounts),Decimal(0))
        extra=Decimal(money(subtotal*contingency))
        return {'amounts':amounts,'subtotal_usd':money(subtotal),'contingency_usd':money(extra),'total_usd':money(subtotal+extra)}
