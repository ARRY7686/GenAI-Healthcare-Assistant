from __future__ import annotations

import hashlib

from pydantic import BaseModel
from ..domain import (
    CONSERVATIVE_FALLBACK_TIER,
    TIER_TEXT,
    Duration,
    Onset,
    PatientCase,
    QAEntry,
    Severity,
    Symptom,
    SymptomStatus,
)
from ..llm import LLMFailure, LLMGateway, build_provider
from ..llm.schema import LLMExtractedSymptom, LLMTriageOutput


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
    
    def step(self, case: PatientCase, transcript: list[dict], user_message: str) -> TurnResult:
        if out.action == "ask" and out.next_question and case.turns < self._max_turns and not emergency:
            q = out.next_question
            case.question_log.append(QAEntry(turn=case.turns, question=q.text, rationale=q.rationale))
            transcript.append({"role": "assistant", "content": q.text})
            self._audit.log_turn(
                case=case, output=out, provider_name=provider, event="question",
                user_message=user_message, prompt_sha=self._prompt_sha,
            )
            return TurnResult(kind="question", message=q.text, question_rationale=q.rationale)
        