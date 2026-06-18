"""Feature #5 — Patient Summary: structured clinician handoff."""

from __future__ import annotations

from app.config import Settings
from app.domain import Onset, PatientCase, Severity, Sex, Symptom, SymptomStatus
from app.handoff import build_clinician_summary
from app.triage import build_engine


def _engine():
    return build_engine(Settings(llm_provider="mock"))


def _case() -> PatientCase:
    return PatientCase(session_id="t")


def test_summary_has_all_structured_fields():
    eng = _engine()
    c = _case()
    c.age_band = "40-64"
    c.sex = Sex.FEMALE
    c.presenting_complaint = "sore throat"
    c.symptoms.append(Symptom(
        id="sore_throat", label="sore throat", severity=Severity.MILD,
        status=SymptomStatus.PRESENT, onset=Onset.GRADUAL,
    ))
    c.disposition = eng.assess(c)

    s = build_clinician_summary(c)
    assert s.presenting_complaint == "sore throat"
    assert any("sore throat" in t for t in s.timeline)
    assert "sore throat" in s.associated_symptoms
    assert s.tier_code == "SELF_CARE"
    assert s.rationale != ""
    assert "Age band: 40-64" in s.history
    assert "Sex: female" in s.history
    assert s.provenance  # disclaimer always present


def test_absent_symptom_recorded_as_denial_not_timeline():
    eng = _engine()
    c = _case()
    c.presenting_complaint = "headache"
    c.symptoms.append(Symptom(
        id="headache", label="headache", severity=Severity.MODERATE, status=SymptomStatus.PRESENT,
    ))
    c.symptoms.append(Symptom(
        id="chest_pain", label="chest pain", severity=Severity.UNKNOWN, status=SymptomStatus.ABSENT,
    ))
    c.disposition = eng.assess(c)

    s = build_clinician_summary(c)
    assert "chest pain" not in s.associated_symptoms  # ABSENT not listed as associated
    assert "Denies chest pain" in s.history
    assert all("chest pain" not in t for t in s.timeline)


def test_emergency_summary_carries_red_flags():
    eng = _engine()
    c = _case()
    c.presenting_complaint = "chest pain radiating to my arm with sweating"
    c.symptoms.append(Symptom(
        id="chest_pain", label="chest pain", severity=Severity.SEVERE, status=SymptomStatus.PRESENT,
    ))
    c.disposition = eng.assess(c)

    s = build_clinician_summary(c)
    assert s.tier_code == "EMERGENCY_NOW"
    assert "cardiac_chest_pain" in s.red_flags


def test_summary_api_flow():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    sid = client.post("/api/triage/start").json()["session_id"]
    client.post("/api/triage/respond", json={
        "session_id": sid, "message": "severe sore throat for two days",
    })
    res = client.post("/api/summary", json={"session_id": sid})
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == sid
    assert data["tier_code"] in [
        "EMERGENCY_NOW", "CASUALTY_TODAY", "PHYSICIAN_URGENT", "PHYSICIAN_ROUTINE", "SELF_CARE"
    ]
    for field in ("presenting_complaint", "timeline", "associated_symptoms", "history", "provenance"):
        assert field in data


def test_summary_requires_intake():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    sid = client.post("/api/triage/start").json()["session_id"]
    res = client.post("/api/summary", json={"session_id": sid})
    assert res.status_code == 409


def test_summary_unknown_session_404():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    res = client.post("/api/summary", json={"session_id": "does-not-exist"})
    assert res.status_code == 404
