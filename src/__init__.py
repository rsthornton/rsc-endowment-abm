"""
RSC Decentralized Endowment ABM

Simple model: Stake RSC -> Earn Credits (APY) -> Deploy to Proposals -> 2% Burn
"""

from .model import EndowmentModel
from .agents import EndowmentStaker, EndowmentProposal
from .constants import TIERS, DESIGN_QUESTIONS, DEFAULT_PARAMS, get_tier, list_tiers

__all__ = [
    "EndowmentModel",
    "EndowmentStaker",
    "EndowmentProposal",
    "TIERS",
    "DESIGN_QUESTIONS",
    "DEFAULT_PARAMS",
    "get_tier",
    "list_tiers",
]
