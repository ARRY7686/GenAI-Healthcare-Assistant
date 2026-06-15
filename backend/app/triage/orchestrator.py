

from __future__ import annotations

import hashlib

from pydantic import BaseModel

from ..audit import AuditLogger
from ..clinical import care_pathway_for
from ..config import Settings
from ..domain import (
    CONSERVATIVE_FALLBACK_TIER,
    TIER_TEXT,
    Disposition,
    Duration,
    Onset,
    PatientCase,
    QAEntry,
    ScopeStatus,
    Severity,
    Symptom,
    SymptomStatus,
    Tier,
    most_urgent,
)
from ..llm import LLMFailure, LLMGateway, build_provider
from ..llm.schema import LLMExtractedSymptom, LLMTriageOutput
from ..safety import build_system_prompt


class TurnResult(BaseModel):
    kind: str  # "question" | "disposition" | "refusal"
    message: str
    question_rationale: str | None = None
    disposition: Disposition | None = None
    scope_status: str = "ok"
    fail_closed: bool = False


def _enum(cls, value, default):
    try:
        return cls(value)
    except (ValueError, KeyError):
        return default


def _to_symptom(s: LLMExtractedSymptom) -> Symptom:
    return Symptom(
        id=s.id,
        label=s.label,
        status=_enum(SymptomStatus, s.status, SymptomStatus.PRESENT),
        severity=_enum(Severity, s.severity, Severity.UNKNOWN),
        onset=_enum(Onset, s.onset, Onset.UNKNOWN),
        duration=Duration(value=s.duration_value, unit=s.duration_unit),
        note=s.note,
    )


