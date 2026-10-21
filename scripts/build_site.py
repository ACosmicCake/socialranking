"""Build the static website (for GitHub Pages or any static host).

Renders templates/ with Jinja2 into _site/, copies static/, and writes
static/js/data.js with everything the in-browser scorer (static/js/ses.js)
needs: the generated datasets, the cited facts and the questionnaire.

Usage:
    python scripts/build_site.py                      # relative links, open _site/index.html
    python scripts/build_site.py --base-path /socialranking   # absolute links for GitHub Pages
    python -m http.server -d _site                    # preview at http://localhost:8000
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ses import data, facts  # noqa: E402
from ses import questionnaire as qn  # noqa: E402
from ses.distributions import global_cdf, global_quantile  # noqa: E402

PAGES = ["index", "quiz", "results", "methodology", "questionnaire", "sources", "faq", "about", "creator", "404"]

def exact_income_available(country):
    """Mirrors exactIncomeAvailable in static/js/ses.js."""
    return bool(country.get("prices", {}).get("exact_income"))


# ---------------------------------------------------------------------------
# Template filters
# ---------------------------------------------------------------------------

def pct(value, digits=1):
    """Format a 0-100 number as a percentage."""
    return "-" if value is None else f"{value:.{digits}f}%"


def people(value):
    """Format a head count: 8.2 billion, 655 million, 12,345."""
    if value is None:
        return "-"
    if value >= 1e9:
        return f"{value / 1e9:.1f} billion"
    if value >= 1e6:
        return f"{value / 1e6:,.0f} million"
    return f"{value:,.0f}"


def money(value, digits=2):
    return f"${value:,.{digits}f}"


def num(value, digits=0):
    return f"{value:,.{digits}f}"


# ---------------------------------------------------------------------------
# Data for the browser
# ---------------------------------------------------------------------------

def browser_data():
    questions = [
        {"id": q["id"], "type": q["type"], "options": [k for k, _ in q.get("options", [])]}
        for _, q in qn.all_questions()
    ]
    return {
        "global": {k: v for k, v in data.global_data().items() if k != "sources"},
        "countries": data.countries(),
        "facts": {
            "access": facts.ACCESS,
            "gallup": facts.GALLUP_VULNERABILITY,
            "gallup_order": list(facts.GALLUP_ORDER),
            "gallup_people_high": facts.GALLUP_PEOPLE_HIGH,
            "findex": facts.FINDEX,
            "food": facts.FOOD_INSECURITY,
            "wealth_pyramid": facts.WEALTH_PYRAMID,
            "citations": facts.CITATIONS,
        },
        "questionnaire": {
            "questions": questions,
            "income_bands": qn.INCOME_BANDS,
            "education_options": qn.EDUCATION_OPTIONS,
            "cooking_options": qn.COOKING_OPTIONS,
            "water_options": qn.WATER_OPTIONS,
            "sanitation_options": qn.SANITATION_OPTIONS,
            "fies_items": qn.FIES_ITEMS,
        },
    }


def page_context():
    g = data.global_data()
    countries = data.countries()
    return {
        "world_population": data.world_population(),
        "sections": qn.SECTIONS,
        "fies_stem": qn.FIES_STEM,
        "countries": countries,
        "country_options": [
            {"iso3": c["iso3"], "name": c["name"], "currency": c.get("currency") or "",
             "currency_name": c.get("currency_name") or "", "exact": exact_income_available(c)}
            for c in countries
        ],
        "g": g,
        "data_sources": g["sources"],
        "coverage": {
            "economies": len(countries),
            "income": sum("income" in c for c in countries),
            "prices": sum("prices" in c for c in countries),
            "exact": sum(exact_income_available(c) for c in countries),
            "education": sum("education" in c for c in countries),
            "gdp": sum("gdp_per_capita_usd" in c for c in countries),
        },
        "quantiles": [{"p": p, "world": global_quantile(p / 100)} for p in (10, 25, 50, 75, 90, 99)],
        "band_rows": [
            {"label": label, "low": global_cdf(low) * 100, "high": global_cdf(high) * 100}
            for _, low, high, label in qn.INCOME_BANDS
        ],
        "access": facts.ACCESS,
        "gallup": facts.GALLUP_VULNERABILITY,
        "gallup_order": facts.GALLUP_ORDER,
        "wealth": facts.WEALTH_PYRAMID,
        "wealth_year": facts.WEALTH_YEAR,
        "food": facts.FOOD_INSECURITY,
        "findex": facts.FINDEX,
        "poverty": facts.EXTREME_POVERTY,
        "citations": facts.CITATIONS,
    }


def build(out_dir, base_path=""):
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(ROOT / "static", out_dir / "static")
    (out_dir / "static" / "js" / "data.js").write_text(
        "window.SES_DATA = " + json.dumps(browser_data(), ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    env.filters.update(pct=pct, people=people, money=money, num=num)
    # "" gives relative links (works from disk); "/repo/" gives absolute ones,
    # which the 404 page needs because GitHub Pages serves it at any path.
    env.globals["base"] = base_path.rstrip("/") + "/" if base_path else ""
    context = page_context()
    for page in PAGES:
        html = env.get_template(f"{page}.html").render(page=page, **context)
        (out_dir / f"{page}.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("")
    return out_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "_site"), help="output directory (default: _site)")
    parser.add_argument("--base-path", default="", help="URL path the site is served from, e.g. /socialranking")
    args = parser.parse_args()
    out = build(args.out, args.base_path)
    print(f"built {len(PAGES)} pages into {out}")


if __name__ == "__main__":
    main()
