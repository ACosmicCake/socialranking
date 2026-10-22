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
IMF_EDITION = "IMF World Economic Outlook (October 2026)"

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
    **{
        f"barro_lee_{sex}": {
            "url": "https://raw.githubusercontent.com/barrolee/BarroLeeDataSet/"
                   f"ee575b42f659bad7445dfc26d19816ede8000e47/BLData/BL_v3_{sex}.csv",
            "file": f"BL_v3_{sex}.csv",
            "name": f"Barro-Lee Educational Attainment Dataset v3, 10-year age groups ({label})",
            "home": "https://github.com/barrolee/BarroLeeDataSet",
        }
        for sex, label in (("MF", "both sexes"), ("F", "women"), ("M", "men"))
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

# Country-level World Development Indicators (latest value since WDI_SINCE).
WDI_SINCE = 2014
WDI_INDICATORS = {
    # household services: total, urban, rural (% of population)
    "EG.ELC.ACCS.ZS": "Access to electricity",
    "EG.ELC.ACCS.UR.ZS": "Access to electricity, urban",
    "EG.ELC.ACCS.RU.ZS": "Access to electricity, rural",
    "EG.CFT.ACCS.ZS": "Access to clean fuels and technologies for cooking",
    "EG.CFT.ACCS.UR.ZS": "Access to clean cooking, urban",
    "EG.CFT.ACCS.RU.ZS": "Access to clean cooking, rural",
    "SH.H2O.SMDW.ZS": "Safely managed drinking water",
    "SH.H2O.SMDW.UR.ZS": "Safely managed drinking water, urban",
    "SH.H2O.SMDW.RU.ZS": "Safely managed drinking water, rural",
    "SH.H2O.BASW.ZS": "At least basic drinking water",
    "SH.STA.SMSS.ZS": "Safely managed sanitation",
    "SH.STA.SMSS.UR.ZS": "Safely managed sanitation, urban",
    "SH.STA.SMSS.RU.ZS": "Safely managed sanitation, rural",
    "SH.STA.BASS.ZS": "At least basic sanitation",
    "SH.STA.ODFC.ZS": "Open defecation",
    "SH.STA.HYGN.ZS": "Basic handwashing facilities at home",
    "SH.STA.HYGN.UR.ZS": "Basic handwashing facilities, urban",
    "SH.STA.HYGN.RU.ZS": "Basic handwashing facilities, rural",
    "IT.NET.USER.ZS": "Individuals using the Internet",
    "FX.OWN.TOTL.ZS": "Account ownership (% of age 15+)",
    # food security (FAO)
    "SN.ITK.MSFI.ZS": "Moderate or severe food insecurity",
    "SN.ITK.SVFI.ZS": "Severe food insecurity",
    "SN.ITK.DEFC.ZS": "Prevalence of undernourishment",
    # work (ILO modelled estimates, % of total employment unless noted)
    "SL.EMP.WORK.ZS": "Wage and salaried workers",
    "SL.EMP.MPYR.ZS": "Employers",
    "SL.FAM.WORK.ZS": "Contributing family workers",
    "SL.EMP.VULN.ZS": "Vulnerable employment (own-account + contributing family)",
    "SL.AGR.EMPL.ZS": "Employment in agriculture",
    "SL.IND.EMPL.ZS": "Employment in industry",
    "SL.SRV.EMPL.ZS": "Employment in services",
    "SL.UEM.TOTL.ZS": "Unemployment (% of labour force)",
    "SL.TLF.CACT.ZS": "Labour force participation (% of population 15+)",
    # context
    "SP.URB.TOTL.IN.ZS": "Urban population",
    "SP.DYN.LE00.IN": "Life expectancy at birth (years)",
    "SH.DYN.MORT": "Under-5 mortality (per 1,000 live births)",
    "NY.GDP.PCAP.PP.KD": "GDP per capita, PPP (constant 2021 international $)",
    "SH.XPD.OOPC.CH.ZS": "Out-of-pocket spending (% of health spending)",
    "SE.ADT.LITR.ZS": "Adult literacy rate (15+)",
    "EN.POP.SLUM.UR.ZS": "Urban population living in slums",
    "SI.POV.GINI": "Gini index (latest survey)",
    "SI.DST.10TH.10": "Income share held by highest 10%",
    "SI.DST.FRST.20": "Income share held by lowest 20%",
    "SI.POV.NAHC": "Poverty headcount ratio at national poverty lines (% of population)",
    "GD_WBL_OVL_LAW": "Women, Business and the Law: legal framework index (0-100)",
    "EN.ATM.PM25.MC.M3": "PM2.5 air pollution, mean annual exposure (micrograms per cubic metre)",
    "VC.IHR.PSRC.P5": "Intentional homicides (per 100,000 people)",
    "IQ.SPI.OVRL": "Statistical Performance Indicators overall score (0-100)",
    "SH.STA.STNT.ZS": "Prevalence of stunting, height for age (% of children under 5)",
    "SH.MED.PHYS.ZS": "Physicians (per 1,000 people)",
    "SH.MED.NUMW.P3": "Nurses and midwives (per 1,000 people)",
    "SH.MED.BEDS.ZS": "Hospital beds (per 1,000 people)",
    "SE.PRM.CMPT.ZS": "Primary completion rate (% of relevant age group, gross)",
    "SE.TER.ENRR": "School enrollment, tertiary (% gross)",
    # by sex
    "SP.DYN.LE00.FE.IN": "Life expectancy at birth, female (years)",
    "SP.DYN.LE00.MA.IN": "Life expectancy at birth, male (years)",
    "SE.ADT.LITR.FE.ZS": "Adult literacy rate, female (15+)",
    "SE.ADT.LITR.MA.ZS": "Adult literacy rate, male (15+)",
    "IT.NET.USER.FE.ZS": "Individuals using the Internet, female",
    "IT.NET.USER.MA.ZS": "Individuals using the Internet, male",
    "FX.OWN.TOTL.FE.ZS": "Account ownership, female (% of age 15+)",
    "FX.OWN.TOTL.MA.ZS": "Account ownership, male (% of age 15+)",
    **{f"{base}.{sex}.ZS": f"{label}, {'female' if sex == 'FE' else 'male'}"
       for base, label in (("SL.EMP.WORK", "Wage and salaried workers"), ("SL.EMP.MPYR", "Employers"),
                           ("SL.FAM.WORK", "Contributing family workers"), ("SL.EMP.VULN", "Vulnerable employment"),
                           ("SL.AGR.EMPL", "Employment in agriculture"), ("SL.IND.EMPL", "Employment in industry"),
                           ("SL.SRV.EMPL", "Employment in services"), ("SL.UEM.TOTL", "Unemployment"),
                           ("SL.TLF.CACT", "Labour force participation"))
       for sex in ("FE", "MA")},
    # account ownership by household income, age and education (Global Findex)
    "FX.OWN.TOTL.40.ZS": "Account ownership, poorest 40% of households",
    "FX.OWN.TOTL.60.ZS": "Account ownership, richest 60% of households",
    "FX.OWN.TOTL.YG.ZS": "Account ownership, young adults (15-24)",
    "FX.OWN.TOTL.OL.ZS": "Account ownership, older adults (25+)",
    "FX.OWN.TOTL.PL.ZS": "Account ownership, primary education or less",
    "FX.OWN.TOTL.SO.ZS": "Account ownership, secondary education or more",
    # human capital, learning, connectivity, health spending
    "HD.HCI.OVRL": "Human Capital Index (0-1)",
    "HD.HCI.OVRL.FE": "Human Capital Index, female (0-1)",
    "HD.HCI.OVRL.MA": "Human Capital Index, male (0-1)",
    "HD.HCI.EYRS": "Expected years of school (HCI component)",
    "HD.HCI.LAYS": "Learning-adjusted years of school (HCI component)",
    "SE.LPV.PRIM": "Learning poverty (% of 10-year-olds unable to read a simple text)",
    "IT.CEL.SETS.P2": "Mobile cellular subscriptions (per 100 people)",
    "SH.XPD.CHEX.PC.CD": "Current health expenditure per person (current US$)",
    # Findex sets its emergency amount at 1/20 of GNI per person in local currency.
    "NY.GNP.PCAP.CN": "GNI per capita (current local currency)",
}
# Social protection coverage from the World Bank ASPIRE database: % of the population
# living in households that receive each kind of programme, in total and by
# quintile of pre-transfer welfare (q1 = poorest fifth). Surveys are infrequent,
# so these use an older cut-off than WDI_SINCE.
ASPIRE_SINCE = 2008
WDI_SOCIAL_PROTECTION = {
    "per_allsp.cov_pop_tot": "Coverage of social protection and labour programmes (% of population)",
    "per_sa_allsa.cov_pop_tot": "Coverage of social assistance (% of population)",
    "per_si_allsi.cov_pop_tot": "Coverage of social insurance (% of population)",
    "per_lm_alllm.cov_pop_tot": "Coverage of labour market programmes (% of population)",
    **{f"per_{p}.cov_q{q}_tot": f"Coverage of {name}, quintile {q} (% of population)"
       for p, name in (("sa_allsa", "social assistance"), ("si_allsi", "social insurance"))
       for q in range(1, 6)},
}
# Global Findex 2025 financial-resilience items (World Bank API source 28): each
# answer's share of adults 15+. Main source of emergency money is asked only of
# those who could raise it, so every group is normalised to sum to one.
FINDEX_SOURCE = 28
FINDEX_SINCE = 2021
FINDEX_ITEMS = {
    "emergency": [("not_possible", "fin24aN"), ("very_difficult", "fin24aVD"),
                  ("somewhat_difficult", "fin24aSD"), ("not_difficult", "fin24aND")],
    "emergency_source": [("savings", "fin24sav"), ("family", "fin24fam"), ("work", "fin24work"),
                         ("borrowing", "fin24bor"), ("sale_of_assets", "fin24sell"), ("other", "fin24other")],
    "cover_expenses": [("under_2_weeks", "fin24ba"), ("one_month", "fin24bb"), ("two_months", "fin24bc"),
                       ("over_2_months", "fin24bd")],
    "worry": [("old_age", "fin45a"), ("business", "fin45b"), ("medical", "fin45c"), ("bills", "fin45d"),
              ("school", "fin45e")],
}
# Phone ownership from the Findex 2025 connectivity module (% of adults): owns a mobile
# phone (con1) and main phone is a smartphone (con9a), split into none/basic/smartphone.
FINDEX_DERIVED = {
    "phone": (["con1", "con9a"], ["none", "basic", "smartphone"],
              lambda own, smart: [100 - own, max(own - smart, 0.0), smart]),
}
# Yes/no Findex items shown as context next to your answers (% of adults, latest wave).
FINDEX_YES = {"saved": "save.any.t.d", "borrowed": "fin22a.22a1.22g.d", "digital_payment": "g20.any"}
# Findex breakdowns of the derived groups (indicator suffixes): women, men, rural, urban.
FINDEX_GROUP_SUFFIXES = {".1": ("by_sex", "F"), ".2": ("by_sex", "M"), ".9": ("by_area", "rural"),
                         ".10": ("by_area", "urban")}
# Occupations: ISCO-08 major groups from the World Bank's Global Jobs Indicators
# Database (JOIN, API source 86), harmonised household and labour-force surveys,
# as shares of employed people aged 15-64; also by sex and urban/rural. Skill
# levels follow ISCO-08 (managers 3-4, professionals 4, technicians 3, groups
# 4-8 level 2, elementary 1; armed forces span levels and are left out of ranks).
JOIN_SOURCE = 86
OCCUPATIONS = [("managers", "SEOF", 4), ("professionals", "PROF", 4), ("technicians", "TECH", 3),
               ("clerks", "CLRK", 2), ("service_sales", "SVMK", 2), ("skilled_agri", "SKAG", 2),
               ("craft", "CRFT", 2), ("machine", "MACH", 2), ("elementary", "ELEM", 1),
               ("armed_forces", "ARFC", None)]
OCCUPATION_SINCE = 2010
OCCUPATION_TOP_RATIO, OCCUPATION_TOP_FLOOR = 2.5, 0.10
OCCUPATION_SUFFIXES = {"": None, ".FE": ("by_sex", "F"), ".MA": ("by_sex", "M"),
                       ".UR": ("by_area", "urban"), ".RU": ("by_area", "rural")}

# Population by 5-year age group and sex (% of each sex's population, UN WPP via WDI).
AGE_GROUPS = ["0004", "0509", "1014", "1519", "2024", "2529", "3034", "3539", "4044", "4549", "5054",
              "5559", "6064", "6569", "7074", "7579", "80UP"]

# World Bank Food Prices for Nutrition (API source 88): cost of the least-cost
# healthy diet and the share of people who can't afford it (cost > 52% of income).
FPN_SOURCE = 88
FPN_SERIES = ["CoHD_LCU", "CoHD_PPP", "CoHD_headcount", "CoHD_unafford_n"]
HEALTHY_DIET_INCOME_SHARE = 0.52

# Educational attainment, population 25+, cumulative (% with at least this level).
WDI_EDUCATION = ["SE.PRM.CUAT.ZS", "SE.SEC.CUAT.LO.ZS", "SE.SEC.CUAT.UP.ZS", "SE.SEC.CUAT.PO.ZS",
                 "SE.TER.CUAT.ST.ZS", "SE.TER.CUAT.BA.ZS", "SE.TER.CUAT.MS.ZS", "SE.TER.CUAT.DO.ZS"]
EDUCATION_SINCE = 2010
POP_25_PLUS_PARTS = ["SP.POP.0014.TO", "SP.POP.1519.FE", "SP.POP.1519.MA", "SP.POP.2024.FE", "SP.POP.2024.MA"]
WDI_AGGREGATES = ["WLD", "EAS", "ECS", "LCN", "MEA", "NAC", "SAS", "SSF", "LIC", "LMC", "UMC", "HIC"]

# Separate urban and rural distributions, where PIP publishes them (only China in
# the September 2026 release; India and Indonesia are now national only).
URBAN_RURAL_COUNTRIES = ["CHN", "IND", "IDN"]
URBAN_RURAL_LINES = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4.2, 5, 6, 7, 8.3, 10, 12.5, 15, 20, 25, 30, 40, 50, 60, 80,
                     100, 150, 200]
