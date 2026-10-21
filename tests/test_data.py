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
    # PIP September 2026: about 824 million people (10.1%) below $3.00 a day in 2024.
    assert 0.09 < global_cdf(3.0) < 0.11
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
        assert math.isclose(national_cdf(dist, dist["median"]), 0.5, abs_tol=0.01), c["iso3"]
        xs = [dist["x"][0] * 0.5] + dist["x"] + [dist["x"][-1] * 5]
        values = [national_cdf(dist, x) for x in xs]
        assert all(b >= a for a, b in zip(values, values[1:])), c["iso3"]
        for p in (0.005, 0.03, 0.3, 0.75, 0.97, 0.995):
            assert math.isclose(national_cdf(dist, national_quantile(dist, p)), p, abs_tol=1e-6), c["iso3"]


def test_education_shares_sum_to_one():
    edu = data.global_data()["education"]
    assert math.isclose(sum(edu["world_shares"]), 1, abs_tol=1e-3)
    for c in data.countries():
        if "education" in c:
            assert math.isclose(sum(c["education"]["shares"]), 1, abs_tol=1e-3), c["iso3"]


def test_price_data_is_sane():
    us = data.country("USA")["prices"]
    assert us["ppp_2021"] == 1.0
    # US consumer prices rose about 16% from 2021 to 2024 (IMF: 8.0%, 4.1%, 3.0%).
    assert 1.14 < us["price_index"]["2024"] < 1.18


def test_imf_inflation_agrees_with_pip_survey_cpi():
    """PIP reports each survey year's CPI relative to 2021; our IMF-based index should agree."""
    import csv
    path = data.DATA_DIR / "raw" / "pip_surveys.csv"
    if not path.exists():
        import pytest
        pytest.skip("raw PIP download not available (run scripts/build_data.py)")
    ratios = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            year = row["reporting_year"]
            c = data.country(row["country_code"])
            if not c or "prices" not in c or year not in ("2022", "2023", "2024") or not row["cpi"]:
                continue
            if row["country_code"] in ("HRV", "BGR", "SLE", "BLR", "MRT"):
                continue  # PIP's CPI for these folds in the currency change
            ratios.append(c["prices"]["price_index"][year] / float(row["cpi"]))
    # PIP deflates to the survey period, the IMF uses annual averages, and a few
    # countries (Argentina, Lebanon, Nigeria) have since rebased or had very high
    # inflation, so require broad agreement rather than an exact match.
    close = sum(0.9 < r < 1.1 for r in ratios)
    assert len(ratios) > 20 and close / len(ratios) > 0.9, (close, len(ratios))


def test_exact_income_coverage():
    exact = {c["iso3"] for c in data.countries() if c.get("prices", {}).get("exact_income")}
    assert {"USA", "VNM", "CHL", "SVK", "ARG", "HRV", "BGR", "SLE"} <= exact
    assert not {"ZWE", "VEN"} & exact


def test_location_shares():
    total = sum(c.get("gdp_pc_population_share_same", 0) for c in data.countries())
    assert math.isclose(total, 1, abs_tol=1e-3)
