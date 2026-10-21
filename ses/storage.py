"""Optional, anonymous storage of questionnaire responses (opt-in only).

Only derived, coarse values are stored: no free text, no exact income and no
IP address or timestamp finer than the day.  Aggregates are shown on /stats
and only for groups of at least MIN_GROUP responses.
"""

import datetime
import math
import os
import sqlite3
from contextlib import closing

MIN_GROUP = 5

SCHEMA = """
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    country TEXT NOT NULL,
    income_mode TEXT NOT NULL,
    income_log2_bucket INTEGER,
    education TEXT,
    services_lacking INTEGER,
    gallup_group TEXT,
    fies_raw INTEGER,
    has_account INTEGER,
    saved INTEGER,
    wealth_band TEXT,
    ladder_country INTEGER,
    ladder_world INTEGER,
    pct_income REAL,
    pct_income_national REAL,
    pct_education REAL,
    pct_living REAL,
    pct_security REAL,
    pct_wealth REAL,
    ses_index REAL
)
"""

COLUMNS = ["day", "country", "income_mode", "income_log2_bucket", "education", "services_lacking",
           "gallup_group", "fies_raw", "has_account", "saved", "wealth_band", "ladder_country",
           "ladder_world", "pct_income", "pct_income_national", "pct_education", "pct_living",
           "pct_security", "pct_wealth", "ses_index"]


def db_path():
    return os.environ.get("RESPONSES_DB", os.path.join(os.path.dirname(__file__), "..", "instance", "responses.db"))


def connect(path=None):
    path = path or db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def _bool(value):
    return None if value is None else int(bool(value))


def row_from_result(answers, result, today=None):
    income = result["income"]
    living = result["living"]
    security = result["security"]
    ppp = income.get("ppp_per_day")
    return {
        "day": (today or datetime.date.today()).isoformat(),
        "country": result["country"]["iso3"],
        "income_mode": income["mode"],
        # Coarsened to powers of two ($1-2, $2-4, ... a day) so no exact income is kept.
        "income_log2_bucket": math.floor(math.log2(ppp)) if ppp and ppp > 0 else None,
        "education": answers.get("education"),
        "services_lacking": len(living["lacking"]) if living.get("answered") else None,
        "gallup_group": security.get("gallup_group"),
        "fies_raw": security.get("fies_raw"),
        "has_account": _bool(security.get("account")),
        "saved": _bool(security.get("saved")),
        "wealth_band": answers.get("wealth") if answers.get("wealth") != "skip" else None,
        "ladder_country": result["perception"].get("ladder_country"),
        "ladder_world": result["perception"].get("ladder_world"),
        "pct_income": income["global_pct"],
        "pct_income_national": income.get("national_pct"),
        "pct_education": result["education"]["global_pct"],
        "pct_living": living.get("global_pct"),
        "pct_security": security.get("global_pct"),
        "pct_wealth": result["wealth"].get("global_pct"),
        "ses_index": result["ses_index"],
    }


def save(row, path=None):
    with closing(connect(path)) as conn, conn:
        conn.execute(f"INSERT INTO responses ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
                     [row[c] for c in COLUMNS])


def summary(path=None):
    with closing(connect(path)) as conn:
        n = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        out = {"n": n, "min_group": MIN_GROUP}
        if n < MIN_GROUP:
            return out
        avg = conn.execute(
            "SELECT AVG(ses_index), AVG(pct_income), AVG(pct_education), AVG(pct_living),"
            " AVG(pct_security), AVG(pct_wealth) FROM responses").fetchone()
        out["averages"] = dict(zip(["ses_index", "income", "education", "living", "security", "wealth"], avg))
        out["income_deciles"] = [
            conn.execute("SELECT COUNT(*) FROM responses WHERE pct_income >= ? AND pct_income < ?",
                         (d * 10, d * 10 + 10 if d < 9 else 101)).fetchone()[0]
            for d in range(10)
        ]
        ladder = conn.execute(
            "SELECT AVG(ladder_world), AVG(MIN(10, MAX(1, CAST((ses_index + 9.999) / 10 AS INTEGER)))), COUNT(*)"
            " FROM responses WHERE ladder_world IS NOT NULL").fetchone()
        if ladder[2] >= MIN_GROUP:
            out["ladder"] = {"self": ladder[0], "measured": ladder[1], "n": ladder[2]}
        out["countries"] = [
            dict(r) for r in conn.execute(
                "SELECT country, COUNT(*) AS n, AVG(ses_index) AS ses_index, AVG(pct_income) AS income"
                " FROM responses GROUP BY country HAVING COUNT(*) >= ? ORDER BY n DESC", (MIN_GROUP,))
        ]
        return out


def export_rows(path=None):
    with closing(connect(path)) as conn:
        return [dict(r) for r in conn.execute(f"SELECT {', '.join(COLUMNS)} FROM responses ORDER BY id")]
