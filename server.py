"""
Flask server for RSC Decentralized Endowment ABM

Real mechanism: RSC in RH account auto-earns yield (passive, no staking action).
Primary question: What participation_rate does the market equilibrate to?
"""

import os

from flask import Flask, jsonify, request, render_template

from src import (
    EndowmentModel,
    TIME_WEIGHT_MULTIPLIERS,
    EMISSION_PARAMS,
    DEFAULT_PARAMS,
    ARCHETYPES,
    DEFAULT_ARCHETYPE_MIX,
    list_multipliers,
    list_archetypes,
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
        "description": "RSC in RH account auto-earns yield. Yield = (your RSC / total RSC) x emissions x multiplier.",
        "primary_question": "What participation rate does the market equilibrate to?",
        "endpoints": {
            "/api/init": "POST - Initialize model with parameters",
            "/api/step": "POST - Advance simulation by 1 step (1 week)",
            "/api/run": "POST - Run N steps",
            "/api/state": "GET - Get current model state",
            "/api/metrics": "GET - Get computed metrics",
            "/api/holders": "GET - List all holders",
            "/api/proposals": "GET - List all proposals",
            "/api/history": "GET - Get time series data",
            "/api/events": "GET - Get event log",
            "/api/multipliers": "GET - List time-weight multipliers",
            "/api/archetypes": "GET - List behavioral archetypes",
            "/api/participation": "GET - Participation rate data + reference scenarios",
        },
        "status": "ready",
    })


@app.route("/api/init", methods=["POST"])
def api_init():
    """Initialize model with parameters."""
    data = request.get_json() or {}

    params = {
        "num_holders": data.get("num_holders") or data.get("num_stakers"),
        "num_proposals": data.get("num_proposals"),
        "burn_rate": data.get("burn_rate"),
        "success_rate": data.get("success_rate"),
        "funding_target_min": data.get("funding_target_min"),
        "funding_target_max": data.get("funding_target_max"),
        "deploy_probability": data.get("deploy_probability"),
        "archetype_mix": data.get("archetype_mix"),
        "yield_threshold_mean": data.get("yield_threshold_mean"),
        "initial_participation_rate": data.get("initial_participation_rate"),
        "seed": data.get("seed"),
        # Design Lab params
        "credit_expiry_enabled": data.get("credit_expiry_enabled"),
        "credit_expiry_weeks": data.get("credit_expiry_weeks"),
        "failure_mode": data.get("failure_mode"),
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
    """Advance model by one step (1 week)."""
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


@app.route("/api/holders")
def api_holders():
    """List all holders."""
    m = get_model()
    return jsonify(m.get_holders())


@app.route("/api/stakers")
def api_stakers():
    """Legacy alias for /api/holders."""
    m = get_model()
    return jsonify(m.get_holders())


@app.route("/api/holders/<int:holder_id>")
def api_holder_detail(holder_id: int):
    """Get single holder details."""
    m = get_model()
    for holder in m.holders:
        if holder.unique_id == holder_id:
            return jsonify(holder.to_dict())
    return jsonify({"error": "Holder not found"}), 404


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


@app.route("/api/multipliers")
def api_multipliers():
    """List time-weight multipliers."""
    return jsonify(list_multipliers())


@app.route("/api/tiers")
def api_tiers():
    """Legacy alias for /api/multipliers."""
    return jsonify(list_multipliers())


@app.route("/api/archetypes")
def api_archetypes():
    """List behavioral archetypes and current distribution."""
    m = get_model()
    return jsonify({
        "archetypes": list_archetypes(),
        "default_mix": DEFAULT_ARCHETYPE_MIX,
        "current_distribution": m.get_archetype_distribution(),
        "current_metrics": m.get_archetype_metrics(),
    })


@app.route("/api/participation")
def api_participation():
    """Participation rate data with reference scenarios from CSV model."""
    m = get_model()
    return jsonify(m.get_participation_data())


@app.route("/api/defaults")
def api_defaults():
    """Get default parameter values."""
    return jsonify({
        **DEFAULT_PARAMS,
        "emission_params": EMISSION_PARAMS,
    })


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    get_model()

    print("=" * 60)
    print("RSC Decentralized Endowment ABM Server")
    print("=" * 60)
    print("Mechanism: RSC held in RH account -> passive yield")
    print("Yield = (your RSC / total RSC) x emissions x multiplier")
    print("Emissions: E(t) = 9.5M / 2^(t/64)")
    print()
    print("Primary question: What participation rate equilibrates?")
    print()
    print("Endpoints:")
    print("  GET  /                   - Dashboard")
    print("  POST /api/init           - Initialize model")
    print("  POST /api/step           - Advance 1 week")
    print("  POST /api/run            - Run N weeks")
    print("  GET  /api/state          - Current state")
    print("  GET  /api/participation  - Participation data + scenarios")
    print("  GET  /api/multipliers    - Time-weight multipliers")
    print("  GET  /api/holders        - List holders")
    print()
    print("Open http://localhost:5000 in your browser")
    print("=" * 60)

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
