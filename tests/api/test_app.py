"""Tests for the FastAPI application."""

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed; install with pip install audio-engineer[api]")
from fastapi.testclient import TestClient  # noqa: E402

from audio_engineer.api.app import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_create_session(client):
    resp = client.post("/api/sessions/", json={
        "genre": "classic_rock",
        "key_root": "E",
        "key_mode": "minor",
        "tempo": 120,
        "with_keys": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"]
    assert data["status"] == "complete"
    assert data["genre"] == "classic_rock"
    assert data["key"] == "E minor"
    assert data["tempo"] == 120
    assert len(data["tracks"]) >= 3


def test_get_session(client):
    # Create a session first
    create_resp = client.post("/api/sessions/", json={
        "genre": "blues",
        "key_root": "A",
        "key_mode": "minor",
        "tempo": 90,
    })
    session_id = create_resp.json()["id"]

    # Retrieve it
    resp = client.get(f"/api/sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == session_id
    assert data["genre"] == "blues"


def test_get_session_not_found(client):
    resp = client.get("/api/sessions/nonexistent")
    assert resp.status_code == 404


def test_list_sessions(client):
    # Create a session
    client.post("/api/sessions/", json={"genre": "pop", "tempo": 100})

    resp = client.get("/api/sessions/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
