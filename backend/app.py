from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173"))


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Healthcare Triage API is running"})


# ---------------------------------------------------------------------------
# Triage Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/triage/start", methods=["POST"])
def start_triage():
    """
    Initialise a new triage session.
    Expected request body: {}
    Returns a session_id and the first question.
    TODO: Implement session initialisation and first-question logic.
    """
    return jsonify({
        "session_id": None,
        "question": "What is your main symptom or concern today?",
        "progress": 0,
    }), 501


@app.route("/api/triage/respond", methods=["POST"])
def respond_to_triage():
    """
    Accept a patient response and return the next adaptive question.
    Expected request body: { "session_id": str, "message": str }
    TODO: Implement adaptive clinical questioning logic.
    """
    data = request.get_json(silent=True) or {}
    return jsonify({
        "session_id": data.get("session_id"),
        "question": None,          # next clarifying question
        "is_complete": False,      # True when enough info has been collected
        "progress": None,          # 0–100 progress indicator
    }), 501


@app.route("/api/triage/assess", methods=["POST"])
def assess_urgency():
    """
    Produce a urgency-tier classification from the collected symptom profile.
    Expected request body: { "session_id": str }
    Urgency tiers: emergency | ae_today | gp_urgent | gp_routine | self_care
    TODO: Implement urgency stratification and safety-guardrail logic.
    """
    data = request.get_json(silent=True) or {}
    return jsonify({
        "session_id": data.get("session_id"),
        "urgency_tier": None,      # one of the five tiers above
        "care_pathway": None,      # short description of recommended action
        "red_flags": [],           # list of red-flag symptoms to watch for
        "guidance": None,          # what to do / what to tell the provider
    }), 501


# ---------------------------------------------------------------------------
# Patient Summary Endpoint
# ---------------------------------------------------------------------------

@app.route("/api/summary", methods=["POST"])
def generate_summary():
    """
    Generate a structured patient summary for the healthcare provider.
    Expected request body: { "session_id": str }
    TODO: Implement summary generation from collected session data.
    """
    data = request.get_json(silent=True) or {}
    return jsonify({
        "session_id": data.get("session_id"),
        "presenting_complaint": None,
        "symptom_timeline": None,
        "associated_symptoms": [],
        "history": None,
        "urgency_assessment": None,
        "care_pathway": None,
        "red_flags": [],
    }), 501


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
    )
