"""Build the datasets the quiz scores against.

Every number the quiz uses either comes out of this script or out of the
hand-curated, cited figures in ``ses/facts.py``.  This script downloads raw
files from pinned commits of public GitHub mirrors, so re-running it always
produces the same output:

* World Bank Poverty and Inequality Platform (PIP), as published by
  Our World in Data (owid/poverty-data)       -> income distributions
* World Bank WDI mirrors from datahub.io (datasets/*)
    - SP.POP.TOTL  population
    - NY.GDP.MKTP.CD  GDP (current US$)
    - PA.NUS.PPP  PPP conversion factor (LCU per international $)
    - FP.CPI.TOTL.ZG  consumer price inflation (annual %)
  plus ISO 3166 / ISO 4217 country and currency codes
* Barro-Lee Educational Attainment Dataset v3 (barrolee/BarroLeeDataSet)
                                              -> education distributions

Usage:  pip install -r requirements-dev.txt && python scripts/build_data.py
"""

import json
import math
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data"

# Pinned commits: bump these deliberately when refreshing the data.
SOURCES = {
    "pip": {
        "url": "https://raw.githubusercontent.com/owid/poverty-data/"
               "52ef469292cfe29b7d492813b5c97e631abd5427/datasets/pip_dataset.csv",
        "file": "pip_dataset.csv",
        "name": "World Bank Poverty and Inequality Platform (via Our World in Data, owid/poverty-data)",
        "home": "https://github.com/owid/poverty-data",
    },
    "population": {
        "url": "https://raw.githubusercontent.com/datasets/population/"
               "d4b1a4a9a17e2123baf0ef119de05bceced1ab1b/data/population.csv",
        "file": "population.csv",
        "name": "World Bank WDI SP.POP.TOTL (via datahub.io datasets/population)",
        "home": "https://github.com/datasets/population",
    },
    "gdp": {
        "url": "https://raw.githubusercontent.com/datasets/gdp/"
               "36d761dc5617982d3e50b213e02b9a1b47c4e958/data/gdp.csv",
        "file": "gdp.csv",
        "name": "World Bank WDI NY.GDP.MKTP.CD (via datahub.io datasets/gdp)",
        "home": "https://github.com/datasets/gdp",
    },
    "ppp": {
        "url": "https://raw.githubusercontent.com/datasets/ppp/"
               "f997d4ce8272975292b555c437dbdbe98940f0cf/data/ppp-gdp.csv",
        "file": "ppp-gdp.csv",
        "name": "World Bank WDI PA.NUS.PPP (via datahub.io datasets/ppp)",
        "home": "https://github.com/datasets/ppp",
    },
    "cpi": {
        "url": "https://raw.githubusercontent.com/datasets/cpi/"
               "3750e45064a99b0452deb1423a416e4d5473a58e/data/cpi.csv",
        "file": "cpi.csv",
        "name": "World Bank WDI FP.CPI.TOTL (via datahub.io datasets/cpi)",
        "home": "https://github.com/datasets/cpi",
    },
    "country_codes": {
        "url": "https://raw.githubusercontent.com/datasets/country-codes/"
               "2d84034a0cae19ea5444b78c2131304a5c7f4bb9/data/country-codes.csv",
        "file": "country-codes.csv",
        "name": "ISO 3166 / ISO 4217 codes (via datahub.io datasets/country-codes)",
        "home": "https://github.com/datasets/country-codes",
    },
    "barro_lee": {
        "url": "https://raw.githubusercontent.com/barrolee/BarroLeeDataSet/"
               "ee575b42f659bad7445dfc26d19816ede8000e47/BLData/BL_v3_MF2564.csv",
        "file": "BL_v3_MF2564.csv",
        "name": "Barro-Lee Educational Attainment Dataset v3, ages 25-64",
        "home": "https://github.com/barrolee/BarroLeeDataSet",
    },
}

PPP_BASE_YEAR = 2017      # PIP data below are expressed in 2017 international $
GLOBAL_REF_YEAR = 2019    # latest lined-up World estimate in the PIP release

# World headcount ratios published by PIP are reported at these lines ($/day).
WORLD_ANCHOR_COLUMNS = {
    1.0: "headcount_ratio_100",
    2.15: "headcount_ratio_international_povline",
    3.65: "headcount_ratio_lower_mid_income_povline",
    6.85: "headcount_ratio_upper_mid_income_povline",
    10.0: "headcount_ratio_1000",
    20.0: "headcount_ratio_2000",
    30.0: "headcount_ratio_3000",
    40.0: "headcount_ratio_4000",
}