HISTORY_YEARS = [1990, 2000, 2010, 2019]   # plus REFERENCE_YEAR and NOWCAST_YEAR
NOWCAST_YEAR = 2026

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

# ISCED 2011 attainment levels, matching WDI's cumulative indicators.
EDUCATION_LEVELS = [
    ("below_primary", "Less than primary (no schooling or primary not completed)"),
    ("primary", "Primary"),
    ("lower_secondary", "Lower secondary"),
    ("upper_secondary", "Upper secondary"),
    ("post_secondary", "Post-secondary non-tertiary"),
    ("short_tertiary", "Short-cycle tertiary"),
    ("bachelor", "Bachelor's or equivalent"),
    ("master", "Master's or equivalent"),
    ("doctoral", "Doctoral or equivalent"),
]
# Barro-Lee's broad groups, for comparisons within an age and sex group.
BROAD_EDUCATION = ["No schooling or primary not completed", "Primary", "Secondary (some or completed)",
                   "Tertiary (some or completed)"]
BROAD_FROM_LEVEL = [0, 1, 2, 2, 2, 3, 3, 3, 3]
BL_AGE_GROUPS = [(25, 34), (35, 44), (45, 54), (55, 64)]
# Parents' generations: each sex's attainment at ages 35-44 in every Barro-Lee year from
# 1965 (parents of today's 65+) to 2015 (parents of today's 15-24), so a parent is compared
# with their own birth cohort at prime age rather than with the survivors of it today.
BL_COHORT_AGES = (35, 44)
BL_COHORT_YEARS = range(1965, 2016, 5)


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
    # ASPIRE aggregates carry period labels such as "2011-21W"; keep single years only.
    return [r for r in rows or [] if r["value"] is not None and str(r["date"]).isdigit()]


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
    # Likewise a flat stretch of the CDF: keep the lowest income for each share.
    points = [pt for i, pt in enumerate(points) if i == 0 or pt[0] > points[i - 1][0]]
    points = [(p, x) for p, x in points if 0 < p < 0.9995]
    ps = [p for p, _ in points]
    xs = [x for _, x in points]
    if len(points) < 5 or any(b <= a for a, b in zip(xs, xs[1:])) or any(b <= a for a, b in zip(ps, ps[1:])) \
            or xs[0] <= 0 or ps[-1] < 0.9:
        return None
    # Pareto tail from the 95th-percentile point (or the nearest below) to the last point.
    i_low = max(i for i, p in enumerate(ps) if p <= max(0.95, ps[-2]) and i < len(ps) - 1)
    alpha = math.log((1 - ps[i_low]) / (1 - ps[-1])) / math.log(xs[-1] / xs[i_low])
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

    # Each economy's median and $3.00 poverty rate for every year since 1990.
    hist = pip_csv("pip", "pip_national_history.csv", country="all", year="all", povline=3, fill_gaps="true")
    for code, dist in countries.items():
        rows = hist[(hist["country_code"] == code) & (hist["reporting_level"] == dist["coverage"])
                    & (hist["reporting_year"] >= 1990) & (hist["reporting_year"] <= REFERENCE_YEAR)].sort_values("reporting_year")
        if len(rows):
            dist["history"] = {
                "start": int(rows["reporting_year"].iloc[0]),
                "median": [round(float(v), 2) for v in rows["median"]],
                "below_3": [round(float(v), 4) for v in rows["headcount"]],
            }

    # Urban and rural distributions, where PIP publishes them separately.
    for code, levels in build_urban_rural().items():
        if code in countries:
            countries[code]["by_area"] = levels

    # Headcounts at WORLD_LINES for every year, world and regions, from PIP's
    # own aggregation (actual estimates plus the nowcast years).
    frames = []
    for line in WORLD_LINES:
        for nowcast in ("false", "true"):
            df = pip_csv("pip-grp", f"pip_grp_{line}_{nowcast}.csv", country="all", year="all",
                         povline=line, group_by="wb", nowcast=nowcast)
            df["line"] = float(line)
            frames.append(df)
    grp = pd.concat(frames).drop_duplicates(subset=["region_code", "reporting_year", "line"])
    world = grp[grp["region_code"] == "WLD"]

    def anchors_for(year):
        rows = world[world["reporting_year"] == year].sort_values("line")
        return [(float(r["line"]), float(r["headcount"])) for _, r in rows.iterrows()]

    anchors = anchors_for(REFERENCE_YEAR)
    ref = world[(world["reporting_year"] == REFERENCE_YEAR) & (world["line"] == 3)].iloc[0]
    world_mean, world_pop = float(ref["mean"]), int(ref["reporting_pop"])

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
    calibrated = calibrate(grid, mixture, anchors)
    median = float(np.exp(np.interp(0.5, calibrated, np.log(grid))))

    # Other years: the same shape calibrated to that year's world headcounts.
    history = {}
    for year in HISTORY_YEARS + [REFERENCE_YEAR, NOWCAST_YEAR]:
        a = anchors_for(year)
        if len(a) != len(WORLD_LINES):
            continue
        cdf = calibrate(grid, mixture, a)
        estimate = world[world["reporting_year"] == year]["estimate_type"].iloc[0]
        history[str(year)] = {
            "cdf": [round(float(f), 6) for f in cdf],
            "estimate_type": estimate,
            "share_below_3": round(dict(a)[3.0], 6),
            "population": int(world[(world["reporting_year"] == year) & (world["line"] == 3)]["reporting_pop"].iloc[0]),
        }

    # Regional check: our mixtures against PIP's regional headcounts at $3.00.
    regions = {}
    for _, r in grp[(grp["reporting_year"] == REFERENCE_YEAR) & (grp["line"] == 3)].iterrows():
        if r["region_code"] != "WLD":
            regions[r["region_code"]] = {"name": r["region_name"], "share_below_3": round(float(r["headcount"]), 6),
                                         "population": int(r["reporting_pop"])}

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
        "history": history,
        "pip_regions": regions,
    }


