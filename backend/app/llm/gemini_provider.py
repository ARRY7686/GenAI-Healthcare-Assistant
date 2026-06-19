"""Gemini provider — Google Gemini via google-generativeai (ADR-0003, ADR-0009).

Uses JSON output mode at temperature 0; the gateway validates the parsed object against the
triage schema and retries / fails closed on a bad shape. Lazy-imports the SDK so the app runs
in mock mode without it installed.
"""

from __future__ import annotations

import json

from .base import LLMFailure

_JSON_INSTRUCTION = (
    "\n\nReturn ONLY a single JSON object with these keys: extracted_symptoms (array), "
    "detected_red_flags (array of strings), scope ({is_violation, reason}), action "
    '("ask" or "decide"), next_question ({text, rationale} or null), and disposition '
    "({tier_code, rationale, red_flags, contributing_factors, confidence, safety_net} or null). "
    "tier_code is one of EMERGENCY_NOW, CASUALTY_TODAY, PHYSICIAN_URGENT, PHYSICIAN_ROUTINE, SELF_CARE."
)


class GeminiLLMProvider:
    name = "gemini"

    def __init__(self, *, api_key: str, model_id: str, timeout: float) -> None:
        if not api_key:
            raise LLMFailure("TRIAGE_GEMINI_API_KEY is not set")
        try:
            import google.generativeai as genai  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise LLMFailure(
                "google-generativeai not installed (pip install google-generativeai)"
            ) from exc
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_id = model_id
        self._timeout = timeout

    def triage_step(self, *, system_prompt: str, transcript: list[dict], case_context: dict) -> dict:
        system = (
            system_prompt + _JSON_INSTRUCTION + "\n\nCURRENT_CASE_STATE (JSON):\n" + json.dumps(case_context)
        )
        convo = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in transcript
            if m.get("role") in ("user", "assistant") and m.get("content")
        ) or "(patient has not said anything yet)"

        model = self._genai.GenerativeModel(
            self._model_id,
            system_instruction=system,
            generation_config={"temperature": 0, "response_mime_type": "application/json"},
        )
        try:
            resp = model.generate_content(convo, request_options={"timeout": self._timeout})
        except Exception as exc:
            raise LLMFailure(f"gemini call failed: {exc}") from exc

        text = (getattr(resp, "text", "") or "").strip()
        if not text:
            raise LLMFailure("gemini returned an empty response")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMFailure(f"gemini returned non-JSON: {exc}") from exc
