"""
Constants for RSC Decentralized Endowment ABM

Real mechanism: RSC in RH account auto-earns yield (no staking action).
Yield = (your RSC / total RH RSC) × annual emissions × time_weight_multiplier
Emissions decay: E(t) = 9,500,000 / 2^(t/64)

Ground truth: docs/rh-reference/
"""

# ============================================
# TIME-WEIGHT MULTIPLIERS (replaces tiers)
# No lockups — duration rewards holding behavior
# ============================================

TIME_WEIGHT_MULTIPLIERS = [
    {
        "label": "New",
        "max_weeks": 4,
        "multiplier": 1.00,
        "description": "Holding < 4 weeks. Base yield share.",
    },
    {
        "label": "Holder",
        "max_weeks": 52,
        "multiplier": 1.15,
        "description": "Holding 4 weeks–1 year. 15% boost.",
    },
    {
        "label": "LongTerm",
        "max_weeks": None,  # No upper bound
        "multiplier": 1.20,
        "description": "Holding > 1 year. 20% boost.",
    },
]


def get_time_weight_multiplier(weeks_held: int) -> dict:
    """Get multiplier tier for a given holding duration (in weeks)."""
    for tier in TIME_WEIGHT_MULTIPLIERS:
        if tier["max_weeks"] is None or weeks_held < tier["max_weeks"]:
            return tier
    return TIME_WEIGHT_MULTIPLIERS[-1]


def list_multipliers() -> list:
    """List all time-weight multipliers."""
    return TIME_WEIGHT_MULTIPLIERS


# ============================================
# EMISSION PARAMETERS (from RH product doc + CSV)
# E(t) = 9,500,000 / 2^(t/64) RSC/year
# ============================================

EMISSION_PARAMS = {
    "year0_emission": 9_500_000,       # RSC/year at t=0
    "half_life_years": 64,              # Halves every 64 years
    "year0_circulating": 134_157_343,  # RSC circulating at simulation start
    "total_supply": 1_000_000_000,     # Hard cap
    "burn_rate": 0.02,                 # 2% on RH Foundation transactions
}


# ============================================
# MODEL PARAMETERS (defaults)
# ============================================

DEFAULT_PARAMS = {
    "num_holders": 100,
    "burn_rate": 0.02,                  # 2% burn on credit deployment
    "success_rate": 0.80,               # 80% proposal completion probability
    "num_proposals": 10,                # Initial open proposals
    "funding_target_min": 1000,         # Minimum credits to fund
    "funding_target_max": 10000,        # Maximum credits to fund
    "deploy_probability": 0.3,          # Probability agent deploys credits each step
    "yield_threshold_mean": 0.08,       # Mean APY below which agents consider exiting (8%)
    "initial_participation_rate": 0.30, # % of circulating RSC held in RH at sim start
}


# ============================================
# BEHAVIORAL ARCHETYPES
# B=f(P,E): Behavior is a function of Person attributes + Environment
# Matches RH's actual target holder types from product doc
# ============================================

# Person attributes (continuous 0-1 scales)
# - mission_alignment: cares about open science vs. just earning yield
# - engagement: how actively they deploy credits to proposals
# - price_sensitivity: how yield-sensitive their hold/exit decisions are (drives self-balancing)
# - hold_horizon: tendency toward long-term holding (affects time-weight progression)

ARCHETYPES = {
    "believer": {
        "name": "Believer",
        "description": "Believes in open science. Holds long-term (reaches 1.2x), deploys reliably, low churn.",
        "mission_alignment": (0.7, 1.0),
        "engagement": (0.6, 0.9),
        "price_sensitivity": (0.0, 0.2),   # Not yield-driven, stays through low yields
        "hold_horizon": (0.7, 1.0),         # Strong long-term tendency
        "rsc_range": (5_000, 50_000),       # Moderate RSC holdings
        "yield_threshold_offset": -0.04,    # Tolerates 4% below mean threshold
    },
    "yield_seeker": {
        "name": "Yield Seeker",
        "description": "Joins when yield > threshold, exits when it falls. Primary self-balancing force.",
        "mission_alignment": (0.1, 0.4),
        "engagement": (0.2, 0.5),
        "price_sensitivity": (0.7, 1.0),   # Highly yield-sensitive — drives equilibrium
        "hold_horizon": (0.2, 0.5),
        "rsc_range": (1_000, 20_000),
        "yield_threshold_offset": 0.01,    # Exits slightly above mean threshold
    },
    "institution": {
        "name": "Institution",
        "description": "Universities/foundations — RH's primary pitch target. Large RSC, very long-term, reaches 1.2x.",
        "mission_alignment": (0.6, 0.9),
        "engagement": (0.4, 0.7),
        "price_sensitivity": (0.0, 0.15),  # Near-zero sensitivity — anchors participation
        "hold_horizon": (0.85, 1.0),        # Always long-term
        "rsc_range": (100_000, 1_000_000), # Large institutional holdings
        "yield_threshold_offset": -0.06,   # Very tolerant of low yields
    },
    "speculator": {
        "name": "Speculator",
        "description": "Enters on high yield, exits quickly. Amplifies participation rate swings.",
        "mission_alignment": (0.0, 0.15),
        "engagement": (0.05, 0.2),
        "price_sensitivity": (0.85, 1.0),  # Extreme yield sensitivity
        "hold_horizon": (0.0, 0.2),         # Short-term — exits before reaching Holder tier
        "rsc_range": (500, 15_000),
        "yield_threshold_offset": 0.03,    # Exits well above mean threshold
    },
}

# Default archetype weights (fraction of population)
DEFAULT_ARCHETYPE_MIX = {
    "believer": 0.25,
    "yield_seeker": 0.35,
    "institution": 0.15,
    "speculator": 0.25,
}


def get_archetype(archetype_id: str) -> dict:
    """Get archetype configuration by ID."""
    if archetype_id not in ARCHETYPES:
        raise ValueError(f"Unknown archetype: {archetype_id}. Available: {list(ARCHETYPES.keys())}")
    return ARCHETYPES[archetype_id]


def list_archetypes() -> list:
    """List all archetypes with metadata."""
    return [
        {"id": key, **{k: v for k, v in arch.items()}}
        for key, arch in ARCHETYPES.items()
    ]
