"""Unit tests for Lab 6 production agent — used in CI pipeline."""
import os

# Set env before importing app (config loads at import time)
os.environ.setdefault("AGENT_API_KEY", "test-ci-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")

from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "test-ci-key"}


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
        assert response.json()["ready"] is True


def test_ask_without_api_key():
    with TestClient(app) as client:
        response = client.post("/ask", json={"question": "hello"})
        assert response.status_code == 401


def test_ask_with_invalid_api_key():
    with TestClient(app) as client:
        response = client.post(
            "/ask",
            json={"question": "hello"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


def test_ask_with_valid_api_key():
    with TestClient(app) as client:
        response = client.post(
            "/ask",
            json={"question": "What is deployment?"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "What is deployment?"
        assert len(data["answer"]) > 0


def test_ask_validation_empty_question():
    with TestClient(app) as client:
        response = client.post("/ask", json={"question": ""}, headers=HEADERS)
        assert response.status_code == 422
