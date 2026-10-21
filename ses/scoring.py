"""Turn questionnaire answers into comparisons with the world's population.

Conventions
-----------
* A *percentile* here is the share of people (0-100) who are worse off than
  you on that measure.  For categorical answers (education level,
  vulnerability group, wealth band) we use the mid-rank: everyone in a lower
  category plus half of the people in your own category.
* Each dimension is compared against its own source population: everyone
  (income, services), adults 25-64 (education), adults 15+ (Gallup, Findex)
  or adults (wealth).
* The SES index is the plain average of the dimension percentiles you
  answered.  It summarises your position; it is *not* itself a percentile,
  because no dataset gives the joint distribution of all dimensions.
"""

import datetime
import math

from . import data, facts
from .distributions import global_cdf, global_quantile, national_cdf, national_quantile
from .questionnaire import (COOKING_OPTIONS, EDUCATION_OPTIONS, FIES_ITEMS, INCOME_BANDS,
                            SANITATION_OPTIONS, WATER_OPTIONS, all_questions)

# Above this average annual inflation (or after a currency redenomination) a
# CPI-based conversion of today's income to 2017 prices isn't trustworthy.
MAX_RELIABLE_INFLATION = 1.0
MAX_EXTRAPOLATION_YEARS = 3
MAX_HOUSEHOLD_SIZE = 50

POVERTY_LINES_2017 = [
    (2.15, "International poverty line ($2.15)", "extreme poverty"),
    (3.65, "Lower-middle-income line ($3.65)", "the poverty line typical of lower-middle-income countries"),
    (6.85, "Upper-middle-income line ($6.85)", "the poverty line typical of upper-middle-income countries"),
]

DIMENSION_LABELS = {
    "income": "Income",
    "education": "Education",
    "living": "Living standards",
    "security": "Financial security",
    "wealth": "Wealth",
}


class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("invalid answers")
        self.errors = errors


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _number(raw):
    if raw is None:
        return None
    raw = str(raw).strip().replace(",", "").replace(" ", "").replace("_", "")
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def exact_income_available(country):
    """Can a local-currency amount be converted to 2017 PPP dollars?"""
    prices = country.get("prices")
    if not prices:
        return False
    return prices["inflation_recent_annual"] <= MAX_RELIABLE_INFLATION


def parse_answers(form):
    """Validate a submitted form (any mapping) -> clean answers dict.

    Raises ValidationError with {field: message}.
    """
    answers = {}
    errors = {}
    for _, q in all_questions():
        value = form.get(q["id"])
        value = value.strip() if isinstance(value, str) else value
        if q["type"] in ("radio", "ladder"):
            allowed = {key for key, _ in q["options"]}
            if value and value not in allowed:
                errors[q["id"]] = "Please choose one of the options."
                continue
        answers[q["id"]] = value or None

    country = data.country(answers.get("country") or "")
    if country is None:
        errors["country"] = "Please choose your country."
    if not answers.get("education"):
        errors["education"] = "Please choose your highest completed level of education."

    mode = answers.get("income_mode")
    if mode == "exact":
        if country is not None and not exact_income_available(country):
            errors["income_mode"] = (f"We don't have reliable price data for {country['name']}, "
                                     "so please pick a range instead.")
        amount = _number(answers.get("income_amount"))
        size = _number(answers.get("household_size"))
        if amount is None or amount < 0:
            errors["income_amount"] = "Please enter your household income as a number (0 or more)."
        if size is None or size < 1 or size > MAX_HOUSEHOLD_SIZE or size != int(size):
            errors["household_size"] = f"Please enter a whole number of people from 1 to {MAX_HOUSEHOLD_SIZE}."
        if answers.get("income_period") not in ("month", "year"):
            errors["income_period"] = "Please say whether the amount is per month or per year."
        answers["income_amount"] = amount
        answers["household_size"] = int(size) if size and size == int(size) else size
    elif mode == "band":
        if not answers.get("income_band"):
            errors["income_band"] = "Please choose a range."
    else:
        errors["income_mode"] = "Please choose how you'd like to answer the income question."

    answers["research_consent"] = form.get("research_consent") in ("on", "yes", "true", "1", True)

    if errors:
        raise ValidationError(errors)
    return answers


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

