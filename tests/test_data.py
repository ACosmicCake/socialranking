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
    assert len(edu["world_shares"]) == 9
    assert math.isclose(sum(edu["world_shares"]), 1, abs_tol=1e-3)
    assert edu["population_25_plus_covered"] / edu["population_25_plus_world"] > 0.95
    for c in data.countries():
        if "education" in c:
            assert math.isclose(sum(c["education"]["shares"]), 1, abs_tol=1e-3), c["iso3"]
            assert min(c["education"]["shares"]) >= 0, c["iso3"]
    for group in edu["groups"].values():
        for shares in group.values():
            assert math.isclose(sum(shares), 1, abs_tol=2e-3)


def test_regional_mixtures_match_pip_regions():
    """Our population-weighted regional mixtures should reproduce PIP's regional
    headcounts at $3.00 (where WDI and PIP use the same region codes)."""
    regions = data.global_data()["income"]["pip_regions"]
    by_region = {}
    for c in data.countries():
        if c.get("income") and c.get("region"):
            by_region.setdefault(c["region"], []).append(c)
    checked = 0
    for code, official in regions.items():
        if code not in by_region:
            continue
        members = by_region[code]
        share = sum(c["population"] * national_cdf(c["income"], 3.0) for c in members) / \
            sum(c["population"] for c in members)
        assert abs(share - official["share_below_3"]) < 0.02, (code, share, official["share_below_3"])
        checked += 1
    assert checked >= 6


def test_history_and_nowcast():
    history = data.global_data()["income"]["history"]
    assert {"1990", "2024", "2026"} <= set(history)
    assert history["1990"]["share_below_3"] > history["2024"]["share_below_3"]


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


def test_findex_resilience_shares():
    findex = data.global_data()["findex"]
    for group, w in findex.items():
        assert math.isclose(sum(w["shares"]), 1, abs_tol=1e-3), group
        assert len(w["shares"]) == len(w["keys"])
    # Emergency funds cover nearly all adults; the coverage question is asked in developing economies only.
    assert findex["emergency"]["adults_covered"] / findex["emergency"]["adults_world"] > 0.9
    assert findex["cover_expenses"]["economies"] > 80
    # Phone ownership: about 85% of adults own a phone and two-thirds use a smartphone (Findex 2025).
    assert findex["phone"]["economies"] > 120
    yes = data.global_data()["findex_yes"]
    assert all(v["economies"] > (90 if k == "saved_old_age" else 120) for k, v in yes.items())
    assert 0.4 < yes["saved"]["share"] < 0.7 and 0.15 < yes["borrowed"]["share"] < 0.4
    assert 0.5 < yes["digital_payment"]["share"] < 0.8
    assert 0.08 < findex["phone"]["shares"][0] < 0.25 and 0.55 < findex["phone"]["shares"][2] < 0.8
    for c in data.countries():
        for group, v in c.get("findex", {}).items():
            if group != "emergency_amount":
                assert math.isclose(sum(v["shares"]), 1, abs_tol=1e-3), (c["iso3"], group)


def test_healthy_diet_costs():
    hd = data.global_data()["healthy_diet"]
    assert 0.2 < hd["world"]["unaffordable_share"] < 0.5
    assert hd["checked"] > 120 and len(hd["outliers"]) <= 5
    costs = [c["healthy_diet"]["cost_2021ppp"] for c in data.countries() if "cost_2021ppp" in c.get("healthy_diet", {})]
    assert len(costs) > 140
    assert all(1 < x < 10 for x in costs)


def test_occupation_shares():
    occ = data.global_data()["occupation"]
    assert len(occ["keys"]) == len(occ["skill_levels"]) == len(occ["shares"]) == 10
    assert math.isclose(sum(occ["shares"]), 1, abs_tol=1e-3)
    assert occ["economies"] > 100 and occ["employed_covered"] / occ["employed_world"] > 0.5
    assert "NGA" in occ["dropped"]  # miscoded survey
    for c in data.countries():
        o = c.get("occupation")
        if o:
            assert o["year"] >= occ["since"]
            assert math.isclose(sum(o["shares"]), 1, abs_tol=1e-3), c["iso3"]


def test_parent_cohorts():
    cohorts = data.global_data()["education"]["cohorts"]
    assert list(cohorts) == [str(y) for y in range(1965, 2016, 5)]
    for year, by_sex in cohorts.items():
        for sex, shares in by_sex.items():
            assert math.isclose(sum(shares), 1, abs_tol=1e-3)
    # Schooling expanded: fewer women without primary in each later generation, worldwide.
    no_school = [cohorts[y]["F"][0] for y in cohorts]
    assert all(b < a for a, b in zip(no_school, no_school[1:]))
    assert sum("cohorts" in c.get("education", {}) for c in data.countries()) > 130


def test_exchange_rates():
    # Official rates whose units match our PPPs: price level vs the US between 0.1 and 2.
    rated = [c for c in data.countries() if "exchange_rate" in c]
    assert len(rated) > 170
    vnm = next(c for c in rated if c["iso3"] == "VNM")["exchange_rate"]
    assert 20000 < vnm["lcu_per_usd"] < 30000 and vnm["year"] >= 2020


def test_aggregates_have_indicators():
    # Income-group aggregates come from the API under 2-character ids (XM, XN, XT, XD) with no
    # ISO3 code; they must still be stored under LIC/LMC/UMC/HIC like the regions and the world.
    aggregates = data.global_data()["aggregates"]
    for code in ["WLD", "EAS", "SSF", "LIC", "LMC", "UMC", "HIC"]:
        assert len(aggregates[code]["wdi"]) > 50, code
    le = {code: aggregates[code]["wdi"]["SP.DYN.LE00.IN"][1] for code in ["LIC", "LMC", "UMC", "HIC"]}
    assert le["LIC"] < le["LMC"] < le["UMC"] < le["HIC"]
