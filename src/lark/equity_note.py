from __future__ import annotations
import math
import pandas as pd
from bisect import bisect_right
from . import curve as curve_helpers

def ndtr(x):
    return .5 * (1. + math.erf(x / math.sqrt(2.)))


def call(s, k, discount, sigma, t):
    if t <= 1e-12:
        return max(s - k, 0.)
    if sigma <= 1e-12:
        return max(s - k * discount, 0.)
    sig_t = sigma * math.sqrt(t)
    d1 = (math.log(s / (k * discount)) + .5 * sig_t**2) / sig_t
    d2 = d1 - sig_t
    return s * ndtr(d1) - k * discount * ndtr(d2)

