import pytest

from ses import facts, scoring
from tests.conftest import TODAY


def run(answers):
    return scoring.score(scoring.parse_answers(answers), today=TODAY)


def test_full_answers_produce_all_dimensions(full_answers):
    r = run(full_answers)
    assert [d["key"] for d in r["dimensions"]] == ["income", "education", "living", "security", "wealth"]
    assert 0 < r["ses_index"] < 100
    assert r["perception"]["ladder_world"] == 5
    assert 1 <= r["perception"]["measured_rung"] <= 10


def test_income_conversion(full_answers):
    r = run(full_answers)
    inc = r["income"]
    expected_local = 20_000_000 * 12 / 365 / 4
    assert inc["local_per_day"] == pytest.approx(expected_local)
    assert inc["ppp_per_day"] == pytest.approx(expected_local / inc["price_level_vs_2017"] / inc["ppp_2017"])
    assert 0 < inc["global_pct"] < 100 and 0 < inc["national_pct"] < 100


def test_more_income_ranks_higher(full_answers):
    low = run({**full_answers, "income_amount": "5000000"})["income"]
    high = run({**full_answers, "income_amount": "80000000"})["income"]
    assert high["global_pct"] > low["global_pct"]
    assert high["national_pct"] > low["national_pct"]


def test_us_median_household_is_near_national_median(full_answers):
    # A US household at the national median per-capita income should land near the 50th percentile.
    import ses.data as data
    us = data.country("USA")
    median_2017 = us["income"]["median"]
    r = scoring.score(scoring.parse_answers({**full_answers, "country": "USA", "income_amount": "1", "household_size": "1"}),
                      today=TODAY)
    price_level = r["income"]["price_level_vs_2017"]
    monthly = median_2017 * price_level * 365 / 12
    r = run({**full_answers, "country": "USA", "income_amount": f"{monthly:.2f}", "household_size": "1"})
    assert r["income"]["national_pct"] == pytest.approx(50, abs=0.2)
    assert r["income"]["global_pct"] > 85


def test_yearly_period_matches_monthly(full_answers):
    monthly = run(full_answers)["income"]["ppp_per_day"]
    yearly = run({**full_answers, "income_amount": "240000000", "income_period": "year"})["income"]["ppp_per_day"]
    assert yearly == pytest.approx(monthly)


def test_band_mode_reports_range(minimal_answers):
    r = run(minimal_answers)
    inc = r["income"]
    lo, hi = inc["global_range"]
    assert lo < inc["global_pct"] < hi
    assert [d["key"] for d in r["dimensions"]] == ["income", "education"]


def test_zero_income_is_bottom(full_answers):
    r = run({**full_answers, "income_amount": "0"})
    assert r["income"]["global_pct"] == 0
    assert r["income"]["person_of_100"] == 1


def test_education_midrank(minimal_answers):
    lowest = run({**minimal_answers, "education": "none"})["education"]
    highest = run({**minimal_answers, "education": "tertiary"})["education"]
    assert lowest["global_pct"] < 10
    assert highest["global_pct"] > 90
    assert highest["higher_pct"] == 0


def test_living_standards_scores(full_answers):
    everything = run(full_answers)["living"]
    s = [a["share_without"] for a in facts.ACCESS.values()]
    assert everything["global_pct"] == pytest.approx(100 * sum((x + 1) / 2 for x in s) / len(s), abs=0.1)
    assert everything["lower_bound_pct"] == pytest.approx(100 * max(s), abs=0.1)
    nothing = run({**full_answers, "electricity": "no", "cooking": "biomass", "water": "surface",
                   "sanitation": "open", "hygiene": "no", "internet": "no", "health_hardship": "yes"})["living"]
    assert nothing["global_pct"] < everything["global_pct"]
    assert len(nothing["lacking"]) == 7


def test_no_cooking_at_home_is_not_counted(full_answers):
    r = run({**full_answers, "cooking": "none"})["living"]
    assert r["answered"] == 6


def test_gallup_groups(full_answers):
    low = run(full_answers)["security"]
    assert low["gallup_group"] == "low"
    moderate = run({**full_answers, "food_money": "yes"})["security"]
    assert moderate["gallup_group"] == "moderate"
    high = run({**full_answers, "food_money": "yes", "count_on": "no"})["security"]
    assert high["gallup_group"] == "high"
    assert high["global_pct"] < moderate["global_pct"] < low["global_pct"]


def test_fies_levels(full_answers):
    keys = [k for k in full_answers if k.startswith("fies_")]
    assert run(full_answers)["security"]["fies_level"] == "secure"
    answers = {**full_answers, **{k: "yes" for k in keys[:5]}}
    assert run(answers)["security"]["fies_level"] == "moderate"
    answers = {**full_answers, **{k: "yes" for k in keys}}
    assert run(answers)["security"]["fies_raw"] == 8
    assert run(answers)["security"]["fies_level"] == "severe"


def test_wealth_skip_and_bands(full_answers):
    assert run({**full_answers, "wealth": "skip"})["wealth"] == {}
    top = run({**full_answers, "wealth": "over_1m"})["wealth"]
    assert top["range"] == (98.5, 100.0)


@pytest.mark.parametrize("field,value", [
    ("country", "XXX"),
    ("income_mode", ""),
    ("income_amount", "abc"),
    ("income_amount", "-5"),
    ("household_size", "0"),
    ("household_size", "2.5"),
    ("education", ""),
    ("water", "not-an-option"),
])
def test_validation_errors(full_answers, field, value):
    with pytest.raises(scoring.ValidationError) as e:
        scoring.parse_answers({**full_answers, field: value})
    assert field in e.value.errors


def test_exact_mode_rejected_without_reliable_prices(full_answers):
    for iso3 in ("ZWE", "CHL"):  # hyperinflation / missing PPP
        with pytest.raises(scoring.ValidationError) as e:
            scoring.parse_answers({**full_answers, "country": iso3})
        assert "income_mode" in e.value.errors


def test_country_without_survey_has_no_national_rank(minimal_answers):
    r = run({**minimal_answers, "country": "SAU"})
    assert "national_pct" not in r["income"]
    assert r["income"]["national_available"] is False
