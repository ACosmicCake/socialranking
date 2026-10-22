"""Build the static website (for GitHub Pages or any static host).

Renders templates/ with Jinja2 into _site/ (English at the root, each other
language in LANGS under its own folder, e.g. vi/), copies static/, and writes
static/js/data.js (data.vi.js, ...) with everything the in-browser scorer
(static/js/ses.js) needs: the generated datasets, the cited facts, the
questionnaire and translated labels. A language is a strings module like
ses/i18n.py plus an entry in LANGS.

Usage:
    python scripts/build_site.py                      # relative links, open _site/index.html
    python scripts/build_site.py --base-path /socialranking   # absolute links for GitHub Pages
    python -m http.server -d _site                    # preview at http://localhost:8000
"""

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ses import data, facts, i18n  # noqa: E402
from ses import questionnaire as qn  # noqa: E402
from ses.distributions import global_cdf, global_quantile  # noqa: E402
from jsi18n import inject  # noqa: E402

PAGES = ["index", "quiz", "results", "methodology", "questionnaire", "sources", "faq", "about", "creator", "404"]

# Languages: the strings module (None for English, the source), output folder, bundle suffix
# and the pages translated (the rest link to the English version).
LANGS = {
    "en": {"module": None, "subdir": "", "suffix": "", "pages": PAGES},
    "vi": {"module": i18n, "subdir": "vi/", "suffix": ".vi",
           "pages": ["index", "quiz", "results", "methodology", "questionnaire", "faq", "about", "creator", "404"]},
}
LANGUAGES = {code: name for code, name in i18n.LANGUAGES.items() if code in LANGS}


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
# Translation
# ---------------------------------------------------------------------------

def country_names(lang):
    """Country names in `lang`: the module's own names first, then CLDR's (via Babel)."""
    if lang == "en":
        return {c["iso3"]: c["name"] for c in data.countries()}
    from babel import Locale
    mod = LANGS[lang]["module"]
    territories = Locale(lang).territories
    return {c["iso3"]: mod.COUNTRY_NAMES.get(c["iso3"]) or territories.get(c.get("iso2") or "", c["name"])
            for c in data.countries()}


def translate_sections(sections, mod):
    """Copy of the questionnaire sections in the language of strings module `mod`."""
    out = copy.deepcopy(sections)
    for section in out:
        section["title"], section["intro"] = mod.SECTIONS[section["key"]]
        for q in section["questions"]:
            tr = mod.QUESTIONS.get(q["id"], {})
            q["text"] = tr.get("text", q["text"])
            if "help" in q:
                q["help"] = tr.get("help", q["help"])
            if q.get("stem"):
                q["stem"] = mod.FIES_STEM
            if "options" in q:
                labels = {**mod.YES_NO, **tr.get("options", {})}
                q["options"] = [(k, labels.get(k, label)) for k, label in q["options"]]
    return out


def option_map(qid, sections):
    for section in sections:
        for q in section["questions"]:
            if q["id"] == qid:
                return dict(q["options"])
    raise KeyError(qid)


# ---------------------------------------------------------------------------
# Data for the browser
# ---------------------------------------------------------------------------

