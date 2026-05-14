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