def calibrate(grid, mixture, anchors):
    """Rescale the mixture CDF piecewise so it passes through the anchors."""
    mix_at = lambda v: float(np.interp(math.log(v), np.log(grid), mixture))
    lines = [a[0] for a in anchors]
    out = np.empty_like(mixture)
    for i, x in enumerate(grid):
        m = mixture[i]
        if x <= lines[0]:
            out[i] = anchors[0][1] * m / mix_at(lines[0])
        elif x >= lines[-1]:
            m_top, f_top = mix_at(lines[-1]), anchors[-1][1]
            out[i] = f_top + (1 - f_top) * (m - m_top) / (1 - m_top)
        else:
            j = next(k for k in range(len(lines) - 1) if lines[k] <= x <= lines[k + 1])
            (a, fa), (b, fb) = anchors[j], anchors[j + 1]
            ma, mb = mix_at(a), mix_at(b)
            out[i] = fa + (fb - fa) * (m - ma) / (mb - ma)
    return np.maximum.accumulate(np.clip(out, 0, 1))


def build_urban_rural():
    """Urban and rural distributions for the countries PIP splits by area.

    PIP's population-share queries return the national line for these
    countries, so instead we read each area's headcount at a grid of lines."""
    frames = []
    for line in URBAN_RURAL_LINES:
        df = pip_csv("pip", f"pip_area_{line}.csv", country=",".join(URBAN_RURAL_COUNTRIES),
                     year=REFERENCE_YEAR, povline=line, fill_gaps="true")
        frames.append(df)
    df = pd.concat(frames)
    out = {}
    for (code, level), rows in df.groupby(["country_code", "reporting_level"]):
        if level not in ("urban", "rural"):
            continue
        rows = rows.sort_values("poverty_line")
        dist = quantile_distribution(list(zip(rows["headcount"], rows["poverty_line"])))
        if dist:
            median = math.exp(float(np.interp(0.5, dist["p"], np.log(dist["x"]))))
            dist.update({"population": int(rows["reporting_pop"].iloc[0]), "median": round(median, 4),
                         "mean": round(float(rows["mean"].iloc[0]), 4)})
            out.setdefault(code, {})[level] = dist
    return out


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

