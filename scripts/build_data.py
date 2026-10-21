"""Build the datasets the quiz scores against.

Every number the quiz uses comes either from this script or from the
hand-curated, cited figures in ``ses/facts.py``.  Sources:

* World Bank Poverty and Inequality Platform (PIP) API, pinned release
  PIP_VERSION (2021 PPP)                     -> income distributions
* World Bank World Development Indicators (WDI) API
    - list of economies and income classification
    - SP.POP.TOTL      population
    - NY.GDP.PCAP.CD   GDP per capita (current US$)
    - PA.NUS.PRVT.PP   2021 PPP conversion factor, private consumption
* IMF World Economic Outlook (DataMapper API), PCPIPCH
                                             -> consumer price inflation since 2021
* Barro-Lee Educational Attainment Dataset v3 (GitHub, pinned commit)
                                             -> education distributions
* ISO 3166 / ISO 4217 codes (datahub.io, pinned commit) -> currency names

Raw responses are cached in data/raw/ (git-ignored).  Delete that folder, or
pass --refresh, to download again.

Usage:  pip install -r requirements-dev.txt && python scripts/build_data.py
"""

import argparse
import datetime
import io
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data"

PIP_API = "https://api.worldbank.org/pip/v1"
PIP_VERSION = "20260922_2021_01_02_PROD"   # September 2026 release, 2021 PPPs
WDI_API = "https://api.worldbank.org/v2"
IMF_API = "https://www.imf.org/external/datamapper/api/v1"

PPP_BASE_YEAR = 2021      # PIP incomes are in 2021 international dollars
REFERENCE_YEAR = 2024     # latest year of PIP's lined-up (non-nowcast) estimates
INFLATION_LAST_YEAR = 2026
IMF_EDITION = "IMF World Economic Outlook, October 2026"

# Population shares at which PIP reports each country's income threshold.
POPSHARES = [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99]

# Lines ($/day, 2021 PPP) at which we take PIP's official world headcounts.
WORLD_LINES = [1, 2, 3, 4.2, 6, 8.3, 10, 15, 20, 30, 40, 60, 80, 100, 150]