def _pct(share):
    return round(100 * share, 1)


def _people(share):
    return share * data.world_population()


def to_ppp_per_day(amount, period, household_size, country, today=None):
    """Local-currency household income -> 2017 international $ per person per day."""
    today = today or datetime.date.today()
    prices = country["prices"]
    per_day = amount * (12 if period == "month" else 1) / 365 / household_size
    years_ahead = max(0, min(today.year - prices["inflation_latest_year"], MAX_EXTRAPOLATION_YEARS))
    price_level = prices["inflation_factor_since_2017"] * (1 + prices["inflation_recent_annual"]) ** years_ahead
    return {
        "local_per_day": per_day,
        "price_level_vs_2017": price_level,
        "extrapolated_years": years_ahead,
        "prices_through": prices["inflation_latest_year"],
        "recent_inflation": prices["inflation_recent_annual"],
        "ppp_2017": prices["ppp_2017"],
        "ppp_per_day": per_day / price_level / prices["ppp_2017"],
    }


def score_income(answers, country, today=None):
    dist = country.get("income")
    result = {"mode": answers["income_mode"], "national_available": dist is not None}
    if answers["income_mode"] == "exact":
        conv = to_ppp_per_day(answers["income_amount"], answers["income_period"],
                              answers["household_size"], country, today)
        x = conv["ppp_per_day"]
        result.update(conv)
        result["global_share"] = global_cdf(x)
        if dist:
            result["national_share"] = national_cdf(dist, x)
    else:
        key, low, high, label = next(b for b in INCOME_BANDS if b[0] == answers["income_band"])
        x = math.sqrt(low * high) if low else high / 2
        result.update({"band_label": label, "band_low": low, "band_high": high, "ppp_per_day": x})
        g_low, g_high = global_cdf(low), global_cdf(high)
        result.update({"global_share": (g_low + g_high) / 2,
                       "global_range": (_pct(g_low), _pct(g_high))})
        if dist:
            n_low, n_high = national_cdf(dist, low), national_cdf(dist, high)
            result.update({"national_share": (n_low + n_high) / 2,
                           "national_range": (_pct(n_low), _pct(n_high))})

    share = result["global_share"]
    result["global_pct"] = _pct(share)
    result["top_pct"] = round(100 - 100 * share, 1)
    result["people_below"] = _people(share)
    result["person_of_100"] = min(100, max(1, math.ceil(share * 100)))
    if "national_share" in result:
        result["national_pct"] = _pct(result["national_share"])
    result["lines"] = [
        {"line": line, "label": label, "meaning": meaning, "above": x >= line,
         "share_below": _pct(global_cdf(line))}
        for line, label, meaning in POVERTY_LINES_2017
    ]
    result["world_median"] = data.global_data()["income"]["world_median"]
    result["multiple_of_world_median"] = x / result["world_median"]
    result["chart"] = income_chart(country, x)
    return result


def income_chart(country, x):
    """Points for the cumulative-distribution chart on the results page."""
    grid = [0.5 * (1.12 ** i) for i in range(0, 72)]  # $0.50 .. ~$1,500 a day
    dist = country.get("income")
    return {
        "x": [round(v, 3) for v in grid],
        "world": [round(100 * global_cdf(v), 2) for v in grid],
        "country": [round(100 * national_cdf(dist, v), 2) for v in grid] if dist else None,
        "you": round(x, 3),
        "you_world": round(100 * global_cdf(x), 2),
        "you_country": round(100 * national_cdf(dist, x), 2) if dist else None,
    }


def _midrank(shares, index):
    return sum(shares[:index]) + shares[index] / 2


