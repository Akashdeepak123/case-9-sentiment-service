import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_predict_positive_high_confidence(client: TestClient) -> None:
    response = client.post(
        "/predict",
        json={"text": "I love this movie, it was amazing"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "POSITIVE"
    assert data["score"] > 0.9


def test_predict_negative_high_confidence(client: TestClient) -> None:
    response = client.post(
        "/predict",
        json={"text": "This was terrible, worst film ever"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "NEGATIVE"
    assert data["score"] > 0.9


def test_predict_empty_string_returns_422(client: TestClient) -> None:
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422


def test_predict_missing_text_returns_422(client: TestClient) -> None:
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_predict_logs_to_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_path = tmp_path / "logs.db"
    monkeypatch.setenv("LOG_DB_PATH", str(db_path))
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={"text": "Unique log test phrase for sqlite row"},
        )
    assert response.status_code == 200
    expected_label = response.json()["label"]
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute("SELECT COUNT(*), predicted_label FROM predictions")
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 1
        assert row[1] == expected_label
    finally:
        conn.close()
