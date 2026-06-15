"""API request/response models for the triage flow."""

from __future__ import annotations

from pydantic import BaseModel


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