def score_education(answers, country):
    keys = [k for k, _ in EDUCATION_OPTIONS]
    idx = keys.index(answers["education"])
    edu = data.global_data()["education"]
    world = edu["world_shares"]
    result = {
        "level": idx,
        "label": EDUCATION_OPTIONS[idx][1],
        "global_pct": _pct(_midrank(world, idx)),
        "world_shares": [_pct(s) for s in world],
        "same_level_pct": _pct(world[idx]),
        "higher_pct": _pct(sum(world[idx + 1:])),
        "levels": [label for _, label in EDUCATION_OPTIONS],
        "year": edu["year"],
    }
    if country.get("education"):
        shares = country["education"]["shares"]
        result.update({
            "national_pct": _pct(_midrank(shares, idx)),
            "country_shares": [_pct(s) for s in shares],
            "country_mean_years": country["education"]["mean_years"],
        })
    return result


def _access_items(answers):
    """Map answers to (has_service: bool|None, status label) per service."""
    cooking = {k: clean for k, _, clean in COOKING_OPTIONS}
    water = {k: label for k, _, label in WATER_OPTIONS}
    sanitation = {k: label for k, _, label in SANITATION_OPTIONS}
    yes_no = {"yes": True, "no": False}
    items = {}

    items["electricity"] = (yes_no.get(answers.get("electricity")), None)
    c = answers.get("cooking")
    items["clean_cooking"] = (cooking.get(c) if c else None,
                              "No cooking at home" if c == "none" else None)
    w = answers.get("water")
    items["water"] = ((w == "safely_managed") if w else None, water.get(w))
    s = answers.get("sanitation")
    items["sanitation"] = ((s == "safely_managed") if s else None, sanitation.get(s))
    items["hygiene"] = (yes_no.get(answers.get("hygiene")), None)
    items["internet"] = (yes_no.get(answers.get("internet")), None)
    h = answers.get("health_hardship")
    items["health_hardship"] = ({"no": True, "yes": False}.get(h), None)
    return items


def score_living(answers):
    """Average of per-service percentile ranks.

    For one service with a share s of people lacking it, having it puts you
    at mid-rank (s + 1)/2 and lacking it at s/2.  We average these over the
    services answered, which needs no assumption about how deprivations
    overlap.  We also report the strict lower bound: at least max(s) of
    people lack something you have.
    """
    items = []
    ranks = []
    for key, (has, status) in _access_items(answers).items():
        info = facts.ACCESS[key]
        s = info["share_without"]
        item = {
            "key": key,
            "label": info["label"],
            "has": has,
            "status": status,
            "share_without_pct": _pct(s),
            "people_without": info["people_without"],
            "note": info["note"],
            "cite": info["cite"],
            "year": info["year"],
        }
        items.append(item)
        if has is not None:
            ranks.append((s + 1) / 2 if has else s / 2)
    answered = [i for i in items if i["has"] is not None]
    if not answered:
        return {"items": items, "answered": 0}
    have = [i for i in answered if i["has"]]
    lacking = [i for i in answered if not i["has"]]
    return {
        "items": items,
        "answered": len(answered),
        "global_pct": _pct(sum(ranks) / len(ranks)),
        "lower_bound_pct": max((i["share_without_pct"] for i in have), default=0.0),
        "lacking": [i["label"] for i in lacking],
        "water_status": answers.get("water"),
        "sanitation_status": answers.get("sanitation"),
    }


