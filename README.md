# TriageAI — AI-Powered Healthcare Triage Assistant

A conversational triage assistant that directs patients to the right level of care — *call
emergency now · casualty/ED today · physician urgent · physician routine · self-care* — via
symptom intake, adaptive clarifying questions, urgency stratification with safety overrides,
and a structured clinician handoff summary. Built for **India** (emergency **112** /
ambulance **108**).

> **Status:** group-project engineering MVP on **synthetic data — no real patients.** It runs
> with zero secrets via a deterministic offline **mock** LLM provider (real providers are a
> follow-up). This is triage signposting, **not a diagnosis**.

---

## Stack

> **Architecture change:** the backend was migrated from **Flask → FastAPI** (async, typed
> request/response models via Pydantic, and auto-generated OpenAPI docs at `/docs`). The
> domain layer is a canonical Pydantic `PatientCase`, and the LLM is accessed through a
> pluggable gateway so the app runs offline by default.

- **Backend** — FastAPI + Pydantic (Python 3.11+; CI/dev on 3.14)
- **Frontend** — React + Vite
- **LLM** — pluggable gateway; deterministic offline **mock** by default (anthropic / openai /
  gemini are an optional follow-up)

---

## Features & ownership (group project)

Each of the six core features is a teammate's contribution merged via its own PR.

| # | Feature | Status | Where |
|---|---------|--------|-------|
| 1 | **Symptom Intake** — structured `PatientCase` + LLM extraction schema | ✅ merged | `app/domain/`, `app/llm/schema.py` |
| 2 | **Adaptive Questioning** — clarifying-question loop with clinical rationale | ✅ this PR | `app/triage/orchestrator.py`, `POST /api/triage/respond` |
| 3 | **Urgency Stratification** — classify into the 5 tiers | 🚧 stub (501) | `POST /api/triage/assess` |
| 4 | **Care Pathway Guidance** — per-tier actionable guidance | 🚧 stub | — |
| 5 | **Patient Summary** — structured clinician handoff | 🚧 stub (501) | `POST /api/summary` |
| 6 | **Safety Guardrails** — deterministic red-flag override | 🚧 stub | minimal safety stop in the mock only |

---

## Project structure

```
GenAI-Healthcare-Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory (uvicorn app.main:app)
│   │   ├── config.py            # TRIAGE_* settings (pydantic-settings)
│   │   ├── domain/              # canonical PatientCase, Symptom, tiers  (feature #1)
│   │   ├── llm/                 # provider protocol, gateway, offline mock, I/O schema
│   │   ├── triage/
│   │   │   └── orchestrator.py  # the adaptive-questioning engine        (feature #2)
│   │   └── api/                 # routes, request/response schemas, session store
│   ├── tests/                   # pytest — adaptive-questioning suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/                    # React + Vite chat UI
```

---

## Running locally

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000   (interactive API docs at http://localhost:8000/docs)
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Tests
```bash
cd backend && source .venv/bin/activate
pytest          # adaptive-questioning suite
```

---

## API routes

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET  | `/api/health` | Health check (provider + model) | ✅ |
| POST | `/api/triage/start` | Start a session; returns `session_id` + opening question | ✅ |
| POST | `/api/triage/respond` | **Adaptive clarifying question** for the symptom profile | ✅ feature #2 |
| POST | `/api/triage/assess` | Urgency-tier classification | 🚧 501 (feature #3) |
| POST | `/api/summary` | Structured patient summary | 🚧 501 (feature #5) |

---

## Feature #2 — Adaptive Questioning

`POST /api/triage/respond` runs one turn of the clinical-decision loop: it ingests the
patient's message, updates the canonical `PatientCase`, and asks the **single most
informative missing detail** — severity/onset → duration/trajectory → associated symptoms —
each with a short clinical **rationale**, until it has enough to hand off to urgency
assessment.

```jsonc
// POST /api/triage/respond  { "session_id": "...", "message": "I have a headache" }
{
  "question": "How would you rate it — mild, moderate, or severe — and did it come on suddenly or gradually?",
  "rationale": "Severity and onset are the primary discriminators between routine and urgent care.",
  "is_complete": false,
  "progress": 17
}
```

When enough information is collected (or an obvious emergency pattern appears, which stops
the loop), the response returns `is_complete: true` and `progress: 100`. Producing the
urgency tier from the collected profile is feature #3 (`/api/triage/assess`).

---

## ⚠️ Safety & scope

Decision-support **triage signposting, not a diagnosis**, and not a substitute for a
clinician. Runs on **synthetic data only** and is **not** cleared for real-patient use. In a
real emergency, call **112**.
