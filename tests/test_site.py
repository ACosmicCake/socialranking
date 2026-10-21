"""Builds the static site and checks it, then runs the JavaScript scorer tests."""

import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ses import data
from ses.distributions import global_cdf, global_quantile, national_cdf, national_quantile

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="Node.js is not installed")


def test_all_pages_built(site):
    import build_site
    for page in build_site.PAGES:
        html = (site / f"{page}.html").read_text(encoding="utf-8")
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
    assert (site / ".nojekyll").exists()


def test_internal_links_resolve(site):
    """Every relative href/src points at a file that exists in the build."""
    for page in site.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        for target in re.findall(r'(?:href|src|action)="([^"#?]+)', html):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            assert (site / target).exists(), f"{page.name} -> {target}"


def test_no_root_absolute_links_without_base_path(site):
    for page in site.glob("*.html"):
        assert not re.search(r'(?:href|src|action)="/(?!/)', page.read_text(encoding="utf-8")), page.name


def test_base_path_build(tmp_path):
    import build_site
    out = build_site.build(tmp_path / "site", base_path="/socialranking")
    html = (out / "404.html").read_text(encoding="utf-8")
    assert 'href="/socialranking/static/styles.css"' in html
    assert 'href="/socialranking/quiz.html"' in html


def test_data_bundle(site):
    text = (site / "static" / "js" / "data.js").read_text(encoding="utf-8")
    assert text.startswith("window.SES_DATA = ")
    bundle = json.loads(text[len("window.SES_DATA = "):].rstrip().rstrip(";"))
    assert len(bundle["countries"]) == len(data.countries())
    assert "sources" not in bundle["global"]
    assert set(bundle["facts"]["access"]) == {"electricity", "clean_cooking", "water", "sanitation",
                                              "hygiene", "internet", "health_hardship"}


def test_quiz_has_every_question(site):
    from ses.questionnaire import all_questions
    html = (site / "quiz.html").read_text(encoding="utf-8")
    for _, q in all_questions():
        assert f'id="q-{q["id"]}"' in html, q["id"]
    assert 'value="VNM"' in html and 'data-currency="VND"' in html


@needs_node
def test_js_scorer(site):
    env = {**os.environ, "SES_SITE": str(site)}
    result = subprocess.run([NODE, "--test", str(ROOT / "tests" / "js" / "ses.test.js")],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_node
def test_js_distributions_match_python(site):
    env = {**os.environ, "SES_SITE": str(site)}
    out = subprocess.run([NODE, str(ROOT / "tests" / "js" / "dump_distributions.js")],
                         env=env, capture_output=True, text=True, check=True).stdout
    js = json.loads(out)
    for x, v in zip(js["xs"], js["global_cdf"]):
        assert math.isclose(v, global_cdf(x), abs_tol=1e-12)
    for p, v in zip(js["ps"], js["global_quantile"]):
        assert math.isclose(v, global_quantile(p), rel_tol=1e-9)
    for iso3, values in js["national"].items():
        dist = data.country(iso3)["income"]
        for x, v in zip(js["xs"], values["cdf"]):
            assert math.isclose(v, national_cdf(dist, x), abs_tol=1e-12), iso3
        for p, v in zip(js["ps"], values["quantile"]):
            assert math.isclose(v, national_quantile(dist, p), rel_tol=1e-9), iso3
