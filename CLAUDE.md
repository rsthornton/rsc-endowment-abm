# RSC Decentralized Endowment ABM - Claude Context

## Project Identity

This is the **simple Endowment** model matching ResearchHub's plan:

```
Stake RSC -> Earn Credits (APY) -> Deploy to Proposals -> 2% Burn
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
| `src/model.py` | EndowmentModel (simple credit-based) |
| `src/agents.py` | EndowmentStaker, EndowmentProposal |
| `src/constants.py` | Tiers, design questions |
| `server.py` | Flask REST API |
| `templates/index.html` | Interactive dashboard with educational features |

## Dashboard Features

The dashboard at `http://localhost:5000` includes:
- **📖 This Week's Activity**: Round-by-round narrative
- **🔍 Agent Inspector**: Individual staker exploration (3 tabs)
- **📚 How This Model Works**: Visual flow + detailed explanations
- **Tooltips**: Hover any metric for explanation

## Model Parameters

```python
EndowmentModel(
    num_stakers=100,
    num_proposals=10,
    base_apy=0.10,        # 10% base APY
    burn_rate=0.02,       # 2% burn on deployment
    success_rate=0.80,    # 80% proposal completion
    deploy_probability=0.3,
    funding_target_min=1000,
    funding_target_max=10000,
)
```

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
curl -X POST localhost:5000/api/init -d '{"num_stakers": 50}'

# Run 10 steps
curl -X POST localhost:5000/api/run -d '{"steps": 10}'

# Get state
curl localhost:5000/api/state

# Get metrics
curl localhost:5000/api/metrics

# List tiers
curl localhost:5000/api/tiers
```

## Design Questions Endpoint

The `/api/design-questions` endpoint surfaces open questions for ResearchHub:
- Credit expiry policy
- Pooled vs individual deployment
- Failure consequences
- Yield source
- Success criteria

## Difference from Process Fidelity Model

| Feature | Endowment (this) | Process Fidelity |
|---------|------------------|------------------|
| Credits | Yes | No |
| Panel voting | No | Yes (5 stakers) |
| Slashing | No | Yes (dissenters) |
| Quality scores | No | Yes (0-6) |
| Researchers | No | Yes (submit proposals) |
| Burn trigger | Credit deployment | Failed proposals |