def wdi_latest(indicator, since, name=None):
    """Latest non-null value per economy/aggregate since `since` -> {code: (year, value)}."""
    rows = wdi(indicator, name or f"wdi_{indicator}.json", date=f"{since}:{INFLATION_LAST_YEAR}")
    out = {}
    for r in rows:
        code, year = r["countryiso3code"] or r["country"]["id"], int(r["date"])
        if code and (code not in out or year > out[code][0]):
            out[code] = (year, float(r["value"]))
    return out


def wdi_by_year(indicator, since):
    rows = wdi(indicator, f"wdi_{indicator}_years.json", date=f"{since}:{INFLATION_LAST_YEAR}")
    out = {}
    for r in rows:
        out.setdefault(r["countryiso3code"], {})[int(r["date"])] = float(r["value"])
    return out


def build_findex(adults, economies):
    """Findex resilience answers per economy (latest complete year) and adult-weighted world shares."""
    raw = {}
    groups = {g: ([ind for _, ind in items], [k for k, _ in items], lambda *v: list(v))
              for g, items in FINDEX_ITEMS.items()}
    groups.update(FINDEX_DERIVED)
    for inds, _, _ in groups.values():
        for ind in inds:
            rows = wdi(ind, f"findex_{ind}.json", source=FINDEX_SOURCE, date=f"{FINDEX_SINCE}:{INFLATION_LAST_YEAR}")
            for r in rows:
                raw.setdefault(ind, {}).setdefault(r["countryiso3code"] or r["country"]["id"], {})[int(r["date"])] = \
                    float(r["value"])
    out, world = {}, {}
    for group, (inds, keys, split) in groups.items():
        acc, weight, n = np.zeros(len(keys)), 0.0, 0
        codes = set().union(*(raw.get(ind, {}).keys() for ind in inds)) & set(economies)
        for code in codes:
            years = [y for y in raw[inds[0]].get(code, {})
                     if all(y in raw.get(ind, {}).get(code, {}) for ind in inds)]
            # Keep the latest year with a usable answer set (some 2024 phone surveys report zeros only).
            for y in sorted(years, reverse=True):
                vals = np.array(split(*(raw[ind][code][y] for ind in inds)))
                if vals.sum() > 50:
                    break
            else:
                continue
            shares = vals / vals.sum()
            out.setdefault(code, {})[group] = {"year": y, "shares": [round(float(v), 4) for v in shares]}
            if adults.get(code):
                acc += shares * adults[code]
                weight += adults[code]
                n += 1
        if group in FINDEX_DERIVED:
            findex_breakdowns(group, out)
        world[group] = {"keys": keys, "indicators": inds,
                        "shares": [round(float(v), 4) for v in acc / weight], "economies": n,
                        "adults_covered": int(weight), "adults_world": int(adults.get("WLD", 0))}
    return out, world


def build_findex_yes(adults, economies):
    """Shares of adults answering yes, per economy (latest wave, with sex and area splits) and world."""
    out, world = {}, {}
    for key, ind in FINDEX_YES.items():
        raw = {}
        for suffix in ["", *FINDEX_GROUP_SUFFIXES]:
            for r in wdi(ind + suffix, f"findex_{ind}{suffix}.json", source=FINDEX_SOURCE,
                         date=f"{FINDEX_SINCE}:{INFLATION_LAST_YEAR}"):
                raw.setdefault(suffix, {}).setdefault(r["countryiso3code"] or r["country"]["id"], {})[int(r["date"])] = \
                    float(r["value"]) / 100
        acc = weight = 0.0
        n = 0
        for code, years in raw.get("", {}).items():
            if code not in economies:
                continue
            y = max(years)
            item = {"year": y, "share": round(years[y], 4)}
            for suffix, (by, group) in FINDEX_GROUP_SUFFIXES.items():
                v = raw.get(suffix, {}).get(code, {}).get(y)
                if v is not None:
                    item.setdefault(by, {})[group] = round(v, 4)
            out.setdefault(code, {})[key] = item
            if adults.get(code):
                acc += years[y] * adults[code]
                weight += adults[code]
                n += 1
        world[key] = {"indicator": ind, "share": round(acc / weight, 4), "economies": n,
                      "adults_covered": int(weight), "adults_world": int(adults.get("WLD", 0))}
    return out, world


