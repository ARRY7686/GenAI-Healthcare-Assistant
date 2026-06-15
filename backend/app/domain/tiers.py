"""The five urgency tiers as a total order.

IMPORTANT: lower numeric value = MORE urgent. "Under-triage" (the dangerous direction)
means the system assigned a tier with a HIGHER number than ground truth.

Patient-facing text is India-localized (ADR-0002): emergency 112 / ambulance 108,
"casualty / emergency department" (not "A&E"), "physician / clinic" (not "GP").
"""

from __future__ import annotations

from enum import IntEnum


class Tier(IntEnum):
    EMERGENCY_NOW = 1
    CASUALTY_TODAY = 2
    PHYSICIAN_URGENT = 3
    PHYSICIAN_ROUTINE = 4
    SELF_CARE = 5


# Patient-facing copy per tier (India). `headline` is shown big on the disposition card.
TIER_TEXT: dict[Tier, dict[str, str]] = {
    Tier.EMERGENCY_NOW: {
        "code": "EMERGENCY_NOW",
        "headline": "Call 112 now",
        "action": (
            "This may be a medical emergency. Call 112 immediately "
            "(or 108 for an ambulance). If you can, have someone stay with you."
        ),
    },
    Tier.CASUALTY_TODAY: {
        "code": "CASUALTY_TODAY",
        "headline": "Go to casualty / emergency department today",
        "action": (
            "Please go to the nearest casualty / emergency department today. "
            "Do not wait for a routine appointment."
        ),
    },
    Tier.PHYSICIAN_URGENT: {
        "code": "PHYSICIAN_URGENT",
        "headline": "See a physician urgently",
        "action": (
            "Please see a physician urgently — today or tomorrow. "
            "Use a clinic, urgent care, or teleconsultation."
        ),
    },
    Tier.PHYSICIAN_ROUTINE: {
        "code": "PHYSICIAN_ROUTINE",
        "headline": "Book a routine physician visit",
        "action": "Please book a routine appointment with a physician in the next few days.",
    },
    Tier.SELF_CARE: {
        "code": "SELF_CARE",
        "headline": "Self-care with monitoring",
        "action": (
            "This can usually be managed at home with self-care. "
            "Monitor your symptoms and seek care if anything changes."
        ),
    },
}


def most_urgent(a: Tier, b: Tier) -> Tier:
    """Return the more urgent of two tiers (lower numeric value)."""
    return a if a <= b else b


# Fail-closed conservative referral floor (ADR-0009). On any model/parse failure the
# system routes here (or higher, if a red flag was already detected) — never to self-care.
CONSERVATIVE_FALLBACK_TIER = Tier.PHYSICIAN_URGENT
