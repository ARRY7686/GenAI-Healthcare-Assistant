"""Tests for Feature #2 — Adaptive Questioning (POST /api/triage/respond).

Run from the backend/ directory:  pytest
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start() -> dict:
    r = client.post("/api/triage/start")
    assert r.status_code == 200
    return r.json()


def _respond(sid: str, message: str) -> dict:
    r = client.post("/api/triage/respond", json={"session_id": sid, "message": message})
    assert r.status_code == 200
    return r.json()


def test_health_ok():
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"


def test_start_returns_session_and_opening_question():
    body = _start()
    assert body["session_id"]
    assert body["question"]
    assert body["progress"] == 0


def test_start_accepts_consent_demographics():
    r = client.post("/api/triage/start", json={"age_band": "40-64", "sex": "male", "pregnancy_flag": False})
    assert r.status_code == 200
    assert r.json()["session_id"]


def test_respond_asks_clarifying_question_with_rationale():
    sid = _start()["session_id"]
    body = _respond(sid, "I have a headache")
    assert body["is_complete"] is False
    assert body["question"]
    # Adaptive questioning ALWAYS explains why it is asking (clinical decision evidence).
    assert body["rationale"]
    assert 0 < body["progress"] < 100


def test_adaptive_questions_advance_then_complete():
    sid = _start()["session_id"]
    q1 = _respond(sid, "I have a headache")                       # -> asks severity/onset
    q2 = _respond(sid, "it's moderate and came on gradually")     # -> asks duration
    q3 = _respond(sid, "it's been about two days")                # -> asks associated symptoms
    done = _respond(sid, "I also have some nausea")               # -> enough info, completes

    # Each clarifying question targets a DIFFERENT discriminator (adaptive narrowing).
    asked = [q1["question"], q2["question"], q3["question"]]
    assert all(asked)
    assert len(set(asked)) == 3
    assert q1["is_complete"] is False
    assert done["is_complete"] is True
    assert done["question"] is None
    assert done["progress"] == 100


def test_emergency_red_flag_stops_intake():
    sid = _start()["session_id"]
    body = _respond(sid, "I have crushing chest pain spreading to my left arm and I'm sweating")
    # An obvious emergency pattern ends the clarifying loop immediately.
    assert body["is_complete"] is True


def test_respond_unknown_session_returns_404():
    r = client.post("/api/triage/respond", json={"session_id": "does-not-exist", "message": "hi"})
    assert r.status_code == 404


def test_respond_rejects_empty_message():
    sid = _start()["session_id"]
    r = client.post("/api/triage/respond", json={"session_id": sid, "message": "   "})
    assert r.status_code == 400


def test_summary_is_stubbed_501():
    sid = _start()["session_id"]
    # Urgency assessment (feature #3) is now implemented; only the patient summary remains a stub.
    assert client.post("/api/summary", json={"session_id": sid}).status_code == 501
