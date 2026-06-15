"""API request/response models for the triage flow."""

from __future__ import annotations

from pydantic import BaseModel


class StartRequest(BaseModel):
    """Optional consent-gate demographics captured before the chat begins."""

    age_band: str | None = None  # e.g. "under_16", "16-39", "40-64", "65+"
    sex: str | None = None  # male | female | other | unknown
    pregnancy_flag: bool | None = None


class StartResponse(BaseModel):
    session_id: str
    question: str  # the opening question
    progress: int = 0


class RespondRequest(BaseModel):
    session_id: str
    message: str


class RespondResponse(BaseModel):
    """One adaptive-questioning turn (feature #2)."""

    session_id: str
    question: str | None = None  # next clarifying question (None once intake is complete)
    rationale: str | None = None  # why that question was asked
    is_complete: bool = False  # True → hand off to urgency assessment (feature #3)
    progress: int = 0  # 0–100
    fail_closed: bool = False


class SessionRef(BaseModel):
    session_id: str