def findex_breakdowns(group, out):
    """Add a derived group's shares for women, men, rural and urban adults, in the economy's year."""
    inds, _, split = FINDEX_DERIVED[group]
    for suffix, (by, key) in FINDEX_GROUP_SUFFIXES.items():
        raw = {}
        for ind in inds:
            for r in wdi(ind + suffix, f"findex_{ind}{suffix}.json", source=FINDEX_SOURCE,
                         date=f"{FINDEX_SINCE}:{INFLATION_LAST_YEAR}"):
                raw.setdefault(ind, {})[(r["countryiso3code"] or r["country"]["id"], int(r["date"]))] = float(r["value"])
        for code, groups in out.items():
            if group not in groups:
                continue
            k = (code, groups[group]["year"])
            if all(k in raw.get(ind, {}) for ind in inds):
                vals = np.array(split(*(raw[ind][k] for ind in inds)))
                if vals.sum() > 50:
                    shares = vals / vals.sum()
                    groups[group].setdefault(by, {})[key] = [round(float(v), 4) for v in shares]


def market_rate(code, rates, prices):
    """Official exchange rate (local currency per US$) if its units match our PPPs.

    The ratio of the PPP factor (moved to the rate's year) to the exchange rate is the price
    level relative to the US; anything outside 0.1-2 means mismatched currency units.
    """
    r = rates.get(code)
    if not (r and prices and str(r[0]) in prices["price_index"]):
        return None
    level = prices["ppp_2021"] * prices["price_index"][str(r[0])] / r[1]
    if not 0.1 <= level <= 2:
        return None
    return {"lcu_per_usd": round(r[1], 6), "year": r[0]}


def emergency_amount(code, indicators, prices):
    """Findex's emergency amount, 1/20 of GNI per capita in local currency, if its units check out.

    GNI in local currency, converted with our PPPs and prices, should be near GDP per person
    in 2021 PPP $; a large gap means WDI and PIP use different currency units (e.g. Liberia).
    """
    gni = indicators["NY.GNP.PCAP.CN"].get(code)
    gdp = indicators["NY.GDP.PCAP.PP.KD"].get(code)
    if not (gni and gdp and prices and str(gni[0]) in prices["price_index"]):
        return None
    ratio = gni[1] / prices["ppp_2021"] / prices["price_index"][str(gni[0])] / gdp[1]
    if not 1 / 3 <= ratio <= 3:
        return None
    return {"lcu": round(gni[1] / 20, 2), "year": gni[0]}


def build_occupation(adults, employment_ratio, education, agriculture):
    """ISCO-08 major-group shares per economy (latest survey since OCCUPATION_SINCE) and pooled.

    A survey is dropped when managers and professionals together exceed both 10% of workers and
    2.5 times the share of adults with post-secondary education, a sign of miscoded occupations
    (e.g. Nigeria 2018: 41% managers or professionals, 11% post-secondary). It is also dropped
    when farm and elementary workers are under half of the ILO's agricultural employment share
    (where that is at least 5%), a sign the survey misses rural areas (e.g. Argentina's urban
    survey, China 2013).
    """
    raw = {}
    for _, code, _ in OCCUPATIONS:
        for sfx in OCCUPATION_SUFFIXES:
            ind = f"JI.EMP.{code}{sfx}.ZS"
            for r in wdi(ind, f"join_{ind}.json", source=JOIN_SOURCE, date=f"{OCCUPATION_SINCE}:{INFLATION_LAST_YEAR}"):
                raw.setdefault(ind, {}).setdefault(r["country"]["id"], {})[int(r["date"])] = float(r["value"])
    codes = [c for _, c, _ in OCCUPATIONS]
    out, dropped = {}, []
    pooled = {k: np.zeros(len(codes)) for k in ("all", "F", "M")}
    weights = {k: 0.0 for k in pooled}
    for country in raw[f"JI.EMP.{codes[0]}.ZS"]:
        def shares(sfx, year):
            vals = [raw.get(f"JI.EMP.{c}{sfx}.ZS", {}).get(country, {}).get(year) for c in codes]
            if any(v is None for v in vals[:-1]):
                return None
            vals = np.array([v or 0.0 for v in vals])
            return vals / vals.sum() if 0.95 <= vals.sum() <= 1.05 else None
        years = sorted(raw[f"JI.EMP.{codes[0]}.ZS"][country], reverse=True)
        year = next((y for y in years if shares("", y) is not None), None)
        if year is None:
            continue
        total = shares("", year)
        edu = education.get(country, {}).get("shares")
        if edu and total[0] + total[1] > max(OCCUPATION_TOP_RATIO * sum(edu[4:]), OCCUPATION_TOP_FLOOR):
            dropped.append(country)
            continue
        agri = agriculture.get(country)
        if agri and agri[1] >= 5 and total[5] + total[8] < 0.5 * agri[1] / 100:
            dropped.append(country)
            continue
        entry = {"year": year, "shares": [round(float(v), 4) for v in total]}
        for sfx, where in OCCUPATION_SUFFIXES.items():
            if where and (sh := shares(sfx, year)) is not None:
                entry.setdefault(where[0], {})[where[1]] = [round(float(v), 4) for v in sh]
        out[country] = entry
        ratio = employment_ratio.get(country)
        if adults.get(country) and ratio:
            w = adults[country] * ratio[1] / 100
            pooled["all"] += total * w
            weights["all"] += w
            for sex in ("F", "M"):
                if sex in entry.get("by_sex", {}):
                    # Half the adults of each sex, times the overall employment ratio, is close enough for weights.
                    pooled[sex] += np.array(entry["by_sex"][sex]) * w / 2
                    weights[sex] += w / 2
    world = {
        "keys": [k for k, _, _ in OCCUPATIONS],
        "skill_levels": [lvl for _, _, lvl in OCCUPATIONS],
        "shares": [round(float(v), 4) for v in pooled["all"] / weights["all"]],
        "by_sex": {sex: [round(float(v), 4) for v in pooled[sex] / weights[sex]] for sex in ("F", "M")},
        "economies": len(out),
        "dropped": sorted(dropped),
        "employed_covered": int(weights["all"]),
        "employed_world": int(adults.get("WLD", 0) * employment_ratio["WLD"][1] / 100),
        "since": OCCUPATION_SINCE,
    }
    return out, world


def build_age_structure():
    """{code: {year, shares, by_sex: {F, M}}}: share of the population in each 5-year age group."""
    totals = {sex: wdi_latest(f"SP.POP.TOTL.{sex}.IN", WDI_SINCE) for sex in ("FE", "MA")}
    groups = {(sex, g): wdi_latest(f"SP.POP.{g}.{sex}.5Y", WDI_SINCE) for sex in ("FE", "MA") for g in AGE_GROUPS}
    out = {}
    for code in totals["FE"]:
        if code not in totals["MA"] or not all(code in groups[(sex, g)] for sex in ("FE", "MA") for g in AGE_GROUPS):
            continue
        by_sex = {}
        for sex, key in (("FE", "F"), ("MA", "M")):
            shares = np.array([groups[(sex, g)][code][1] for g in AGE_GROUPS])
            by_sex[key] = shares / shares.sum()
        f, m = totals["FE"][code][1], totals["MA"][code][1]
        combined = (by_sex["F"] * f + by_sex["M"] * m) / (f + m)
        out[code] = {"year": groups[("FE", "2529")][code][0],
                     "shares": [round(float(x), 5) for x in combined],
                     "by_sex": {k: [round(float(x), 5) for x in v] for k, v in by_sex.items()}}
    return out