GITHUB_SOURCES = {
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

# PIP keeps PPPs in the currency of the survey; these countries have since
# changed currency at a fixed rate (old units per new unit).
CURRENCY_CHANGES = {
    "HRV": {"rate": 7.53450, "note": "kuna to euro, 1 January 2023 (Council Decision (EU) 2022/1211)"},
    "BGR": {"rate": 1.95583, "note": "lev to euro, 1 January 2026 (Council Decision (EU) 2025/1407)"},
    "SLE": {"rate": 1000.0, "note": "old to new leone, 1 July 2022 (Bank of Sierra Leone)"},
    "BLR": {"rate": 10000.0, "note": "old to new Belarusian ruble, 1 July 2016 (National Bank of Belarus)"},
    "MRT": {"rate": 10.0, "note": "old to new ouguiya, 1 January 2018 (Central Bank of Mauritania)"},
}
# Where WDI and PIP use different currencies we keep PIP's, which matches the
# currency in the ISO 4217 list: Liberia (LRD, WDI uses USD) and West Bank and
# Gaza (ILS, WDI uses USD).
# Currency replaced without a fixed conversion rate, or hyperinflation in the
# current year: local-currency answers can't be converted reliably.
NO_EXACT_INCOME = {
    "ZWE": "Zimbabwe changed currency in 2019 and 2024 (ZWG) without a fixed conversion rate.",
    "VEN": "Venezuela redenominated its currency in 2021 and inflation remains extreme.",
}
MAX_CURRENT_INFLATION = 1.0     # 100% a year
IMF_CODE_FIXES = {"UVK": "XKX", "WBG": "PSE"}

# Barro-Lee uses a few legacy World Bank codes.
BARRO_LEE_CODE_FIXES = {"ROM": "ROU", "ZAR": "COD", "TMP": "TLS", "SER": "SRB"}

# Friendlier display names than the World Bank's ("Korea, Rep." etc.).
DISPLAY_NAMES = {
    "USA": "United States",
    "GBR": "United Kingdom",
    "COG": "Congo (Republic)",
    "COD": "Congo (Democratic Republic)",
    "FSM": "Micronesia (Federated States)",
    "BIH": "Bosnia and Herzegovina",
    "TWN": "Taiwan",
    "XKX": "Kosovo",
    "CHI": "Channel Islands",
    "HKG": "Hong Kong",
    "MAC": "Macao",
    "PSE": "West Bank and Gaza",
}

EDUCATION_LEVELS = [
    ("none", "No formal schooling"),
    ("primary_incomplete", "Some primary school"),
    ("primary", "Completed primary school"),
    ("secondary_incomplete", "Some secondary school"),
    ("secondary", "Completed secondary school"),
    ("tertiary_incomplete", "Some post-secondary / university"),
    ("tertiary", "Completed post-secondary / university degree"),
]


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------

REFRESH = False


def fetch(url, name):
    """Download url once into data/raw/name and return the bytes."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    if REFRESH or not path.exists():
        print(f"downloading {url}")
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; socialranking-data-build)", "Accept": "*/*"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    path.write_bytes(r.read())
                break
            except OSError:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
    return path.read_bytes()


def pip_csv(endpoint, name, **params):
    params = {"version": PIP_VERSION, "format": "csv", **params}
    url = f"{PIP_API}/{endpoint}?{urllib.parse.urlencode(params)}"
    return pd.read_csv(io.BytesIO(fetch(url, name)))


def wdi(indicator, name, **params):
    params = {"format": "json", "per_page": 20000, **params}
    url = f"{WDI_API}/country/all/indicator/{indicator}?{urllib.parse.urlencode(params)}"
    meta, rows = json.loads(fetch(url, name))
    return [r for r in rows or [] if r["value"] is not None]


# ---------------------------------------------------------------------------
# Income distributions
# ---------------------------------------------------------------------------

def quantile_distribution(points):
    """Describe a distribution by PIP's income thresholds at POPSHARES.

    Matches ses/distributions.py: linear from zero to the first point,
    log-linear between points, Pareto above the last point with the slope of
    the 95th-99th percentile segment.
    """
    # Bottom percentiles can share a threshold (a mass point at the survey's
    # floor); keep only the highest share for each repeated value.
    dedup = {}
    for p, x in points:
        dedup[round(x, 9)] = max(p, dedup.get(round(x, 9), 0))
    points = sorted((p, x) for x, p in dedup.items())
    ps = [p for p, _ in points]
    xs = [x for _, x in points]
    if any(b <= a for a, b in zip(xs, xs[1:])) or xs[0] <= 0 or not {0.95, 0.99} <= set(ps):
        return None
    i95, i99 = ps.index(0.95), ps.index(0.99)
    alpha = math.log((1 - ps[i95]) / (1 - ps[i99])) / math.log(xs[i99] / xs[i95])
    return {"p": ps, "x": [round(x, 4) for x in xs], "pareto_alpha": round(min(max(alpha, 1.05), 10.0), 4)}


def dist_cdf(dist, x):
    """CDF of a quantile_distribution at x (vectorised). Mirrors ses.distributions."""
    x = np.asarray(x, dtype=float)
    ps, xs = np.array(dist["p"]), np.array(dist["x"])
    out = np.empty_like(x)
    low = x < xs[0]
    out[low] = np.clip(x[low] / xs[0], 0, 1) * ps[0]
    high = x > xs[-1]
    out[high] = 1 - (1 - ps[-1]) * (xs[-1] / x[high]) ** dist["pareto_alpha"]
    mid = ~low & ~high
    out[mid] = np.interp(np.log(x[mid]), np.log(xs), ps)
    return out


def build_income():
    frames = []
    for share in POPSHARES:
        df = pip_csv("pip", f"pip_popshare_{share}.csv", country="all", year=REFERENCE_YEAR,
                     popshare=share, fill_gaps="true")
        df["share"] = share
        frames.append(df)
    lineup = pd.concat(frames)

    surveys = pip_csv("pip", "pip_surveys.csv", country="all", year="all", povline=3)
    latest = surveys.sort_values("reporting_year").groupby(["country_code", "reporting_level"]).tail(1)

    countries = {}
    for code, group in lineup.groupby("country_code"):
        levels = set(group["reporting_level"])
        level = "national" if "national" in levels else "urban" if "urban" in levels else None
        if level is None:
            continue
        rows = group[group["reporting_level"] == level].sort_values("share")
        if len(rows) != len(POPSHARES):
            continue
        dist = quantile_distribution(list(zip(rows["share"], rows["poverty_line"])))
        if dist is None:
            continue
        first = rows.iloc[0]
        survey = latest[(latest["country_code"] == code) & (latest["reporting_level"] == level)]
        dist.update({
            "reference_year": REFERENCE_YEAR,
            "mean": round(float(first["mean"]), 4),
            "median": round(float(first["median"]), 4),
            "population": int(first["reporting_pop"]),
            "welfare_type": first["welfare_type"],
            "coverage": level,
            "estimation_type": first["estimation_type"],
            "survey_year": int(survey["reporting_year"].iloc[0]) if len(survey) else None,
            "survey_ppp": float(survey["ppp"].iloc[0]) if len(survey) and survey["ppp"].iloc[0] > 0 else None,
        })
        countries[code] = dist

    # World headcounts at WORLD_LINES, from PIP's own global aggregation.
    anchors = []
    world_mean = None
    for line in WORLD_LINES:
        df = pip_csv("pip-grp", f"pip_world_{line}.csv", country="WLD", year=REFERENCE_YEAR,
                     povline=line, group_by="wb")
        row = df[df["region_code"] == "WLD"].iloc[0]
        anchors.append((float(line), float(row["headcount"])))
        world_mean = float(row["mean"])
        world_pop = int(row["reporting_pop"])

    # Population-weighted mixture of national lineups = shape of the global
    # distribution; then calibrate it so it passes through PIP's world headcounts.
    grid = np.exp(np.linspace(math.log(0.2), math.log(2000), 281))
    total = np.zeros_like(grid)
    weight = 0
    for dist in countries.values():
        total += dist["population"] * dist_cdf(dist, grid)
        weight += dist["population"]
    mixture = total / weight
    mix_at = lambda v: float(np.interp(math.log(v), np.log(grid), mixture))

    lines = [a[0] for a in anchors]
    calibrated = np.empty_like(mixture)
    for i, x in enumerate(grid):
        m = mixture[i]
        if x <= lines[0]:
            calibrated[i] = anchors[0][1] * m / mix_at(lines[0])
        elif x >= lines[-1]:
            m_top, f_top = mix_at(lines[-1]), anchors[-1][1]
            calibrated[i] = f_top + (1 - f_top) * (m - m_top) / (1 - m_top)
        else:
            j = next(k for k in range(len(lines) - 1) if lines[k] <= x <= lines[k + 1])
            (a, fa), (b, fb) = anchors[j], anchors[j + 1]
            ma, mb = mix_at(a), mix_at(b)
            calibrated[i] = fa + (fb - fa) * (m - ma) / (mb - ma)
    calibrated = np.maximum.accumulate(np.clip(calibrated, 0, 1))
    median = float(np.exp(np.interp(0.5, calibrated, np.log(grid))))

    return countries, {
        "ppp_year": PPP_BASE_YEAR,
        "reference_year": REFERENCE_YEAR,
        "pip_version": PIP_VERSION,
        "grid": [round(float(x), 4) for x in grid],
        "cdf": [round(float(f), 6) for f in calibrated],
        "anchors": [{"line": l, "share_below": round(s, 6)} for l, s in anchors],
        "validation": [{"line": l, "official": round(s * 100, 2), "mixture": round(mix_at(l) * 100, 2)}
                       for l, s in anchors],
        "countries_in_mixture": len(countries),
        "population_in_mixture": int(weight),
        "world_population": world_pop,
        "world_mean": round(world_mean, 4),
        "world_median": round(median, 4),
    }


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

def build_prices(codes, pip_income):
    """Local currency today -> 2021 international dollars, per economy."""
    ppp_wdi = {r["countryiso3code"]: float(r["value"])
               for r in wdi("PA.NUS.PRVT.PP", "wdi_ppp_prvt_2021.json", date=PPP_BASE_YEAR)}
    imf = json.loads(fetch(f"{IMF_API}/PCPIPCH?periods=" + ",".join(
        str(y) for y in range(PPP_BASE_YEAR + 1, INFLATION_LAST_YEAR + 1)), "imf_pcpipch.json"))
    inflation = {IMF_CODE_FIXES.get(k, k): v for k, v in imf["values"]["PCPIPCH"].items()}

    prices, ppp_checks = {}, []
    for code in codes:
        survey_ppp = pip_income.get(code, {}).get("survey_ppp")
        change = CURRENCY_CHANGES.get(code)
        if survey_ppp:
            # PIP's own PPP keeps the conversion consistent with its distributions.
            ppp, ppp_source = survey_ppp / (change["rate"] if change else 1), "PIP"
        elif code in ppp_wdi:
            ppp, ppp_source = ppp_wdi[code], "WDI PA.NUS.PRVT.PP"
        else:
            continue
        if survey_ppp and code in ppp_wdi:
            ppp_checks.append((code, ppp / ppp_wdi[code]))

        rates = inflation.get(code, {})
        index, level, last_rate, estimated = {str(PPP_BASE_YEAR): 1.0}, 1.0, None, []
        for year in range(PPP_BASE_YEAR + 1, INFLATION_LAST_YEAR + 1):
            rate = rates.get(str(year))
            if rate is None:
                if last_rate is None or len(estimated) >= 2:
                    break
                rate = last_rate * 100          # carry the last known rate forward
                estimated.append(year)
            last_rate = rate / 100
            level *= 1 + last_rate
            index[str(year)] = round(level, 6)
        if str(INFLATION_LAST_YEAR) not in index:
            continue

        entry = {
            "ppp_2021": round(ppp, 6),
            "ppp_source": ppp_source,
            "price_index": index,                # consumer prices relative to 2021
            "inflation_estimated_years": estimated,
            "current_inflation": round(last_rate, 4),
        }
        if change:
            entry["currency_change"] = change["note"]
        reason = NO_EXACT_INCOME.get(code)
        if not reason and last_rate > MAX_CURRENT_INFLATION:
            reason = f"Inflation is expected to exceed {MAX_CURRENT_INFLATION:.0%} in {INFLATION_LAST_YEAR}."
        entry["exact_income"] = reason is None
        if reason:
            entry["exact_income_reason"] = reason
        prices[code] = entry

    outliers = [(c, round(r, 3)) for c, r in ppp_checks if not 0.75 < r < 1.33 and c not in ("LBR", "PSE")]
    return prices, outliers


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

def build_education(bl, known):
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
        if r["iso3"] in known:
            countries[r["iso3"]] = {
                "year": int(r["year"]),
                "shares": [round(float(s), 5) for s in shares],
                "mean_years": round(float(r["yr_sch"]), 2),
            }
        totals += shares * r["pop"]
        weight += r["pop"]
    return countries, {
        "year": int(bl["year"].max()),
        "ages": "25-64",
        "levels": [{"key": k, "label": label} for k, label in EDUCATION_LEVELS],
        "world_shares": [round(float(s), 5) for s in totals / weight],
        "countries_covered": int(len(bl)),
        "population_covered_thousands": round(float(weight)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global REFRESH
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="download every source again")
    REFRESH = parser.parse_args().refresh

    # Economies: World Bank list (217) plus any extra economies PIP covers (Taiwan).
    meta = json.loads(fetch(f"{WDI_API}/country?format=json&per_page=400", "wdi_countries.json"))[1]
    economies = {c["id"]: c for c in meta if c["region"]["id"] != "NA"}

    income, global_income = build_income()
    for code in income:
        if code not in economies:
            economies[code] = {"id": code, "name": code, "incomeLevel": {"value": ""}}

    population = {r["countryiso3code"]: (int(r["date"]), int(r["value"]))
                  for r in wdi("SP.POP.TOTL", "wdi_population.json", mrnev=1)}
    gdp_pc = {r["countryiso3code"]: (int(r["date"]), float(r["value"]))
              for r in wdi("NY.GDP.PCAP.CD", "wdi_gdp_pc.json", mrnev=1)}
    world_pop_year, world_pop = population["WLD"]

    codes_df = pd.read_csv(io.BytesIO(fetch(GITHUB_SOURCES["country_codes"]["url"], "country-codes.csv")),
                           keep_default_na=False)
    currency = {r["ISO3166-1-Alpha-3"]: (r["ISO4217-currency_alphabetic_code"].split(",")[0],
                                         r["ISO4217-currency_name"].split(",")[0])
                for _, r in codes_df.iterrows() if r["ISO3166-1-Alpha-3"]}
    common_names = {r["ISO3166-1-Alpha-3"]: r["CLDR display name"]
                    for _, r in codes_df.iterrows() if r["ISO3166-1-Alpha-3"] and r["CLDR display name"]}
    currency["XKX"] = ("EUR", "Euro")
    currency["CHI"] = ("GBP", "Pound Sterling")
    currency["PSE"] = ("ILS", "New Israeli Sheqel")

    prices, ppp_outliers = build_prices(economies, income)
    bl = pd.read_csv(io.BytesIO(fetch(GITHUB_SOURCES["barro_lee"]["url"], "BL_v3_MF2564.csv")))
    education, global_education = build_education(bl, set(economies))

    countries = []
    for code, m in economies.items():
        pop = population.get(code) or ((REFERENCE_YEAR, income[code]["population"]) if code in income else None)
        if pop is None:
            continue
        cur = currency.get(code, ("", ""))
        entry = {
            "iso3": code,
            "name": DISPLAY_NAMES.get(code) or common_names.get(code) or m["name"],
            "income_group": m["incomeLevel"]["value"] or None,
            "currency": cur[0] or None,
            "currency_name": cur[1] or None,
            "population": pop[1],
            "population_year": pop[0],
        }
        if code in gdp_pc:
            entry["gdp_per_capita_usd"] = round(gdp_pc[code][1], 1)
            entry["gdp_year"] = gdp_pc[code][0]
        if code in prices:
            entry["prices"] = prices[code]
        if code in income:
            entry["income"] = {k: v for k, v in income[code].items() if k not in ("population", "survey_ppp")}
        if code in education:
            entry["education"] = education[code]
        countries.append(entry)
    countries.sort(key=lambda c: c["name"].casefold())

    # Location: share of the world's population in economies with lower GDP per capita.
    ranked = sorted((c for c in countries if "gdp_per_capita_usd" in c), key=lambda c: c["gdp_per_capita_usd"])
    ranked_pop = sum(c["population"] for c in ranked)
    below = 0
    for c in ranked:
        c["gdp_pc_population_share_below"] = round(below / ranked_pop, 5)
        c["gdp_pc_population_share_same"] = round(c["population"] / ranked_pop, 5)
        below += c["population"]

    sources = {
        "pip": {"name": f"World Bank Poverty and Inequality Platform API, release {PIP_VERSION}",
                "url": f"{PIP_API}/pip?version={PIP_VERSION}", "home": "https://pip.worldbank.org"},
        "wdi": {"name": "World Bank World Development Indicators API (SP.POP.TOTL, NY.GDP.PCAP.CD, "
                        "PA.NUS.PRVT.PP, country classifications)",
                "url": f"{WDI_API}/country/all/indicator/SP.POP.TOTL",
                "home": "https://datatopics.worldbank.org/world-development-indicators/"},
        "imf": {"name": f"{IMF_EDITION}: inflation, average consumer prices (PCPIPCH)",
                "url": f"{IMF_API}/PCPIPCH", "home": "https://www.imf.org/external/datamapper/PCPIPCH@WEO"},
        **{k: {kk: v[kk] for kk in ("name", "url", "home")} for k, v in GITHUB_SOURCES.items()},
    }
    out = {
        "built": datetime.date.today().isoformat(),
        "sources": sources,
        "world_population": world_pop,
        "world_population_year": world_pop_year,
        "income": global_income,
        "education": global_education,
        "prices": {"base_year": PPP_BASE_YEAR, "last_year": INFLATION_LAST_YEAR, "source": IMF_EDITION,
                   "max_current_inflation": MAX_CURRENT_INFLATION},
        "location": {"economies_ranked": len(ranked), "population_ranked": ranked_pop},
    }
    (OUT_DIR / "countries.json").write_text(json.dumps(countries, ensure_ascii=False, indent=1))
    (OUT_DIR / "global.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    exact = [c["iso3"] for c in countries if c.get("prices", {}).get("exact_income")]
    print(f"{len(countries)} economies: {sum('income' in c for c in countries)} with income distributions, "
          f"{len(exact)} accept exact income, {sum('education' in c for c in countries)} with education data")
    print(f"income mixture: {global_income['countries_in_mixture']} economies, "
          f"{global_income['population_in_mixture'] / global_income['world_population']:.1%} of world population")
    for v in global_income["validation"]:
        print(f"  ${v['line']:>5}/day  official {v['official']:6.2f}%  mixture {v['mixture']:6.2f}%")
    print("no exact income:", sorted(c["iso3"] for c in countries if c["iso3"] not in exact))
    print("PIP vs WDI PPP mismatches (ratio outside 0.8-1.25):", ppp_outliers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
