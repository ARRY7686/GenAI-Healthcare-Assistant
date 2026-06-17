"""Core triage-engine tests: tier ordering, emergency routing, scope, sticky, fail-closed."""

from __future__ import annotations

import tempfile

from app.config import Settings
from app.domain import PatientCase, Severity, SymptomStatus, Symptom, Tier, most_urgent
from app.llm import LLMGateway
from app.triage import TriageEngine, build_engine


def _engine() -> TriageEngine:
    settings = Settings(llm_provider="mock", audit_log_path=tempfile.mkstemp(suffix=".jsonl")[1])
    return build_engine(settings)


def _new_case() -> PatientCase:
    return PatientCase(session_id="t")


# ── Existing tier ordering tests ───────────────────────────────────────────

def test_tier_ordering():
    assert Tier.EMERGENCY_NOW < Tier.SELF_CARE
    assert most_urgent(Tier.SELF_CARE, Tier.CASUALTY_TODAY) == Tier.CASUALTY_TODAY


# ── Feature #3: Urgency Stratification ────────────────────────────────────

def test_severe_symptom_routes_casualty_today():
    eng = _engine()
    case = _new_case()
    case.symptoms.append(Symptom(
        id="sore_throat", label="sore throat",
        severity=Severity.SEVERE, status=SymptomStatus.PRESENT
    ))
    d = eng.assess(case)
    assert d.tier == Tier.CASUALTY_TODAY


def test_moderate_symptom_routes_physician_urgent():
    eng = _engine()
    case = _new_case()
    case.symptoms.append(Symptom(
        id="sore_throat", label="sore throat",
        severity=Severity.MODERATE, status=SymptomStatus.PRESENT
    ))
    d = eng.assess(case)
    assert d.tier == Tier.PHYSICIAN_URGENT


def test_mild_symptom_routes_self_care():
    eng = _engine()
    case = _new_case()
    case.symptoms.append(Symptom(
        id="sore_throat", label="sore throat",
        severity=Severity.MILD, status=SymptomStatus.PRESENT
    ))
    d = eng.assess(case)
    assert d.tier == Tier.SELF_CARE


def test_red_flag_overrides_mild_symptom_to_emergency():
    eng = _engine()
    case = _new_case()
    case.symptoms.append(Symptom(
        id="chest_pain", label="chest pain",
        severity=Severity.MILD, status=SymptomStatus.PRESENT
    ))
    case.add_sticky_red_flags(["cardiac_chest_pain"])
    d = eng.assess(case)
    assert d.tier == Tier.EMERGENCY_NOW


def test_red_flag_overrides_severe_symptom_to_emergency():
    eng = _engine()
    case = _new_case()
    case.symptoms.append(Symptom(
        id="headache", label="headache",
        severity=Severity.SEVERE, status=SymptomStatus.PRESENT
    ))
    case.add_sticky_red_flags(["thunderclap_headache"])
    d = eng.assess(case)
    assert d.tier == Tier.EMERGENCY_NOW


def test_no_symptoms_is_conservative():
    eng = _engine()
    case = _new_case()
    d = eng.assess(case)
    assert d.tier != Tier.SELF_CARE
    assert d.tier != Tier.EMERGENCY_NOW  # no red flags so not emergency either


def test_severe_vs_mild_same_complaint_differ():
    eng = _engine()
    case_severe = _new_case()
    case_severe.symptoms.append(Symptom(
        id="sore_throat", label="sore throat",
        severity=Severity.SEVERE, status=SymptomStatus.PRESENT
    ))
    case_mild = _new_case()
    case_mild.symptoms.append(Symptom(
        id="sore_throat", label="sore throat",
        severity=Severity.MILD, status=SymptomStatus.PRESENT
    ))
    assert eng.assess(case_severe).tier != eng.assess(case_mild).tier


def test_absent_symptom_ignored_in_severity():
    """ABSENT symptoms must not influence the tier — only PRESENT counts."""
    eng = _engine()
    case = _new_case()
    case.symptoms.append(Symptom(
        id="chest_pain", label="chest pain",
        severity=Severity.SEVERE, status=SymptomStatus.ABSENT  # ABSENT — must be ignored
    ))
    case.symptoms.append(Symptom(
        id="sore_throat", label="sore throat",
        severity=Severity.MILD, status=SymptomStatus.PRESENT
    ))
    d = eng.assess(case)
    assert d.tier == Tier.SELF_CARE  # severe ABSENT ignored, only mild PRESENT counts


def test_assess_api_flow():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    # start session
    sid = client.post("/api/triage/start").json()["session_id"]
    # respond with a symptom
    client.post("/api/triage/respond", json={
        "session_id": sid,
        "message": "severe sore throat"
    })
    # assess
    res = client.post("/api/triage/assess", json={"session_id": sid})
    assert res.status_code == 200
    data = res.json()
    assert data["tier_code"] in [
        "EMERGENCY_NOW", "CASUALTY_TODAY", "PHYSICIAN_URGENT", "SELF_CARE"
    ]
    assert data["session_id"] == sid
    assert data["rationale"] != ""
    assert data["safety_net"] != ""

# ── End Feature #3 ────────────────────────────────────────────────────────