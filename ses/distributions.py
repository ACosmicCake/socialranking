"""Income distribution helpers (reference implementation of static/js/ses.js).

A national distribution is stored as PIP's income thresholds ``x`` at
population shares ``p`` (1st to 99th percentile, see scripts/build_data.py):

* below the first threshold: linear from zero
* between thresholds: linear in log income
* above the last threshold: Pareto with the stored alpha

The global distribution is a calibrated CDF on a log-spaced grid.
All incomes are per person per day in 2021 international dollars (PPP).
"""

import bisect
import math

from . import data


def national_cdf(dist, x):
    """Share of the national population with income/consumption below x."""
    ps, xs = dist["p"], dist["x"]
    if x <= 0:
        return 0.0
    if x < xs[0]:
        return ps[0] * x / xs[0]
    if x >= xs[-1]:
        return 1 - (1 - ps[-1]) * (xs[-1] / x) ** dist["pareto_alpha"]
    i = bisect.bisect_right(xs, x) - 1
    frac = (math.log(x) - math.log(xs[i])) / (math.log(xs[i + 1]) - math.log(xs[i]))
    return ps[i] + frac * (ps[i + 1] - ps[i])


def national_quantile(dist, p):
    """Inverse of national_cdf: income at population share p (0-1)."""
    ps, xs = dist["p"], dist["x"]
    if p <= ps[0]:
        return xs[0] * p / ps[0]
    if p >= ps[-1]:
        return xs[-1] * ((1 - ps[-1]) / max(1 - p, 1e-9)) ** (1 / dist["pareto_alpha"])
    i = bisect.bisect_right(ps, p) - 1
    frac = (p - ps[i]) / (ps[i + 1] - ps[i])
    return math.exp(math.log(xs[i]) + frac * (math.log(xs[i + 1]) - math.log(xs[i])))


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
    """Income ($/day, 2021 PPP) below which share p of the world lives."""
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
