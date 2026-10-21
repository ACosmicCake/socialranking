"""Income distribution helpers.

A national distribution is stored as nine decile thresholds plus two tails
(see ``decile_distribution`` in scripts/build_data.py):

* below the first threshold: uniform on [low, thr1] (holds the bottom 10%)
* between thresholds: linear in log income
* above the ninth threshold: Pareto with the stored alpha (holds the top 10%)

The global distribution is a calibrated CDF on a log-spaced grid.
All incomes are per person per day in 2017 international dollars (PPP).
"""

import bisect
import math

from . import data


def national_cdf(dist, x):
    """Share of the national population with income/consumption below x."""
    thr = dist["thresholds"]
    if x <= 0:
        return 0.0
    if x < thr[0]:
        low = dist["low"]
        return max(0.0, min(1.0, (x - low) / (thr[0] - low))) * 0.1
    if x > thr[-1]:
        return 1 - 0.1 * (thr[-1] / x) ** dist["pareto_alpha"]
    i = bisect.bisect_right(thr, x) - 1
    if i >= len(thr) - 1:
        return 0.9
    frac = (math.log(x) - math.log(thr[i])) / (math.log(thr[i + 1]) - math.log(thr[i]))
    return (i + 1 + frac) / 10


def national_quantile(dist, p):
    """Inverse of national_cdf: income at population share p (0-1)."""
    thr = dist["thresholds"]
    if p <= 0.1:
        low = dist["low"]
        return low + (thr[0] - low) * p / 0.1
    if p >= 0.9:
        return thr[-1] * (0.1 / max(1 - p, 1e-9)) ** (1 / dist["pareto_alpha"])
    k = p * 10 - 1
    i = int(k)
    frac = k - i
    return math.exp(math.log(thr[i]) + frac * (math.log(thr[i + 1]) - math.log(thr[i])))


def global_cdf(x):
    """Share of the world's population living on less than x per day."""
    income = data.global_data()["income"]
    grid, cdf = income["grid"], income["cdf"]
    if x <= 0:
        return 0.0
    if x <= grid[0]:
        return cdf[0] * x / grid[0]
    if x >= grid[-1]:
        return cdf[-1]
    i = bisect.bisect_right(grid, x) - 1
    lx, l0, l1 = math.log(x), math.log(grid[i]), math.log(grid[i + 1])
    return cdf[i] + (cdf[i + 1] - cdf[i]) * (lx - l0) / (l1 - l0)


def global_quantile(p):
    """Income ($/day, 2017 PPP) below which share p of the world lives."""
    income = data.global_data()["income"]
    grid, cdf = income["grid"], income["cdf"]
    if p <= cdf[0]:
        return grid[0] * p / cdf[0] if cdf[0] else grid[0]
    if p >= cdf[-1]:
        return grid[-1]
    i = bisect.bisect_right(cdf, p) - 1
    while cdf[i + 1] == cdf[i]:
        i += 1
    l0, l1 = math.log(grid[i]), math.log(grid[i + 1])
    return math.exp(l0 + (l1 - l0) * (p - cdf[i]) / (cdf[i + 1] - cdf[i]))
