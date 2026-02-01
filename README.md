# RSC Decentralized Endowment ABM

Agent-based model for RSC staking with **simple credit-based funding** and behavioral archetypes.

## Overview

This model simulates the core endowment mechanism:

```
Stake RSC -> Earn Funding Credits -> Deploy to Research Proposals
```

**Key features:**
- 4 behavioral archetypes (Believers, Yield Seekers, Governance, Speculators)
- 4 staking tiers based on lock period (Flexible/3mo/6mo/12mo)
- Yield multipliers reward longer commitments
- Credits are deployment tokens (no RSC value)
- Configurable burn fee on credit deployment
- B=f(P,E) behavioral model: Person attributes + Environment = Behavior
- Scenario save/compare for parameter exploration

**Note**: The complex "Process Fidelity" model with panel voting, slashing, and quality scores is in the separate `rsc-process-fidelity-abm` project.

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
# Open http://localhost:5000
```

## Interactive Dashboard

The web dashboard at `http://localhost:5000` provides:

**Sidebar Controls**

| Section | Contents |
|---------|----------|
| Parameters | Yield, Deploy Rate, Proposal Success, Stakers |
| Archetype Mix | Linked sliders (sum to 100%) with behavioral descriptions |
| Staking Tiers | Distribution bar across Flexible/3mo/6mo/12mo |
| Advanced | Burn Rate, Credit Expiry, Failure Mode, Min Stake |
| Scenarios | Save/Compare parameter runs side-by-side |
| How It Works | B=f(P,E) explanation, step-by-step mechanics |
| Design Questions | Open questions for ResearchHub discussion |

**Main Area (4 tabs)**
- **Agent Field**: Grid visualization showing each staker as a cell (color = archetype, opacity = satisfaction, glow = credit pressure). Hover for tooltip, click for details.
- **Time Series**: Staked/Credits/Burned over time
- **Proposals & Funding**: Proposal status and funding progress
- **Agent Inspector**: Individual staker deep-dive (Top Stakers, Recent Deployers, Tier Breakdown)

**Pinned KPIs**: RSC Staked, Satisfaction, Churned (always visible)

## Dashboard Parameters

The dashboard exposes these as sliders mapped to backend params:

| Slider | Range | Default | Backend param |
|--------|-------|---------|---------------|
| Yield | 1-25% | 10% | `base_apy` (/ 100) |
| Deploy Rate | 0-100% | 30% | `deploy_probability` (/ 100) |
| Proposal Success | 20-100% | 80% | `success_rate` (/ 100) |
| Stakers | 20-500 | 100 | `num_stakers` (int) |
| Burn Rate | 0.5-10% | 2% | `burn_rate` (/ 100) |

Archetype sliders (Believers/Yield Seekers/Governance/Speculators) are linked: adjusting one proportionally redistributes the others, always summing to 100% with a 5% minimum each.

## Behavioral Model

### B = f(P, E)

Each staker has **Person attributes** that interact with **Environment conditions** to produce behavior:

**Person attributes** (continuous 0-1 scales):
- `mission_alignment` - cares about funding research vs. earning yield
- `risk_tolerance` - willingness to back uncertain proposals
- `engagement` - how actively they participate
- `price_sensitivity` - reactivity to RSC price changes

### Archetypes

| Archetype | Behavior | Default Mix |
|-----------|----------|-------------|
| Believer | Mission-driven. Deploy eagerly, back risky research, stick around. | 25% |
| Yield Seeker | Return-focused. Deploy selectively, leave if returns disappoint. | 30% |
| Governance | Community-oriented. Moderate deployers, value ecosystem health. | 20% |
| Speculator | Short-term. Hoard credits, rarely deploy, first to churn. | 25% |

### Deployment Decision

`deploy_probability` acts as a scaling factor on the behavioral deployment decision:
- Base probability from engagement level
- Credit pressure boost (sigmoid, increases when credits accumulate)
- Satisfaction dampening (low satisfaction reduces willingness)
- Deploy scale = `deploy_probability / 0.3` (default 0.3 = no change)

