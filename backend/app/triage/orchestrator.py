"""Triage orchestrator — Feature #2: Adaptive Questioning.

This is the clinical-decision loop that drives the conversation. Each turn it ingests the
patient's message, updates the canonical PatientCase (intake — feature #1), and decides
whether to ask ONE more clarifying question or that enough information has been collected.

Scope of THIS feature (#2): the adaptive-questioning loop only. It deliberately does NOT
produce an urgency tier, care pathway, patient summary, or the deterministic safety
override — those are owned by features #3/#4/#5/#6 and are stubbed elsewhere. When the
engine has enough information, `ask_step` returns `is_complete=True` and the downstream
`/api/triage/assess` endpoint (feature #3) takes over.

The model (real or mock) chooses the single most informative question to ask and supplies a
short clinical rationale for it; both the question and its rationale are recorded on the
PatientCase so the adaptive path is fully traceable.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..config import Settings
from ..domain import (
    Duration,
    Onset,
    PatientCase,
    QAEntry,
    Severity,
    Symptom,
    SymptomStatus,
)
from ..llm import LLMFailure, LLMGateway, build_provider
from ..llm.schema import LLMExtractedSymptom

OPENING_QUESTION = "What is your main symptom or concern today?"

# Concise triage system prompt. The offline mock ignores it; it guides real providers once
# they are wired in. Deeper guardrail prompting is feature #6's responsibility.
SYSTEM_PROMPT = (
    "You are a careful clinical triage assistant for adults in India. Collect the patient's "
    "symptoms through a short, adaptive conversation. Each turn, extract any symptoms mentioned "
    "(id, label, status, severity, onset, duration) and decide whether to ASK one more clarifying "
    "question or that you have enough to stop. Ask the single most informative question that would "
    "best narrow the urgency assessment, and always give a short clinical rationale for why you are "
    "asking it. This is triage signposting, not a diagnosis."
)


class AskResult(BaseModel):
    """Outcome of one adaptive-questioning turn (feature #2)."""

    is_complete: bool  # True once enough info is collected → hand off to urgency assessment
    question: str | None = None  # next clarifying question (None when complete)
    rationale: str | None = None  # why that question was asked (adaptive-questioning evidence)
    progress: int = 0  # 0–100 intake progress indicator
    fail_closed: bool = False  # True if the LLM failed and intake stopped conservatively


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
    def __init__(self, gateway: LLMGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._settings = settings
        self._max_turns = settings.max_clarifying_turns

    @staticmethod
    def opening_question() -> str:
        return OPENING_QUESTION

    def ask_step(self, case: PatientCase, transcript: list[dict], user_message: str) -> AskResult:
        """Ingest one patient message and decide: ask another clarifying question, or stop."""
        transcript.append({"role": "user", "content": user_message})
        case.turns += 1
        case.prompt_version = self._settings.prompt_version
        provider = self._gateway.provider_name
        case.model_version = provider if provider == "mock" else self._settings.resolve_model()

        # Anchor the presenting complaint on the first message; record the patient's answer to
        # the clarifying question we asked last turn (provenance for the adaptive loop).
        if case.presenting_complaint is None:
            case.presenting_complaint = user_message
        if case.question_log and case.question_log[-1].answer is None:
            case.question_log[-1].answer = user_message

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
                system_prompt=SYSTEM_PROMPT, transcript=transcript, case_context=context
            )
        except LLMFailure:
            # Fail-closed for intake: stop asking and hand off to assessment rather than
            # dead-ending the conversation. Downstream tier logic (feature #3) errs safe.
            return AskResult(is_complete=True, progress=100, fail_closed=True)

        self._merge_symptoms(case, out.extracted_symptoms)
        case.add_sticky_red_flags(out.detected_red_flags)

        # Adaptive ask: keep clarifying only while the model wants more info AND we have turn
        # budget. The model picks the single most informative question (ADR-0006).
        wants_more = out.action == "ask" and out.next_question is not None
        if wants_more and case.turns < self._max_turns:
            q = out.next_question
            case.question_log.append(QAEntry(turn=case.turns, question=q.text, rationale=q.rationale))
            transcript.append({"role": "assistant", "content": q.text})
            return AskResult(
                is_complete=False,
                question=q.text,
                rationale=q.rationale,
                progress=self._progress(case.turns),
            )

        # Enough information collected (or out of turn budget) → intake complete.
        return AskResult(is_complete=True, progress=100)

    def _progress(self, turns: int) -> int:
        # Coarse progress while still asking; never report 100 until intake is complete.
        return min(90, round(100 * turns / max(1, self._max_turns)))

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


def build_engine(settings: Settings) -> TriageEngine:
    gateway = LLMGateway(build_provider(settings), max_retries=settings.llm_max_retries)
    return TriageEngine(gateway, settings)
