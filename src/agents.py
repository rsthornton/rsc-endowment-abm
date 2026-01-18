"""
Agent classes for RSC Decentralized Endowment ABM

Simple model: Stake RSC -> Earn Credits -> Deploy to Proposals -> 2% Burn
"""

import random
from mesa import Agent
from .constants import TIERS, get_tier


class EndowmentStaker(Agent):
    """
    A staker who locks RSC to earn funding credits.

    Mechanics:
    - Stake RSC with a chosen lock tier
    - Earn credits at tier's APY rate (weekly)
    - Deploy credits to fund proposals
    - 2% of backing RSC burned on deployment

    Attributes:
        stake: RSC locked
        tier_id: flexible, 3_month, 6_month, 12_month
        lock_until: Step when stake unlocks (0 = flexible)
        credits: Accumulated funding credits
        total_deployed: Credits deployed over lifetime
        total_burned: RSC burned from deployments
    """

    def __init__(
        self,
        model,
        stake: int = None,
        tier_id: str = None,
    ):
        super().__init__(model)  # Mesa 3.x: unique_id auto-assigned

        # Initialize stake (random if not specified)
        if stake is None:
            stake = random.randint(500, 20000)
        self.stake = stake
        self.initial_stake = stake

        # Initialize tier (weighted random if not specified)
        if tier_id is None:
            # Weight toward shorter lock periods
            tier_weights = [
                ("flexible", 0.4),
                ("3_month", 0.3),
                ("6_month", 0.2),
                ("12_month", 0.1),
            ]
            r = random.random()
            cumulative = 0
            for tid, weight in tier_weights:
                cumulative += weight
                if r < cumulative:
                    tier_id = tid
                    break

        self.tier_id = tier_id
        tier = get_tier(tier_id)

        # Lock until step (0 for flexible = always unlocked)
        self.lock_until = model.step_count + tier["lock_steps"] if tier["lock_steps"] > 0 else 0

        # Credits and tracking
        self.credits = 0.0
        self.total_deployed = 0.0
        self.total_burned = 0.0
        self.deployments = []  # List of {step, proposal_id, amount}

    @property
    def tier(self) -> dict:
        """Get current tier configuration."""
        return get_tier(self.tier_id)

    @property
    def is_locked(self) -> bool:
        """Check if stake is still locked."""
        return self.lock_until > self.model.step_count

    @property
    def apy_rate(self) -> float:
        """Calculate effective APY based on tier."""
        return self.model.base_apy * self.tier["apy_multiplier"]

    @property
    def weekly_credit_rate(self) -> float:
        """Credits earned per week (step)."""
        return self.stake * (self.apy_rate / 52)

    def generate_credits(self):
        """Generate weekly credits based on APY."""
        new_credits = self.weekly_credit_rate
        self.credits += new_credits
        return new_credits

    def deploy_credits(self, proposal, amount: float) -> float:
        """
        Deploy credits to a proposal.

        Returns the amount of RSC burned.
        """
        if amount > self.credits:
            amount = self.credits

        if amount <= 0:
            return 0

        # Calculate RSC burn (2% of proportional stake)
        credit_ratio = amount / max(self.credits, 1)
        rsc_backing = self.stake * credit_ratio * self.model.burn_rate

        # Apply deployment
        self.credits -= amount
        self.total_deployed += amount

        # Burn RSC
        burn_amount = min(rsc_backing, self.stake * 0.1)  # Cap at 10% stake per deployment
        self.stake -= burn_amount
        self.total_burned += burn_amount

        # Record
        self.deployments.append({
            "step": self.model.step_count,
            "proposal_id": proposal.unique_id,
            "credits": amount,
            "burned": burn_amount,
        })

        # Add to proposal
        proposal.receive_credits(self, amount)

        return burn_amount

    def step(self):
        """
        Each step:
        1. Generate credits
        2. Maybe deploy to a proposal
        """
        # Generate credits
        self.generate_credits()

        # Maybe deploy credits
        if self.credits > 0 and random.random() < self.model.deploy_probability:
            # Find an open proposal
            open_proposals = [p for p in self.model.proposals if p.status == "open"]
            if open_proposals:
                proposal = random.choice(open_proposals)
                # Deploy a portion of credits
                deploy_amount = self.credits * random.uniform(0.1, 0.5)
                self.deploy_credits(proposal, deploy_amount)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": f"S{self.unique_id}",
            "type": "staker",
            "stake": round(self.stake, 2),
            "initial_stake": self.initial_stake,
            "tier": self.tier["name"],
            "tier_id": self.tier_id,
            "apy_multiplier": self.tier["apy_multiplier"],
            "apy_rate": self.apy_rate,
            "is_locked": self.is_locked,
            "lock_until": self.lock_until,
            "credits": round(self.credits, 2),
            "weekly_rate": round(self.weekly_credit_rate, 2),
            "total_deployed": round(self.total_deployed, 2),
            "total_burned": round(self.total_burned, 2),
            "deployments_count": len(self.deployments),
        }


class EndowmentProposal:
    """
    A research funding proposal.

    Mechanics:
    - Has a funding target (in credits)
    - Stakers deploy credits to fund
    - When target reached, becomes "funded"
    - Funded proposals complete or fail (binary probability)

    Attributes:
        funding_target: Credits needed to fund
        credits_received: Current backing amount
        backers: Dict of staker_id -> amount
        status: open, funded, completed, failed
    """

    def __init__(self, unique_id: int, model, funding_target: int = None):
        self.unique_id = unique_id
        self.model = model

        # Set funding target
        if funding_target is None:
            funding_target = random.randint(
                model.funding_target_min,
                model.funding_target_max
            )
        self.funding_target = funding_target

        # Tracking
        self.credits_received = 0.0
        self.backers = {}  # staker_id -> amount
        self.status = "open"
        self.step_created = model.step_count
        self.step_funded = None
        self.step_resolved = None

    @property
    def funding_progress(self) -> float:
        """Percentage of funding target reached."""
        return (self.credits_received / self.funding_target) * 100

    @property
    def is_funded(self) -> bool:
        """Check if funding target reached."""
        return self.credits_received >= self.funding_target

    def receive_credits(self, staker, amount: float):
        """Receive credits from a staker."""
        self.credits_received += amount

        staker_id = staker.unique_id
        if staker_id not in self.backers:
            self.backers[staker_id] = 0
        self.backers[staker_id] += amount

        # Check if now funded
        if self.is_funded and self.status == "open":
            self.status = "funded"
            self.step_funded = self.model.step_count
            self.model.log_event(
                "funded",
                f"P{self.unique_id} reached funding target ({self.credits_received:.0f}/{self.funding_target})"
            )

    def resolve(self, success: bool):
        """Resolve the proposal outcome."""
        if success:
            self.status = "completed"
            self.model.log_event(
                "completed",
                f"P{self.unique_id} completed successfully"
            )
        else:
            self.status = "failed"
            self.model.log_event(
                "failed",
                f"P{self.unique_id} failed"
            )
        self.step_resolved = self.model.step_count

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": f"P{self.unique_id}",
            "type": "proposal",
            "funding_target": self.funding_target,
            "credits_received": round(self.credits_received, 2),
            "funding_progress": round(self.funding_progress, 1),
            "backer_count": len(self.backers),
            "status": self.status,
            "step_created": self.step_created,
            "step_funded": self.step_funded,
            "step_resolved": self.step_resolved,
        }