## Staking Tiers

| Tier | Lock Period | Yield Multiplier |
|------|-------------|------------------|
| Flexible | None | 1.0x |
| 3-Month | 90 days | 1.5x |
| 6-Month | 180 days | 2.0x |
| 12-Month | 365 days | 3.0x |

## Credit Flow

1. **Generation**: Stakers earn credits at `stake * yield * tier_multiplier / 52` per step (week)
2. **Deployment**: Behavioral decision to deploy credits to proposals
3. **Fee**: Burn rate % of backing RSC burned on deployment
4. **Resolution**: Funded proposals complete or fail (success_rate probability)
5. **Satisfaction**: Updated from outcomes; affects future deployment and churn
6. **Churn**: Unsatisfied + unlocked stakers may leave

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init` | POST | Initialize model with parameters |
| `/api/step` | POST | Advance simulation by 1 step |
| `/api/run` | POST | Run N steps `{steps: 10}` |
| `/api/state` | GET | Get current model state |
| `/api/metrics` | GET | Get computed metrics |
| `/api/stakers` | GET | List all stakers |
| `/api/proposals` | GET | List all proposals |
| `/api/history` | GET | Time series data |
| `/api/tiers` | GET | List staking tiers |
| `/api/design-questions` | GET | Open design questions |

### Example Usage

```bash
# Initialize with custom parameters
curl -X POST http://localhost:5000/api/init \
  -H "Content-Type: application/json" \
  -d '{"num_stakers": 50, "base_apy": 0.15, "deploy_probability": 0.5}'

# Run 52 steps (1 year)
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"steps": 52}'

# Get metrics
curl http://localhost:5000/api/metrics
```

## Project Structure

```
rsc-endowment-abm/
├── src/
│   ├── __init__.py
│   ├── model.py        # EndowmentModel (Mesa ABM)
│   ├── agents.py       # EndowmentStaker, EndowmentProposal
│   └── constants.py    # Tiers, archetypes, design questions
├── templates/
│   └── index.html      # Single-page dashboard (HTML/CSS/JS)
├── server.py           # Flask REST API
├── requirements.txt
├── ARCHITECTURE.md     # System architecture with diagrams
└── README.md
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams.

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Server (server.py)                  │
│  /api/init  /api/step  /api/run  /api/state  /api/metrics  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   EndowmentModel (Mesa ABM)                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │EndowmentStaker   │  │EndowmentProposal │  │DataCollector│ │
│  │ - archetype      │  │ - funding_target │  │ - history  │ │
│  │ - stake / tier   │─▶│ - credits_recv   │  │ - metrics  │ │
│  │ - credits        │  │ - backers        │  └────────────┘ │
│  │ - satisfaction   │  │ - status         │                  │
│  │ - _should_deploy │  └──────────────────┘                  │
│  └─────────────────┘                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Interactive Dashboard (index.html)              │
│  Sidebar                    Main Area                       │
│  ┌──────────────┐  ┌─────────────────────────────────────┐  │
│  │ Parameters   │  │ Agent Field │ Time Series │ ...     │  │
│  │ Archetypes   │  │ ┌─────────────────────────────────┐ │  │
│  │ Staking Tiers│  │ │  Grid: color=arch, opacity=sat  │ │  │
│  │ Advanced     │  │ │  + archetype behavior cards      │ │  │
│  │ Scenarios    │  │ └─────────────────────────────────┘ │  │
│  └──────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Open Design Questions

The model surfaces these questions for ResearchHub team discussion:

1. **Credit Expiry**: Should credits expire if not deployed?
2. **Pooled vs Individual**: Individual staker deployment or common pool?
3. **Failure Consequences**: What happens when funded proposals fail?
4. **Yield Source**: Emissions vs revenue-funded?
5. **Success Criteria**: How is proposal success determined?

Access via `/api/design-questions`. Credit expiry and failure mode are explorable in the Advanced section.
