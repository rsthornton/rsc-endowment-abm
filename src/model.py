"""
Main Mesa Model for RSC Decentralized Endowment ABM

Real mechanism: RSC in RH account auto-earns yield.
Yield = (your RSC / total RH RSC) x annual_emissions x time_weight_multiplier
Emissions: E(t) = 9,500,000 / 2^(t/64)

Key output: participation_rate -- what % of circulating RSC is held in RH?
This is the primary equilibrium question the RH team wants to reason about.
"""

import random
import math
from mesa import Model, DataCollector

from .agents import EndowmentHolder, EndowmentStaker, EndowmentProposal
from .constants import (
    DEFAULT_PARAMS, EMISSION_PARAMS, ARCHETYPES,
    DEFAULT_ARCHETYPE_MIX, TIME_WEIGHT_MULTIPLIERS,
    get_archetype, get_time_weight_multiplier,
)


class EndowmentModel(Model):
    """
    RSC Decentralized Endowment Model (Redesigned to match RH's actual 2026 plan)

    Mechanics:
    1. RSC held in RH account auto-earns yield (passive, no staking action)
    2. Yield = (your_rsc / total_rsc) x annual_emission x time_weight_multiplier
    3. Emissions decay: E(t) = 9,500,000 / 2^(t/64)
    4. Time-weight multipliers: 1.0x (new), 1.15x (holder >4wk), 1.20x (long-term >1yr)
    5. Agents exit when APY falls below their personal yield_threshold
    6. New Yield Seekers enter when APY rises above threshold (self-balancing)
    7. Agents deploy credits to fund proposals -> 2% burn

    Primary question: What participation_rate does the market equilibrate to?
    """

    def __init__(
        self,
        num_holders: int = None,
        num_proposals: int = None,
        burn_rate: float = None,
        success_rate: float = None,
        funding_target_min: int = None,
        funding_target_max: int = None,
        deploy_probability: float = None,
        archetype_mix: dict = None,
        yield_threshold_mean: float = None,
        initial_participation_rate: float = None,
        seed: int = None,
        # Design Lab params
        credit_expiry_enabled: bool = False,
        credit_expiry_weeks: int = 8,
        failure_mode: str = "nothing",
        # Legacy compat (ignored, kept to avoid breaking init calls)
        num_stakers: int = None,
        base_apy: float = None,
    ):
        super().__init__()

        if seed is not None:
            random.seed(seed)

        # Handle legacy param alias
        if num_holders is None and num_stakers is not None:
            num_holders = num_stakers

        # Parameters
        self.num_holders = num_holders or DEFAULT_PARAMS["num_holders"]
        self.burn_rate = burn_rate if burn_rate is not None else DEFAULT_PARAMS["burn_rate"]
        self.success_rate = success_rate if success_rate is not None else DEFAULT_PARAMS["success_rate"]
        self.funding_target_min = funding_target_min or DEFAULT_PARAMS["funding_target_min"]
        self.funding_target_max = funding_target_max or DEFAULT_PARAMS["funding_target_max"]
        self.deploy_probability = deploy_probability if deploy_probability is not None else DEFAULT_PARAMS["deploy_probability"]
        self.archetype_mix = archetype_mix or DEFAULT_ARCHETYPE_MIX
        self.yield_threshold_mean = yield_threshold_mean if yield_threshold_mean is not None else DEFAULT_PARAMS["yield_threshold_mean"]
        self.initial_participation_rate = initial_participation_rate if initial_participation_rate is not None else DEFAULT_PARAMS["initial_participation_rate"]

        # Emission params from constants
        self.year0_emission = EMISSION_PARAMS["year0_emission"]
        self.half_life_years = EMISSION_PARAMS["half_life_years"]
        self.year0_circulating = EMISSION_PARAMS["year0_circulating"]

        # Design Lab params
        self.credit_expiry_enabled = credit_expiry_enabled
        self.credit_expiry_weeks = credit_expiry_weeks
        self.failure_mode = failure_mode

        num_proposals = num_proposals or DEFAULT_PARAMS["num_proposals"]

        # Tracking
        self.step_count = 0
        self.total_burned = 0.0
        self.total_credits_generated = 0.0
        self.total_credits_deployed = 0.0
        self.cumulative_emissions = 0.0  # RSC emitted so far (adds to circulating supply)
        self.events = []
        self._proposal_counter = 0

        # Per-step tracking
        self._step_credits_generated = 0.0
        self._step_credits_deployed = 0.0
        self._step_exit_count = 0
        self._step_entry_count = 0

        # Create holders
        self.holders = []
        self._spawn_holders(self.num_holders)

        # Create initial proposals
        self.proposals = []
        for _ in range(num_proposals):
            self.add_proposal()

        # Data collector
        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.step_count,
                "Year": lambda m: round(m.step_count / 52, 2),
                "Participation_Rate": lambda m: round(m.participation_rate, 4),
                "Current_APY": lambda m: round(m.current_apy(), 4),
                "Total_RSC_Held": lambda m: round(m.total_rsc_held, 0),
                "Effective_RSC": lambda m: round(m.total_effective_rsc, 0),
                "Circulating_Supply": lambda m: round(m.circulating_supply, 0),
                "Weekly_Emission": lambda m: round(m.weekly_emission(), 2),
                "Total_Burned": lambda m: round(m.total_burned, 2),
                "Cumulative_Emissions": lambda m: round(m.cumulative_emissions, 2),
                "Active_Holders": lambda m: len([h for h in m.holders if h.active]),
                "Exited_Holders": lambda m: len([h for h in m.holders if not h.active]),
                "Open_Proposals": lambda m: len([p for p in m.proposals if p.status == "open"]),
                "Funded_Proposals": lambda m: len([p for p in m.proposals if p.status == "funded"]),
                "Completed_Proposals": lambda m: len([p for p in m.proposals if p.status == "completed"]),
                # Per-archetype RSC held
                "RSC_Believer": lambda m: m._rsc_for_archetype("believer"),
                "RSC_YieldSeeker": lambda m: m._rsc_for_archetype("yield_seeker"),
                "RSC_Institution": lambda m: m._rsc_for_archetype("institution"),
                "RSC_Speculator": lambda m: m._rsc_for_archetype("speculator"),
                # Per-multiplier holder counts
                "Count_New": lambda m: m._count_at_multiplier("New"),
                "Count_Holder": lambda m: m._count_at_multiplier("Holder"),
                "Count_LongTerm": lambda m: m._count_at_multiplier("LongTerm"),
                # Flow tracking
                "Exits_Step": lambda m: m._step_exit_count,
                "Entries_Step": lambda m: m._step_entry_count,
                "Credits_Generated_Step": lambda m: m._step_credits_generated,
                "Credits_Deployed_Step": lambda m: m._step_credits_deployed,
            },
        )

        self.datacollector.collect(self)
        self.log_event(
            "init",
            f"Model initialized: {len(self.holders)} holders, "
            f"{self.initial_participation_rate:.0%} participation target, "
            f"APY={self.current_apy():.1%}"
        )

    # ============================================
    # Emissions engine
    # ============================================

    def weekly_emission(self) -> float:
        """RSC emitted this week. E(t) = 9.5M / 2^(t/64), weekly."""
        t_years = self.step_count / 52
        annual = self.year0_emission / (2 ** (t_years / self.half_life_years))
        return annual / 52

    def annual_emission(self) -> float:
        """Annual emission at current time."""
        t_years = self.step_count / 52
        return self.year0_emission / (2 ** (t_years / self.half_life_years))

    @property
    def circulating_supply(self) -> float:
        """Current circulating supply (year0 + cumulative emissions)."""
        return self.year0_circulating + self.cumulative_emissions

    # ============================================
    # Participation and APY
    # ============================================

    @property
    def total_rsc_held(self) -> float:
        """Total RSC held by active holders."""
        return sum(h.rsc_held for h in self.holders if h.active)

    @property
    def total_effective_rsc(self) -> float:
        """
        Total effective RSC (weighted by time-weight multipliers).
        Used for yield share calculation so multipliers expand your share.
        """
        return sum(
            h.rsc_held * h._time_weight_multiplier()
            for h in self.holders if h.active
        )

    @property
    def participation_rate(self) -> float:
        """% of circulating RSC currently held in RH. The key equilibrium metric."""
        circ = self.circulating_supply
        if circ <= 0:
            return 0.0
        return self.total_rsc_held / circ

    def current_apy(self) -> float:
        """
        Current annualized yield rate (base 1.0x multiplier).
        Formula: annual_emission / total_rsc_held
        Individual effective APY = this * their_multiplier.
        """
        total = self.total_rsc_held
        if total <= 0:
            return 0.0
        return self.annual_emission() / total

    # ============================================
    # Holder management
    # ============================================

    def _spawn_holders(self, count: int):
        """Create holders with archetype distribution."""
        archetype_counts = {}
        remaining = count
        sorted_archetypes = sorted(self.archetype_mix.items(), key=lambda x: x[1], reverse=True)
        for archetype_id, fraction in sorted_archetypes[:-1]:
            n = round(count * fraction)
            archetype_counts[archetype_id] = n
            remaining -= n
        archetype_counts[sorted_archetypes[-1][0]] = max(remaining, 0)

        for archetype_id, n in archetype_counts.items():
            for _ in range(n):
                holder = EndowmentHolder(
                    self,
                    archetype=archetype_id,
                    credit_expiry_enabled=self.credit_expiry_enabled,
                    credit_expiry_weeks=self.credit_expiry_weeks,
                )
                self.holders.append(holder)

    def _maybe_spawn_entrants(self):
        """
        Spawn new Yield Seeker entrants when APY rises above their threshold.

        This is the market self-balancing re-entry mechanism:
        exits -> lower total RSC -> higher APY -> new entrants attracted.
        """
        current_apy = self.current_apy()

        # Entry threshold slightly above mean (seekers need better yield to join)
        entry_threshold = self.yield_threshold_mean * 1.1

        if current_apy > entry_threshold:
            attractiveness = min((current_apy - entry_threshold) / entry_threshold, 1.0)
            spawn_prob = attractiveness * 0.15  # up to 15%/step

            if random.random() < spawn_prob:
                n_new = random.randint(1, 3)
                for _ in range(n_new):
                    holder = EndowmentHolder(
                        self,
                        archetype="yield_seeker",
                        credit_expiry_enabled=self.credit_expiry_enabled,
                        credit_expiry_weeks=self.credit_expiry_weeks,
                    )
                    self.holders.append(holder)
                self._step_entry_count += n_new
                self.log_event(
                    "entry",
                    f"{n_new} new Yield Seeker(s) entered -- APY {current_apy:.1%} > threshold"
                )

    # ============================================
    # Proposal management
    # ============================================

    def next_proposal_id(self) -> int:
        self._proposal_counter += 1
        return self._proposal_counter

    def add_proposal(self, funding_target: int = None) -> EndowmentProposal:
        proposal = EndowmentProposal(
            unique_id=self.next_proposal_id(),
            model=self,
            funding_target=funding_target,
        )
        self.proposals.append(proposal)
        self.log_event("new_proposal", f"P{proposal.unique_id} created (target: {proposal.funding_target:,} credits)")
        return proposal

    def resolve_funded_proposals(self):
        """Resolve proposals that have been funded for at least 1 step."""
        funded = [p for p in self.proposals if p.status == "funded"]
        for proposal in funded:
            if proposal.step_funded is not None and self.step_count > proposal.step_funded:
                success = random.random() < self.success_rate
                proposal.resolve(success)

                if not success and self.failure_mode == "partial_refund":
                    for holder_id, credits in proposal.backers.items():
                        holder = next((h for h in self.holders if h.unique_id == holder_id), None)
                        if holder and holder.active:
                            holder.credits += credits * 0.5

    def maybe_spawn_proposal(self):
        open_proposals = len([p for p in self.proposals if p.status == "open"])
        if open_proposals < 5:
            if random.random() < 0.3:
                self.add_proposal()

    # ============================================
    # Data helpers
    # ============================================

    def _rsc_for_archetype(self, archetype_id: str) -> float:
        return round(sum(h.rsc_held for h in self.holders if h.archetype == archetype_id and h.active), 0)

    def _count_at_multiplier(self, label: str) -> int:
        return sum(1 for h in self.holders if h.active and h.multiplier_label == label)

    def get_multiplier_distribution(self) -> dict:
        """Get count and RSC by time-weight multiplier tier."""
        dist = {}
        for tier in TIME_WEIGHT_MULTIPLIERS:
            label = tier["label"]
            holders = [h for h in self.holders if h.active and h.multiplier_label == label]
            dist[label] = {
                "count": len(holders),
                "rsc": round(sum(h.rsc_held for h in holders), 0),
                "multiplier": tier["multiplier"],
            }
        return dist

    def get_archetype_distribution(self) -> dict:
        dist = {}
        for h in self.holders:
            if h.active:
                dist[h.archetype] = dist.get(h.archetype, 0) + 1
        return dist

    def get_archetype_metrics(self) -> dict:
        metrics = {}
        for archetype_id in ARCHETYPES:
            group = [h for h in self.holders if h.archetype == archetype_id]
            active = [h for h in group if h.active]
            if not group:
                continue
            metrics[archetype_id] = {
                "total": len(group),
                "active": len(active),
                "exited": len(group) - len(active),
                "avg_rsc": round(sum(h.rsc_held for h in active) / max(len(active), 1), 2),
                "avg_weeks_held": round(sum(h.weeks_held for h in active) / max(len(active), 1), 1),
                "avg_multiplier": round(sum(h._time_weight_multiplier() for h in active) / max(len(active), 1), 3),
                "avg_credits": round(sum(h.credits for h in active) / max(len(active), 1), 2),
                "total_deployed": round(sum(h.total_deployed for h in group), 2),
                "total_burned": round(sum(h.total_burned for h in group), 2),
            }
        return metrics

    def get_participation_data(self) -> dict:
        """Participation rate data with CSV reference scenarios."""
        rate = self.participation_rate
        apy = self.current_apy()
        ann_emit = self.annual_emission()
        circ = self.circulating_supply
        return {
            "participation_rate": round(rate, 4),
            "current_apy": round(apy, 4),
            "total_rsc_held": round(self.total_rsc_held, 0),
            "circulating_supply": round(circ, 0),
            "annual_emission": round(ann_emit, 0),
            "year": round(self.step_count / 52, 2),
            # Reference scenario APYs (from CSV ground truth)
            "scenarios": {
                "15pct": round(ann_emit / (circ * 0.15), 4) if circ > 0 else 0,
                "30pct": round(ann_emit / (circ * 0.30), 4) if circ > 0 else 0,
                "70pct": round(ann_emit / (circ * 0.70), 4) if circ > 0 else 0,
            },
        }

    def get_step_deployments(self) -> list:
        deployments = []
        for holder in self.holders:
            for d in holder.deployments:
                if d["step"] == self.step_count:
                    deployments.append({
                        "holder_id": f"H{holder.unique_id}",
                        "archetype": holder.archetype,
                        "proposal_id": f"P{d['proposal_id']}",
                        "credits": round(d["credits"], 2),
                        "burned": round(d["burned"], 2),
                    })
        return deployments

    def log_event(self, event_type: str, message: str):
        self.events.append({
            "step": self.step_count,
            "type": event_type,
            "message": message,
        })

    # ============================================
    # Main step
    # ============================================

    def step(self):
        """Advance model by one step (1 week)."""
        self.step_count += 1

        # Reset per-step counters
        self._step_credits_generated = 0.0
        self._step_credits_deployed = 0.0
        self._step_exit_count = 0
        self._step_entry_count = 0

        pre_deployed = self.total_credits_deployed
        pre_active = len([h for h in self.holders if h.active])

        # Agents take actions
        self.agents.shuffle_do("step")

        post_active = len([h for h in self.holders if h.active])
        self._step_exit_count = max(0, pre_active - post_active)

        deployed_this_step = sum(h.total_deployed for h in self.holders) - pre_deployed
        self._step_credits_deployed = deployed_this_step

        # Update totals
        self._step_credits_generated = self.weekly_emission()
        self.cumulative_emissions += self.weekly_emission()
        self.total_credits_deployed = sum(h.total_deployed for h in self.holders)
        self.total_burned = sum(h.total_burned for h in self.holders)
        self.total_credits_generated += self._step_credits_generated

        # Resolve funded proposals
        self.resolve_funded_proposals()

        # Spawn new entrants (self-balancing re-entry)
        self._maybe_spawn_entrants()

        # Maybe spawn new proposals
        self.maybe_spawn_proposal()

        # Collect data
        self.datacollector.collect(self)

    def run_steps(self, n: int):
        for _ in range(n):
            self.step()

    # ============================================
    # Serialization
    # ============================================

    def get_events(self, limit: int = 50) -> list:
        return list(reversed(self.events[-limit:]))

    def get_history(self) -> dict:
        df = self.datacollector.get_model_vars_dataframe()
        return df.to_dict(orient="list")

    def get_holders(self) -> list:
        return [h.to_dict() for h in self.holders]

    # Legacy alias
    def get_stakers(self) -> list:
        return self.get_holders()

    def get_proposals(self) -> list:
        return [p.to_dict() for p in self.proposals]

    def get_metrics(self) -> dict:
        active_holders = [h for h in self.holders if h.active]
        total_rsc = self.total_rsc_held
        total_credits = sum(h.credits for h in active_holders)

        open_props = len([p for p in self.proposals if p.status == "open"])
        funded_props = len([p for p in self.proposals if p.status == "funded"])
        completed_props = len([p for p in self.proposals if p.status == "completed"])
        failed_props = len([p for p in self.proposals if p.status == "failed"])
        resolved = completed_props + failed_props
        success_rate_actual = completed_props / resolved if resolved > 0 else 0

        return {
            "step": self.step_count,
            "year": round(self.step_count / 52, 2),
            # Primary equilibrium metrics
            "participation_rate": round(self.participation_rate, 4),
            "current_apy": round(self.current_apy(), 4),
            "total_rsc_held": round(total_rsc, 2),
            "circulating_supply": round(self.circulating_supply, 2),
            "annual_emission": round(self.annual_emission(), 2),
            "weekly_emission": round(self.weekly_emission(), 2),
            # Credit / burn
            "total_credits": round(total_credits, 2),
            "total_burned": round(self.total_burned, 2),
            "total_credits_generated": round(self.total_credits_generated, 2),
            "total_credits_deployed": round(self.total_credits_deployed, 2),
            "deployment_rate": round(self.total_credits_deployed / max(self.step_count, 1), 2),
            # Multiplier distribution
            "multiplier_distribution": self.get_multiplier_distribution(),
            # Proposal stats
            "open_proposals": open_props,
            "funded_proposals": funded_props,
            "completed_proposals": completed_props,
            "failed_proposals": failed_props,
            "success_rate_actual": round(success_rate_actual, 3),
            # Holder stats
            "num_holders": len(self.holders),
            "active_holders": len(active_holders),
            "exited_holders": len(self.holders) - len(active_holders),
            "num_proposals": len(self.proposals),
        }

    def to_dict(self) -> dict:
        metrics = self.get_metrics()
        return {
            **metrics,
            "archetype_distribution": self.get_archetype_distribution(),
            "archetype_metrics": self.get_archetype_metrics(),
            "participation_data": self.get_participation_data(),
            "step_deployments": self.get_step_deployments(),
            "credits_generated_step": round(self._step_credits_generated, 2),
            "credits_deployed_step": round(self._step_credits_deployed, 2),
            "exits_step": self._step_exit_count,
            "entries_step": self._step_entry_count,
            "params": {
                "burn_rate": self.burn_rate,
                "success_rate": self.success_rate,
                "deploy_probability": self.deploy_probability,
                "funding_target_min": self.funding_target_min,
                "funding_target_max": self.funding_target_max,
                "archetype_mix": self.archetype_mix,
                "yield_threshold_mean": self.yield_threshold_mean,
                "initial_participation_rate": self.initial_participation_rate,
                "credit_expiry_enabled": self.credit_expiry_enabled,
                "credit_expiry_weeks": self.credit_expiry_weeks,
                "failure_mode": self.failure_mode,
            },
        }
