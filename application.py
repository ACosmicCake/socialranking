import csv
import io
import os
import secrets

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from ses import data, facts, storage
from ses.distributions import global_cdf
from ses.questionnaire import FIES_STEM, INCOME_BANDS, SECTIONS
from ses.scoring import ValidationError, describe_quantiles, exact_income_available, parse_answers, score

# Configure application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(16)
app.config["TEMPLATES_AUTO_RELOAD"] = True


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

@app.template_filter("pct")
def pct(value, digits=1):
    """Format a 0-100 number as a percentage."""
    if value is None:
        return "-"
    return f"{value:.{digits}f}%"


@app.template_filter("people")
def people(value):
    """Format a head count: 8.2 billion, 655 million, 12,345."""
    if value is None:
        return "-"
    if value >= 1e9:
        return f"{value / 1e9:.1f} billion"
    if value >= 1e6:
        return f"{value / 1e6:,.0f} million"
    return f"{value:,.0f}"


@app.template_filter("money")
def money(value, digits=2):
    return f"${value:,.{digits}f}"


@app.template_filter("num")
def num(value, digits=0):
    return f"{value:,.{digits}f}"


@app.context_processor
def inject_globals():
    return {"citations": facts.CITATIONS}


def country_options():
    """Country list for the quiz, with what the client-side form needs to know."""
    return [
        {
            "iso3": c["iso3"],
            "name": c["name"],
            "currency": c.get("currency") or "",
            "currency_name": c.get("currency_name") or "",
            "exact": exact_income_available(c),
        }
        for c in data.countries()
    ]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", world_population=data.world_population())


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "GET":
        return render_template("quiz.html", sections=SECTIONS, countries=country_options(),
                               fies_stem=FIES_STEM, values={}, errors={})
    try:
        answers = parse_answers(request.form)
    except ValidationError as e:
        return render_template("quiz.html", sections=SECTIONS, countries=country_options(),
                               fies_stem=FIES_STEM, values=request.form, errors=e.errors), 400
    result = score(answers)
    saved = False
    if answers["research_consent"]:
        storage.save(storage.row_from_result(answers, result))
        saved = True
    return render_template("results.html", r=result, saved=saved, access=facts.ACCESS,
                           food=facts.FOOD_INSECURITY, findex=facts.FINDEX,
                           gallup_people=facts.GALLUP_PEOPLE_HIGH)


@app.route("/result", methods=["GET", "POST"])
def legacy_result():
    """The old multi-page quiz posted here; send visitors to the new quiz."""
    return redirect(url_for("quiz"))


@app.route("/api/score", methods=["POST"])
def api_score():
    """Score a JSON body with the same fields as the quiz form."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"errors": {"_": "Send a JSON object."}}), 400
    try:
        answers = parse_answers({k: v if isinstance(v, str) else str(v) for k, v in payload.items()})
    except ValidationError as e:
        return jsonify({"errors": e.errors}), 400
    result = score(answers)
    result["income"].pop("chart", None)
    return jsonify(result)


@app.route("/methodology")
def methodology():
    g = data.global_data()
    countries = data.countries()
    selected = data.country(request.args.get("country", "")) if request.args.get("country") else None
    coverage = {
        "economies": len(countries),
        "income": sum("income" in c for c in countries),
        "prices": sum("prices" in c for c in countries),
        "exact": sum(exact_income_available(c) for c in countries),
        "education": sum("education" in c for c in countries),
        "gdp": sum("gdp_per_capita_usd" in c for c in countries),
    }
    band_rows = [
        {"label": label, "low": global_cdf(low) * 100, "high": global_cdf(high) * 100}
        for _, low, high, label in INCOME_BANDS
    ]
    return render_template("methodology.html", g=g, coverage=coverage, quantiles=describe_quantiles(selected),
                           selected=selected, countries=countries, band_rows=band_rows,
                           access=facts.ACCESS, gallup=facts.GALLUP_VULNERABILITY, gallup_order=facts.GALLUP_ORDER,
                           wealth=facts.WEALTH_PYRAMID, wealth_year=facts.WEALTH_YEAR,
                           food=facts.FOOD_INSECURITY, findex=facts.FINDEX, poverty=facts.EXTREME_POVERTY)


@app.route("/questionnaire")
def questionnaire():
    return render_template("questionnaire.html", sections=SECTIONS, fies_stem=FIES_STEM)


@app.route("/source")
@app.route("/sources")
def sources():
    return render_template("source.html", data_sources=data.global_data()["sources"])


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/creator")
def creator():
    return render_template("creator.html")


@app.route("/stats")
def stats():
    names = {c["iso3"]: c["name"] for c in data.countries()}
    return render_template("stats.html", s=storage.summary(), names=names)


@app.route("/stats.csv")
def stats_csv():
    """Export of the anonymous responses, for the site owner only."""
    token = os.environ.get("STATS_TOKEN")
    if not token or not secrets.compare_digest(request.args.get("token", ""), token):
        abort(404)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=storage.COLUMNS)
    writer.writeheader()
    writer.writerows(storage.export_rows())
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=responses.csv"})


@app.errorhandler(HTTPException)
def errorhandler(e):
    return render_template("apology.html", code=e.code, name=e.name, description=e.description), e.code


@app.errorhandler(Exception)
def internal_error(e):
    app.logger.exception(e)
    return render_template("apology.html", code=500, name="Internal Server Error",
                           description="Something went wrong on our side."), 500


if __name__ == "__main__":
    app.run(debug=True)
