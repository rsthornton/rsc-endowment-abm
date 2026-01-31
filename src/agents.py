"""
Agent classes for RSC Decentralized Endowment ABM

Behavioral model: B = f(P, E)
- P = Person attributes (mission_alignment, risk_tolerance, engagement, price_sensitivity)
- E = Environment (APY, proposal quality, peer behavior, credit accumulation)
- B = Tier choice, deployment decision, proposal selection, churn
"""

import random
import math
from mesa import Agent
from .constants import TIERS, ARCHETYPES, get_tier


class EndowmentStaker(Agent):
    """
    A staker with behavioral attributes that drive decisions.

    Person attributes (P):
        mission_alignment: 0-1, cares about research quality vs. just yield
        risk_tolerance: 0-1, willingness to lock longer for higher APY
        engagement: 0-1, how actively they deploy credits
        price_sensitivity: 0-1, how much external conditions matter (future)
        archetype: named preset that generated these attributes

    Mechanics (unchanged):
        stake: RSC locked
        tier_id: flexible, 3_month, 6_month, 12_month
        credits: Accumulated funding credits
        total_deployed: Credits deployed over lifetime
        total_burned: RSC burned from deployments
    """

    def __init__(
        self,
        model,
        stake: int = None,
        tier_id: str = None,
        archetype: str = None,
        mission_alignment: float = None,
        risk_tolerance: float = None,
        engagement: float = None,
        price_sensitivity: float = None,
    ):
        super().__init__(model)

        # --- Person attributes (P) ---
        self.archetype = archetype or "custom"

        if archetype and archetype in ARCHETYPES:
            arch = ARCHETYPES[archetype]
            self.mission_alignment = mission_alignment if mission_alignment is not None else random.uniform(*arch["mission_alignment"])
            self.risk_tolerance = risk_tolerance if risk_tolerance is not None else random.uniform(*arch["risk_tolerance"])
            self.engagement = engagement if engagement is not None else random.uniform(*arch["engagement"])
            self.price_sensitivity = price_sensitivity if price_sensitivity is not None else random.uniform(*arch["price_sensitivity"])
        else:
            self.mission_alignment = mission_alignment if mission_alignment is not None else random.random()
            self.risk_tolerance = risk_tolerance if risk_tolerance is not None else random.random()
            self.engagement = engagement if engagement is not None else random.random()
            self.price_sensitivity = price_sensitivity if price_sensitivity is not None else random.random()

        # --- Stake ---
        if stake is None:
            stake = random.randint(500, 20000)
        self.stake = stake
        self.initial_stake = stake

        # --- Tier selection: driven by risk_tolerance ---
        if tier_id is None:
            tier_id = self._choose_tier()
        self.tier_id = tier_id
        tier = get_tier(tier_id)
        self.lock_until = model.step_count + tier["lock_steps"] if tier["lock_steps"] > 0 else 0

        # --- Tracking ---
        self.credits = 0.0
        self.total_deployed = 0.0
        self.total_burned = 0.0
        self.deployments = []
        self.satisfaction = 1.0  # 0-1, decays if outcomes are bad
        self.consecutive_idle_steps = 0
        self.active = True

    def _choose_tier(self) -> str:
        """
        Choose tier based on risk_tolerance.

        High risk_tolerance -> longer locks (higher APY).
        Low risk_tolerance -> flexible (liquidity).
        """
        r = self.risk_tolerance
        if r > 0.75:
            return "12_month"
        elif r > 0.50:
            return "6_month"
        elif r > 0.25:
            return "3_month"
        else:
            return "flexible"

    @property
    def tier(self) -> dict:
        return get_tier(self.tier_id)

    @property
    def is_locked(self) -> bool:
        return self.lock_until > self.model.step_count

    @property
    def apy_rate(self) -> float:
        return self.model.base_apy * self.tier["apy_multiplier"]

    @property
    def weekly_credit_rate(self) -> float:
        return self.stake * (self.apy_rate / 52)

    def generate_credits(self):
        """Generate weekly credits based on APY."""
        new_credits = self.weekly_credit_rate
        self.credits += new_credits
        return new_credits

    def _should_deploy(self) -> bool:
        """
        Decide whether to deploy credits this step.

        Factors:
        - engagement (P): base probability
        - credit accumulation pressure (E): more credits = more likely to deploy
        - satisfaction (P×E): low satisfaction reduces activity
        """
        if self.credits <= 0:
            return False

        # Base probability from engagement
        base_prob = self.engagement * 0.6  # engagement=1.0 -> 60% base chance

        # Credit accumulation pressure: sigmoid around weekly rate * 4
        # When credits > ~4 weeks of generation, pressure increases
        weekly = max(self.weekly_credit_rate, 1)
        accumulation_ratio = self.credits / (weekly * 4)
        pressure = 1 / (1 + math.exp(-2 * (accumulation_ratio - 1)))  # sigmoid centered at 1
        pressure_boost = pressure * 0.3  # up to +30%

        # Satisfaction dampening
        sat_factor = 0.3 + (0.7 * self.satisfaction)  # floor at 30%

        final_prob = min((base_prob + pressure_boost) * sat_factor, 0.95)
        return random.random() < final_prob

    def _select_proposal(self, open_proposals: list):
        """
        Choose which proposal to fund.

        Mission-aligned agents prefer proposals closer to funding target.
        Low-mission agents pick randomly (spray and pray).
        """
        if not open_proposals:
            return None

        if self.mission_alignment > 0.5:
            # Prefer proposals closer to being funded (higher impact per credit)
            scored = []
            for p in open_proposals:
                progress = p.funding_progress / 100  # 0-1
                # Closer to funded = higher score
                score = progress * self.mission_alignment + random.random() * (1 - self.mission_alignment)
                scored.append((score, p))
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
        else:
            return random.choice(open_proposals)

    def _deploy_amount(self) -> float:
        """
        How much to deploy.

        Engaged agents deploy larger portions.
        Speculators deploy minimally.
        """
        min_frac = 0.05
        max_frac = 0.15 + (self.engagement * 0.45)  # engagement=1 -> up to 60%
        frac = random.uniform(min_frac, max_frac)
        return self.credits * frac

    def deploy_credits(self, proposal, amount: float) -> float:
        """Deploy credits to a proposal. Returns RSC burned."""
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
        burn_amount = min(rsc_backing, self.stake * 0.1)
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

    def _update_satisfaction(self):
        """
        Update satisfaction based on outcomes.

        Factors:
        - Proposals I backed: did they succeed or fail?
        - Am I generating enough credits relative to burn?
        - How long have I been idle?
        """
        # Check recent proposal outcomes
        backed_ids = set()
        for d in self.deployments:
            backed_ids.add(d["proposal_id"])

        if backed_ids:
            resolved = [p for p in self.model.proposals
                        if p.unique_id in backed_ids and p.status in ("completed", "failed")]
            if resolved:
                successes = sum(1 for p in resolved if p.status == "completed")
                success_rate = successes / len(resolved)
                # Blend toward observed success rate
                self.satisfaction = self.satisfaction * 0.8 + success_rate * 0.2

        # Idle penalty
        if self.consecutive_idle_steps > 8:
            self.satisfaction *= 0.98

        self.satisfaction = max(0.1, min(1.0, self.satisfaction))

    def _check_churn(self) -> bool:
        """
        Should this staker exit the system?

        Low satisfaction + not locked = potential churn.
        Speculators churn faster. Believers are stickier.
        """
        if self.is_locked:
            return False

        # Churn threshold: believers tolerate more, speculators less
        churn_threshold = 0.15 + (self.mission_alignment * 0.25)  # 0.15-0.40
        if self.satisfaction < churn_threshold and self.consecutive_idle_steps > 12:
            return random.random() < 0.3  # 30% chance per step when conditions met
        return False

    def step(self):
        """
        Each step:
        1. Generate credits
        2. Decide whether to deploy (behavioral)
        3. Select proposal and deploy amount (behavioral)
        4. Update satisfaction
        5. Check churn
        """
        if not self.active:
            return

        # Generate credits
        self.generate_credits()

        # Behavioral deployment decision
        if self._should_deploy():
            open_proposals = [p for p in self.model.proposals if p.status == "open"]
            proposal = self._select_proposal(open_proposals)
            if proposal:
                amount = self._deploy_amount()
                self.deploy_credits(proposal, amount)
                self.consecutive_idle_steps = 0
            else:
                self.consecutive_idle_steps += 1
        else:
            self.consecutive_idle_steps += 1

        # Update satisfaction from outcomes
        self._update_satisfaction()

        # Check churn
        if self._check_churn():
            self.active = False
            self.model.log_event(
                "churn",
                f"S{self.unique_id} ({self.archetype}) left the system (satisfaction: {self.satisfaction:.2f})"
            )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": f"S{self.unique_id}",
            "type": "staker",
            "archetype": self.archetype,
            "active": self.active,
            # Person attributes
            "mission_alignment": round(self.mission_alignment, 2),
            "risk_tolerance": round(self.risk_tolerance, 2),
            "engagement": round(self.engagement, 2),
            "price_sensitivity": round(self.price_sensitivity, 2),
            "satisfaction": round(self.satisfaction, 2),
            # Stake
            "stake": round(self.stake, 2),
            "initial_stake": self.initial_stake,
            "tier": self.tier["name"],
            "tier_id": self.tier_id,
            "apy_multiplier": self.tier["apy_multiplier"],
            "apy_rate": self.apy_rate,
            "is_locked": self.is_locked,
            "lock_until": self.lock_until,
            # Credits
            "credits": round(self.credits, 2),
            "weekly_rate": round(self.weekly_credit_rate, 2),
            "total_deployed": round(self.total_deployed, 2),
            "total_burned": round(self.total_burned, 2),
            "deployments_count": len(self.deployments),
            "idle_steps": self.consecutive_idle_steps,
        }


