"""Unit tests for Lab 6 production agent — used in CI pipeline."""
import os

os.environ.setdefault("AGENT_API_KEY", "test-ci-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("MODEL_NAME", "mock-agent")

from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "test-ci-key"}
ASK_BODY = {"question": "What is deployment?", "user_id": "user1"}


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "endpoints" in data


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data


def test_ready():
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["redis"] == "ok"


def test_ask_without_api_key():
    with TestClient(app) as client:
        response = client.post("/ask", json=ASK_BODY)
        assert response.status_code == 401


def test_ask_with_invalid_api_key():
    with TestClient(app) as client:
        response = client.post(
            "/ask",
            json=ASK_BODY,
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


def test_ask_with_valid_api_key():
    with TestClient(app) as client:
        response = client.post("/ask", json=ASK_BODY, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user1"
        assert data["conversation_length"] == 1
        assert len(data["answer"]) > 0
        assert data["metadata"]["model"] == "mock-agent"
        assert data["metadata"]["cost_usd"] == 0.001


def test_ask_validation_empty_question():
    with TestClient(app) as client:
        response = client.post(
            "/ask",
            json={"question": "", "user_id": "user1"},
            headers=HEADERS,
        )
        assert response.status_code == 422
