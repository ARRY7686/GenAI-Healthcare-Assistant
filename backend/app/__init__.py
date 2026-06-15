"""AI Healthcare Triage Assistant — FastAPI backend.

Group-project feature ownership (each feature is a separate teammate's PR):
- #1 Symptom Intake .......... domain models + LLM schema           (merged: app/domain, app/llm/schema.py)
- #2 Adaptive Questioning .... THIS PR: the triage orchestrator loop + POST /api/triage/respond
- #3 Urgency Stratification .. POST /api/triage/assess              (stub — 501)
- #4 Care Pathway Guidance ... per-tier guidance content           (stub)
- #5 Patient Summary ......... POST /api/summary                    (stub — 501)
- #6 Safety Guardrails ....... deterministic red-flag override      (stub — minimal safety stop only)
"""
