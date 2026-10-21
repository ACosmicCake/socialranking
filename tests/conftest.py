import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TODAY = datetime.date(2026, 10, 21)

FULL_ANSWERS = {
    "country": "VNM",
    "income_mode": "exact",
    "income_amount": "20,000,000",
    "income_period": "month",
    "household_size": "4",
    "education": "tertiary",
    "electricity": "yes",
    "cooking": "gas",
    "water": "safely_managed",
    "sanitation": "safely_managed",
    "hygiene": "yes",
    "internet": "yes",
    "health_hardship": "no",
    "food_money": "no",
    "shelter_money": "no",
    "count_on": "yes",
    "fies_worried": "no",
    "fies_healthy": "no",
    "fies_few_kinds": "no",
    "fies_skipped": "no",
    "fies_ate_less": "no",
    "fies_ran_out": "no",
    "fies_hungry": "no",
    "fies_whole_day": "no",
    "account": "yes",
    "saved": "yes",
    "wealth": "10k_100k",
    "ladder_country": "6",
    "ladder_world": "5",
}

MINIMAL_ANSWERS = {
    "country": "USA",
    "income_mode": "band",
    "income_band": "b5",
    "education": "secondary",
}


@pytest.fixture
def full_answers():
    return dict(FULL_ANSWERS)


@pytest.fixture
def minimal_answers():
    return dict(MINIMAL_ANSWERS)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RESPONSES_DB", str(tmp_path / "responses.db"))
    from application import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