# Names in the OWID PIP file that don't match a World Bank population name.
PIP_NAME_TO_ISO3 = {
    "Cape Verde": "CPV",
    "Congo": "COG",
    "Cote d'Ivoire": "CIV",
    "Czechia": "CZE",
    "Democratic Republic of Congo": "COD",
    "Egypt": "EGY",
    "Gambia": "GMB",
    "Iran": "IRN",
    "Kyrgyzstan": "KGZ",
    "Laos": "LAO",
    "Micronesia (country)": "FSM",
    "Palestine": "PSE",
    "Russia": "RUS",
    "Saint Lucia": "LCA",
    "Slovakia": "SVK",
    "South Korea": "KOR",
    "Syria": "SYR",
    "Taiwan": "TWN",
    "Timor": "TLS",
    "Turkey": "TUR",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
    "Yemen": "YEM",
}

# Barro-Lee uses a few legacy World Bank codes.
BARRO_LEE_CODE_FIXES = {"ROM": "ROU", "ZAR": "COD", "TMP": "TLS", "SER": "SRB"}

# Economies that have no ISO 3166 entry or a different code in the WB files.
EXTRA_ECONOMIES = {
    "XKX": {"name": "Kosovo", "currency": "EUR", "currency_name": "Euro"},
    "TWN": {"name": "Taiwan", "currency": "TWD", "currency_name": "New Taiwan Dollar"},
    "CHI": {"name": "Channel Islands", "currency": "GBP", "currency_name": "Pound Sterling"},
}

# Friendlier display names where the CLDR short name is ambiguous or terse.
DISPLAY_NAMES = {
    "USA": "United States",
    "GBR": "United Kingdom",
    "COG": "Congo (Republic)",
    "COD": "Congo (Democratic Republic)",
    "FSM": "Micronesia (Federated States)",
    "BIH": "Bosnia and Herzegovina",
}

# Ordered education levels (Barro-Lee categories made mutually exclusive).
EDUCATION_LEVELS = [
    ("none", "No formal schooling"),
    ("primary_incomplete", "Some primary school"),
    ("primary", "Completed primary school"),
    ("secondary_incomplete", "Some secondary school"),
    ("secondary", "Completed secondary school"),
    ("tertiary_incomplete", "Some post-secondary / university"),
    ("tertiary", "Completed post-secondary / university degree"),
]


