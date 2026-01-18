"""
Constants for RSC Decentralized Endowment ABM

Simple model: Stake RSC -> Earn Credits (APY) -> Deploy to Proposals -> 2% Burn
"""

# ============================================
# STAKING TIERS (based on lock period)
# ============================================

TIERS = {
    "flexible": {
        "name": "Flexible",
        "lock_days": 0,
        "lock_steps": 0,  # weeks
        "apy_multiplier": 1.0,
        "description": "No lock period, base APY",
    },
    "3_month": {
        "name": "3-Month",
        "lock_days": 90,
        "lock_steps": 13,  # ~13 weeks
        "apy_multiplier": 1.5,
        "description": "90-day lock, 1.5x APY",
    },
    "6_month": {
        "name": "6-Month",
        "lock_days": 180,
        "lock_steps": 26,  # ~26 weeks
        "apy_multiplier": 2.0,
        "description": "180-day lock, 2x APY",
    },
    "12_month": {
        "name": "12-Month",
        "lock_days": 365,
        "lock_steps": 52,  # ~52 weeks
        "apy_multiplier": 3.0,
        "description": "365-day lock, 3x APY",
    },
}


def get_tier(tier_id: str) -> dict:
    """Get tier configuration by ID."""
    if tier_id not in TIERS:
        raise ValueError(f"Unknown tier: {tier_id}. Available: {list(TIERS.keys())}")
    return TIERS[tier_id]


def list_tiers() -> list:
    """List all tiers with metadata."""
    return [
        {
            "id": key,
            "name": tier["name"],
            "lock_days": tier["lock_days"],
            "apy_multiplier": tier["apy_multiplier"],
            "description": tier["description"],
        }
        for key, tier in TIERS.items()
    ]


# ============================================
# MODEL PARAMETERS (defaults)
# ============================================

DEFAULT_PARAMS = {
    "base_apy": 0.10,  # 10% base APY
    "burn_rate": 0.02,  # 2% burn on credit deployment
    "success_rate": 0.80,  # 80% proposal completion probability
    "num_stakers": 100,
    "num_proposals": 10,  # Initial open proposals
    "funding_target_min": 1000,  # Minimum credits to fund
    "funding_target_max": 10000,  # Maximum credits to fund
    "deploy_probability": 0.3,  # Probability staker deploys credits each step
}


# ============================================
# OPEN DESIGN QUESTIONS
# ============================================

DESIGN_QUESTIONS = [
    {
        "id": "credit_expiry",
        "question": "Should credits expire if not deployed?",
        "options": [
            "No expiry (accumulate forever)",
            "Expire after 4 weeks",
            "Expire after 12 weeks",
            "Use-it-or-lose-it each period",
        ],
        "current": "No expiry (simpler)",
        "implications": "Expiry creates urgency but complexity",
    },
    {
        "id": "deployment_model",
        "question": "Pooled vs individual credit deployment?",
        "options": [
            "Individual (each staker picks proposals)",
            "Pooled (credits go to common fund)",
            "Hybrid (individual with fallback pool)",
        ],
        "current": "Individual",
        "implications": "Individual = more engagement, Pooled = simpler UX",
    },
    {
        "id": "failure_consequences",
        "question": "What happens when funded proposals fail?",
        "options": [
            "Nothing (credits already consumed)",
            "Partial refund to backers",
            "Reputation penalty for researcher",
            "Backer gets reduced future credits",
        ],
        "current": "Nothing",
        "implications": "Consequences add accountability but complexity",
    },
    {
        "id": "yield_source",
        "question": "Where does staking yield come from?",
        "options": [
            "New RSC emissions",
            "Platform fee revenue",
            "Separate yield pool",
        ],
        "current": "Not specified",
        "implications": "Emissions = inflation, Revenue = sustainable but variable",
    },
    {
        "id": "success_criteria",
        "question": "How is proposal success determined?",
        "options": [
            "Binary complete/fail",
            "Milestone-based",
            "Peer review",
            "Time-based (auto-complete)",
        ],
        "current": "Binary (probability-based)",
        "implications": "More nuance = more realistic but complex",
    },
]
