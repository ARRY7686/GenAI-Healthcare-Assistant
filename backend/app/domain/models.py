"""Domain models — the canonical PatientCase (ADR-0010) and its parts.

The PatientCase is the single source of truth the disposition reads from; raw chat
history is only used for conversational phrasing. Tri-state symptom status keeps
"denies chest pain" distinct from "never asked".
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from .tiers import Tier


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SymptomStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class Onset(str, Enum):
    SUDDEN = "sudden"
    GRADUAL = "gradual"
    UNKNOWN = "unknown"


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class ScopeStatus(str, Enum):
    OK = "ok"
    REFUSED_MINOR = "refused_minor"
    REFUSED_PREGNANCY = "refused_pregnancy"


class Duration(BaseModel):
    value: float | None = None
    unit: str | None = None  # e.g. "minutes", "hours", "days"


class Symptom(BaseModel):
    id: str  # custom enum code, e.g. "chest_pain"
    label: str
    status: SymptomStatus = SymptomStatus.PRESENT
    severity: Severity = Severity.UNKNOWN
    onset: Onset = Onset.UNKNOWN
    duration: Duration = Field(default_factory=Duration)
    note: str | None = None
    snomed_code: str | None = None  # optional interoperability hook (ADR-0005)


class QAEntry(BaseModel):
    turn: int
    question: str
    rationale: str  # why this question was asked (ADR-0006 — adaptive-questioning evidence)
    answer: str | None = None


class Consent(BaseModel):
    accepted: bool
    version: str
    text_hash: str
    accepted_at: str = Field(default_factory=_utcnow_iso)


class CarePathway(BaseModel):
    what_to_do: str
    what_to_tell_clinician: str
    red_flags_to_watch: list[str] = Field(default_factory=list)


class Disposition(BaseModel):
    tier: Tier
    rationale: str
    red_flags: list[str] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)
    confidence: float | None = None  # advisory only — never shortens the conversation
    safety_net: str = ""
    care_pathway: CarePathway | None = None
    fail_closed: bool = False  # True if this disposition came from the fail-closed fallback


class PatientCase(BaseModel):
    session_id: str
    created_at: str = Field(default_factory=_utcnow_iso)

    # Minimal demographics the rules/prompt consume (ADR-0007). Age band, not DOB.
    age_band: str | None = None
    sex: Sex = Sex.UNKNOWN
    pregnancy_flag: bool | None = None
    risk_flags: list[str] = Field(default_factory=list)

    presenting_complaint: str | None = None
    symptoms: list[Symptom] = Field(default_factory=list)
    question_log: list[QAEntry] = Field(default_factory=list)

    # Sticky session red-flag state — only ratchets up (ADR-0010). Once a named emergency
    # pattern is seen at any turn, it persists so a later reassuring answer cannot erase it.
    sticky_red_flags: list[str] = Field(default_factory=list)

    scope_status: ScopeStatus = ScopeStatus.OK
    turns: int = 0
    disposition: Disposition | None = None
    consent: Consent | None = None

    # Provenance (ADR-0011)
    model_version: str | None = None
    prompt_version: str | None = None

    def add_sticky_red_flags(self, flags: list[str]) -> None:
        for f in flags:
            if f and f not in self.sticky_red_flags:
                self.sticky_red_flags.append(f)


class ClinicianSummary(BaseModel):
    """Human-readable mirror of the FHIR/ABDM-shaped handoff (ADR-0013)."""

    session_id: str
    presenting_complaint: str | None
    timeline: list[str]
    associated_symptoms: list[str]
    history: list[str]
    tier_code: str
    tier_headline: str
    rationale: str
    red_flags: list[str]
    confidence: float | None
    provenance: str = "AI-generated triage — not a diagnosis. Clinician must verify."