class TriageEngine:
    def __init__(self, gateway: LLMGateway, settings: Settings, audit: AuditLogger) -> None:
        self._gateway = gateway
        self._settings = settings
        self._audit = audit
        self._system_prompt = build_system_prompt(settings.prompt_version)
        self._prompt_sha = hashlib.sha256(self._system_prompt.encode("utf-8")).hexdigest()[:12]
        self._max_turns = settings.max_clarifying_turns

    def log_consent(self, case: PatientCase) -> None:
        """Record an audit event when consent is accepted (provenance for processing basis)."""
        self._audit.log_consent(case)

    def step(self, case: PatientCase, transcript: list[dict], user_message: str) -> TurnResult:
        transcript.append({"role": "user", "content": user_message})
        case.turns += 1
        # Truthful provenance: stamp the resolved model id when a real provider ran, else "mock".
        provider = self._gateway.provider_name
        case.model_version = provider if provider == "mock" else self._settings.resolve_model()
        case.prompt_version = self._settings.prompt_version
        # Record the patient's answer to the pending clarifying question (provenance/timeline).
        if case.question_log and case.question_log[-1].answer is None:
            case.question_log[-1].answer = user_message
        if case.presenting_complaint is None:
            case.presenting_complaint = user_message

        context = {
            "turns": case.turns,
            "age_band": case.age_band,
            "sex": case.sex.value,
            "pregnancy_flag": case.pregnancy_flag,
            "sticky_red_flags": list(case.sticky_red_flags),
            "known_symptoms": [s.model_dump(mode="json") for s in case.symptoms],
        }

        try:
            out = self._gateway.triage_step(
                system_prompt=self._system_prompt, transcript=transcript, case_context=context
            )
        except LLMFailure:
            return self._fail_closed(case, transcript, user_message)

        self._merge_symptoms(case, out.extracted_symptoms)
        case.add_sticky_red_flags(out.detected_red_flags)

        emergency = bool(set(out.detected_red_flags) | set(case.sticky_red_flags)) or (
            out.disposition is not None and out.disposition.tier_code == "EMERGENCY_NOW"
        )

        # Scope: refuse/redirect minors & pregnancy — but never dead-end an emergency.
        if out.scope.is_violation and not emergency:
            return self._refuse(case, transcript, out, user_message)

        # Adaptive questioning (only when not an emergency and within the turn budget).
        if out.action == "ask" and out.next_question and case.turns < self._max_turns and not emergency:
            q = out.next_question
            case.question_log.append(QAEntry(turn=case.turns, question=q.text, rationale=q.rationale))
            transcript.append({"role": "assistant", "content": q.text})
            self._audit.log_turn(
                case=case, output=out, provider_name=provider, event="question",
                user_message=user_message, prompt_sha=self._prompt_sha,
            )
            return TurnResult(kind="question", message=q.text, question_rationale=q.rationale)

        # Decide.
        if out.disposition is None:
            # Model wanted to keep asking but we're out of budget, or inconsistent output.
            return self._fail_closed(case, transcript, user_message)

        tier = Tier[out.disposition.tier_code]        
        active_red_flags = sorted(
            set(out.disposition.red_flags) | set(out.detected_red_flags) | set(case.sticky_red_flags)
        )
        rationale = out.disposition.rationale
        if active_red_flags and tier != Tier.EMERGENCY_NOW:
            tier = Tier.EMERGENCY_NOW
            rationale = (
                f"Safety clamp: a named red-flag pattern ({', '.join(active_red_flags)}) was present, "
                f"so urgency was raised to emergency. " + rationale
            )
        disposition = self._build_disposition(
            tier=tier,
            rationale=rationale,
            red_flags=active_red_flags or out.disposition.red_flags,
            contributing=out.disposition.contributing_factors,
            confidence=out.disposition.confidence,
            safety_net=out.disposition.safety_net,
        )
        case.disposition = disposition
        msg = self._compose(disposition)
        transcript.append({"role": "assistant", "content": msg})
        self._audit.log_turn(
            case=case, output=out, provider_name=provider, event="disposition",
            user_message=user_message, prompt_sha=self._prompt_sha,
        )
        return TurnResult(kind="disposition", message=msg, disposition=disposition)

   

    def _merge_symptoms(self, case: PatientCase, extracted: list[LLMExtractedSymptom]) -> None:
        by_id = {s.id: s for s in case.symptoms}
        for e in extracted:
            sym = _to_symptom(e)
            if sym.id in by_id:
                existing = by_id[sym.id]
                # Update only fields that became more specific.
                if sym.severity != Severity.UNKNOWN:
                    existing.severity = sym.severity
                if sym.onset != Onset.UNKNOWN:
                    existing.onset = sym.onset
                if sym.duration.value is not None:
                    existing.duration = sym.duration
                # No silent decay (ADR-0010): a symptom already reported PRESENT is not silently
                # flipped to ABSENT (a real retraction would be an explicit, logged confirm step).
                if not (existing.status == SymptomStatus.PRESENT and sym.status == SymptomStatus.ABSENT):
                    existing.status = sym.status
            else:
                case.symptoms.append(sym)
                by_id[sym.id] = sym    

    def _fail_closed(self, case: PatientCase, transcript: list[dict], user_message: str) -> TurnResult:
        # ADR-0009: conservative referral, escalated to emergency if a red flag was already seen.
        tier = CONSERVATIVE_FALLBACK_TIER
        if case.sticky_red_flags:
            tier = most_urgent(tier, Tier.EMERGENCY_NOW)
        disposition = self._build_disposition(
            tier=tier,
            rationale="We could not fully complete the automated assessment, so we are erring on the side of caution.",
            red_flags=list(case.sticky_red_flags),
            contributing=[],
            confidence=None,
            safety_net=(
                "If you have severe or worsening symptoms — chest pain, trouble breathing, weakness "
                "on one side, or the worst headache of your life — call 112 now."
            ),
            fail_closed=True,
        )
        case.disposition = disposition
        msg = "I couldn't fully assess your symptoms just now, so to be safe:\n" + self._compose(disposition)
        transcript.append({"role": "assistant", "content": msg})
        self._audit.log_turn(
            case=case,
            output=None,
            provider_name=self._gateway.provider_name,
            event="disposition",
            user_message=user_message,
            prompt_sha=self._prompt_sha,
            fail_closed=True,
        )
        return TurnResult(kind="disposition", message=msg, disposition=disposition, fail_closed=True)


def build_engine(settings: Settings) -> TriageEngine:
    gateway = LLMGateway(build_provider(settings), max_retries=settings.llm_max_retries)
    audit = AuditLogger(settings.audit_log_path)
    return TriageEngine(gateway, settings, audit)