class EndowmentProposal:
    """
    A research funding proposal.

    Unchanged from original — system mechanics are correct.
    """

    def __init__(self, unique_id: int, model, funding_target: int = None):
        self.unique_id = unique_id
        self.model = model

        if funding_target is None:
            funding_target = random.randint(
                model.funding_target_min,
                model.funding_target_max
            )
        self.funding_target = funding_target

        self.credits_received = 0.0
        self.backers = {}
        self.status = "open"
        self.step_created = model.step_count
        self.step_funded = None
        self.step_resolved = None

    @property
    def funding_progress(self) -> float:
        return (self.credits_received / self.funding_target) * 100

    @property
    def is_funded(self) -> bool:
        return self.credits_received >= self.funding_target

    def receive_credits(self, staker, amount: float):
        self.credits_received += amount
        staker_id = staker.unique_id
        if staker_id not in self.backers:
            self.backers[staker_id] = 0
        self.backers[staker_id] += amount

        if self.is_funded and self.status == "open":
            self.status = "funded"
            self.step_funded = self.model.step_count
            self.model.log_event(
                "funded",
                f"P{self.unique_id} reached funding target ({self.credits_received:.0f}/{self.funding_target})"
            )

    def resolve(self, success: bool):
        if success:
            self.status = "completed"
            self.model.log_event("completed", f"P{self.unique_id} completed successfully")
        else:
            self.status = "failed"
            self.model.log_event("failed", f"P{self.unique_id} failed")
        self.step_resolved = self.model.step_count

    def to_dict(self) -> dict:
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