def browser_data(lang="en"):
    questions = [
        {"id": q["id"], "type": q["type"], "options": [k for k, _ in q.get("options", [])]}
        for _, q in qn.all_questions()
    ]
    g = {k: v for k, v in data.global_data().items() if k != "sources"}
    countries = data.countries()
    access, gallup, pyramid = facts.ACCESS, facts.GALLUP_VULNERABILITY, facts.WEALTH_PYRAMID
    q = {
        "questions": questions,
        "income_bands": qn.INCOME_BANDS,
        "education_options": qn.EDUCATION_OPTIONS,
        "cooking_options": qn.COOKING_OPTIONS,
        "water_options": qn.WATER_OPTIONS,
        "sanitation_options": qn.SANITATION_OPTIONS,
        "fies_items": qn.FIES_ITEMS,
        "work_options": qn.WORK_OPTIONS,
        "sector_options": qn.SECTOR_OPTIONS,
        "occupation_options": qn.OCCUPATION_OPTIONS,
        "parent_education_options": qn.PARENT_EDUCATION_OPTIONS,
        "employed": list(qn.EMPLOYED),
        "vulnerable": list(qn.VULNERABLE),
        "small_assets": list(qn.SMALL_ASSETS),
        "social_protection_types": qn.SOCIAL_PROTECTION_TYPES,
        "online_options": dict(qn.ONLINE_OPTIONS),
    }
    labels = None
    mod = LANGS[lang]["module"]
    if mod:
        sections = translate_sections(qn.SECTIONS, mod)
        g = copy.deepcopy(g)
        names = country_names(lang)
        countries = copy.deepcopy(countries)
        for c in countries:
            c["name"] = names[c["iso3"]]
            c["income_group_label"] = mod.INCOME_GROUPS.get(c["income_group"], c["income_group"])
            prices = c.get("prices", {})
            for key, note in mod.PRICE_NOTES.items():
                if prices.get(key):
                    prices[key] = note
        countries.sort(key=lambda c: c["name"].casefold())
        g["regions"] = {k: mod.REGIONS.get(k, v) for k, v in g["regions"].items()}
        for code, agg in g["aggregates"].items():
            agg["name"] = mod.REGIONS.get(code, agg["name"])
        g["education"]["levels"] = [{"key": l["key"], "label": mod.EDUCATION_LEVELS[l["key"]]}
                                    for l in g["education"]["levels"]]
        g["education"]["broad_levels"] = mod.BROAD_EDUCATION
        access = copy.deepcopy(access)
        for k, (label, note) in mod.ACCESS.items():
            access[k]["label"], access[k]["note"] = label, note
        gallup = copy.deepcopy(gallup)
        for k, (label, definition) in mod.GALLUP.items():
            gallup[k]["label"], gallup[k]["definition"] = label, definition
        pyramid = [{**b, "label": mod.WEALTH[b["key"]]} for b in pyramid]
        opts = {qid: option_map(qid, sections) for qid in ("income_band", "education", "cooking", "water",
                                                          "sanitation", "work_status", "work_sector", "occupation",
                                                          "mother_education", "online")}
        q.update({
            "income_bands": [(k, lo, hi, opts["income_band"][k]) for k, lo, hi, _ in qn.INCOME_BANDS],
            "education_options": [(k, opts["education"][k]) for k, _ in qn.EDUCATION_OPTIONS],
            "cooking_options": [(k, opts["cooking"][k], clean) for k, _, clean in qn.COOKING_OPTIONS],
            "water_options": [(k, opts["water"][k], mod.WATER_STATUS[k]) for k, _, _ in qn.WATER_OPTIONS],
            "sanitation_options": [(k, opts["sanitation"][k], mod.SANITATION_STATUS[k])
                                   for k, _, _ in qn.SANITATION_OPTIONS],
            "work_options": [(k, opts["work_status"][k]) for k, _ in qn.WORK_OPTIONS],
            "sector_options": [(k, opts["work_sector"][k]) for k, _ in qn.SECTOR_OPTIONS],
            "occupation_options": [(k, opts["occupation"][k]) for k, _ in qn.OCCUPATION_OPTIONS],
            "parent_education_options": [(k, opts["mother_education"][k]) for k, _ in qn.PARENT_EDUCATION_OPTIONS],
            "online_options": {k: opts["online"][k] for k, _ in qn.ONLINE_OPTIONS},
        })
        labels = mod.LABELS
    out = {
        "lang": lang,
        "global": g,
        "countries": countries,
        "facts": {
            "access": access,
            "gallup": gallup,
            "gallup_order": list(facts.GALLUP_ORDER),
            "gallup_people_high": facts.GALLUP_PEOPLE_HIGH,
            "findex": facts.FINDEX,
            "food": facts.FOOD_INSECURITY,
            "wealth_pyramid": pyramid,
            "citations": facts.CITATIONS,
            "mpi": facts.MPI,
            "extreme_poverty": facts.EXTREME_POVERTY,
            "social_protection": facts.SOCIAL_PROTECTION,
        },
        "questionnaire": q,
    }
    if labels:
        out["labels"] = labels
    return out


SITE_ORIGIN = "https://acosmiccake.github.io"


