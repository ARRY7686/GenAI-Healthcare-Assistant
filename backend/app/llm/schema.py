"""The structured contract between the orchestrator and the LLM (ADR-0009).

The model returns exactly this shape every turn. `action` is "ask" (emit a clarifying
question) or "decide" (emit a final disposition). Anything malformed is treated as a
failure by the gateway and routed fail-closed — never parsed leniently.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

VALID_TIER_CODES = [
    "EMERGENCY_NOW",
    "CASUALTY_TODAY",
    "PHYSICIAN_URGENT",
    "PHYSICIAN_ROUTINE",
    "SELF_CARE",
]


class LLMExtractedSymptom(BaseModel):
    id: str
    label: str
    status: str = "present"  # present | absent | unknown
    severity: str = "unknown"  # mild | moderate | severe | unknown
    onset: str = "unknown"  # sudden | gradual | unknown
    duration_value: float | None = None
    duration_unit: str | None = None
    note: str | None = None


class LLMScope(BaseModel):
    is_violation: bool = False
    reason: str | None = None  # "minor" | "pregnancy" | None


class LLMNextQuestion(BaseModel):
    text: str
    rationale: str


class LLMDisposition(BaseModel):
    tier_code: str
    rationale: str
    red_flags: list[str] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)
    confidence: float | None = None
    safety_net: str = ""


class LLMTriageOutput(BaseModel):
    extracted_symptoms: list[LLMExtractedSymptom] = Field(default_factory=list)
    detected_red_flags: list[str] = Field(default_factory=list)
    scope: LLMScope = Field(default_factory=LLMScope)
    action: str  # "ask" | "decide"
    next_question: LLMNextQuestion | None = None
    disposition: LLMDisposition | None = None


# JSON schema handed to the Anthropic tool so the model is forced to emit the shape above.
TRIAGE_TOOL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "extracted_symptoms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "status": {"type": "string", "enum": ["present", "absent", "unknown"]},
                    "severity": {
                        "type": "string",
                        "enum": ["mild", "moderate", "severe", "unknown"],
                    },
                    "onset": {"type": "string", "enum": ["sudden", "gradual", "unknown"]},
                    "duration_value": {"type": ["number", "null"]},
                    "duration_unit": {"type": ["string", "null"]},
                    "note": {"type": ["string", "null"]},
                },
                "required": ["id", "label"],
            },
        },
        "detected_red_flags": {"type": "array", "items": {"type": "string"}},
        "scope": {
            "type": "object",
            "properties": {
                "is_violation": {"type": "boolean"},
                "reason": {"type": ["string", "null"], "enum": ["minor", "pregnancy", None]},
            },
            "required": ["is_violation"],
        },
        "action": {"type": "string", "enum": ["ask", "decide"]},
        "next_question": {
            "type": ["object", "null"],
            "properties": {
                "text": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": ["text", "rationale"],
        },
        "disposition": {
            "type": ["object", "null"],
            "properties": {
                "tier_code": {"type": "string", "enum": VALID_TIER_CODES},
                "rationale": {"type": "string"},
                "red_flags": {"type": "array", "items": {"type": "string"}},
                "contributing_factors": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": ["number", "null"]},
                "safety_net": {"type": "string"},
            },
            "required": ["tier_code", "rationale"],
        },
    },
    "required": ["action"],
}
