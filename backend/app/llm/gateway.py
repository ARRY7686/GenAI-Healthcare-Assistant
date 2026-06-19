"""LLM gateway — provider selection, bounded retries, and strict validation.

Validation failures and provider errors raise LLMFailure; the orchestrator turns that into
a conservative stop. Malformed output is never parsed leniently into a question/decision.

Only the offline `mock` provider is wired in this build. Real providers (anthropic / openai /
gemini) are an optional follow-up — the mock runs the whole flow with zero secrets.
"""

from __future__ import annotations

from pydantic import ValidationError

from ..config import Settings
from .base import LLMFailure, LLMProvider
from .schema import VALID_TIER_CODES, LLMTriageOutput


def build_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider
    if provider == "mock":
        from .mock_provider import MockLLMProvider

        return MockLLMProvider()
    if provider == "gemini":
        from .gemini_provider import GeminiLLMProvider

        return GeminiLLMProvider(
            api_key=settings.gemini_api_key or "",
            model_id=settings.resolve_model(),
            timeout=settings.llm_timeout_seconds,
        )
    # anthropic / openai aren't bundled in this build — add the provider module to wire them.
    raise NotImplementedError(
        f"LLM provider {provider!r} is not wired in this build. "
        "Set TRIAGE_LLM_PROVIDER=mock (default) or gemini."
    )


class LLMGateway:
    def __init__(self, provider: LLMProvider, max_retries: int = 2) -> None:
        self._provider = provider
        self._max_retries = max_retries

    @property
    def provider_name(self) -> str:
        return getattr(self._provider, "name", "unknown")

    def triage_step(
        self, *, system_prompt: str, transcript: list[dict], case_context: dict
    ) -> LLMTriageOutput:
        last: Exception | None = None
        for _ in range(self._max_retries + 1):
            try:
                raw = self._provider.triage_step(
                    system_prompt=system_prompt,
                    transcript=transcript,
                    case_context=case_context,
                )
                out = LLMTriageOutput.model_validate(raw)
                self._check_consistency(out)
                return out
            except LLMFailure as exc:
                last = exc
            except ValidationError as exc:
                last = LLMFailure(f"invalid LLM output: {exc}")
            except Exception as exc:  # noqa: BLE001 — any failure is fail-closed
                last = LLMFailure(f"unexpected LLM error: {exc}")
        raise last or LLMFailure("LLM failed with no diagnostic")

    @staticmethod
    def _check_consistency(out: LLMTriageOutput) -> None:
        if out.action not in ("ask", "decide"):
            raise LLMFailure(f"invalid action: {out.action!r}")
        if out.action == "ask" and out.next_question is None:
            raise LLMFailure("action=ask but no next_question")
        if out.action == "decide":
            if out.disposition is None:
                raise LLMFailure("action=decide but no disposition")
            if out.disposition.tier_code not in VALID_TIER_CODES:
                raise LLMFailure(f"invalid tier_code: {out.disposition.tier_code!r}")