def fetch(key):
    """Download a source once into data/raw/ and return its path."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / SOURCES[key]["file"]
    if not path.exists():
        print(f"downloading {SOURCES[key]['url']}")
        urllib.request.urlretrieve(SOURCES[key]["url"], path)
    return path


def latest(df, code_col, value_col, max_year=None):
    """Latest non-null value per country -> {code: (year, value)}."""
    df = df.dropna(subset=[value_col])
    if max_year is not None:
        df = df[df["Year"] <= max_year]
    df = df.sort_values("Year").groupby(code_col).tail(1)
    return {r[code_col]: (int(r["Year"]), float(r[value_col])) for _, r in df.iterrows()}


def price_change_since_base(cpi_df, iso3):
    """Cumulative consumer-price change from PPP_BASE_YEAR to the latest year.

    The datahub "cpi" mirror holds WDI FP.CPI.TOTL.ZG, i.e. *annual inflation
    in percent* (despite its metadata describing an index), so we compound the
    yearly rates.  Returns None if any year is missing.
    """
    rates = cpi_df[(cpi_df["Country Code"] == iso3) & (cpi_df["Year"] > PPP_BASE_YEAR)]
    rates = rates.dropna(subset=["CPI"]).set_index("Year")["CPI"].sort_index()
    if rates.empty:
        return None
    years = list(range(PPP_BASE_YEAR + 1, int(rates.index.max()) + 1))
    if any(y not in rates.index for y in years):
        return None
    factor = float(np.prod([1 + rates[y] / 100 for y in years]))
    recent = rates.loc[years[-3:]]
    return {
        "factor": round(factor, 6),
        "latest_year": years[-1],
        "recent_annual": round(float(np.prod(1 + recent / 100)) ** (1 / len(recent)) - 1, 5),
    }


# ---------------------------------------------------------------------------
# Income distributions
# ---------------------------------------------------------------------------

def decile_average(row, k):
    """Mean welfare in decile k; derived from its share of the total when the
    average itself is missing (avg_k = share_k * mean * 10)."""
    avg = row[f"decile{k}_avg"]
    if pd.isna(avg):
        share = row[f"decile{k}_share"]
        if pd.isna(share) or pd.isna(row["mean"]):
            return None
        avg = share / 100 * row["mean"] * 10
    return float(avg)


def decile_distribution(row):
    """Describe a survey distribution by its decile thresholds plus tails.

    Returns a dict the app's ``ses.distributions`` module can evaluate:
    log-linear interpolation between decile thresholds, a linear bottom decile
    whose mean matches the published decile-1 average, and a Pareto top decile
    whose mean matches the published decile-10 average.
    """
    thr = [row[f"decile{k}_thr"] for k in (1, 2, 3, 4)] + [row["median"]] + \
          [row[f"decile{k}_thr"] for k in (6, 7, 8, 9)]
    if any(pd.isna(t) or t <= 0 for t in thr):
        return None
    thr = [float(t) for t in thr]
    if any(b <= a for a, b in zip(thr, thr[1:])):
        return None
    avg1 = decile_average(row, 1)
    avg10 = decile_average(row, 10)
    if avg1 is None or avg10 is None:
        return None
    # Bottom decile uniform on [low, thr1] with mean avg1  ->  low = 2*avg1 - thr1
    low = max(2 * avg1 - thr[0], thr[0] * 0.05)
    # Pareto tail above thr9: E[x | x > thr9] = alpha/(alpha-1) * thr9
    alpha = avg10 / (avg10 - thr[8]) if avg10 > thr[8] else 3.0
    alpha = min(max(alpha, 1.05), 10.0)
    return {
        "low": round(low, 4),
        "thresholds": [round(t, 4) for t in thr],
        "pareto_alpha": round(alpha, 4),
        "mean": round(float(row["mean"]), 4),
        "median": round(float(row["median"]), 4),
        "gini": None if pd.isna(row["gini"]) else round(float(row["gini"]), 4),
    }


def dist_cdf(dist, x):
    """CDF of a decile_distribution at x (vectorised). Mirrors ses.distributions."""
    x = np.asarray(x, dtype=float)
    thr = np.array(dist["thresholds"])
    low = dist["low"]
    out = np.empty_like(x)
    bottom = x < thr[0]
    out[bottom] = np.clip((x[bottom] - low) / (thr[0] - low), 0, 1) * 0.1
    top = x > thr[-1]
    out[top] = 1 - 0.1 * (thr[-1] / x[top]) ** dist["pareto_alpha"]
    mid = ~bottom & ~top
    out[mid] = np.interp(np.log(x[mid]), np.log(thr), np.arange(1, 10) / 10)
    return out


def build_income(pip, iso_by_name, population):
    pip = pip[pip["ppp_version"] == PPP_BASE_YEAR]

    countries = {}
    for name, group in pip.groupby("country"):
        iso3 = PIP_NAME_TO_ISO3.get(name) or iso_by_name.get(name)
        if iso3 is None:
            continue  # regional / income-group aggregates
        # Prefer national coverage; fall back to urban-only surveys (e.g. Argentina).
        for level in ("national", "urban"):
            rows = group[group["reporting_level"] == level].dropna(subset=["decile1_thr"])
            if len(rows):
                row = rows.sort_values("year").iloc[-1]
                dist = decile_distribution(row)
                if dist:
                    dist.update({
                        "survey_year": int(row["year"]),
                        "welfare_type": row["welfare_type"],
                        "coverage": level,
                    })
                    countries[iso3] = dist
                break

    world = pip[pip["country"] == "World"].set_index("year").loc[GLOBAL_REF_YEAR]
    anchors = sorted((line, float(world[col]) / 100) for line, col in WORLD_ANCHOR_COLUMNS.items())

    # Population-weighted mixture of national distributions = shape of the
    # global distribution; then calibrate it to PIP's official World headcounts.
    grid = np.exp(np.linspace(math.log(0.2), math.log(1500), 241))
    total = np.zeros_like(grid)
    weight = 0.0
    for iso3, dist in countries.items():
        pop = population.get(iso3, {}).get(GLOBAL_REF_YEAR)
        if not pop:
            continue
        total += pop * dist_cdf(dist, grid)
        weight += pop
    mixture = total / weight
    mix_at = lambda v: float(np.interp(math.log(v), np.log(grid), mixture))

    calibrated = np.empty_like(mixture)
    lines = [a[0] for a in anchors]
    for i, x in enumerate(grid):
        m = mixture[i]
        if x <= lines[0]:
            calibrated[i] = anchors[0][1] * m / mix_at(lines[0])
        elif x >= lines[-1]:
            m40, f40 = mix_at(lines[-1]), anchors[-1][1]
            calibrated[i] = f40 + (1 - f40) * (m - m40) / (1 - m40)
        else:
            j = next(k for k in range(len(lines) - 1) if lines[k] <= x <= lines[k + 1])
            (a, fa), (b, fb) = anchors[j], anchors[j + 1]
            ma, mb = mix_at(a), mix_at(b)
            calibrated[i] = fa + (fb - fa) * (m - ma) / (mb - ma)
    calibrated = np.maximum.accumulate(np.clip(calibrated, 0, 1))

    validation = [
        {"line": line, "official": round(share * 100, 2), "mixture": round(mix_at(line) * 100, 2)}
        for line, share in anchors
    ]
    covered = sum(population.get(c, {}).get(GLOBAL_REF_YEAR, 0) for c in countries)
    world_pop = population["WLD"][GLOBAL_REF_YEAR]
    global_income = {
        "ppp_year": PPP_BASE_YEAR,
        "reference_year": GLOBAL_REF_YEAR,
        "grid": [round(float(x), 4) for x in grid],
        "cdf": [round(float(f), 6) for f in calibrated],
        "anchors": [{"line": l, "share_below": round(s, 6)} for l, s in anchors],
        "validation": validation,
        "countries_in_mixture": len(countries),
        "population_coverage": round(covered / world_pop, 4),
        "world_mean": round(float(world["mean"]), 4),
        "world_median": round(float(world["median"]), 4),
    }
    return countries, global_income


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

def build_education(bl, known_iso3):
    bl = bl[bl["year"] == bl["year"].max()].copy()
    bl["iso3"] = bl["WBcode"].replace(BARRO_LEE_CODE_FIXES)
    countries = {}
    totals = np.zeros(len(EDUCATION_LEVELS))
    weight = 0.0
    for _, r in bl.iterrows():
        shares = np.array([
            r["lu"],
            r["lp"] - r["lpc"], r["lpc"],
            r["ls"] - r["lsc"], r["lsc"],
            r["lh"] - r["lhc"], r["lhc"],
        ], dtype=float).clip(min=0)
        shares = shares / shares.sum()
        if r["iso3"] in known_iso3:
            countries[r["iso3"]] = {
                "year": int(r["year"]),
                "shares": [round(float(s), 5) for s in shares],
                "mean_years": round(float(r["yr_sch"]), 2),
            }
        totals += shares * r["pop"]
        weight += r["pop"]
    world = totals / weight
    return countries, {
        "year": int(bl["year"].max()),
        "ages": "25-64",
        "levels": [{"key": k, "label": label} for k, label in EDUCATION_LEVELS],
        "world_shares": [round(float(s), 5) for s in world],
        "countries_covered": int(len(bl)),
        "population_covered_thousands": round(float(weight)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    codes = pd.read_csv(fetch("country_codes"), keep_default_na=False)
    pop_df = pd.read_csv(fetch("population"))
    gdp_df = pd.read_csv(fetch("gdp"))
    ppp_df = pd.read_csv(fetch("ppp"), keep_default_na=False, na_values=[""])
    cpi_df = pd.read_csv(fetch("cpi"))
    pip_df = pd.read_csv(fetch("pip"))
    bl_df = pd.read_csv(fetch("barro_lee"))

    population = {}
    for _, r in pop_df.iterrows():
        population.setdefault(r["Country Code"], {})[int(r["Year"])] = int(r["Value"])

    iso_meta = {}
    for _, r in codes.iterrows():
        iso3 = r["ISO3166-1-Alpha-3"]
        if not iso3:
            continue
        iso_meta[iso3] = {
            "iso2": r["ISO3166-1-Alpha-2"],
            "name": r["CLDR display name"] or r["official_name_en"],
            "currency": r["ISO4217-currency_alphabetic_code"].split(",")[0],
            "currency_name": r["ISO4217-currency_name"].split(",")[0],
        }
    for iso3, meta in EXTRA_ECONOMIES.items():
        iso_meta.setdefault(iso3, {"iso2": "", **meta})
    iso3_by_iso2 = {m["iso2"]: k for k, m in iso_meta.items() if m["iso2"]}
    iso3_by_iso2["XK"] = "XKX"

    # World Bank economies = codes in the population file that are real countries.
    wb_names = dict(zip(pop_df["Country Code"], pop_df["Country Name"]))
    economies = [c for c in wb_names if c in iso_meta]
    iso_by_name = {wb_names[c]: c for c in economies}
    iso_by_name.update({iso_meta[c]["name"]: c for c in economies})

    ppp_df["iso3"] = ppp_df["Country ID"].map(iso3_by_iso2)
    ppp_2017 = {r["iso3"]: float(r["PPP"]) for _, r in ppp_df[ppp_df["Year"] == PPP_BASE_YEAR].iterrows()
                if isinstance(r["iso3"], str) and not pd.isna(r["PPP"])}
    gdp_latest = latest(gdp_df, "Country Code", "Value")

    income, global_income = build_income(pip_df, iso_by_name, population)
    education, global_education = build_education(bl_df, set(economies))

    countries = []
    for iso3 in economies:
        pops = population[iso3]
        pop_year = max(pops)
        meta = iso_meta[iso3]
        entry = {
            "iso3": iso3,
            "name": DISPLAY_NAMES.get(iso3) or (wb_names[iso3] if iso3 in ("XKX", "CHI") else meta["name"]),
            "currency": meta["currency"] or None,
            "currency_name": meta["currency_name"] or None,
            "population": pops[pop_year],
            "population_year": pop_year,
        }
        if iso3 in gdp_latest:
            year, gdp = gdp_latest[iso3]
            if pops.get(year):
                entry["gdp_per_capita_usd"] = round(gdp / pops[year], 1)
                entry["gdp_year"] = year
        change = price_change_since_base(cpi_df, iso3) if iso3 in ppp_2017 else None
        if change:
            entry["prices"] = {
                "ppp_2017": round(ppp_2017[iso3], 6),
                "inflation_factor_since_2017": change["factor"],
                "inflation_latest_year": change["latest_year"],
                "inflation_recent_annual": change["recent_annual"],
            }
        if iso3 in income:
            entry["income"] = income[iso3]
        if iso3 in education:
            entry["education"] = education[iso3]
        countries.append(entry)
    countries.sort(key=lambda c: c["name"])

    # Location: share of world population in economies with lower GDP per capita.
    ranked = sorted((c for c in countries if "gdp_per_capita_usd" in c), key=lambda c: c["gdp_per_capita_usd"])
    ranked_pop = sum(c["population"] for c in ranked)
    below = 0
    for c in ranked:
        c["gdp_pc_population_share_below"] = round(below / ranked_pop, 5)
        c["gdp_pc_population_share_same"] = round(c["population"] / ranked_pop, 5)
        below += c["population"]

    world_pop_year = max(population["WLD"])
    meta = {
        "sources": {k: {kk: v[kk] for kk in ("name", "url", "home")} for k, v in SOURCES.items()},
        "world_population": population["WLD"][world_pop_year],
        "world_population_year": world_pop_year,
        "income": global_income,
        "education": global_education,
        "location": {
            "economies_ranked": len(ranked),
            "population_ranked": ranked_pop,
        },
    }

    (OUT_DIR / "countries.json").write_text(json.dumps(countries, ensure_ascii=False, indent=1))
    (OUT_DIR / "global.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))

    n_income = sum("income" in c for c in countries)
    n_prices = sum("prices" in c for c in countries)
    n_edu = sum("education" in c for c in countries)
    print(f"{len(countries)} economies: {n_income} with income distributions, "
          f"{n_prices} with price data, {n_edu} with education data")
    print(f"income mixture covers {global_income['population_coverage']:.1%} of world population")
    for v in global_income["validation"]:
        print(f"  ${v['line']:>5}/day  official {v['official']:6.2f}%  mixture {v['mixture']:6.2f}%")
    unmatched = sorted(set(pip_df["country"]) - set(PIP_NAME_TO_ISO3) - set(iso_by_name))
    print("PIP names without an economy (should be aggregates only):", unmatched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
