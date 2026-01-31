"""
Main Mesa Model for RSC Decentralized Endowment ABM

Simple model: Stake RSC -> Earn Credits (APY) -> Deploy to Proposals -> 2% Burn
"""

import random
from mesa import Model, DataCollector

from .agents import EndowmentStaker, EndowmentProposal
from .constants import DEFAULT_PARAMS, TIERS, ARCHETYPES, DEFAULT_ARCHETYPE_MIX


class EndowmentModel(Model):
    """
    RSC Decentralized Endowment Model (Simple Version)

    Mechanics:
    1. Stakers lock RSC in tiers (Flexible/3mo/6mo/12mo)
    2. Stakers earn credits at tier's APY rate (weekly)
    3. Stakers deploy credits to fund proposals
    4. 2% of backing RSC burned on deployment
    5. Funded proposals resolve (success_rate probability)

    No panel voting, no slashing, no researchers.
    """

    def __init__(
        self,
        num_stakers: int = None,
        num_proposals: int = None,
        base_apy: float = None,
        burn_rate: float = None,
        success_rate: float = None,
        funding_target_min: int = None,
        funding_target_max: int = None,
        deploy_probability: float = None,
        archetype_mix: dict = None,
        seed: int = None,
    ):
        super().__init__()

        if seed is not None:
            random.seed(seed)

        # Set parameters (use defaults if not specified)
        self.num_stakers = num_stakers or DEFAULT_PARAMS["num_stakers"]
        self.base_apy = base_apy if base_apy is not None else DEFAULT_PARAMS["base_apy"]
        self.burn_rate = burn_rate if burn_rate is not None else DEFAULT_PARAMS["burn_rate"]
        self.success_rate = success_rate if success_rate is not None else DEFAULT_PARAMS["success_rate"]
        self.funding_target_min = funding_target_min or DEFAULT_PARAMS["funding_target_min"]
        self.funding_target_max = funding_target_max or DEFAULT_PARAMS["funding_target_max"]
        self.deploy_probability = deploy_probability if deploy_probability is not None else DEFAULT_PARAMS["deploy_probability"]
        self.archetype_mix = archetype_mix or DEFAULT_ARCHETYPE_MIX

        num_proposals = num_proposals or DEFAULT_PARAMS["num_proposals"]

        # Tracking
        self.step_count = 0
        self.total_burned = 0.0
        self.total_credits_generated = 0.0
        self.total_credits_deployed = 0.0
        self.events = []
        self._proposal_counter = 0

        # Create stakers with archetype distribution
        self.stakers = []
        archetype_counts = {}
        remaining = self.num_stakers
        sorted_archetypes = sorted(self.archetype_mix.items(), key=lambda x: x[1], reverse=True)
        for archetype_id, fraction in sorted_archetypes[:-1]:
            count = round(self.num_stakers * fraction)
            archetype_counts[archetype_id] = count
            remaining -= count
        # Last archetype gets remainder to handle rounding
        archetype_counts[sorted_archetypes[-1][0]] = max(remaining, 0)

        for archetype_id, count in archetype_counts.items():
            for _ in range(count):
                staker = EndowmentStaker(self, archetype=archetype_id)
                self.stakers.append(staker)

        # Create initial proposals
        self.proposals = []
        for _ in range(num_proposals):
            self.add_proposal()

        # Data collector
        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.step_count,
                "Total_Staked": lambda m: sum(s.stake for s in m.stakers if s.active),
                "Total_Credits": lambda m: sum(s.credits for s in m.stakers if s.active),
                "Total_Burned": lambda m: m.total_burned,
                "Credits_Generated": lambda m: m.total_credits_generated,
                "Credits_Deployed": lambda m: m.total_credits_deployed,
                "Active_Stakers": lambda m: len([s for s in m.stakers if s.active]),
                "Churned_Stakers": lambda m: len([s for s in m.stakers if not s.active]),
                "Avg_Satisfaction": lambda m: (
                    sum(s.satisfaction for s in m.stakers if s.active) /
                    max(len([s for s in m.stakers if s.active]), 1)
                ),
                "Open_Proposals": lambda m: len([p for p in m.proposals if p.status == "open"]),
                "Funded_Proposals": lambda m: len([p for p in m.proposals if p.status == "funded"]),
                "Completed_Proposals": lambda m: len([p for p in m.proposals if p.status == "completed"]),
                "Failed_Proposals": lambda m: len([p for p in m.proposals if p.status == "failed"]),
            },
        )

        self.datacollector.collect(self)
        self.log_event("init", f"Model initialized with {self.num_stakers} stakers, {num_proposals} proposals")

    def next_proposal_id(self) -> int:
        """Get next proposal ID."""
        self._proposal_counter += 1
        return self._proposal_counter

    def add_proposal(self, funding_target: int = None) -> EndowmentProposal:
        """Create and add a new proposal."""
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
            # Wait at least 1 step after funding before resolution
            if proposal.step_funded is not None and self.step_count > proposal.step_funded:
                success = random.random() < self.success_rate
                proposal.resolve(success)

    def maybe_spawn_proposal(self):
        """Maybe spawn a new proposal if too few are open."""
        open_proposals = len([p for p in self.proposals if p.status == "open"])
        if open_proposals < 5:
            if random.random() < 0.3:  # 30% chance per step
                self.add_proposal()

    def log_event(self, event_type: str, message: str):
        """Log an event."""
        self.events.append({
            "step": self.step_count,
            "type": event_type,
            "message": message,
        })

    def get_tier_distribution(self) -> dict:
        """Get distribution of stakers across tiers."""
        dist = {tier_id: 0 for tier_id in TIERS.keys()}
        for staker in self.stakers:
            dist[staker.tier_id] += 1
        return dist

    def get_tier_stakes(self) -> dict:
        """Get total stake by tier."""
        stakes = {tier_id: 0 for tier_id in TIERS.keys()}
        for staker in self.stakers:
            stakes[staker.tier_id] += staker.stake
        return stakes

    def get_archetype_distribution(self) -> dict:
        """Get count of active stakers by archetype."""
        dist = {}
        for staker in self.stakers:
            if staker.active:
                dist[staker.archetype] = dist.get(staker.archetype, 0) + 1
        return dist

    def get_step_deployments(self) -> list:
        """Get all deployments from the current step (for canvas visualization)."""
        deployments = []
        for staker in self.stakers:
            for d in staker.deployments:
                if d["step"] == self.step_count:
                    deployments.append({
                        "staker_id": f"S{staker.unique_id}",
                        "archetype": staker.archetype,
                        "proposal_id": f"P{d['proposal_id']}",
                        "credits": round(d["credits"], 2),
                        "burned": round(d["burned"], 2),
                    })
        return deployments

    def get_archetype_metrics(self) -> dict:
        """Get per-archetype behavioral metrics."""
        metrics = {}
        for archetype_id in ARCHETYPES:
            group = [s for s in self.stakers if s.archetype == archetype_id]
            active = [s for s in group if s.active]
            if not group:
                continue
            metrics[archetype_id] = {
                "total": len(group),
                "active": len(active),
                "churned": len(group) - len(active),
                "avg_stake": round(sum(s.stake for s in active) / max(len(active), 1), 2),
                "avg_satisfaction": round(sum(s.satisfaction for s in active) / max(len(active), 1), 2),
                "avg_credits": round(sum(s.credits for s in active) / max(len(active), 1), 2),
                "total_deployed": round(sum(s.total_deployed for s in group), 2),
                "total_burned": round(sum(s.total_burned for s in group), 2),
            }
        return metrics

    def step(self):
        """Advance model by one step (week)."""
        self.step_count += 1

        # Track pre-step values
        pre_credits = sum(s.credits for s in self.stakers)
        pre_deployed = self.total_credits_deployed

        # Agents take actions (generate credits, maybe deploy)
        # Mesa 3.x: use agents.shuffle_do() instead of scheduler
        self.agents.shuffle_do("step")

        # Track post-step values
        post_credits = sum(s.credits for s in self.stakers)
        deployed_this_step = sum(s.total_deployed for s in self.stakers) - pre_deployed

        # Update totals
        self.total_credits_generated += (post_credits - pre_credits + deployed_this_step)
        self.total_credits_deployed = sum(s.total_deployed for s in self.stakers)
        self.total_burned = sum(s.total_burned for s in self.stakers)

        # Resolve funded proposals
        self.resolve_funded_proposals()

        # Maybe spawn new proposals
        self.maybe_spawn_proposal()

        # Collect data
        self.datacollector.collect(self)

    def run_steps(self, n: int):
        """Run model for n steps."""
        for _ in range(n):
            self.step()

    def get_events(self, limit: int = 50) -> list:
        """Get recent events."""
        return list(reversed(self.events[-limit:]))

    def get_history(self) -> dict:
        """Get time series data."""
        df = self.datacollector.get_model_vars_dataframe()
        return df.to_dict(orient="list")

    def get_stakers(self) -> list:
        """Get all stakers as dicts."""
        return [s.to_dict() for s in self.stakers]

    def get_proposals(self) -> list:
        """Get all proposals as dicts."""
        return [p.to_dict() for p in self.proposals]

    def get_metrics(self) -> dict:
        """Compute current metrics."""
        active_stakers = [s for s in self.stakers if s.active]
        total_staked = sum(s.stake for s in active_stakers)
        total_credits = sum(s.credits for s in active_stakers)

        # Tier distribution
        tier_dist = self.get_tier_distribution()
        tier_stakes = self.get_tier_stakes()

        # Proposal stats
        open_props = len([p for p in self.proposals if p.status == "open"])
        funded_props = len([p for p in self.proposals if p.status == "funded"])
        completed_props = len([p for p in self.proposals if p.status == "completed"])
        failed_props = len([p for p in self.proposals if p.status == "failed"])

        resolved = completed_props + failed_props
        success_rate_actual = completed_props / resolved if resolved > 0 else 0

        # Credit rates
        credit_rate = sum(s.weekly_credit_rate for s in active_stakers)
        deployment_rate = self.total_credits_deployed / max(self.step_count, 1)

        # Satisfaction
        avg_satisfaction = (
            sum(s.satisfaction for s in active_stakers) / max(len(active_stakers), 1)
        )

        return {
            "step": self.step_count,
            "total_staked": round(total_staked, 2),
            "total_credits": round(total_credits, 2),
            "total_burned": round(self.total_burned, 2),
            "total_credits_generated": round(self.total_credits_generated, 2),
            "total_credits_deployed": round(self.total_credits_deployed, 2),
            "credit_generation_rate": round(credit_rate, 2),
            "deployment_rate": round(deployment_rate, 2),
            "burn_rate_per_step": round(self.total_burned / max(self.step_count, 1), 2),
            "tier_distribution": tier_dist,
            "tier_stakes": {k: round(v, 2) for k, v in tier_stakes.items()},
            "open_proposals": open_props,
            "funded_proposals": funded_props,
            "completed_proposals": completed_props,
            "failed_proposals": failed_props,
            "success_rate_actual": round(success_rate_actual, 3),
            "num_stakers": len(self.stakers),
            "active_stakers": len(active_stakers),
            "churned_stakers": len(self.stakers) - len(active_stakers),
            "avg_satisfaction": round(avg_satisfaction, 3),
            "num_proposals": len(self.proposals),
        }

    def to_dict(self) -> dict:
        """Serialize model state."""
        metrics = self.get_metrics()
        return {
            **metrics,
            "archetype_distribution": self.get_archetype_distribution(),
            "archetype_metrics": self.get_archetype_metrics(),
            "step_deployments": self.get_step_deployments(),
            "params": {
                "base_apy": self.base_apy,
                "burn_rate": self.burn_rate,
                "success_rate": self.success_rate,
                "deploy_probability": self.deploy_probability,
                "funding_target_min": self.funding_target_min,
                "funding_target_max": self.funding_target_max,
                "archetype_mix": self.archetype_mix,
            },
        }
