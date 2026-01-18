"""
Flask server for RSC Decentralized Endowment ABM

Simple REST API for running simulations.
"""

from flask import Flask, jsonify, request, render_template

from src import (
    EndowmentModel,
    TIERS,
    DESIGN_QUESTIONS,
    DEFAULT_PARAMS,
    list_tiers,
)

app = Flask(__name__)

# Global model instance
model = None


def get_model():
    """Get or create the global model instance."""
    global model
    if model is None:
        model = EndowmentModel()
    return model


def reset_model(**kwargs):
    """Reset the model with new parameters."""
    global model
    model = EndowmentModel(**kwargs)
    return model


# ============================================
# API Endpoints
# ============================================

@app.route("/")
def index():
    """Interactive dashboard."""
    return render_template("index.html")


@app.route("/api")
def api_info():
    """API info."""
    return jsonify({
        "name": "RSC Decentralized Endowment ABM",
        "description": "Simple model: Stake RSC -> Earn Credits -> Deploy -> 2% Burn",
        "endpoints": {
            "/api/init": "POST - Initialize model with parameters",
            "/api/step": "POST - Advance simulation by 1 step",
            "/api/run": "POST - Run N steps",
            "/api/state": "GET - Get current model state",
            "/api/metrics": "GET - Get computed metrics",
            "/api/stakers": "GET - List all stakers",
            "/api/proposals": "GET - List all proposals",
            "/api/history": "GET - Get time series data",
            "/api/events": "GET - Get event log",
            "/api/tiers": "GET - List staking tiers",
            "/api/design-questions": "GET - List open design questions",
        },
        "status": "ready",
    })


@app.route("/api/init", methods=["POST"])
def api_init():
    """Initialize model with parameters."""
    data = request.get_json() or {}

    # Extract parameters
    params = {
        "num_stakers": data.get("num_stakers"),
        "num_proposals": data.get("num_proposals"),
        "base_apy": data.get("base_apy"),
        "burn_rate": data.get("burn_rate"),
        "success_rate": data.get("success_rate"),
        "funding_target_min": data.get("funding_target_min"),
        "funding_target_max": data.get("funding_target_max"),
        "deploy_probability": data.get("deploy_probability"),
        "seed": data.get("seed"),
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    m = reset_model(**params)
    return jsonify({
        "status": "initialized",
        "model": m.to_dict(),
    })


@app.route("/api/step", methods=["POST"])
def api_step():
    """Advance model by one step."""
    m = get_model()
    m.step()
    return jsonify({
        "model": m.to_dict(),
        "events": m.get_events(10),
    })


@app.route("/api/run", methods=["POST"])
def api_run():
    """Run model for N steps."""
    data = request.get_json() or {}
    n = data.get("steps", 10)

    m = get_model()
    m.run_steps(n)

    return jsonify({
        "model": m.to_dict(),
        "steps_run": n,
    })


@app.route("/api/state")
def api_state():
    """Get current model state."""
    m = get_model()
    return jsonify({
        "model": m.to_dict(),
        "events": m.get_events(20),
    })


@app.route("/api/metrics")
def api_metrics():
    """Get computed metrics."""
    m = get_model()
    return jsonify(m.get_metrics())


@app.route("/api/stakers")
def api_stakers():
    """List all stakers."""
    m = get_model()
    return jsonify(m.get_stakers())


@app.route("/api/stakers/<int:staker_id>")
def api_staker_detail(staker_id: int):
    """Get single staker details."""
    m = get_model()
    for staker in m.stakers:
        if staker.unique_id == staker_id:
            return jsonify(staker.to_dict())
    return jsonify({"error": "Staker not found"}), 404


@app.route("/api/proposals")
def api_proposals():
    """List all proposals."""
    m = get_model()
    return jsonify(m.get_proposals())


@app.route("/api/proposals/<int:proposal_id>")
def api_proposal_detail(proposal_id: int):
    """Get single proposal details."""
    m = get_model()
    for proposal in m.proposals:
        if proposal.unique_id == proposal_id:
            return jsonify(proposal.to_dict())
    return jsonify({"error": "Proposal not found"}), 404


@app.route("/api/history")
def api_history():
    """Get time series data."""
    m = get_model()
    return jsonify(m.get_history())


@app.route("/api/events")
def api_events():
    """Get event log."""
    m = get_model()
    limit = request.args.get("limit", 50, type=int)
    return jsonify(m.get_events(limit))


@app.route("/api/tiers")
def api_tiers():
    """List staking tiers."""
    return jsonify(list_tiers())


@app.route("/api/design-questions")
def api_design_questions():
    """List open design questions for ResearchHub discussion."""
    return jsonify(DESIGN_QUESTIONS)


@app.route("/api/defaults")
def api_defaults():
    """Get default parameter values."""
    return jsonify(DEFAULT_PARAMS)


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # Initialize model on startup
    get_model()

    print("=" * 50)
    print("RSC Decentralized Endowment ABM Server")
    print("=" * 50)
    print("Model: Stake -> Credits -> Deploy -> 2% Burn")
    print()
    print("Endpoints:")
    print("  GET  /             - API info")
    print("  POST /api/init     - Initialize model")
    print("  POST /api/step     - Advance 1 step")
    print("  POST /api/run      - Run N steps")
    print("  GET  /api/state    - Current state")
    print("  GET  /api/metrics  - Computed metrics")
    print("  GET  /api/stakers  - List stakers")
    print("  GET  /api/proposals - List proposals")
    print()
    print("Open http://localhost:5000 in your browser")
    print("=" * 50)

    app.run(debug=True, port=5000)
