"""HTTP routes for the triage flow.

Feature #2 (Adaptive Questioning) owns POST /api/triage/respond — the clarifying-question
loop. The urgency, summary, and safety endpoints are stubs owned by other teammates.

Engine and store are lazily constructed (no import-time side effects). The mutating
/respond endpoint goes through `store.session(sid)` — a per-session locked load->mutate
cycle — so concurrent requests to one session can't interleave.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..triage import build_engine
from .schemas import RespondRequest, RespondResponse, SessionRef, StartResponse
from .store import build_store

router = APIRouter(prefix="/api")


@lru_cache
def _engine():
    return build_engine(get_settings())


@lru_cache
def _store():
    return build_store(get_settings())


@router.get("/health")
def health() -> dict:
    s = get_settings()
    # Only advertise the model id when a real provider is actually in use.
    return {
        "status": "ok",
        "provider": s.llm_provider,
        "model": None if s.llm_provider == "mock" else s.resolve_model(),
    }


@router.post("/triage/start", response_model=StartResponse)
def start_triage() -> StartResponse:
    """Initialise a new triage session and return the opening question."""
    session = _store().create()
    return StartResponse(
        session_id=session.case.session_id,
        question=_engine().opening_question(),
        progress=0,
    )


@router.post("/triage/respond", response_model=RespondResponse)
def respond_to_triage(body: RespondRequest) -> RespondResponse:
    """Feature #2 — accept a patient response and return the next adaptive question.

    Keeps asking the single most informative clarifying question until enough information has
    been collected, then returns `is_complete=True` (hand off to urgency assessment).
    """
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="empty message")
    if len(message) > 4000:
        raise HTTPException(status_code=413, detail="message too long")
    with _store().session(body.session_id) as session:
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")
        result = _engine().ask_step(session.case, session.transcript, message)
    return RespondResponse(
        session_id=body.session_id,
        question=result.question,
        rationale=result.rationale,
        is_complete=result.is_complete,
        progress=result.progress,
        fail_closed=result.fail_closed,
    )


@router.post("/triage/assess")
def assess_urgency(body: SessionRef) -> dict:
    """Feature #3 — Urgency Stratification. Not implemented in the feature-2 PR."""
    raise HTTPException(
        status_code=501,
        detail="Urgency stratification (feature #3) is not implemented yet.",
    )


@router.post("/summary")
def generate_summary(body: SessionRef) -> dict:
    """Feature #5 — Patient Summary. Not implemented in the feature-2 PR."""
    raise HTTPException(
        status_code=501,
        detail="Patient summary (feature #5) is not implemented yet.",
    )
