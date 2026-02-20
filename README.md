# RSC Decentralized Endowment ABM

An interactive agent-based model simulating [ResearchHub's](https://www.researchhub.com/) 2026 Endowment mechanism. Adjust population parameters, watch the self-balancing yield mechanic play out, and explore what participation rate equilibrates — all in your browser.

### **[Try the Live Demo](https://rsc-endowment-abm-production.up.railway.app)** — no install required

Built with Python, [Mesa](https://mesa.readthedocs.io/) (ABM framework), Flask, and Chart.js.

## Overview

This model simulates the real RH Endowment mechanism:

```
Hold RSC in RH account → Passive yield (dilution-based) → Deploy credits to Research Proposals
```

**No lockups. No staking action required.** RSC held in a ResearchHub account automatically earns yield proportional to your share of total held RSC.

**Yield formula:**
```
Weekly yield = (your RSC / total RSC in RH) × weekly_emission × time_weight_multiplier
Annual emission: E(t) = 9,500,000 / 2^(t/64)   [halves every 64 years]
```

**Primary design question:** What participation rate (% of circulating RSC held in RH) does the market equilibrate to?

**Key features:**
- Self-balancing yield: more RSC → lower APY → yield seekers exit → APY recovers → new entrants join
- 4 behavioral archetypes (Believers, Yield Seekers, Institutions, Speculators)
- Time-weight multipliers (1.0x → 1.15x → 1.2x) reward continuous holding
- Decaying emission schedule matched to RH's actual plan (9.5M RSC/yr, year 0)
- Participation rate as the primary emergent output — not a fixed input
- New entrant spawning: yield seekers re-enter when APY rises above their threshold
- B=f(P,E) behavioral model: Person attributes × Environment = Behavior
- Scenario save/compare for exploring equilibrium under different archetype mixes

**Reference docs**: `docs/rh-reference/` — 5 files from RH's product doc, community doc, and yield model CSV

## Quick Start

The fastest way to explore is the **[live demo](https://rsc-endowment-abm-production.up.railway.app)**.

To run locally:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
# Open http://localhost:5000
```

## Interactive Dashboard

**Sidebar Controls**

| Section | Contents |
|---------|----------|
| Parameters | Yield Threshold, Deploy Rate, Proposal Success, Holders |
| Archetype Mix | Linked sliders (sum to 100%) with behavioral descriptions |
| Time-Weight Multipliers | Distribution bar (New/Holder/LongTerm) |
| Advanced | Burn Rate, Credit Expiry, Failure Mode |
| Scenarios | Save/Compare parameter runs side-by-side |
| How It Works | Mechanism explanation, self-balancing description |

**Main Area (5 tabs)**
- **Agent Field**: Grid visualization. Color = archetype, opacity = holding duration (LongTerm holders glow at full opacity). Hover for tooltip.
- **Yield Dynamics**: APY over time with 15%/30%/70% reference lines from RH's CSV model. Participation rate trajectory.
- **Time Series**: RSC held, credits, burned over time
- **Proposals & Funding**: Proposal status and funding progress
- **Agent Inspector**: Individual holder deep-dive (Top Holders, Deployers, By Archetype, Exited)

**Pinned KPIs**: Participation Rate, Current APY, Exited (always visible)

## Self-Balancing Mechanic

The core equilibrium dynamic:

1. High APY → Yield Seekers join → total RSC increases → APY falls
2. Low APY → Yield Seekers exit (below their `yield_threshold`) → total RSC decreases → APY rises
3. Believers and Institutions stay throughout (mission-driven, high hold_horizon)
4. Equilibrium emerges when exits ≈ entrants

The `yield_threshold_mean` slider controls the average APY below which agents exit — this is the primary lever for the equilibrium participation rate.

## Behavioral Model

### B = f(P, E)

Each holder has **Person attributes** that interact with **Environment conditions** to produce behavior:

**Person attributes** (continuous 0-1 scales):
- `mission_alignment` - cares about funding research vs. earning yield
- `engagement` - how actively they deploy credits to proposals
- `price_sensitivity` - reactivity to APY changes (drives exit decisions)
- `hold_horizon` - tendency toward long-term holding (dampens exits)

**Environment**:
- `current_apy` - annual yield at current participation rate
- `yield_threshold` - personal minimum APY to stay (agent-specific)

### Archetypes

| Archetype | Behavior | Default Mix | Hold Horizon |
|-----------|----------|-------------|--------------|
| Believer | Mission-driven. Holds long-term, deploys credits reliably. | 25% | High |
| Yield Seeker | Return-focused. Enters when APY is attractive, exits when it falls. | 30% | Medium |
| Institution | Large RSC stake (universities, foundations). Very long-term. Reaches 1.2x multiplier. | 20% | Very high |
| Speculator | Short-term. Deploys rarely, exits quickly on APY decline. | 25% | Low |

### Time-Weight Multipliers

Continuous holding duration determines the multiplier (no lockups — just time):

| Tier | Duration | Multiplier |
|------|----------|-----------|
| New | < 4 weeks | 1.00x |
| Holder | 4 weeks – 1 year | 1.15x |
| LongTerm | > 1 year | 1.20x |

Effective share = `(your RSC × your multiplier) / sum(all RSC × multipliers)`

## Credit Flow

1. **Earn**: Each week, earn credits = `weekly_emission × (effective_RSC / total_effective_RSC)`
2. **Deploy**: Behavioral decision to deploy credits to open proposals
3. **Burn**: 2% of backing RSC burned on deployment
4. **Resolve**: Funded proposals complete or fail (success_rate probability)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init` | POST | Initialize model with parameters |
| `/api/step` | POST | Advance simulation by 1 step (1 week) |
| `/api/run` | POST | Run N steps `{"steps": 52}` |
| `/api/state` | GET | Current model state |
| `/api/metrics` | GET | Computed metrics |
| `/api/holders` | GET | List all holders |
| `/api/proposals` | GET | List all proposals |
| `/api/history` | GET | Time series data |
| `/api/multipliers` | GET | Time-weight multiplier tiers |
| `/api/participation` | GET | Participation rate + reference scenarios (15%/30%/70%) |

### Example Usage

```bash
# Initialize: 100 holders, yield threshold 8%, starting at 30% participation
curl -X POST http://localhost:5000/api/init \
  -H "Content-Type: application/json" \
  -d '{"num_holders": 100, "yield_threshold_mean": 0.08, "initial_participation_rate": 0.30}'

# Run 1 year
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"steps": 52}'

# Check equilibrium
curl http://localhost:5000/api/participation
```

## Project Structure

```
rsc-endowment-abm/
├── src/
│   ├── __init__.py
│   ├── model.py        # EndowmentModel (emissions engine, participation tracking)
│   ├── agents.py       # EndowmentHolder (passive yield, exit dynamics), EndowmentProposal
│   └── constants.py    # TIME_WEIGHT_MULTIPLIERS, EMISSION_PARAMS, ARCHETYPES
├── templates/
│   └── index.html      # Single-page dashboard (HTML/CSS/JS)
├── docs/
│   └── rh-reference/   # RH product doc, community doc, yield CSV (5 files)
├── server.py           # Flask REST API
├── requirements.txt
├── ARCHITECTURE.md     # System architecture with Mermaid diagrams
└── README.md
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams.

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Server (server.py)                  │
│  /api/init  /api/step  /api/run  /api/participation  ...   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   EndowmentModel (Mesa ABM)                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │EndowmentHolder   │  │EndowmentProposal │  │DataCollector│ │
│  │ - archetype      │  │ - funding_target │  │ - history  │ │
│  │ - rsc_held       │─▶│ - credits_recv   │  │ - metrics  │ │
│  │ - weeks_held     │  │ - backers        │  └────────────┘ │
│  │ - yield_threshold│  │ - status         │                  │
│  │ - _consider_exit │  └──────────────────┘                  │
│  └─────────────────┘                                         │
│                                                              │
│  weekly_emission() → E(t) = 9.5M / 2^(t/64)               │
│  participation_rate → total_rsc_held / circulating_supply   │
│  current_apy() → annual_emission / total_rsc_held           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Interactive Dashboard (index.html)              │
│  Sidebar                    Main Area                       │
│  ┌──────────────┐  ┌─────────────────────────────────────┐  │
│  │ Parameters   │  │ Agent Field │ Yield Dynamics │ ...  │  │
│  │ Archetypes   │  │ ┌─────────────────────────────────┐ │  │
│  │ Multipliers  │  │ │  Grid: color=arch, opacity=dur  │ │  │
│  │ Advanced     │  │ │  + archetype behavior cards      │ │  │
│  │ Scenarios    │  │ └─────────────────────────────────┘ │  │
│  └──────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Reference Scenarios (from RH Yield Model CSV)

At different participation rates (% of 134M circulating RSC):

| Participation | RSC Held | Year 0 APY | Year 5 APY | Year 10 APY |
|---|---|---|---|---|
| 15% | ~20.1M RSC | ~47.3% | ~33.5% | ~23.7% |
| 30% | ~40.2M RSC | ~23.6% | ~16.7% | ~11.8% |
| 70% | ~93.9M RSC | ~10.1% | ~7.2% | ~5.1% |

See `/api/participation` for these reference lines, and the Yield Dynamics tab to compare your simulation against them.
