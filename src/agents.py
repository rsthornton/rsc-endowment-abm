"""
Agent classes for RSC Decentralized Endowment ABM

Real mechanism: RSC in RH account auto-earns yield passively.
No staking action required — agents simply hold RSC and earn.

Behavioral model: B = f(P, E)
- P = Person attributes (mission_alignment, engagement, price_sensitivity, hold_horizon)
- E = Environment (current APY, peer holding behavior, yield_threshold)
- B = Entry/exit decisions, holding duration, credit deployment

Self-balancing mechanic:
- More RSC in RH -> lower APY for everyone -> yield seekers exit
- RSC exits -> higher APY -> yield seekers re-enter
- Equilibrium participation rate emerges from this process
"""

import random
import math
from collections import deque
from mesa import Agent
from .constants import ARCHETYPES, get_archetype, get_time_weight_multiplier


class EndowmentHolder(Agent):
    """
    An RSC holder whose RSC passively earns endowment yield while in RH account.

    Person attributes (P):
        mission_alignment: 0-1, cares about research quality vs. just yield
        engagement: 0-1, how actively they deploy credits to proposals
        price_sensitivity: 0-1, how quickly yield changes drive exit/entry
        hold_horizon: 0-1, tendency toward long-term holding
        archetype: named preset that generated these attributes

    Holding mechanics:
        rsc_held: RSC currently held in RH account (the "stake" analog)
        weeks_held: continuous holding duration -> determines time-weight multiplier
        yield_threshold: minimum APY to stay (drives self-balancing)
        credits: accumulated funding credits (earned through yield)
        active: False means agent has exited (RSC left RH account)
    """

    def __init__(
        self,
        model,
        rsc_held: int = None,
        archetype: str = None,
        mission_alignment: float = None,
        engagement: float = None,
        price_sensitivity: float = None,
        hold_horizon: float = None,
        yield_threshold: float = None,
        weeks_held: int = None,
        credit_expiry_enabled: bool = False,
        credit_expiry_weeks: int = 8,
    ):
        super().__init__(model)

        # --- Person attributes (P) ---
        self.archetype = archetype or "custom"

        if archetype and archetype in ARCHETYPES:
            arch = ARCHETYPES[archetype]
            self.mission_alignment = mission_alignment if mission_alignment is not None else random.uniform(*arch["mission_alignment"])
            self.engagement = engagement if engagement is not None else random.uniform(*arch["engagement"])
            self.price_sensitivity = price_sensitivity if price_sensitivity is not None else random.uniform(*arch["price_sensitivity"])
            self.hold_horizon = hold_horizon if hold_horizon is not None else random.uniform(*arch["hold_horizon"])
            # RSC amount from archetype range
            rsc_min, rsc_max = arch["rsc_range"]
            if rsc_held is None:
                rsc_held = random.randint(rsc_min, rsc_max)
            # Yield threshold: mean +/- archetype offset +/- personal noise
            if yield_threshold is None:
                offset = arch["yield_threshold_offset"]
                noise = random.gauss(0, 0.01)
                self.yield_threshold = max(0.01, model.yield_threshold_mean + offset + noise)
            else:
                self.yield_threshold = yield_threshold
        else:
            self.mission_alignment = mission_alignment if mission_alignment is not None else random.random()
            self.engagement = engagement if engagement is not None else random.random()
            self.price_sensitivity = price_sensitivity if price_sensitivity is not None else random.random()
            self.hold_horizon = hold_horizon if hold_horizon is not None else random.random()
            self.yield_threshold = yield_threshold if yield_threshold is not None else model.yield_threshold_mean
            if rsc_held is None:
                rsc_held = random.randint(500, 20000)

        # --- Holding state ---
        self.rsc_held = rsc_held
        self.initial_rsc = rsc_held
        # Allow initial weeks_held for "warm start" scenarios
        if weeks_held is not None:
            self.weeks_held = weeks_held
        else:
            # Institutions start with some history; others start fresh
            if self.archetype == "institution":
                self.weeks_held = random.randint(0, 52)
            else:
                self.weeks_held = 0

        # --- Credit expiry (FIFO batches) ---
        self.credit_expiry_enabled = credit_expiry_enabled
        self.credit_expiry_weeks = credit_expiry_weeks
        self.credit_batches = deque()
        self.total_expired = 0.0

        # --- Tracking ---
        self.credits = 0.0
        self.total_deployed = 0.0
        self.total_burned = 0.0
        self.deployments = []
        self.active = True
        self.consecutive_idle_steps = 0
        self.satisfaction = 1.0  # secondary metric, kept for compatibility

    # ============================================
    # Time-weight multiplier
    # ============================================

    def _time_weight_multiplier(self) -> float:
        """Get current multiplier based on continuous holding duration."""
        tier = get_time_weight_multiplier(self.weeks_held)
        return tier["multiplier"]

    @property
    def multiplier_label(self) -> str:
        """Human-readable multiplier tier label."""
        return get_time_weight_multiplier(self.weeks_held)["label"]

    # ============================================
    # Yield earning (the core passive mechanic)
    # ============================================

    def _earn_credits(self):
        """
        Earn credits this week based on dilution-based yield.

        Formula: weekly_emission x (my_effective_rsc / total_effective_rsc) x nothing_more
        (multiplier is already baked into my_effective_rsc)

        Uses effective_total_rsc (all holders' RSC weighted by multiplier) so that
        higher multipliers expand your share relative to others.
        """
        weekly_emission = self.model.weekly_emission()
        effective_total = self.model.total_effective_rsc

        if effective_total <= 0:
            return 0.0

        my_effective_rsc = self.rsc_held * self._time_weight_multiplier()
        my_share = my_effective_rsc / effective_total
        new_credits = weekly_emission * my_share

        self.credits += new_credits
        if self.credit_expiry_enabled:
            self.credit_batches.append((self.model.step_count, new_credits))

        return new_credits

    def _expire_old_credits(self):
        """Expire credit batches older than expiry window (FIFO)."""
        if not self.credit_expiry_enabled:
            return
        current_step = self.model.step_count
        while self.credit_batches:
            step_created, amount = self.credit_batches[0]
            if current_step - step_created > self.credit_expiry_weeks:
                self.credit_batches.popleft()
                self.credits -= amount
                self.total_expired += amount
                self.credits = max(0.0, self.credits)
            else:
                break

    # ============================================
    # Entry / exit dynamics (self-balancing core)
    # ============================================

    def _consider_exit(self):
        """
        Should this holder exit (pull RSC from RH account)?

        Driven by: current APY vs. personal yield_threshold
        - price_sensitivity amplifies the exit probability
        - hold_horizon dampens it (long-term holders resist exiting)
        - Believers and institutions almost never exit regardless of yield
        """
        current_apy = self.model.current_apy()

        if current_apy >= self.yield_threshold:
            return  # Yield is above threshold -- no pressure to exit

        # How far below threshold (0-1 scale)
        gap = (self.yield_threshold - current_apy) / max(self.yield_threshold, 0.001)
        gap = min(gap, 1.0)

        # Exit probability: price_sensitivity amplifies, hold_horizon dampens
        exit_prob = gap * self.price_sensitivity * 0.15  # max ~15%/step at full sensitivity
        exit_prob *= (1.0 - self.hold_horizon * 0.8)    # long-term holders mostly immune

        if random.random() < exit_prob:
            self.active = False
            self.model.log_event(
                "exit",
                f"H{self.unique_id} ({self.archetype}) exited -- APY {current_apy:.1%} < threshold {self.yield_threshold:.1%}"
            )

    # ============================================
    # Credit deployment (secondary mechanic -- unchanged concept)
    # ============================================

    def _should_deploy(self) -> bool:
        """Decide whether to deploy credits this step."""
        if self.credits <= 0:
            return False
        base_prob = self.engagement * 0.6
        # Accumulation pressure
        effective_total = max(self.model.total_effective_rsc, 1)
        my_eff = self.rsc_held * self._time_weight_multiplier()
        weekly_rate = max(self.model.weekly_emission() * (my_eff / effective_total), 1)
        accumulation_ratio = self.credits / (weekly_rate * 4)
        pressure = 1 / (1 + math.exp(-2 * (accumulation_ratio - 1)))
        pressure_boost = pressure * 0.3

        deploy_scale = self.model.deploy_probability / 0.3
        final_prob = min((base_prob + pressure_boost) * deploy_scale, 0.95)
        return random.random() < final_prob

    def _select_proposal(self, open_proposals: list):
        """Choose which proposal to fund."""
        if not open_proposals:
            return None
        if self.mission_alignment > 0.5:
            scored = []
            for p in open_proposals:
                progress = p.funding_progress / 100
                score = progress * self.mission_alignment + random.random() * (1 - self.mission_alignment)
                scored.append((score, p))
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
        else:
            return random.choice(open_proposals)

    def _deploy_amount(self) -> float:
        """How much credits to deploy."""
        min_frac = 0.05
        max_frac = 0.15 + (self.engagement * 0.45)
        frac = random.uniform(min_frac, max_frac)
        return self.credits * frac

    def deploy_credits(self, proposal, amount: float) -> float:
        """Deploy credits to a proposal. Returns RSC burned."""
        if amount > self.credits:
            amount = self.credits
        if amount <= 0:
            return 0

        # 2% burn on proportional RSC
        credit_ratio = amount / max(self.credits, 1)
        rsc_backing = self.rsc_held * credit_ratio * self.model.burn_rate

        self.credits -= amount
        self.total_deployed += amount

        # Consume from oldest batches first (FIFO)
        if self.credit_expiry_enabled:
            remaining = amount
            while remaining > 0 and self.credit_batches:
                step_created, batch_amount = self.credit_batches[0]
                if batch_amount <= remaining:
                    self.credit_batches.popleft()
                    remaining -= batch_amount
                else:
                    self.credit_batches[0] = (step_created, batch_amount - remaining)
                    remaining = 0

        burn_amount = min(rsc_backing, self.rsc_held * 0.1)
        self.rsc_held -= burn_amount
        self.total_burned += burn_amount

        self.deployments.append({
            "step": self.model.step_count,
            "proposal_id": proposal.unique_id,
            "credits": amount,
            "burned": burn_amount,
        })
        proposal.receive_credits(self, amount)
        return burn_amount

    # ============================================
    # Main step
    # ============================================

    def step(self):
        """
        Each step (1 week):
        1. Increment holding duration
        2. Expire old credits (if enabled)
        3. Earn credits from yield share
        4. Decide whether to deploy credits
        5. Consider exit based on yield vs. threshold
        """
        if not self.active:
            return

        # 1. Accumulate holding duration
        self.weeks_held += 1

        # 2. Expire old credits
        self._expire_old_credits()

        # 3. Earn yield
        self._earn_credits()

        # 4. Deploy credits (behavioral)
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

        # 5. Consider exit (self-balancing)
        self._consider_exit()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        multiplier_info = get_time_weight_multiplier(self.weeks_held)
        return {
            "id": f"H{self.unique_id}",
            "type": "holder",
            "archetype": self.archetype,
            "active": self.active,
            # Person attributes
            "mission_alignment": round(self.mission_alignment, 2),
            "engagement": round(self.engagement, 2),
            "price_sensitivity": round(self.price_sensitivity, 2),
            "hold_horizon": round(self.hold_horizon, 2),
            "yield_threshold": round(self.yield_threshold, 4),
            # Holding state
            "rsc_held": round(self.rsc_held, 2),
            "initial_rsc": self.initial_rsc,
            "weeks_held": self.weeks_held,
            "multiplier_label": multiplier_info["label"],
            "multiplier": multiplier_info["multiplier"],
            # Credits
            "credits": round(self.credits, 2),
            "total_deployed": round(self.total_deployed, 2),
            "total_burned": round(self.total_burned, 2),
            "total_expired": round(self.total_expired, 2),
            "deployments_count": len(self.deployments),
            "idle_steps": self.consecutive_idle_steps,
            # Canvas visualization
            "last_step_deployments": [
                d for d in self.deployments if d["step"] == self.model.step_count
            ],
        }


# Backward-compat alias
EndowmentStaker = EndowmentHolder


class EndowmentProposal:
    """
    A research funding proposal.

    Unchanged concept -- agents deploy credits here -> 2% burn -> funded -> resolved.
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

    def receive_credits(self, holder, amount: float):
        self.credits_received += amount
        holder_id = holder.unique_id
        if holder_id not in self.backers:
            self.backers[holder_id] = 0
        self.backers[holder_id] += amount

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
