"""Clinician handoff — Feature #5: Patient Summary (FHIR/ABDM-shaped, ADR-0013).

Turns the canonical PatientCase into a structured, human-readable ClinicianSummary for the
provider: presenting complaint, symptom timeline, associated symptoms, relevant history, and
the AI urgency assessment. Disposition and red flags are discrete coded fields, not prose.

This is SHAPED for interoperability; it is NOT validated against a FHIR server and is NOT wired
to live ABDM/ABHA. Synthetic data only — AI-generated triage, not a diagnosis.
"""

from __future__ import annotations

from ..domain import (
    ClinicianSummary,
    PatientCase,
    Sex,
    SymptomStatus,
    TIER_TEXT,
)


def _duration_phrase(value: float, unit: str | None) -> str:
    # Render 2.0 -> "2", but keep 1.5 -> "1.5".
    num = f"{value:g}"
    return f"for {num} {unit or ''}".strip()


def build_clinician_summary(case: PatientCase) -> ClinicianSummary:
    """Build the structured clinician handoff summary from the collected PatientCase."""
    disp = case.disposition

    # Symptom timeline — only PRESENT symptoms, each with whatever discriminators we captured.
    timeline: list[str] = []
    for s in case.symptoms:
        if s.status != SymptomStatus.PRESENT:
            continue
        parts = [s.label]
        if s.onset.value != "unknown":
            parts.append(f"onset {s.onset.value}")
        if s.duration and s.duration.value:
            parts.append(_duration_phrase(s.duration.value, s.duration.unit))
        if s.severity.value != "unknown":
            parts.append(f"severity {s.severity.value}")
        timeline.append(", ".join(parts))

    associated_symptoms = [
        s.label for s in case.symptoms if s.status == SymptomStatus.PRESENT
    ]

    # Relevant history — risk flags plus the demographics and explicit denials the case holds.
    history: list[str] = list(case.risk_flags)
    if case.age_band:
        history.append(f"Age band: {case.age_band}")
    if case.sex != Sex.UNKNOWN:
        history.append(f"Sex: {case.sex.value}")
    if case.pregnancy_flag:
        history.append("Pregnancy reported")
    history += [f"Denies {s.label}" for s in case.symptoms if s.status == SymptomStatus.ABSENT]

    tier_code = TIER_TEXT[disp.tier]["code"] if disp else "UNDETERMINED"
    tier_headline = TIER_TEXT[disp.tier]["headline"] if disp else "Undetermined"

    return ClinicianSummary(
        session_id=case.session_id,
        presenting_complaint=case.presenting_complaint,
        timeline=timeline,
        associated_symptoms=associated_symptoms,
        history=history,
        tier_code=tier_code,
        tier_headline=tier_headline,
        rationale=disp.rationale if disp else "",
        red_flags=(disp.red_flags if disp else []) or list(case.sticky_red_flags),
        confidence=disp.confidence if disp else None,
    )
