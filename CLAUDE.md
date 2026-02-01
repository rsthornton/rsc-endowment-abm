# RSC Decentralized Endowment ABM - Claude Context

## Project Identity

This is the **simple Endowment** model matching ResearchHub's plan:

```
Stake RSC -> Earn Funding Credits -> Deploy to Research Proposals
```

**Not to be confused with**: `rsc-process-fidelity-abm` (the complex model with panel voting, slashing, etc.)

## Python Environment

```bash
# Always activate venv before running
source venv/bin/activate
python server.py
```

## Key Files

| File | Purpose |
|------|---------|
| `src/model.py` | EndowmentModel (Mesa ABM, accepts all params) |
| `src/agents.py` | EndowmentStaker (archetypes, B=f(P,E)), EndowmentProposal |
| `src/constants.py` | Tiers, archetypes (Believer/Yield Seeker/Governance/Speculator), design questions |
| `server.py` | Flask REST API |
| `templates/index.html` | Single-page dashboard (sidebar + 4-tab main area) |
| `ARCHITECTURE.md` | System architecture with Mermaid diagrams |

## Dashboard Layout

**Sidebar sections:**
- **Parameters**: Yield, Deploy Rate, Proposal Success, Stakers (Apply & Reset + Defaults)
- **Archetype Mix**: Linked sliders (sum=100%, min 5% each) + stacked bar + behavioral hints
- **Staking Tiers**: Distribution bar (Flexible/3mo/6mo/12mo)
- **Advanced** (collapsed): Burn Rate, Credit Expiry, Failure Mode, Min Stake
- **Scenarios** (collapsed): Save/Compare runs side-by-side
- **How It Works** (collapsed): B=f(P,E) explanation, weekly step breakdown
- **Design Questions** (collapsed): Open questions from `/api/design-questions`

**Main area tabs:** Agent Field | Time Series | Proposals & Funding | Agent Inspector

**Pinned KPIs:** RSC Staked, Satisfaction, Churned

## Parameter Mapping (Slider -> Backend)

| Slider | ID | Backend param | Section |
|--------|----|---------------|---------|
| Yield | `slider-yield` | `base_apy` (/ 100) | Parameters |
| Deploy Rate | `slider-deploy` | `deploy_probability` (/ 100) | Parameters |
| Proposal Success | `slider-success` | `success_rate` (/ 100) | Parameters |
| Stakers | `slider-stakers` | `num_stakers` (int) | Parameters |
| Burn Rate | `slider-burn` | `burn_rate` (/ 100) | Advanced |

Archetype sliders (`slider-believer`, `slider-yield_seeker`, `slider-governance`, `slider-speculator`) -> `archetype_mix` dict (values / 100).

## Model Parameters

```python
EndowmentModel(
    num_stakers=100,
    num_proposals=10,
    base_apy=0.10,            # 10% yield
    burn_rate=0.02,           # 2% burn fee on deployment
    success_rate=0.80,        # 80% proposal completion
    deploy_probability=0.3,   # Scales behavioral deployment (0.3 = baseline)
    archetype_mix={           # Population composition
        "believer": 0.25,
        "yield_seeker": 0.30,
        "governance": 0.20,
        "speculator": 0.25,
    },
    # Advanced / Design Lab
    credit_expiry_enabled=False,
    credit_expiry_weeks=8,
    failure_mode="nothing",   # nothing | partial_refund | satisfaction_only
    min_stake_enabled=False,
    min_stake_amount=1000,
)
```

## Behavioral Model

`deploy_probability` scales the behavioral deployment decision in `agents.py:_should_deploy()`:
- `deploy_scale = self.model.deploy_probability / 0.3`
- Default 0.3 -> scale=1.0 (unchanged). 0.0 -> nobody deploys. 1.0 -> 3.3x boost (capped 0.95).

## Staking Tiers

| Tier | Lock | Multiplier |
|------|------|------------|
| Flexible | 0 | 1.0x |
| 3-Month | 90d | 1.5x |
| 6-Month | 180d | 2.0x |
| 12-Month | 365d | 3.0x |

## API Quick Reference

```bash
# Initialize
curl -X POST localhost:5000/api/init -d '{"num_stakers": 50, "deploy_probability": 0.5}'

# Run 52 steps (1 year)
curl -X POST localhost:5000/api/run -d '{"steps": 52}'

# Get state
curl localhost:5000/api/state

# Get metrics
curl localhost:5000/api/metrics
```

## Difference from Process Fidelity Model

| Feature | Endowment (this) | Process Fidelity |
|---------|------------------|------------------|
| Credits | Yes | No |
| Archetypes | Yes (4 types) | No |
| Panel voting | No | Yes (5 stakers) |
| Slashing | No | Yes (dissenters) |
| Quality scores | No | Yes (0-6) |
| Researchers | No | Yes (submit proposals) |
| Burn trigger | Credit deployment | Failed proposals |
