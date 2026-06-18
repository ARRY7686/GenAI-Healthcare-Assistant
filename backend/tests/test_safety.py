"""Feature #6 — Safety Guardrails: deterministic hard-coded emergency override."""

from __future__ import annotations

from app.config import Settings
from app.domain import PatientCase, Severity, Symptom, SymptomStatus, Tier
from app.safety import detect_emergency_patterns
from app.triage import build_engine


def _engine():
    return build_engine(Settings(llm_provider="mock"))


def _case() -> PatientCase:
    return PatientCase(session_id="t")


# ── Pattern detection ──────────────────────────────────────────────────────

def test_chest_pain_plus_arm_detected():
    c = _case()
    c.presenting_complaint = "crushing chest pain spreading to my left arm with sweating"
    assert "cardiac_chest_pain" in detect_emergency_patterns(c)


def test_thunderclap_headache_detected():
    c = _case()
    c.presenting_complaint = "the worst headache of my life, it came on suddenly"
    assert "thunderclap_headache" in detect_emergency_patterns(c)


def test_stroke_signs_detected():
    c = _case()
    c.presenting_complaint = "my face is drooping and my speech is slurred"
    assert "stroke_signs" in detect_emergency_patterns(c)


def test_chest_pain_alone_does_not_fire():
    """Chest pain without any radiation/autonomic feature must NOT fire the cardiac pattern."""
    c = _case()
    c.presenting_complaint = "mild chest pain only"
    assert "cardiac_chest_pain" not in detect_emergency_patterns(c)


def test_negation_does_not_fire():
    c = _case()
    c.presenting_complaint = "no chest pain, just a mild cough"
    assert detect_emergency_patterns(c) == []


def test_pattern_detected_from_symptom_note():
    c = _case()
    c.symptoms.append(Symptom(
        id="chest_pain", label="chest pain", severity=Severity.MILD,
        status=SymptomStatus.PRESENT, note="radiating to the jaw",
    ))
    assert "cardiac_chest_pain" in detect_emergency_patterns(c)


# ── Deterministic override in assess() ─────────────────────────────────────

def test_guardrail_overrides_mild_symptom_to_emergency():
    """A hard-coded emergency pattern routes to EMERGENCY_NOW even when severity is mild."""
    eng = _engine()
    c = _case()
    c.presenting_complaint = "mild chest pain but also pain down my arm and sweating"
    c.symptoms.append(Symptom(
        id="chest_pain", label="chest pain", severity=Severity.MILD, status=SymptomStatus.PRESENT,
    ))
    d = eng.assess(c)
    assert d.tier == Tier.EMERGENCY_NOW
    assert "cardiac_chest_pain" in d.red_flags


def test_guardrail_latches_onto_sticky_red_flags():
    eng = _engine()
    c = _case()
    c.presenting_complaint = "worst headache of my life, sudden"
    eng.assess(c)
    assert "thunderclap_headache" in c.sticky_red_flags


def test_emergency_pattern_api_routes_emergency():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    sid = client.post("/api/triage/start").json()["session_id"]
    client.post("/api/triage/respond", json={
        "session_id": sid,
        "message": "crushing chest pain radiating to my left arm and sweating",
    })
    res = client.post("/api/triage/assess", json={"session_id": sid})
    assert res.status_code == 200
    assert res.json()["tier_code"] == "EMERGENCY_NOW"