def score_security(answers):
    result = {}
    food, shelter, count_on = (answers.get(k) for k in ("food_money", "shelter_money", "count_on"))
    if food and shelter and (count_on or (food == "no" and shelter == "no")):
        struggled = "yes" in (food, shelter)
        group = "low" if not struggled else ("moderate" if count_on == "yes" else "high")
        shares = [facts.GALLUP_VULNERABILITY[g]["share"] for g in facts.GALLUP_ORDER]
        idx = facts.GALLUP_ORDER.index(group)
        result.update({
            "gallup_group": group,
            "gallup_label": facts.GALLUP_VULNERABILITY[group]["label"],
            "gallup_definition": facts.GALLUP_VULNERABILITY[group]["definition"],
            "gallup_share_pct": _pct(shares[idx]),
            "global_pct": _pct(_midrank(shares, idx)),
        })

    fies = [answers.get(k) for k, _ in FIES_ITEMS]
    if all(fies):
        raw = sum(a == "yes" for a in fies)
        if raw == 0:
            level = "secure"
        elif raw <= 3:
            level = "mild"
        elif raw <= 6:
            level = "moderate"
        else:
            level = "severe"
        result.update({"fies_raw": raw, "fies_level": level})
    result["fies_answered"] = sum(a is not None for a in fies)

    for key in ("account", "saved"):
        if answers.get(key):
            result[key] = answers[key] == "yes"
    return result


def score_wealth(answers):
    band = answers.get("wealth")
    if not band or band == "skip":
        return {}
    keys = [b["key"] for b in facts.WEALTH_PYRAMID]
    idx = keys.index(band)
    shares = [b["share"] for b in facts.WEALTH_PYRAMID]
    below = sum(shares[:idx])
    return {
        "band": facts.WEALTH_PYRAMID[idx]["label"],
        "range": (_pct(below), _pct(below + shares[idx])),
        "global_pct": _pct(_midrank(shares, idx)),
        "pyramid": [{"label": b["label"], "pct": _pct(b["share"]), "you": i == idx}
                    for i, b in enumerate(facts.WEALTH_PYRAMID)],
    }


def score_location(country):
    if "gdp_per_capita_usd" not in country:
        return {}
    share = country["gdp_pc_population_share_below"] + country["gdp_pc_population_share_same"] / 2
    return {
        "gdp_per_capita_usd": country["gdp_per_capita_usd"],
        "gdp_year": country["gdp_year"],
        "global_pct": _pct(share),
        "share_in_poorer_countries_pct": _pct(country["gdp_pc_population_share_below"]),
    }


def ladder_rung(pct):
    """Map a 0-100 percentile onto the 10-rung MacArthur ladder."""
    return min(10, max(1, math.ceil(pct / 10)))


def score(answers, today=None):
    country = data.country(answers["country"])
    result = {
        "country": {k: country.get(k) for k in ("iso3", "name", "currency", "currency_name", "population")},
        "income": score_income(answers, country, today),
        "education": score_education(answers, country),
        "living": score_living(answers),
        "security": score_security(answers),
        "wealth": score_wealth(answers),
        "location": score_location(country),
        "world_population": data.world_population(),
    }
    if country.get("income"):
        result["country"]["survey"] = {k: country["income"][k] for k in ("survey_year", "welfare_type", "coverage")}
        result["country"]["median_ppp"] = country["income"]["median"]

    dims = []
    for key in ("income", "education", "living", "security", "wealth"):
        pct = result[key].get("global_pct")
        if pct is not None:
            dims.append({"key": key, "label": DIMENSION_LABELS[key], "pct": pct})
    result["dimensions"] = dims
    result["ses_index"] = round(sum(d["pct"] for d in dims) / len(dims), 1)

    perception = {"measured_rung": ladder_rung(result["ses_index"])}
    for key in ("ladder_country", "ladder_world"):
        if answers.get(key):
            perception[key] = int(answers[key])
    if "ladder_world" in perception:
        perception["gap"] = perception["ladder_world"] - perception["measured_rung"]
    if "national_pct" in result["income"]:
        perception["national_income_rung"] = ladder_rung(result["income"]["national_pct"])
    result["perception"] = perception
    return result


def describe_quantiles(country=None):
    """World (and optionally national) income at selected percentiles, for the methodology page."""
    rows = []
    dist = country.get("income") if country else None
    for p in (10, 25, 50, 75, 90, 99):
        row = {"p": p, "world": global_quantile(p / 100)}
        if dist:
            row["country"] = national_quantile(dist, p / 100)
        rows.append(row)
    return rows
