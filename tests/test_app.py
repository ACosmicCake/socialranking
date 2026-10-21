from ses import storage
from tests.conftest import FULL_ANSWERS, MINIMAL_ANSWERS


def test_static_pages(client):
    for path in ("/", "/quiz", "/methodology", "/methodology?country=IND", "/questionnaire", "/sources",
                 "/source", "/about", "/faq", "/creator", "/stats"):
        response = client.get(path)
        assert response.status_code == 200, path


def test_quiz_lists_countries(client):
    html = client.get("/quiz").get_data(as_text=True)
    assert 'value="VNM"' in html and 'data-currency="VND"' in html


def test_submit_full_quiz(client):
    response = client.post("/quiz", data=FULL_ANSWERS)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "of the world&#39;s population" in html or "of the world's population" in html
    assert "Vietnam" in html
    assert storage.summary()["n"] == 0  # no consent, nothing stored


def test_submit_with_consent_stores_anonymous_row(client):
    for _ in range(5):
        client.post("/quiz", data={**FULL_ANSWERS, "research_consent": "on"})
    rows = storage.export_rows()
    assert len(rows) == 5
    assert rows[0]["country"] == "VNM"
    assert "income_amount" not in rows[0]
    summary = storage.summary()
    assert summary["n"] == 5 and summary["countries"][0]["n"] == 5
    assert client.get("/stats").status_code == 200


def test_invalid_submission_shows_errors(client):
    response = client.post("/quiz", data={"country": "VNM"})
    assert response.status_code == 400
    assert "invalid-feedback" in response.get_data(as_text=True)


def test_api_score(client):
    response = client.post("/api/score", json=MINIMAL_ANSWERS)
    assert response.status_code == 200
    body = response.get_json()
    assert body["country"]["iso3"] == "USA"
    assert "chart" not in body["income"]
    assert client.post("/api/score", json={"country": "USA"}).status_code == 400
    assert client.post("/api/score", data="nope").status_code == 400


def test_csv_export_requires_token(client, monkeypatch):
    assert client.get("/stats.csv").status_code == 404
    monkeypatch.setenv("STATS_TOKEN", "secret")
    assert client.get("/stats.csv?token=wrong").status_code == 404
    response = client.get("/stats.csv?token=secret")
    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith("day,country")


def test_legacy_result_redirects(client):
    assert client.get("/result").status_code == 302


def test_404(client):
    assert client.get("/nope").status_code == 404
