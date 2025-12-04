"""Tests for V2.0 FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.v2.api import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_forms():
    """Test listing available forms."""
    response = client.get("/api/forms/list")
    assert response.status_code == 200
    data = response.json()
    assert "forms" in data
    assert len(data["forms"]) > 0
    # Check that employment_onboarding is in the list
    form_ids = [f["id"] for f in data["forms"]]
    assert "employment_onboarding" in form_ids


def test_start_form_success():
    """Test starting a form session successfully."""
    response = client.post(
        "/api/forms/start",
        json={"form_id": "employment_onboarding", "mode": "speed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "question" in data
    assert "is_complete" in data
    assert data["is_complete"] is False
    assert len(data["question"]) > 0


def test_start_form_invalid_id():
    """Test starting a form with invalid form_id."""
    response = client.post(
        "/api/forms/start",
        json={"form_id": "nonexistent_form", "mode": "speed"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_start_form_invalid_mode():
    """Test starting a form with invalid mode."""
    response = client.post(
        "/api/forms/start",
        json={"form_id": "employment_onboarding", "mode": "invalid_mode"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_answer_flow():
    """Test a complete answer flow: start -> answer -> get result."""
    # Start a form
    start_response = client.post(
        "/api/forms/start",
        json={"form_id": "employment_onboarding", "mode": "speed"}
    )
    assert start_response.status_code == 200
    start_data = start_response.json()
    session_id = start_data["session_id"]
    assert len(session_id) > 0
    
    # Submit an answer
    answer_response = client.post(
        "/api/forms/answer",
        json={"session_id": session_id, "message": "U.S. citizen"}
    )
    assert answer_response.status_code == 200
    answer_data = answer_response.json()
    assert "question" in answer_data or answer_data["is_complete"]
    
    # Get result (even if not complete, should return current state)
    result_response = client.get(f"/api/forms/result/{session_id}")
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert "session_id" in result_data
    assert "form_id" in result_data
    assert "collected_fields" in result_data


def test_answer_invalid_session():
    """Test submitting answer with invalid session_id."""
    response = client.post(
        "/api/forms/answer",
        json={"session_id": "nonexistent_session", "message": "test"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_result_invalid_session():
    """Test getting result for invalid session_id."""
    response = client.get("/api/forms/result/nonexistent_session")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data

