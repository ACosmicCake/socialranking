"""Sanity checks on the generated datasets."""

import math

from ses import data
from ses.distributions import global_cdf, global_quantile, national_cdf, national_quantile


def test_world_population_is_plausible():
    assert 7.9e9 < data.world_population() < 8.5e9


def test_country_list_has_major_economies():
    names = {c["iso3"] for c in data.countries()}
    for iso3 in ("USA", "CHN", "IND", "VNM", "NGA", "BRA", "DEU", "IDN"):
        assert iso3 in names


def test_global_cdf_matches_official_world_headcounts():
    # The calibrated curve must pass through PIP's published world headcounts.
    for anchor in data.global_data()["income"]["anchors"]:
        assert math.isclose(global_cdf(anchor["line"]), anchor["share_below"], abs_tol=0.002)


def test_uncalibrated_mixture_is_close_to_official():
    for v in data.global_data()["income"]["validation"]:
        assert abs(v["official"] - v["mixture"]) < 2.0


def test_global_cdf_is_monotonic_and_bounded():
    xs = [0.1 * 1.1 ** i for i in range(120)]
    values = [global_cdf(x) for x in xs]
    assert all(b >= a for a, b in zip(values, values[1:]))
    assert 0 <= values[0] and values[-1] <= 1


def test_global_quantile_inverts_cdf():
    for p in (0.1, 0.5, 0.9, 0.99):
        assert math.isclose(global_cdf(global_quantile(p)), p, abs_tol=1e-4)


def test_national_distributions_are_consistent():
    for c in data.countries():
        dist = c.get("income")
        if not dist:
            continue
        assert national_cdf(dist, dist["median"]) == 0.5
        assert dist["low"] < dist["thresholds"][0]
        xs = [dist["low"] * 0.5] + dist["thresholds"] + [dist["thresholds"][-1] * 5]
        values = [national_cdf(dist, x) for x in xs]
        assert all(b >= a for a, b in zip(values, values[1:])), c["iso3"]
        for p in (0.05, 0.3, 0.75, 0.95):
            assert math.isclose(national_cdf(dist, national_quantile(dist, p)), p, abs_tol=1e-6)


def test_education_shares_sum_to_one():
    edu = data.global_data()["education"]
    assert math.isclose(sum(edu["world_shares"]), 1, abs_tol=1e-3)
    for c in data.countries():
        if "education" in c:
            assert math.isclose(sum(c["education"]["shares"]), 1, abs_tol=1e-3), c["iso3"]


def test_price_data_is_sane():
    us = data.country("USA")["prices"]
    assert us["ppp_2017"] == 1.0
    # US consumer prices rose about 28% from 2017 to 2024.
    assert 1.2 < us["inflation_factor_since_2017"] < 1.35


def test_location_shares():
    total = sum(c.get("gdp_pc_population_share_same", 0) for c in data.countries())
    assert math.isclose(total, 1, abs_tol=1e-3)
