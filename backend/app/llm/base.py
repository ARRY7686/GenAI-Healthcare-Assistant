"""LLM provider protocol and the failure type that triggers fail-closed behaviour."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class LLMFailure(Exception):
    """Raised on timeout, transport error, or malformed/unparseable model output.

    The orchestrator catches this and stops intake conservatively rather than
    dead-ending the conversation.
    """


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def triage_step(
        self,
        *,
        system_prompt: str,
        transcript: list[dict],
        case_context: dict,
    ) -> dict:
        """Return a raw dict matching LLMTriageOutput. May raise LLMFailure."""
        ...
