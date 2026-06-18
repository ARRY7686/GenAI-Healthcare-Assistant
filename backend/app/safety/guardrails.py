"""Deterministic safety guardrails (Feature #6).

Hard-coded safety logic: certain symptom combinations ALWAYS route to EMERGENCY_NOW regardless
of any other factor (severity, model output, or a later reassuring answer). This is independent
of the LLM/mock — it scans the structured PatientCase's own evidence (presenting complaint,
symptom labels and notes, and the patient's answers) so an emergency is caught even if the model
misses it.

A pattern fires when EVERY keyword group has at least one (negation-aware) match in the text.
Matching mirrors the named red flags in red_flags.py.
"""

from __future__ import annotations

from ..domain import PatientCase

# name -> list of keyword groups. Each group is OR (any synonym); groups are AND-ed together.
_EMERGENCY_PATTERNS: list[tuple[str, list[list[str]]]] = [
    # Chest pain + radiation/autonomic features → possible acute coronary syndrome.
    (
        "cardiac_chest_pain",
        [
            ["chest pain", "chest pressure", "chest tightness", "chest"],
            ["arm", "jaw", "shoulder", "sweat", "clammy", "short of breath", "breathless", "radiat"],
        ],
    ),
    # Sudden, severe "worst ever" headache → possible subarachnoid haemorrhage.
    (
        "thunderclap_headache",
        [
            [
                "worst headache",
                "thunderclap",
                "worst ever headache",
                "headache of my life",
                "sudden severe headache",
                "sudden severe head",
            ],
        ],
    ),
    # Stroke (FAST/BE-FAST) signs.
    (
        "stroke_signs",
        [
            [
                "face droop",
                "facial droop",
                "drooping",
                "slurred",
                "slurring",
                "weakness on one side",
                "one-sided weakness",
                "one side weak",
                "facial weakness",
                "arm went weak",
                "cannot speak",
                "can't speak",
            ],
        ],
    ),
    # Severe breathing difficulty.
    (
        "severe_breathing_difficulty",
        [
            ["cannot breathe", "can't breathe", "gasping", "choking", "blue lips", "struggling to breathe"],
        ],
    ),
    # Uncontrolled bleeding.
    (
        "uncontrolled_bleeding",
        [
            ["bleeding heavily", "heavy bleeding", "won't stop bleeding", "wont stop bleeding", "uncontrolled bleeding"],
        ],
    ),
]

# Negation cues so "no chest pain" / "denies chest pain" does not fire a red flag.
_NEG_PREFIXES = (
    "no ", "not ", "n't ", "without ", "denies ", "deny ", "don't have ", "dont have ",
    "haven't had ", "havent had ", "negative for ",
)


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


def _case_text(case: PatientCase) -> str:
    """All free-text evidence on the case, lower-cased, for deterministic scanning."""
    parts: list[str] = [case.presenting_complaint or ""]
    for s in case.symptoms:
        parts.append(s.label)
        if s.note:
            parts.append(s.note)
    for qa in case.question_log:
        if qa.answer:
            parts.append(qa.answer)
    return " ".join(parts).lower()


def detect_emergency_patterns(case: PatientCase) -> list[str]:
    """Return the names of any hard-coded emergency patterns present in the case evidence."""
    text = _case_text(case)
    return [
        name
        for name, groups in _EMERGENCY_PATTERNS
        if all(any(_present(text, kw) for kw in group) for group in groups)
    ]
