"""Deterministic, offline mock LLM provider.

It lets the whole triage flow run end-to-end with zero secrets and gives the tests a
reproducible target. For feature #2 (adaptive questioning) it plays the clarifying-question
role: it extracts the symptoms it can recognise, then asks the single most informative
*missing* detail — severity/onset → duration/trajectory → associated symptoms — before
signalling it has gathered enough to hand off to urgency assessment.

This is a heuristic stand-in, NOT clinical reasoning. The small red-flag list below is only
a safety stop so the loop does not keep asking through an obvious emergency; the full
red-flag corpus and deterministic override are feature #6 (Safety Guardrails).
"""

from __future__ import annotations

# Minimal canonical red-flag patterns (feature #6 owns the full set). A flag fires when
# every keyword group has at least one match in the (negation-aware) user text.
_RED_FLAG_RULES: list[tuple[str, list[list[str]]]] = [
    ("cardiac_chest_pain", [["chest"], ["arm", "jaw", "shoulder", "sweat", "clammy", "short of breath", "breathless", "radiat"]]),
    ("thunderclap_headache", [["worst headache", "thunderclap", "worst ever headache", "headache of my life", "sudden severe headache"]]),
    ("stroke_signs", [["face droop", "drooping", "slurred", "slurring", "weakness on one side", "facial weakness", "arm went weak"]]),
]

_SYMPTOM_KEYWORDS: dict[str, str] = {
    "chest pain": "chest_pain",
    "headache": "headache",
    "fever": "fever",
    "abdominal pain": "abdominal_pain",
    "stomach pain": "abdominal_pain",
    "belly pain": "abdominal_pain",
    "cough": "cough",
    "back pain": "back_pain",
    "backache": "back_pain",
    "sore throat": "sore_throat",
    "vomiting": "vomiting",
    "nausea": "nausea",
    "diarrhoea": "diarrhoea",
    "diarrhea": "diarrhoea",
    "rash": "rash",
    "dizzy": "dizziness",
    "dizziness": "dizziness",
    "breathless": "breathlessness",
    "shortness of breath": "breathlessness",
}

_SEVERITY_WORDS = {
    "severe": "severe",
    "worst": "severe",
    "unbearable": "severe",
    "excruciating": "severe",
    "10/10": "severe",
    "moderate": "moderate",
    "mild": "mild",
    "slight": "mild",
    "a bit": "mild",
}

_DURATION_CUES = ("hour", "day", "week", "month", "minute", "since", "for ", "yesterday", "today", "ago")

# Lightweight negation handling so "I do NOT have chest pain" doesn't fire a red flag.
_NEG_PREFIXES = (
    "no ", "not ", "n't ", "without ", "denies ", "deny ", "don't have ", "dont have ",
    "haven't had ", "havent had ", "negative for ",
)


def _all_user_text(transcript: list[dict]) -> str:
    return " ".join(m.get("content", "") for m in transcript if m.get("role") == "user").lower()


def _present(text: str, kw: str) -> bool:
    """True if kw appears NOT immediately preceded by a negation cue."""
    start = 0
    while True:
        idx = text.find(kw, start)
        if idx == -1:
            return False
        if not any(neg in text[max(0, idx - 16):idx] for neg in _NEG_PREFIXES):
            return True
        start = idx + len(kw)


def _severity(text: str) -> str:
    return next((v for k, v in _SEVERITY_WORDS.items() if k in text), "unknown")


def _onset(text: str) -> str:
    if any(w in text for w in ("sudden", "suddenly", "out of nowhere", "thunderclap")):
        return "sudden"
    if any(w in text for w in ("gradual", "slowly", "over days", "for days", "few days")):
        return "gradual"
    return "unknown"


def _match_red_flags(text: str) -> list[str]:
    flags = []
    for name, groups in _RED_FLAG_RULES:
        if all(any(_present(text, kw) for kw in group) for group in groups):
            flags.append(name)
    return flags


def _extract_symptoms(text: str) -> list[dict]:
    severity, onset = _severity(text), _onset(text)
    found: dict[str, dict] = {}
    for kw, sid in _SYMPTOM_KEYWORDS.items():
        if _present(text, kw) and sid not in found:
            found[sid] = {
                "id": sid,
                "label": kw,
                "status": "present",
                "severity": severity,
                "onset": onset,
            }
    return list(found.values())


def _ask(text: str, rationale: str) -> dict:
    return {"action": "ask", "next_question": {"text": text, "rationale": rationale}}


def _decide(tier_code: str, rationale: str, red_flags: list[str]) -> dict:
    # Minimal disposition, present only to satisfy the gateway's decide-contract. Feature #2
    # does NOT surface the tier — urgency stratification is feature #3.
    return {
        "action": "decide",
        "disposition": {
            "tier_code": tier_code,
            "rationale": rationale,
            "red_flags": red_flags,
            "contributing_factors": [],
            "confidence": None,
            "safety_net": "",
        },
    }


class MockLLMProvider:
    name = "mock"

    def triage_step(self, *, system_prompt: str, transcript: list[dict], case_context: dict) -> dict:
        text = _all_user_text(transcript)
        symptoms = _extract_symptoms(text)
        active_flags = sorted(set(_match_red_flags(text)) | set(case_context.get("sticky_red_flags", [])))

        base = {
            "extracted_symptoms": symptoms,
            "detected_red_flags": active_flags,
            "scope": {"is_violation": False, "reason": None},
        }

        # Safety stop: an obvious emergency ends intake immediately (feature #6 routes it).
        if active_flags:
            base.update(_decide(
                "EMERGENCY_NOW",
                "A named emergency red-flag pattern is present: " + ", ".join(active_flags) + ".",
                active_flags,
            ))
            return base

        # Adaptive questioning: ask for the single most informative MISSING detail. As each
        # answer arrives it fills a slot, so the next turn advances to the next discriminator.
        has_severity = _severity(text) != "unknown"
        has_duration = any(cue in text for cue in _DURATION_CUES)
        has_associated = len(symptoms) >= 2

        if not has_severity:
            base.update(_ask(
                "How would you rate it — mild, moderate, or severe — and did it come on suddenly or gradually?",
                "Severity and onset are the primary discriminators between routine and urgent care.",
            ))
        elif not has_duration:
            base.update(_ask(
                "How long has this been going on, and is it getting better, worse, or staying the same?",
                "Duration and trajectory separate self-limiting problems from ones that need review.",
            ))
        elif not has_associated:
            base.update(_ask(
                "Is anything else happening alongside it — for example fever, nausea, breathlessness, or dizziness?",
                "Associated symptoms point to which body system is involved and refine the urgency.",
            ))
        else:
            base.update(_decide(
                "PHYSICIAN_ROUTINE",
                "Enough discriminating information collected to proceed to urgency assessment.",
                [],
            ))
        return base