def page_context(lang="en"):
    g = data.global_data()
    countries = data.countries()
    mod = LANGS[lang]["module"]
    names = country_names(lang)
    options = [
        {"iso3": c["iso3"], "name": names[c["iso3"]], "currency": c.get("currency") or "",
         "currency_name": c.get("currency_name") or "", "exact": exact_income_available(c),
         "welfare": c.get("income", {}).get("welfare_type", ""), "iso2": c.get("iso2") or ""}
        for c in countries
    ]
    options.sort(key=lambda c: c["name"].casefold())
    return {
        "world_population": data.world_population(),
        "sections": translate_sections(qn.SECTIONS, mod) if mod else qn.SECTIONS,
        "fies_stem": mod.FIES_STEM if mod else qn.FIES_STEM,
        "countries": countries,
        "country_options": options,
        "g": g,
        "data_sources": g["sources"],
        "question_count": sum(1 for _ in qn.all_questions()),
        "coverage": {
            "economies": len(countries),
            "income": sum("income" in c for c in countries),
            "prices": sum("prices" in c for c in countries),
            "exact": sum(exact_income_available(c) for c in countries),
            "education": sum("education" in c for c in countries),
            "gdp": sum("gdp_per_capita_usd" in c for c in countries),
            "wdi_indicators": len(g["wdi_indicators"]),
            "findex": sum("emergency" in c.get("findex", {}) for c in countries),
            "occupation": sum("occupation" in c for c in countries),
            "healthy_diet": sum("cost_2021ppp" in c.get("healthy_diet", {}) for c in countries),
            "social_protection": sum("per_allsp.cov_pop_tot" in c.get("wdi", {}) or "per_sa_allsa.cov_pop_tot" in c.get("wdi", {})
                                     for c in countries),
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
        "mpi": facts.MPI,
        "social_protection": facts.SOCIAL_PROTECTION,
        "citations": facts.CITATIONS,
        "work_options": qn.WORK_OPTIONS,
    }


def quiz_data(full):
    """The slice of the browser bundle the quiz needs: questions, labels, and per country the
    name, currency, prices and Findex emergency amount (for validation and the live amount)."""
    keep = ("iso3", "name", "currency", "currency_name", "prices")
    countries = []
    for c in full["countries"]:
        entry = {k: c[k] for k in keep if k in c}
        amount = c.get("findex", {}).get("emergency_amount")
        if amount:
            entry["findex"] = {"emergency_amount": amount}
        countries.append(entry)
    slim = {
        "lang": full["lang"],
        "countries": countries,
        "global": {"aggregates": {"WLD": {"wdi": {}}}, "prices": full["global"]["prices"]},
        "facts": {},
        "questionnaire": full["questionnaire"],
    }
    if "labels" in full:
        slim["labels"] = full["labels"]
    return slim


def build(out_dir, base_path=""):
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(ROOT / "static", out_dir / "static")
    results_src = (ROOT / "static" / "js" / "results.js").read_text(encoding="utf-8")
    results_js = {}
    for lang, spec in LANGS.items():
        # Languages beyond English and Vietnamese get their own copy of results.js with the
        # module's RESULTS translations added to each tr() call.
        results_js[lang] = "results.js"
        if getattr(spec["module"], "RESULTS", None) is not None:
            results_js[lang] = f"results{spec['suffix']}.js"
            (out_dir / "static" / "js" / results_js[lang]).write_text(
                inject(results_src, spec["module"].RESULTS)[0], encoding="utf-8")
        suffix = spec["suffix"]
        full = browser_data(lang)
        for name, bundle in ((f"data{suffix}.js", full), (f"data.quiz{suffix}.js", quiz_data(full))):
            (out_dir / "static" / "js" / name).write_text(
                "window.SES_DATA = " + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";\n",
                encoding="utf-8")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    env.filters.update(pct=pct, people=people, money=money, num=num)
    # "" gives relative links (works from disk); "/repo/" gives absolute ones,
    # which the 404 page needs because GitHub Pages serves it at any path.
    root = base_path.rstrip("/") + "/" if base_path else ""
    for lang, spec in LANGS.items():
        context = page_context(lang)
        subdir, pages, mod = spec["subdir"], spec["pages"], spec["module"]
        asset_base = root if base_path else ("../" if subdir else "")
        page_base = root + subdir if base_path else ""
        (out_dir / subdir).mkdir(parents=True, exist_ok=True)
        for page in pages:
            # The same page in every other language (its home page where it isn't translated).
            alternates = [(other, f"{asset_base}{o['subdir']}{page if page in o['pages'] else 'index'}.html")
                          for other, o in LANGS.items() if other != lang]
            html = env.get_template(f"{page}.html").render(
                page=page, lang=lang, base=page_base, asset_base=asset_base,
                # Link previews need absolute URLs; only known for a deployed build.
                site_url=f"{SITE_ORIGIN}{root}" if base_path else "",
                alternates=alternates, languages=LANGUAGES, lang_pages=pages,
                lang_suffix=spec["suffix"], results_js=results_js[lang],
                _=(lambda s, mod=mod: mod.UI.get(s, s)) if mod else (lambda s: s),
                **context)
            (out_dir / subdir / f"{page}.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("")
    return out_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "_site"), help="output directory (default: _site)")
    parser.add_argument("--base-path", default="", help="URL path the site is served from, e.g. /socialranking")
    args = parser.parse_args()
    out = build(args.out, args.base_path)
    print(f"built {', '.join(f'{len(spec['pages'])} {LANGUAGES[lang]}' for lang, spec in LANGS.items())} pages into {out}")


if __name__ == "__main__":
    main()