def fpn_series(series):
    """{iso3: {year: value}} for a Food Prices for Nutrition series."""
    url = (f"{WDI_API}/sources/{FPN_SOURCE}/country/all/series/{series}/classification/all/time/all"
           "?format=json&per_page=20000")
    out = {}
    for r in json.loads(fetch(url, f"fpn_{series}.json"))["source"]["data"]:
        if r["value"] is None:
            continue
        v = {x["concept"]: x["id"] for x in r["variable"]}
        out.setdefault(v["Country"], {})[int(v["Time"][2:])] = float(r["value"])
    return out


def build_healthy_diet(prices):
    """Cost of a healthy diet in local currency and 2021 international $, and who can't afford it."""
    data = {s: fpn_series(s) for s in FPN_SERIES}
    out, checks = {}, []
    for code, by_year in data["CoHD_headcount"].items():
        y = max(by_year)
        entry = {"year": y, "unaffordable_share": round(by_year[y] / 100, 4)}
        people = data["CoHD_unafford_n"].get(code, {}).get(y)
        if people is not None:
            entry["unaffordable_people"] = round(people * 1e6)
        cost = data["CoHD_LCU"].get(code, {})
        if cost:
            # Convert the local-currency cost with the same prices and PPPs as your income. Check it
            # against FPN's own current-PPP cost deflated by US inflation; where they disagree (a
            # redenomination such as Sierra Leone's or Bulgaria's, or very high inflation) use the latter.
            cy = max(cost)
            p = prices.get(code)
            current = data["CoHD_PPP"].get(code, {}).get(cy)
            us = prices["USA"]["price_index"].get(str(cy))
            entry["cost_year"] = cy
            local = cost[cy] / p["price_index"][str(cy)] / p["ppp_2021"] if p and str(cy) in p["price_index"] else None
            alt = current / us if current and us else None
            if local and alt:
                checks.append((code, local / alt))
            if local and (not alt or 0.8 <= local / alt <= 1.25):
                entry.update(cost_lcu=round(cost[cy], 4), cost_2021ppp=round(local, 4), cost_method="local")
            elif alt:
                entry.update(cost_2021ppp=round(alt, 4), cost_method="ppp")
        out[code] = entry
    world = out.get("WLD")
    if world and "WLD" in data["CoHD_PPP"]:
        wy = max(data["CoHD_PPP"]["WLD"])
        world = {**world, "cost_ppp_current": data["CoHD_PPP"]["WLD"][wy], "cost_ppp_year": wy}
    outliers = sorted((c, round(r, 2)) for c, r in checks if not 0.8 <= r <= 1.25)
    return out, {"world": world, "income_share": HEALTHY_DIET_INCOME_SHARE,
                 "checked": len(checks), "outliers": outliers}


def attainment_shares(series, code, ms_over_ba, do_over_ms):
    """Nine exclusive ISCED shares from WDI's cumulative indicators (see build_education)."""
    prm, lo, up, po, st, ba, ms, do = series
    years = [y for y in prm.get(code, {}) if all(y in d.get(code, {}) for d in (lo, up, ba))]
    if not years:
        return None
    y = max(years)
    b = ba[code][y]
    s_ = st.get(code, {}).get(y, b)
    p_ = po.get(code, {}).get(y, s_)
    m = ms.get(code, {}).get(y, b * ms_over_ba)
    d = do.get(code, {}).get(y, m * do_over_ms)
    filled = [k for k, src in (("post-secondary", po), ("short-cycle", st), ("master's", ms), ("doctoral", do))
              if y not in src.get(code, {})]
    cum = [100.0, prm[code][y], lo[code][y], up[code][y], p_, s_, b, m, d]
    for i in range(1, len(cum)):
        cum[i] = max(0.0, min(cum[i], cum[i - 1]))
    shares = [(cum[i] - (cum[i + 1] if i + 1 < len(cum) else 0)) / 100 for i in range(len(cum))]
    return y, [round(x, 5) for x in shares], filled


