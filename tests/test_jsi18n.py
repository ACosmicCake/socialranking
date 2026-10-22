"""The build-time translator for tr() calls in results.js (scripts/jsi18n.py)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import jsi18n  # noqa: E402

SAMPLE = r"""const tr = (en, vi, other) => other ?? en;
const a = tr("Hello", "Xin chào");
const b = `${tr(`Richer than ${pct(x)} of ${f(y, ")")}`, `Khá giả hơn ${pct(x)}`)}!`;
const c = tr('it\'s', "nó");
"""
RICHER = '`Richer than ${pct(x)} of ${f(y, ")")}`'


def test_calls_parse_strings_templates_and_nesting():
    found = [args for _, _, args in jsi18n.calls(SAMPLE)]
    assert found == [['"Hello"', '"Xin chào"'], [RICHER, "`Khá giả hơn ${pct(x)}`"], [r"'it\'s'", '"nó"']]


def test_inject_adds_the_translation_and_reports_missing():
    out, missing = jsi18n.inject(SAMPLE, {'"Hello"': '"Hola"', RICHER: "`Más que ${pct(x)}`"})
    assert 'tr("Hello", "Xin chào", "Hola")' in out
    assert ", `Más que ${pct(x)}`)}!`" in out
    assert missing == [r"'it\'s'"]


def test_results_js_parses_completely():
    src = (ROOT / "static" / "js" / "results.js").read_text(encoding="utf-8")
    found = jsi18n.calls(src)
    assert len(found) > 400 and all(len(args) == 2 for _, _, args in found)
    # Injecting a translation for every call still yields valid JavaScript.
    out, missing = jsi18n.inject(src, {en: en for en in jsi18n.english_sources(src)})
    assert not missing
    check = subprocess.run(["node", "--check", "-"], input=out, text=True, capture_output=True)
    assert check.returncode == 0, check.stderr
