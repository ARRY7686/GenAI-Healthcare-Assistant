"""Core triage-engine tests: tier ordering, emergency routing, scope, sticky, fail-closed."""

from __future__ import annotations

import tempfile

from app.audit import AuditLogger
from app.config import Settings
from app.domain import PatientCase, Tier, most_urgent
from app.llm import LLMFailure, LLMGateway
from app.llm.mock_provider import MockLLMProvider
from app.triage import TriageEngine, build_engine


def _engine(provider=None) -> TriageEngine:
    settings = Settings(llm_provider="mock", audit_log_path=tempfile.mkstemp(suffix=".jsonl")[1])
    if provider is None:
        return build_engine(settings)
    gateway = LLMGateway(provider, max_retries=0)
    return TriageEngine(gateway, settings, AuditLogger(settings.audit_log_path))


def _new_case() -> tuple[PatientCase, list[dict]]:
    return PatientCase(session_id="t"), []


def test_tier_ordering():
    assert Tier.EMERGENCY_NOW < Tier.SELF_CARE
    assert most_urgent(Tier.SELF_CARE, Tier.CASUALTY_TODAY) == Tier.CASUALTY_TODAY


def test_cardiac_chest_pain_routes_emergency():
    eng = _engine()
    case, tx = _new_case()
    res = eng.step(case, tx, "I have bad chest pain spreading to my left arm and I'm sweating")
    assert res.kind == "disposition"
    assert res.disposition.tier == Tier.EMERGENCY_NOW
    assert "cardiac_chest_pain" in res.disposition.red_flags


def test_thunderclap_headache_routes_emergency():
    eng = _engine()
    case, tx = _new_case()
    res = eng.step(case, tx, "the worst headache of my life came on suddenly")
    assert res.disposition.tier == Tier.EMERGENCY_NOW


def test_mild_symptom_is_not_emergency():
    eng = _engine()
    case, tx = _new_case()
    # First turn asks a clarifying question (adaptive), not an emergency.
    res = eng.step(case, tx, "I have a mild sore throat")
    assert res.kind in ("question", "disposition")
    if res.kind == "disposition":
        assert res.disposition.tier != Tier.EMERGENCY_NOW


def test_sticky_red_flag_persists():
    eng = _engine()
    case, tx = _new_case()
    eng.step(case, tx, "I suddenly got the worst headache of my life")
    res2 = eng.step(case, tx, "actually I think I feel a bit better now")
    assert res2.disposition.tier == Tier.EMERGENCY_NOW  # cannot be erased


def test_pregnancy_is_refused_but_emergency_still_escalates():
    eng = _engine()
    # Non-emergency pregnancy → refusal
    case, tx = _new_case()
    case.pregnancy_flag = True
    res = eng.step(case, tx, "I have a mild backache")
    assert res.kind == "refusal"
    # Pregnancy + emergency red flag → still emergency, never dead-ended
    case2, tx2 = _new_case()
    case2.pregnancy_flag = True
    res2 = eng.step(case2, tx2, "I'm pregnant and have chest pain radiating to my arm with sweating")
    assert res2.disposition is not None and res2.disposition.tier == Tier.EMERGENCY_NOW


def test_fail_closed_on_provider_failure():
    class BrokenProvider:
        name = "broken"

        def triage_step(self, **kwargs):
            raise LLMFailure("boom")

    eng = _engine(BrokenProvider())
    case, tx = _new_case()
    res = eng.step(case, tx, "I have a headache")
    assert res.kind == "disposition"
    assert res.fail_closed is True
    assert res.disposition.tier != Tier.SELF_CARE  # never silently self-care


def test_mock_provider_emits_valid_schema():
    out = LLMGateway(MockLLMProvider(), max_retries=0).triage_step(
        system_prompt="x",
        transcript=[{"role": "user", "content": "chest pain radiating to arm, sweating"}],
        case_context={"turns": 1},
    )
    assert out.action == "decide"
    assert out.disposition.tier_code == "EMERGENCY_NOW"
