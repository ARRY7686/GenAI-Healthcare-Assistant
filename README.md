# TriageAI — AI-Powered Healthcare Triage Assistant


## Stack

- **Backend** — Flask (Python)
- **Frontend** — React + Vite
- **UI** — shadcn/ui + Tailwind CSS + lucide-react

---

## Project Structure

```
Health Assistant/
├── backend/
│   ├── app.py            # Flask app — all API routes stubbed (501)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── lib/utils.js       # cn() helper
    │   ├── components/
    │   │   ├── ui/            # shadcn/ui primitives (Button, Card, Badge…)
    │   │   ├── Navbar.jsx
    │   │   ├── ChatBubble.jsx
    │   │   └── UrgencyBadge.jsx
    │   ├── pages/
    │   │   ├── Home.jsx       # Landing page
    │   │   ├── Triage.jsx     # Chat interface (UI only)
    │   │   └── Summary.jsx    # Patient report (skeleton state)
    │   └── App.jsx
    └── package.json
```

---

## Running Locally

### Backend
```bash
cd backend
source .venv/bin/activate
python app.py
# → http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## API Routes (All Stubbed — Return 501)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/triage/start` | Start triage session |
| POST | `/api/triage/respond` | Adaptive follow-up question |
| POST | `/api/triage/assess` | Urgency tier classification |
| POST | `/api/summary` | Generate patient summary |

---

## What's Left to Implement

- [ ] Session management in Flask
- [ ] Symptom intake & adaptive questioning logic
- [ ] Urgency stratification (5 tiers) + safety guardrails
- [ ] Care pathway guidance per tier
- [ ] Patient summary generation
- [ ] Wire frontend `axios` calls to the API
