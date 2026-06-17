"""Care-pathway content per tier (India-localized).

PLACEHOLDER CONTENT — pending RMP authoring & sign-off (ADR-0005, Track 2). The structure
is production-shaped (what to do / what to tell the clinician / red flags to watch) but the
wording must be reviewed and cited by the accountable registered medical practitioner before
any real-patient use.
"""

from __future__ import annotations

from ..domain import CarePathway, Tier

_PATHWAYS: dict[Tier, CarePathway] = {
    Tier.EMERGENCY_NOW: CarePathway(
        what_to_do=(
            "Call 112 now (108 for an ambulance). Do not drive yourself. Unlock your door, "
            "stay still, and keep someone with you if possible."
        ),
        what_to_tell_clinician=(
            "Your main symptom, when it started, and any chest pain, weakness, breathing "
            "difficulty, or severe bleeding."
        ),
        red_flags_to_watch=[
            "Loss of consciousness",
            "Worsening breathing",
            "Weakness or numbness on one side",
        ],
    ),
    Tier.CASUALTY_TODAY: CarePathway(
        what_to_do="Go to the nearest casualty / emergency department today. Take a list of your symptoms and medicines.",
        what_to_tell_clinician="When the symptom started, how severe it is, and anything that makes it worse.",
        red_flags_to_watch=[
            "Symptoms suddenly worsen",
            "New chest pain, breathlessness, or fainting",
        ],
    ),
    Tier.PHYSICIAN_URGENT: CarePathway(
        what_to_do="See a physician urgently — today or tomorrow — at a clinic, urgent care, or by teleconsultation.",
        what_to_tell_clinician="Your symptoms, their duration, and any relevant medical history or medicines.",
        red_flags_to_watch=[
            "Fever that keeps rising",
            "Severe or rapidly worsening pain",
            "Any of the emergency signs below",
        ],
    ),
    Tier.PHYSICIAN_ROUTINE: CarePathway(
        what_to_do="Book a routine appointment with a physician in the next few days.",
        what_to_tell_clinician="How long the symptom has lasted and whether it is improving or not.",
        red_flags_to_watch=[
            "Symptoms persist beyond a week or worsen",
            "New emergency signs appear",
        ],
    ),
    Tier.SELF_CARE: CarePathway(
        what_to_do=(
            "Rest, stay hydrated, and monitor your symptoms at home. Over-the-counter relief may "
            "help — check with a pharmacist."
        ),
        what_to_tell_clinician="If you do see a clinician, mention what you tried and how it responded.",
        red_flags_to_watch=[
            "Symptoms get worse instead of better",
            "Chest pain, breathing difficulty, weakness on one side, or the worst headache of your life",
            "High fever with a stiff neck or rash",
        ],
    ),
}


# Crisis pathway — used when a self-harm / suicidal-ideation red flag is present, so the patient
# never receives the cardiac emergency instructions. India helplines (RMP to confirm/keep current).
_CRISIS_PATHWAY = CarePathway(
    what_to_do=(
        "You deserve support right now, and you don't have to handle this alone. Please call 112, "
        "or a mental-health helpline — Tele-MANAS 14416 or KIRAN 1800-599-0019 (free, 24x7) — and "
        "reach out to someone you trust to be with you. If you feel you might act on these thoughts, "
        "call 112 now."
    ),
    what_to_tell_clinician=(
        "That you are having thoughts of harming yourself, how strong they are, and whether you feel "
        "safe right now."
    ),
    red_flags_to_watch=[
        "Thoughts of acting on harming yourself",
        "Having a specific plan or the means",
        "Feeling unsafe being on your own",
    ],
)


def care_pathway_for(tier: Tier, red_flags: list[str] | None = None) -> CarePathway:
    if red_flags and "self_harm_crisis" in red_flags:
        return _CRISIS_PATHWAY.model_copy(deep=True)
    return _PATHWAYS[tier].model_copy(deep=True)
