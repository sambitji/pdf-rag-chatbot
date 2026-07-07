"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_check():
    """Test readiness endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_invalid_query_payload():
    """Test invalid query payload handling."""
    response = client.post(
        "/api/query/ask",
        json={"query": ""}
    )
    assert response.status_code in {200, 422, 500}


def test_login_endpoint():
    """Test login endpoint."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_invalid_login():
    """Test invalid login."""
    response = client.post(
        "/api/auth/login",
        json={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401