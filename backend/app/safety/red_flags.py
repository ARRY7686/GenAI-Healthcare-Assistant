"""Named emergency red-flag patterns (Feature #6 — Safety Guardrails).

These are the canonical emergency patterns the deterministic guardrail (guardrails.py) matches
against and the basis for any prompt-embedded safety text. Each ALWAYS routes to EMERGENCY_NOW.

`source` citations are PLACEHOLDERS pending RMP sign-off (ADR-0005).
"""

from __future__ import annotations

NAMED_RED_FLAGS: list[dict] = [
    {
        "name": "cardiac_chest_pain",
        "description": "Chest pain/pressure with radiation to arm or jaw, sweating, or breathlessness — possible acute coronary syndrome.",
        "disposition": "EMERGENCY_NOW",
        "source": "RMP to cite (e.g. NICE CG95 / international ACS guidance)",
    },
    {
        "name": "thunderclap_headache",
        "description": "Sudden, severe 'worst ever' headache reaching peak intensity within seconds to minutes.",
        "disposition": "EMERGENCY_NOW",
        "source": "RMP to cite (e.g. NICE / SAH guidance)",
    },
    {
        "name": "stroke_signs",
        "description": "Face droop, arm weakness, or slurred/garbled speech — possible stroke (FAST/BE-FAST).",
        "disposition": "EMERGENCY_NOW",
        "source": "RMP to cite (FAST / stroke guidance)",
    },
    {
        "name": "severe_breathing_difficulty",
        "description": "Severe difficulty breathing, gasping, choking, or blue lips.",
        "disposition": "EMERGENCY_NOW",
        "source": "RMP to cite",
    },
    {
        "name": "uncontrolled_bleeding",
        "description": "Heavy bleeding that will not stop with pressure.",
        "disposition": "EMERGENCY_NOW",
        "source": "RMP to cite",
    },
]

# Quick lookup: red-flag name -> human description (used in summaries / UI).
RED_FLAG_DESCRIPTIONS: dict[str, str] = {rf["name"]: rf["description"] for rf in NAMED_RED_FLAGS}


def red_flag_summary() -> str:
    """Bullet list for embedding in a system prompt."""
    return "\n".join(
        f"- {rf['name']}: {rf['description']} -> {rf['disposition']}" for rf in NAMED_RED_FLAGS
    )
