"""End-to-end browser walkthrough of the built site (optional; not run by pytest or CI).

Builds the site with the GitHub Pages base path, serves it locally, and drives the quiz and
results in Chromium at desktop and phone widths, in English and Vietnamese. It fails on any
JavaScript error, missing results section, horizontal scrolling or broken download.

    pip install playwright && python -m playwright install chromium
    python tests/e2e/walkthrough.py [screenshot-dir]

The page libraries come from jsDelivr. Without internet access, set SES_CDN_DIR to a folder
holding the npm packages (bs, cj, d3, tj, wa, each unpacked as <name>/package/...).
CHROMIUM_PATH can point at a specific Chromium binary.
"""
import functools
import http.server
import json as _json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="ses-e2e-"))
OUT.mkdir(parents=True, exist_ok=True)
CDN_DIR = os.environ.get("SES_CDN_DIR")
LOCAL = {
    "bootstrap@5.3.3/dist/css/bootstrap.min.css": ("bs/package/dist/css/bootstrap.min.css", "text/css"),
    "bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js": ("bs/package/dist/js/bootstrap.bundle.min.js", "application/javascript"),
    "chart.js@4.4.1/dist/chart.umd.js": ("cj/package/dist/chart.umd.js", "application/javascript"),
    "d3@7.9.0/dist/d3.min.js": ("d3/package/dist/d3.min.js", "application/javascript"),
    "topojson-client@3.1.0/dist/topojson-client.min.js": ("tj/package/dist/topojson-client.min.js", "application/javascript"),
    "world-atlas@2.0.2/countries-110m.json": ("wa/package/countries-110m.json", "application/json"),
}


def route(r):
    """Serve CDN files from SES_CDN_DIR when set; otherwise let the request through."""
    if not CDN_DIR:
        return r.continue_()
    for key, (path, content_type) in LOCAL.items():
        if key in r.request.url:
            return r.fulfill(path=str(Path(CDN_DIR) / path), content_type=content_type,
                             headers={"Access-Control-Allow-Origin": "*"})
    return r.abort()


site = Path(tempfile.mkdtemp(prefix="ses-site-"))
subprocess.run([sys.executable, str(ROOT / "scripts/build_site.py"), "--out", str(site / "socialranking"),
                "--base-path", "/socialranking/"], check=True, stdout=subprocess.DEVNULL)
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