def build_education(bl, bl_groups, known, pop25):
    """Attainment of adults 25+ in nine ISCED levels.

    WDI's cumulative attainment indicators are used where a country reports
    primary, lower secondary, upper secondary and bachelor's for the same year
    (latest since EDUCATION_SINCE). Missing finer levels are filled as noted
    below. Countries without WDI data use Barro-Lee 2015, crosswalked.
    """
    series = {ind: wdi_by_year(ind, EDUCATION_SINCE) for ind in WDI_EDUCATION}
    prm, lo, up, po, st, ba, ms, do = (series[i] for i in WDI_EDUCATION)

    # Pooled ratios used to fill missing master's / doctoral shares.
    def pooled_ratio(num, den):
        pairs = [(num[c][y], den[c][y]) for c in num for y in num[c] if c in den and y in den[c] and den[c][y] > 0]
        return sum(a for a, _ in pairs) / sum(b for _, b in pairs)
    ms_over_ba, do_over_ms = pooled_ratio(ms, ba), pooled_ratio(do, ms)

    by_sex = {sex: [wdi_by_year(ind.replace(".ZS", f".{sex}.ZS"), EDUCATION_SINCE) for ind in WDI_EDUCATION]
              for sex in ("FE", "MA")}
    countries = {}
    world_sex = {"F": np.zeros(len(EDUCATION_LEVELS)), "M": np.zeros(len(EDUCATION_LEVELS))}
    sex_weight = {"F": 0.0, "M": 0.0}
    for code in known:
        total = attainment_shares([prm, lo, up, po, st, ba, ms, do], code, ms_over_ba, do_over_ms)
        if not total:
            continue
        y, shares, filled = total
        countries[code] = {"source": "WDI", "year": y, "shares": shares, "filled": filled}
        for sex, wdi_sex in (("F", "FE"), ("M", "MA")):
            res = attainment_shares(by_sex[wdi_sex], code, ms_over_ba, do_over_ms)
            if res:
                countries[code].setdefault("by_sex", {})[sex] = res[1]
                if pop25.get(code):
                    world_sex[sex] += np.array(res[1]) * pop25[code] / 2
                    sex_weight[sex] += pop25[code] / 2

    # Barro-Lee crosswalk for the rest (and age/sex groups for everyone).
    bl = bl[bl["year"] == bl["year"].max()].copy()
    bl["iso3"] = bl["WBcode"].replace(BARRO_LEE_CODE_FIXES)
    tertiary_split = None
    for _, r in bl.iterrows():
        code = r["iso3"]
        if code not in known:
            continue
        mean_years = round(float(r["yr_sch"]), 2)
        if code in countries:
            countries[code]["mean_years"] = mean_years
            continue
        if tertiary_split is None:
            # Split Barro-Lee's completed tertiary by WDI's pooled bachelor/master/doctoral ratios.
            tertiary_split = [1 - ms_over_ba, ms_over_ba * (1 - do_over_ms), ms_over_ba * do_over_ms]
        lhc = r["lhc"]
        shares = [r["lu"] + r["lp"] - r["lpc"], r["lpc"], r["ls"] - r["lsc"], r["lsc"], 0.0, r["lh"] - lhc,
                  lhc * tertiary_split[0], lhc * tertiary_split[1], lhc * tertiary_split[2]]
        total = sum(shares)
        countries[code] = {"source": "Barro-Lee", "year": int(r["year"]),
                           "shares": [round(max(x, 0) / total, 5) for x in shares], "mean_years": mean_years}

    # Age and sex groups (Barro-Lee, broad levels).
    world_groups = {}
    for sex, df in bl_groups.items():
        df = df[df["year"] == df["year"].max()].copy()
        df["iso3"] = df["WBcode"].replace(BARRO_LEE_CODE_FIXES)
        for lo_age, hi_age in BL_AGE_GROUPS:
            g = df[(df["agefrom"] == lo_age) & (df["ageto"] == hi_age)]
            key = f"{lo_age}-{hi_age}"
            totals, weight = np.zeros(4), 0.0
            for _, r in g.iterrows():
                broad = np.array([r["lu"] + r["lp"] - r["lpc"], r["lpc"], r["ls"], r["lh"]]).clip(min=0)
                broad = broad / broad.sum()
                if r["iso3"] in countries:
                    countries[r["iso3"]].setdefault("groups", {}).setdefault(key, {})[sex] = \
                        [round(float(x), 4) for x in broad]
                totals += broad * r["pop"]
                weight += r["pop"]
            world_groups.setdefault(key, {})[sex] = [round(float(x), 4) for x in totals / weight]

    # Parents' generations (see BL_COHORT_YEARS), women and men separately.
    world_cohorts = {}
    for sex in ("F", "M"):
        df = bl_groups[sex]
        df = df[(df["agefrom"] == BL_COHORT_AGES[0]) & (df["ageto"] == BL_COHORT_AGES[1])
                & df["year"].isin(BL_COHORT_YEARS)].copy()
        df["iso3"] = df["WBcode"].replace(BARRO_LEE_CODE_FIXES)
        for year, g in df.groupby("year"):
            totals, weight = np.zeros(4), 0.0
            for _, r in g.iterrows():
                broad = np.array([r["lu"] + r["lp"] - r["lpc"], r["lpc"], r["ls"], r["lh"]]).clip(min=0)
                broad = broad / broad.sum()
                if r["iso3"] in countries:
                    countries[r["iso3"]].setdefault("cohorts", {}).setdefault(str(int(year)), {})[sex] = \
                        [round(float(x), 4) for x in broad]
                totals += broad * r["pop"]
                weight += r["pop"]
            world_cohorts.setdefault(str(int(year)), {})[sex] = [round(float(x), 4) for x in totals / weight]

    # World shares weighted by population aged 25+.
    totals, weight = np.zeros(len(EDUCATION_LEVELS)), 0.0
    for code, e in countries.items():
        w = pop25.get(code)
        if w:
            totals += np.array(e["shares"]) * w
            weight += w
    return countries, {
        "ages": "25+",
        "levels": [{"key": k, "label": label} for k, label in EDUCATION_LEVELS],
        "world_shares": [round(float(x), 5) for x in totals / weight],
        "population_25_plus_covered": int(weight),
        "population_25_plus_world": int(pop25.get("WLD", 0)),
        "countries_wdi": sum(e["source"] == "WDI" for e in countries.values()),
        "countries_barro_lee": sum(e["source"] == "Barro-Lee" for e in countries.values()),
        "fill_ratios": {"master_over_bachelor": round(ms_over_ba, 4), "doctoral_over_master": round(do_over_ms, 4)},
        "world_by_sex": {sex: [round(float(x), 5) for x in world_sex[sex] / sex_weight[sex]] for sex in ("F", "M")},
        "broad_levels": BROAD_EDUCATION,
        "broad_from_level": BROAD_FROM_LEVEL,
        "groups_year": int(bl["year"].max()),
        "groups": world_groups,
        "cohorts": world_cohorts,
        "cohort_ages": f"{BL_COHORT_AGES[0]}-{BL_COHORT_AGES[1]}",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def use_latest_releases():
    """Switch from the pinned releases to the newest ones (used by the monthly refresh)."""
    global PIP_VERSION, REFERENCE_YEAR, NOWCAST_YEAR, INFLATION_LAST_YEAR, IMF_EDITION
    versions = json.loads(fetch(f"{PIP_API}/versions", "pip_versions.json"))
    PIP_VERSION = next(v["version"] for v in versions
                       if str(v["ppp_version"]) == str(PPP_BASE_YEAR) and v["identity"] == "PROD")
    world = pip_csv("pip-grp", "pip_world_years.csv", country="WLD", year="all", povline=3, group_by="wb",
                    nowcast="true")
    world = world[world["region_code"] == "WLD"]
    REFERENCE_YEAR = int(world[world["estimate_type"] == "actual"]["reporting_year"].max())
    NOWCAST_YEAR = int(world["reporting_year"].max())
    INFLATION_LAST_YEAR = datetime.date.today().year
    indicators = json.loads(fetch(f"{IMF_API}/indicators", "imf_indicators.json"))["indicators"]
    IMF_EDITION = "IMF " + indicators["PCPIPCH"]["source"]
    print(f"latest releases: PIP {PIP_VERSION}, reference year {REFERENCE_YEAR}, nowcast {NOWCAST_YEAR}, "
          f"{IMF_EDITION}, prices to {INFLATION_LAST_YEAR}")


def main():
    global REFRESH
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="download every source again")
    parser.add_argument("--latest", action="store_true",
                        help="use the newest PIP release, data years and IMF edition instead of the pinned ones "
                             "(implies --refresh)")
    args = parser.parse_args()
    REFRESH = args.refresh or args.latest
    if args.latest:
        use_latest_releases()

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
    # ISO 3166 numeric codes, which the world map (world-atlas) uses as ids.
    iso2 = {r["ISO3166-1-Alpha-3"]: r["ISO3166-1-Alpha-2"] for _, r in codes_df.iterrows() if r["ISO3166-1-Alpha-3"]}
    iso2["XKX"] = "XK"
    m49 = {r["ISO3166-1-Alpha-3"]: str(r["ISO3166-1-numeric"]).zfill(3)
           for _, r in codes_df.iterrows() if r["ISO3166-1-Alpha-3"] and str(r["ISO3166-1-numeric"]).strip()}
    currency["XKX"] = ("EUR", "Euro")
    currency["CHI"] = ("GBP", "Pound Sterling")
    currency["PSE"] = ("ILS", "New Israeli Sheqel")

    prices, ppp_outliers = build_prices(economies, income)

    pop_parts = {ind: wdi_latest(ind, WDI_SINCE) for ind in POP_25_PLUS_PARTS}
    pop25 = {}
    for code, (year, total) in population.items():
        if all(code in pop_parts[ind] for ind in POP_25_PLUS_PARTS):
            pop25[code] = total - sum(pop_parts[ind][code][1] for ind in POP_25_PLUS_PARTS)
    bl = pd.read_csv(io.BytesIO(fetch(GITHUB_SOURCES["barro_lee"]["url"], "BL_v3_MF2564.csv")))
    bl_groups = {sex: pd.read_csv(io.BytesIO(fetch(GITHUB_SOURCES[f"barro_lee_{sex}"]["url"], f"BL_v3_{sex}.csv")))
                 for sex in ("MF", "F", "M")}
    education, global_education = build_education(bl, bl_groups, set(economies), pop25)

    indicators = {ind: wdi_latest(ind, WDI_SINCE) for ind in WDI_INDICATORS}
    indicators.update({ind: wdi_latest(ind, ASPIRE_SINCE) for ind in WDI_SOCIAL_PROTECTION})
    adults = {code: total - pop_parts["SP.POP.0014.TO"][code][1] for code, (_, total) in population.items()
              if code in pop_parts["SP.POP.0014.TO"]}
    findex, global_findex = build_findex(adults, economies)
    findex_yes, global_findex_yes = build_findex_yes(adults, economies)
    exchange_rates = wdi_latest("PA.NUS.FCRF", WDI_SINCE)
    age_structure = build_age_structure()
    healthy_diet, global_healthy_diet = build_healthy_diet(prices)
    occupation, global_occupation = build_occupation(adults, wdi_latest("SL.EMP.TOTL.SP.ZS", WDI_SINCE), education,
                                                     indicators["SL.AGR.EMPL.ZS"])

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
        if code in findex:
            entry["findex"] = findex[code]
        if code in findex_yes:
            entry["findex_yes"] = findex_yes[code]
        rate = market_rate(code, exchange_rates, prices.get(code))
        if rate:
            entry["exchange_rate"] = rate
        amount = emergency_amount(code, indicators, prices.get(code))
        if amount:
            entry.setdefault("findex", {})["emergency_amount"] = amount
        if code in healthy_diet:
            entry["healthy_diet"] = healthy_diet[code]
        if code in occupation:
            entry["occupation"] = occupation[code]
        if code in age_structure:
            entry["age_structure"] = age_structure[code]
        entry["region"] = m.get("region", {}).get("id") or None
        entry["m49"] = m49.get(code)
        entry["iso2"] = iso2.get(code) or None
        entry["wdi"] = {ind: [vals[code][0], round(vals[code][1], 2)] for ind, vals in indicators.items()
                        if code in vals}
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
        "wdi": {"name": "World Bank World Development Indicators API "
                        f"({len(WDI_INDICATORS) + len(WDI_SOCIAL_PROTECTION) + len(WDI_EDUCATION) + 3} "
                        "indicators: population, GDP, PPP, education, services, food security, work, health, "
                        "social protection (ASPIRE); country classifications)",
                "url": f"{WDI_API}/country/all/indicator/SP.POP.TOTL",
                "home": "https://datatopics.worldbank.org/world-development-indicators/"},
        "findex": {"name": "World Bank Global Findex database via the World Bank API (source 28): financial resilience",
                   "url": f"{WDI_API}/country/all/indicator/fin24aN?source={FINDEX_SOURCE}",
                   "home": "https://www.worldbank.org/en/publication/globalfindex"},
        "join": {"name": "World Bank Global Jobs Indicators Database (JOIN, API source 86): employment by occupation",
                 "url": f"{WDI_API}/country/all/indicator/JI.EMP.PROF.ZS?source={JOIN_SOURCE}",
                 "home": "https://api.worldbank.org/v2/sources/86/indicators?format=json&per_page=1000"},
        "fpn": {"name": "World Bank Food Prices for Nutrition (API source 88): cost and affordability of a healthy diet",
                "url": f"{WDI_API}/sources/{FPN_SOURCE}/country/all/series/CoHD_headcount/classification/all/time/all",
                "home": "https://www.worldbank.org/en/programs/icp/brief/foodpricesfornutrition"},
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
        "findex": global_findex,
        "findex_yes": global_findex_yes,
        "healthy_diet": global_healthy_diet,
        "occupation": global_occupation,
        "age_structure": {"groups": AGE_GROUPS, **age_structure["WLD"]},
        "prices": {"base_year": PPP_BASE_YEAR, "last_year": INFLATION_LAST_YEAR, "source": IMF_EDITION,
                   "max_current_inflation": MAX_CURRENT_INFLATION},
        "location": {"economies_ranked": len(ranked), "population_ranked": ranked_pop},
        "wdi_indicators": {**WDI_INDICATORS, **WDI_SOCIAL_PROTECTION},
        "wdi_since": WDI_SINCE,
        "aspire_since": ASPIRE_SINCE,
        "aggregates": {
            code: {
                "name": next((m["name"] for m in meta if m["id"] == code), code),
                "wdi": {ind: [vals[code][0], round(vals[code][1], 2)] for ind, vals in indicators.items()
                        if code in vals},
            }
            for code in WDI_AGGREGATES
        },
        "regions": {m["region"]["id"]: m["region"]["value"].strip() for m in meta if m["region"]["id"] != "NA"},
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
    e = global_education
    print(f"education: {e['countries_wdi']} WDI + {e['countries_barro_lee']} Barro-Lee, "
          f"{e['population_25_plus_covered'] / e['population_25_plus_world']:.1%} of adults 25+; world shares",
          e["world_shares"])
    print("findex yes/no:", {k: (v["economies"], v["share"]) for k, v in global_findex_yes.items()})
    print("findex:", {k: (v["economies"], round(v["adults_covered"] / max(v["adults_world"], 1), 3), v["shares"])
                      for k, v in global_findex.items()})
    o = global_occupation
    print(f"occupation: {o['economies']} economies, {o['employed_covered'] / o['employed_world']:.1%} of employment;",
          "dropped", o["dropped"], "pooled", o["shares"])
    print("healthy diet:", sum("cost_2021ppp" in c.get("healthy_diet", {}) for c in countries), "economies with a cost;",
          "world", global_healthy_diet["world"], "PPP check outliers:", global_healthy_diet["outliers"])
    print("history:", {y: h["share_below_3"] for y, h in global_income["history"].items()})
    print("urban/rural:", {c["iso3"]: list(c["income"]["by_area"]) for c in countries if "by_area" in c.get("income", {})})
    return 0


if __name__ == "__main__":
    sys.exit(main())
