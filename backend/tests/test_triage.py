"""Feature #3 — Urgency Stratification.

Unit tests for TriageEngine.assess() (tier mapping + escalate-only safety) and API tests for
POST /api/triage/assess. Run from the backend/ directory:  pytest
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain import PatientCase, Severity, Symptom, Tier, most_urgent
from app.llm import LLMGateway
from app.llm.mock_provider import MockLLMProvider
from app.main import app
from app.triage import build_engine

client = TestClient(app)


def _eng():
    return build_engine(get_settings())


def _case(*severities: Severity, red_flags: tuple[str, ...] = ()) -> PatientCase:
    case = PatientCase(session_id="t")
    for i, sev in enumerate(severities):
        case.symptoms.append(Symptom(id=f"s{i}", label=f"symptom_{i}", severity=sev))
    for f in red_flags:
        case.add_sticky_red_flags([f])
    return case


# ── tier mapping ────────────────────────────────────────────────────────────────

def test_tier_ordering():
    assert Tier.EMERGENCY_NOW < Tier.SELF_CARE
    assert most_urgent(Tier.SELF_CARE, Tier.CASUALTY_TODAY) == Tier.CASUALTY_TODAY


def test_red_flag_routes_emergency():
    d = _eng().assess(_case(Severity.MILD, red_flags=("cardiac_chest_pain",)))
    assert d.tier == Tier.EMERGENCY_NOW
    assert "cardiac_chest_pain" in d.red_flags


def test_severe_routes_casualty_today():
    assert _eng().assess(_case(Severity.SEVERE)).tier == Tier.CASUALTY_TODAY


def test_moderate_routes_physician_urgent():
    assert _eng().assess(_case(Severity.MODERATE)).tier == Tier.PHYSICIAN_URGENT


def test_mild_routes_self_care():
    assert _eng().assess(_case(Severity.MILD)).tier == Tier.SELF_CARE


def test_worst_symptom_drives_tier():
    # Mixed severities → the most severe wins.
    assert _eng().assess(_case(Severity.MILD, Severity.SEVERE, Severity.MODERATE)).tier == Tier.CASUALTY_TODAY


def test_similar_complaints_different_urgency():
    # Success metric: two similar complaints with different severity get different urgency.
    mild = _eng().assess(_case(Severity.MILD)).tier
    severe = _eng().assess(_case(Severity.SEVERE)).tier
    assert mild != severe
    assert severe < mild  # lower value = more urgent


def test_red_flag_overrides_severity_escalate_only():
    # A red flag with only mild symptoms still escalates to emergency — never de-escalates.
    assert _eng().assess(_case(Severity.MILD, red_flags=("thunderclap_headache",))).tier == Tier.EMERGENCY_NOW


def test_no_symptoms_is_conservative_not_self_care():
    assert _eng().assess(_case()).tier != Tier.SELF_CARE


def test_mock_provider_emits_valid_schema():
    out = LLMGateway(MockLLMProvider(), max_retries=0).triage_step(
        system_prompt="x",
        transcript=[{"role": "user", "content": "chest pain radiating to arm, sweating"}],
        case_context={"turns": 1},
    )
    assert out.action == "decide"
    assert out.disposition.tier_code == "EMERGENCY_NOW"


# ── API: POST /api/triage/assess ─────────────────────────────────────────────────

def _start() -> str:
    return client.post("/api/triage/start").json()["session_id"]


def test_assess_endpoint_classifies_after_chat():
    sid = _start()
    client.post("/api/triage/respond", json={"session_id": sid, "message": "I have a severe headache"})
    client.post("/api/triage/respond", json={"session_id": sid, "message": "started two days ago, also some nausea"})
    r = client.post("/api/triage/assess", json={"session_id": sid})
    assert r.status_code == 200
    body = r.json()
    assert body["tier"] in {"EMERGENCY_NOW", "CASUALTY_TODAY", "PHYSICIAN_URGENT", "PHYSICIAN_ROUTINE", "SELF_CARE"}
    assert body["headline"] and body["rationale"]


def test_assess_emergency_through_chat():
    sid = _start()
    client.post(
        "/api/triage/respond",
        json={"session_id": sid, "message": "crushing chest pain spreading to my left arm, sweating"},
    )
    assert client.post("/api/triage/assess", json={"session_id": sid}).json()["tier"] == "EMERGENCY_NOW"


def test_assess_unknown_session_404():
    assert client.post("/api/triage/assess", json={"session_id": "nope"}).status_code == 404


def test_assess_before_any_symptoms_409():
    sid = _start()
    assert client.post("/api/triage/assess", json={"session_id": sid}).status_code == 409