handler = functools.partial(QuietHandler, directory=str(site))
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/socialranking/"

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    for width, tag, prefix in ((1280, "desk", ""), (390, "mobile", ""), (1280, "vi-desk", "vi/")):
        ctx = b.new_context(viewport={"width": width, "height": 900})
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        page = ctx.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("https://cdn.jsdelivr.net/**", route)
        page.goto(BASE + prefix + "quiz.html")
        page.select_option("#country", "VNM"); page.click("#next")
        for sel in ["area-urban", "age-25-34", "sex-F"]: page.click(f"label[for={sel}]")
        page.click("#next")
        page.click("label[for=income_mode-exact]"); page.fill("#income_amount", "20,000,000")
        page.click("label[for=income_period-month]"); page.fill("#household_size", "4"); page.click("#next")
        page.click("label[for=education-bachelor]")
        page.click("label[for=mother_education-primary]"); page.click("label[for=father_education-secondary]"); page.click("#next")
        page.click("label[for=work_status-employee]")
        assert page.is_visible("#q-work_sector")
        page.click("label[for=work_sector-services]")
        assert page.is_visible("#q-occupation")
        page.click("label[for=occupation-professionals]"); page.click("#next")
        for q, v in [("electricity","yes"),("cooking","gas"),("water","safely_managed"),("sanitation","safely_managed"),("hygiene","yes"),("internet","yes"),("health_hardship","no")]:
            page.click(f"label[for={q}-{v}]")
        page.click("#next")
        assert not page.is_visible("#q-household_schooling")
        page.click("label[for=housing-floor]"); page.click("label[for=housing-none]")
        assert not page.is_checked("#housing-floor"), "none should clear other boxes"
        for a in ["phone", "tv", "motorbike", "fridge"]: page.click(f"label[for=assets-{a}]")
        page.fill("#sleeping_rooms", "2")
        page.click("label[for=school_attendance-na]"); page.click("label[for=nutrition-no]"); page.click("label[for=child_death-skip]")
        page.screenshot(path=OUT / f"{tag}-household.png", full_page=True)
        page.click("#next")
        for q in ["food_money","shelter_money","fies_worried","fies_healthy","fies_few_kinds","fies_skipped","fies_ate_less","fies_ran_out","fies_hungry","fies_whole_day"]:
            page.click(f"label[for={q}-no]")
        page.click("label[for=count_on-yes]"); page.click("label[for=account-yes]"); page.click("label[for=saved-yes]")
        page.click("label[for=emergency_funds-somewhat_difficult]")
        assert page.is_visible("#q-emergency_source")
        assert page.is_visible("#emergency-amount") and "VND" in page.inner_text("#emergency-amount")
        print(tag, "amount:", page.inner_text("#emergency-amount"))
        page.click("label[for=emergency_source-family]"); page.click("label[for=cover_expenses-two_months]"); page.click("label[for=worry-medical]")
        page.click("label[for=social_protection-in_kind]"); page.click("label[for=social_protection-contributory_pension]")
        page.click("#next"); page.click("label[for=wealth-10k_100k]"); page.click("#next")
        page.click("label[for=ladder_country-6]"); page.click("label[for=ladder_world-5]")
        page.click("#next"); page.click("button[type=submit]")
        page.wait_for_url("**/results.html#*"); page.wait_for_timeout(1500)
        url = page.url
        text = page.inner_text("#results")
        musts = (["Thu nhập của bạn trên khắp thế giới", "Cùng mức thu nhập ở các năm khác", "Chỉ số Nghèo đa chiều",
                  "So với phụ nữ 25-34 tuổi", "Lao động theo vị thế việc làm", "Tổng quan về Việt Nam", "Nếu như?", "Cần bao nhiêu để lên hạng", "An sinh xã hội", "Chỉ số Vốn nhân lực", "Khả năng chống chịu tài chính", "chế độ ăn lành mạnh", "Nghề nghiệp của bạn", "So với bố mẹ bạn"] if prefix else
                 ["Your income around the world", "The same income in other years", "Multidimensional Poverty Index",
                  "Compared with women aged 25-34", "Workers by status", "at a glance", "What if?", "Vietnam over time", "Account ownership among people like you", "Women in Vietnam",
                  "How precise is this?", "What it takes to move up", "Social protection", "Coverage by income fifth in Vietnam", "Human Capital Index",
                  "Financial resilience", "Can you afford a healthy diet?", "Biggest financial worry", "Your occupation", "Compared with your parents", "moved up"])
        for must in musts:
            assert must in text, must
        n_paths = page.evaluate("document.querySelectorAll('#worldMap path.country').length")
        print(tag, "map countries drawn:", n_paths)
        page.evaluate("document.getElementById('whatif').value = 1; document.getElementById('whatif').dispatchEvent(new Event('input'))")
        print(tag, "what-if:", page.inner_text("#whatif-out").replace("\n", " | "))
        page.click("a.btn[href='#mpi']"); page.wait_for_timeout(400)
        page.click("#lang-switch"); page.wait_for_timeout(1200)
        assert page.url.split("#")[1] == url.split("#")[1], "language switch keeps answers"
        print(tag, "switched to:", page.url.split("#")[0], "|", page.inner_text("h1")[:60])
        page.go_back(); page.wait_for_timeout(1000)
        assert page.url == url, "in-page link must not change the fragment"
        with page.expect_download() as dl:
            page.click("#save-image")
        dl.value.save_as(OUT / f"{tag}-share.png")
        with page.expect_download() as dl:
            page.click("#save-csv")
        dl.value.save_as(OUT / f"{tag}.csv")
        csv = (OUT / f"{tag}.csv").read_text(encoding="utf-8-sig")
        assert csv.startswith("section,measure,you,world,country") and "SES index" in csv, csv[:200]
        with page.expect_download() as dl:
            page.click("#save-json")
        dl.value.save_as(OUT / f"{tag}.json")
        payload = _json.loads((OUT / f"{tag}.json").read_text())
        assert payload["results"]["ses_index"] > 0 and payload["answers"]["country"] == "VNM"
        print(tag, "csv rows:", len(csv.splitlines()))
        page.screenshot(path=OUT / f"{tag}-results.png", full_page=True)
        w = page.evaluate("document.documentElement.scrollWidth")
        # minimal answers path
        page.goto(BASE + prefix + "results.html#country=USA&income_mode=band&income_band=b5&education=upper_secondary"); page.wait_for_timeout(800)
        assert ("thế giới" if prefix else "of the world") in page.inner_text("#results")
        if not prefix:
            page.goto(BASE + "methodology.html"); page.select_option("#mcountry", "VNM")
            page.screenshot(path=OUT / f"{tag}-methodology.png", full_page=True)
        for pg in ["index", "questionnaire", "faq", "about", "creator", "404"]:
            page.goto(BASE + prefix + pg + ".html")
            if pg == "index": page.screenshot(path=OUT / f"{tag}-index.png")
        assert not errors, errors
        assert w <= width, f"{tag}: page is {w}px wide"
        print(tag, "ok")
        ctx.close()
    b.close()
    server.shutdown()
    print('screenshots in', OUT)
