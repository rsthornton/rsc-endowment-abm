# RSC Endowment Simulator

An interactive simulator for [ResearchHub's](https://www.researchhub.com/) 2026 Endowment mechanism — built directly from RH's published product docs and yield model CSV.

### **[Try the Live Demo](https://rsc-endowment-abm-production.up.railway.app)** — no install required

Enter an endowment amount, pick a scenario, hit Run. Watch the market find its level.

---

## What it does

ResearchHub lets you hold RSC and earn yield automatically — no lockups, no staking. The yield comes as funding credits you deploy to research proposals. Your principal is never spent.

This simulator makes that mechanism tangible:

- **Enter** a dollar amount ($1M, $100K, whatever)
- **Choose** a starting scenario (Conservative 15% / Expected 30% / High 70% participation)
- **Run** the simulation — watch participation rate, APY, and holder behavior evolve over 4 years
- **See** what credits your endowment would generate, year 1 and cumulatively

The three scenarios are taken verbatim from RH's product doc. The emission schedule, circulating supply figures, and APY reference lines all come from RH's published yield model CSV.

---

## The mechanism, plainly

**Endowment simply:** you spend the interest, never the balance. Your RSC is permanent. The yield (funding credits) is what flows to research, year after year.

**Why yields self-balance:**
```
Your yield = your RSC ÷ total RSC held in RH × annual emissions
```
More people join → each person's share shrinks → yield falls.
People leave → shares grow → yield rises.
No one controls this. It's automatic. The simulator shows where the market settles.

**Emission schedule (from RH product doc):**
```
E(t) = 9,500,000 / 2^(t/64)   RSC/year, halving every 64 years
```

---

## What's grounded in RH docs vs. modeled

| Element | Source |
|---------|--------|
| 15% / 30% / 70% scenarios + APY values | RH Product Doc (verbatim) |
| Circulating supply by year (134.2M at Year 0…) | RH Yield Model CSV |
| Emission formula E(t) = 9.5M / 2^(t/64) | RH Product Doc |
| Time-weight multipliers (1.0× / 1.15× / 1.2×) | RH Product Doc |
| Self-balancing mechanic description | RH Product Doc |
| Holder archetypes — Institution, Yield Seeker | Closely derived from product doc use cases |
| Holder archetypes — Believer, Speculator | Inferred from mechanism descriptions |
| Behavioral parameters (exit thresholds, hold horizons) | Calibrated modeling assumptions |

Reference docs live in `docs/rh-reference/` — the product doc, community doc, and yield model CSV.

---

## Quick Start

The fastest path is the **[live demo](https://rsc-endowment-abm-production.up.railway.app)**.

To run locally:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
# Open http://localhost:5000
```

---

## Dashboard layout

The v3 dashboard is designed for accessibility first — a CFO and a grad student should both find it immediately usable.

**Top:** Framing strip — plain-English explanation of the mechanism, endowment definition, self-balancing math. Collapsed "Sources & grounding" section links every number back to its RH doc.

**Calculator hero:** Dollar input + three scenario cards (Conservative 15% / Expected 30% / High 70%) from RH product doc.

**Sim controls:** `⟳ Setup · ▶ +1 wk · +10 wk · +1 yr · ▶▶ Go / ■ Stop` — Go runs continuously in 4-week chunks until stopped. Tick counter shows current week and year.

**"What Happened" panel:** Appears after running. Plain-English narrative of what the market did — participation rate, which archetypes dominated, proposals resolved.

**Charts:**
- *Archetype Composition* — stacked RSC held by Believers / Institutions / Yield Seekers / Speculators over time. Shows the sticky base vs. volatile top.
- *Science Funding vs Protocol Cost* — weekly credits deployed to science (bars) vs. cumulative RSC emitted and burned (lines). Makes the sustainability gap visible.

**Right column:** Endowment projection — Year 1 credits, 10-year cumulative, Year 10 APY — plus a 10-year sparkline showing the gentle credit taper as emissions halve every 64 years. Updates live as you adjust the dollar amount.

**Agent grid:** Every dot is one RSC holder. Color = archetype. Opacity = hold duration (dim = new, bright = long-term 1.2×). Glow = actively deploying credits. Hover for individual stats.

**Accordions (collapsed by default):** Adjust the Scenario · Advanced Parameters · Data Tables · Detailed Time Series

---

## Holder archetypes

Four types derived from the RH product doc's described holder behaviors:

| Archetype | Grounding | Behavior |
|-----------|-----------|----------|
| **Institution** | Primary use case in product doc ("$1M of grants") | Large RSC, very long-term, near-zero yield sensitivity. Anchors participation. |
| **Yield Seeker** | Self-balancing section: "high yields attract more holders... low yields cause withdrawals" | Enters when APY is attractive, exits when it falls. The self-regulating force. |
| **Believer** | "These credits can only fund research — the more RSC you hold, the more science you fund" | Mission-driven. Holds through low yields. Deploys credits reliably. |
| **Speculator** | Inferred from CRV benchmark + DeFi "death spiral" passage | Short-term. Amplifies participation swings. Exits quickly on APY decline. |

---

## Self-balancing mechanic

1. High APY → Yield Seekers join → total RSC held increases → APY falls
2. Low APY → Yield Seekers exit → total RSC decreases → APY rises
3. Believers and Institutions hold throughout (mission-driven, long horizon)
4. Equilibrium emerges when exits ≈ entrants

The participation chart is the primary output — the simulation's job is to find where that line settles.

---

## Reference scenarios (from RH Yield Model CSV)

| Participation | RSC held in RH | Year 1 APY | Year 10 APY | RH label |
|---|---|---|---|---|
| 15% | ~20.1M RSC | ~47.2% | ~26.6% | Low participation |
| 30% | ~40.2M RSC | ~23.6% | ~13.3% | Anticipated average |
| 70% | ~93.9M RSC | ~10.1% | ~5.7% | High participation |

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init` | POST | Initialize model with parameters |
| `/api/step` | POST | Advance 1 week |
| `/api/run` | POST | Run N weeks `{"steps": 52}` |
| `/api/state` | GET | Current model state |
| `/api/holders` | GET | All holders |
| `/api/proposals` | GET | All proposals |
| `/api/history` | GET | Time series data |
| `/api/participation` | GET | Participation rate + reference scenarios |

---

## Project structure

```
rsc-endowment-abm/
├── src/
│   ├── model.py        # EndowmentModel — emissions engine, participation tracking
│   ├── agents.py       # EndowmentHolder (yield, exit dynamics), EndowmentProposal
│   └── constants.py    # TIME_WEIGHT_MULTIPLIERS, EMISSION_PARAMS, ARCHETYPES
├── templates/
│   └── index.html      # Single-page dashboard (HTML/CSS/JS, no build step)
├── docs/
│   └── rh-reference/   # RH product doc, community doc, yield model CSV
├── server.py           # Flask REST API
└── requirements.txt
```

Built with Python, [Mesa](https://mesa.readthedocs.io/) (ABM framework), Flask, and Chart.js.
