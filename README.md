# RSC Decentralized Endowment ABM

Agent-based model for RSC staking with **simple credit-based funding**.

## Overview

This model simulates the core endowment mechanism:

```
Stake RSC -> Earn Credits (APY) -> Deploy to Proposals -> 2% Burn
```

**Key features:**
- 4 staking tiers based on lock period (Flexible/3mo/6mo/12mo)
- APY multipliers reward longer commitments
- Credits are deployment tokens (no RSC value)
- 2% of backing RSC burned when credits deployed
- Simple binary proposal resolution (no panel voting)

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

**Simulation Controls**
- Step / Run 10 / Run 1 Year / Reset buttons
- Real-time metrics: Staked, Credits, Burned, Generation Rate, Deployment Rate

**Educational Features**
- 📖 **This Week's Activity**: Narrative explanation of what happened each step
- 🔍 **Agent Inspector**: Explore individual stakers (Top Stakers, Recent Deployers, Tier Breakdown)
- 📚 **How This Model Works**: Visual flow diagram and detailed mechanics explanation
- ❓ **Design Questions**: Open questions for ResearchHub team discussion

**Visualizations**
- Time series chart (Staked/Credits/Burned)
- Tier distribution bar
- Proposal funding progress
- Event log

## Model Mechanics

### Staking Tiers

| Tier | Lock Period | APY Multiplier |
|------|-------------|----------------|
| Flexible | None | 1.0x |
| 3-Month | 90 days | 1.5x |
| 6-Month | 180 days | 2.0x |
| 12-Month | 365 days | 3.0x |

Base APY: 10% (configurable)

### Credit Flow

1. **Generation**: Stakers earn credits at `stake * APY * tier_multiplier / 52` per step (week)
2. **Deployment**: Stakers deploy credits to fund proposals
3. **Burn**: 2% of proportional backing RSC burned on deployment
4. **Resolution**: Funded proposals complete or fail (80% success probability)

### Proposals

- Have a funding target (in credits)
- Status: `open` -> `funded` -> `completed`/`failed`
- No researcher stake required (unlike Process Fidelity model)

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
  -d '{"num_stakers": 50, "base_apy": 0.15}'

# Run 20 steps
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"steps": 20}'

# Get metrics
curl http://localhost:5000/api/metrics
```

## Key Metrics

1. **Total Staked** - RSC locked across all tiers
2. **Credit Generation Rate** - Credits/step
3. **Deployment Rate** - Credits deployed/step
4. **Burn Rate** - RSC burned per step
5. **Tier Distribution** - Staker counts by tier
6. **Success Rate** - % of proposals that complete

## Project Structure

```
rsc-endowment-abm/
├── src/
│   ├── __init__.py
│   ├── model.py      # EndowmentModel
│   ├── agents.py     # EndowmentStaker, EndowmentProposal
│   └── constants.py  # Tiers, design questions
├── templates/
│   └── index.html    # Interactive dashboard with educational features
├── server.py         # Flask REST API
├── requirements.txt
├── README.md
├── CLAUDE.md
└── rsc-staking-project-background.md
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Server (server.py)                  │
│  /api/init  /api/step  /api/run  /api/state  /api/stakers  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   EndowmentModel (Mesa ABM)                  │
│  ┌───────────────┐    ┌───────────────┐    ┌─────────────┐ │
│  │ EndowmentStaker│    │EndowmentProposal│  │ DataCollector│ │
│  │ - stake        │───▶│ - funding_target│  │ - history   │ │
│  │ - tier         │    │ - credits_recv  │  │ - metrics   │ │
│  │ - credits      │    │ - backers       │  └─────────────┘ │
│  │ - deploy()     │    │ - status        │                   │
│  └───────────────┘    └───────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Interactive Dashboard (index.html)              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────────┐│
│  │ Metrics │ │ Charts  │ │ Agents  │ │ Educational Content ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Open Design Questions

The model surfaces these questions for ResearchHub team discussion:

1. **Credit Expiry**: Should credits expire if not deployed?
2. **Pooled vs Individual**: Individual staker deployment or common pool?
3. **Failure Consequences**: What happens when funded proposals fail?
4. **Yield Source**: Emissions vs revenue-funded?
5. **Success Criteria**: How is proposal success determined?

Access via `/api/design-questions`.
