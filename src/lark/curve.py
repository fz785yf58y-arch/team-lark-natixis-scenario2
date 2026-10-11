from __future__ import annotations
import math
from datetime import date

def zero_yield_pct(p: tuple[float, ...], t: float) -> float:
    b0, b1, b2, b3, tau1, tau2 = p
    if t <= 1e-10:
        return b0 + b1
    x1, x2 = t / tau1, t / tau2
    a1 = -math.expm1(-x1) / x1
    a2 = -math.expm1(-x2) / x2
    return b0 + b1 * a1 + b2 * (a1 - math.exp(-x1)) + b3 * (a2 - math.exp(-x2))


def zprice(p: tuple[float, ...], t: float) -> float:
    if t <= 1e-10:
        return 1.0
    return math.exp(-zero_yield_pct(p, t) / 100 * t)


def add_year(d: date, n: int = 1) -> date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:
        return d.replace(year=d.year + n, day=28)

