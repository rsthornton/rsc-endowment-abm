# RSC Staking Project — Complete Background

*A comprehensive record for migration to local Claude Code environment*

---

## Table of Contents

1. [Origin Story](#origin-story)
2. [The Problem](#the-problem)
3. [The Solution: Process Fidelity Staking](#the-solution-process-fidelity-staking)
4. [Building the ABM](#building-the-abm)
5. [Key Findings](#key-findings)
6. [Community Engagement](#community-engagement)
7. [Token Talk Session](#token-talk-session)
8. [The Decentralized Endowment Model](#the-decentralized-endowment-model)
9. [Technical Artifacts](#technical-artifacts)
10. [Open Questions](#open-questions)
11. [Philosophical Context](#philosophical-context)

---

## Origin Story

### Initial Spark

The project began with a fundamental question: **Which crypto projects have actually succeeded by focusing on real problems rather than tokenomic theater?**

Examining top examples (Liquity, MakerDAO, Chainlink, Aave), a pattern emerged: simple fee → token holder mechanisms beat elaborate game-theoretic constructions. The best tokens are *required* for some unavoidable action, not optional.

### Connection to ResearchHub

ResearchHub caught attention because:
- Real mission (open science)
- Functioning platform (published papers, funding mechanism)
- Struggling tokenomics despite solid fundamentals
- Active team considering staking for 2026 roadmap

Jeff Koury's Discord announcement was the catalyst:
> "To be clear, RSC is instrumental in the success of ResearchHub and are thus looking to lean into giving it more utility. Staking on funding proposals is looking to be a big part of the plan for 2026, and we'll discuss that on the next token-talk call next week"

---

## The Problem

### RSC Structural Issues

| Issue | Description |
|-------|-------------|
| **No buying pressure** | No mechanism forces users to acquire RSC |
| **No lock-up** | RSC can be sold immediately; no holding incentive |
| **APC disconnect** | Article Processing Charge revenue doesn't flow to token holders |
| **Speculation dominance** | Price tracks crypto market, not platform usage |

### Current State (January 2026)

- Total Supply: 1B RSC
- Circulating: ~130M (13%)
- Holders: ~9,400 addresses
- Price: ~$0.14
- Top 10 addresses hold 93.66% (Gini ~0.93)
- Reviewer earnings: ~1,000 RSC (~$150) per review

### Existing Positive

ResearchHub already burns 100% of platform fees (2% on funding/bounties) weekly. This creates some deflation but doesn't solve the lock-up problem.

**Burn Data Analysis (Aug 2025 - Jan 2026):**
- Total Burned: ~97,000 RSC (~$13,400 USD)
- Average per week: ~4,850 RSC (~$670)
- Highly variable: spikes up to 71K RSC in single week
- Burns correlate with platform activity (good sign for fundamental value)

---

## The Solution: Process Fidelity Staking

### The Key Insight

Most DeSci tokenomics fail because they try to stake on *outcome quality* — which is subjective, slow to measure, and recreates publication bias.

**The move is to stake on process fidelity:** Did you do what you said you'd do?

This is:
- Binary (yes/no)
- Verifiable (against preregistered protocol)
- Outcome-agnostic (null results can pass)

### The Mechanism

```
PROPOSAL LIFECYCLE

1. SUBMISSION
   └── Researcher stakes RSC + Funders back proposal

2. EXECUTION (3+ weeks)
   └── Research conducted per preregistered protocol

3. RESOLUTION
   └── Random 5-person panel evaluates process fidelity
   └── 4/5 supermajority required for Pass/Fail
   └── Otherwise: Partial (no consensus)

4. SETTLEMENT
   ├── PASS → Stake returned + yield
   ├── FAIL → Stake burned
   └── PARTIAL → 70% refund (30% burned)
```

### Process Fidelity Checklist

All binary. All verifiable.

- □ Followed preregistered protocol
- □ Published results (positive, negative, or null)
- □ Deposited raw data to open repository
- □ Shared analysis code
- □ Met timeline (or documented extensions)

**None of these depend on result direction.**

### The Ethereum Parallel

This is Ethereum Proof-of-Stake adapted for science:
- Validators (panelists) stake tokens to participate
- Earn rewards for honest consensus
- Get slashed for deviation from majority

Rhetorical anchor: "This is how Ethereum secures $400B, adapted for scientific consensus."

---

## Building the ABM

### Why an Agent-Based Model?

To stress-test the mechanism before implementation:
- Explore parameter space
- Surface failure modes
- Generate data for discussion
- Make trade-offs visible

### Evolution

| Version | Key Features |
|---------|--------------|
| v1-v4 | Basic simulation, event log, agent inspection |
| v5 | Real RSC calibration, 6 scenarios, power-law wealth |
| v6 | Price model, comparison tab, documentation |
| v7 | minRscForPanel requirement, encoding fixes, light mode default |

### Agent Types

- **Researchers** (50): Submit proposals, stake RSC
- **Funders** (30): Back proposals with stakes
- **Panelists** (100): Vote on resolutions, earn rewards or get slashed

### Scenarios

| Scenario | What It Tests |
|----------|---------------|
| Baseline | Normal operation |
| Sybil Attack | 50% dishonest panelists |
| High Stakes | 5x stake requirement |
| Low Incentive | ¼ vote rewards |
| Whale Capture | 3 funders control 80% |
| Bootstrap | Small panel pool (40) |

### Price Model

Simplified supply/demand for directional reasoning:

- **Buy Pressure**: New stakes + fundings (agents must acquire RSC)
- **Sell Pressure**: ~60% of rewards sold immediately
- **Burns**: Failed proposals + slashing = permanent supply reduction
- **Lock-ups**: Active proposals reduce effective circulating supply
- **External Demand**: Baseline grows 0.2%/week (adoption curve)

---

## Key Findings

### Scenario Comparison (~100 weeks)

| Scenario | Price Δ | Pass % | Gainers | Losers | Big Winners | Gini |
|----------|---------|--------|---------|--------|-------------|------|
| **High Stakes** | +766-882% | 68-82% | 71-89 | 26-37 | 39-43 | 0.327 |
| Bootstrap | +207-393% | 90-96% | 32-49 | 14-23 | 20-26 | 0.41-0.44 |
| Baseline | +293-342% | 38-84% | 54-79 | 16-53 | 3-36 | 0.36-0.37 |
| Sybil Attack | +138-324% | 38-71% | 52-53 | 29-61 | 13-29 | 0.371 |
| Whale Capture | +198-379% | 84-85% | 68-76 | 22-44 | 18-35 | 0.531 |
| Low Incentive | +201-344% | 54-93% | 56-68 | 13-56 | 3-8 | 0.38-0.40 |

### Core Insights

1. **Slashing works** — Sybil attacks are self-limiting; dishonest actors fund their own removal. 50% dishonest panelists only moved metrics ~5%. Extra burns "eat" the attackers.

2. **High Stakes wins everything** — Better price, pass rate, more winners, lower inequality. The selection effect filters for quality (only confident researchers submit).

3. **Low Incentive breaks panelists** — Only funders profit; reviewers earn ~$1.50/week. 93% pass rate but only 8 "big winners" vs 43 in High Stakes.

4. **Bootstrap is viable** — 96% pass rate with only 40 panelists; small communities can start.

5. **Whale Capture increases Gini** — System works but wealth concentrates (0.53 vs 0.36). Cartel dynamics possible.

### Deeper Observations

6. **Pass rate degrades over time** — 75-82% at 20 weeks → 38% at 100 weeks. Good researchers run out of RSC; quality declines as pool exhausts.

7. **"House always wins" dynamic** — Token holders gain +342% by doing nothing; active participants break even on average. Value flows to burns (deflation), not to participants.

8. **50% partial rate problem** — Half of all proposals get no consensus. Researchers slowly bleed RSC on inconclusive results (70% refund = 30% loss each time).

9. **Panelist RSC requirement** — v7 adds `minRscForPanel: 500` to ensure panelists have skin in the game. Without this, broke panelists can vote randomly with zero risk.

### Who Profits?

In most scenarios:
- **Funders** capture most upside (yield scales with stake size)
- **High-honesty panelists** profit modestly through consistent voting
- **Researchers** break even on average (high variance)

In High Stakes:
- More researchers profit (selection effect)
- 2.6:1 gainers:losers ratio (vs 1:1 in baseline)

---

## Community Engagement

### Discord Post (Monday, Week of Token Talk)

```
__**Process Fidelity Staking — a quick simulation**__

Hey all, I've been thinking about how staking might work for RSC. 
Built a rough agent-based model to stress-test one idea: stake on 
process fidelity (did the researcher do what they said?) rather 
than outcomes.

Ran 100-week sims across 6 scenarios.

Takeaways:
• Higher stakes = more skin in the game = better price performance
• Low rewards trap: high pass rate but almost nobody profits
• Sybil attacks don't break the system — dishonest agents get filtered out
• Whale concentration is real — 95% pass rate + 0.56 gini = cartel dynamics

This is a ***thinking tool***, not a proposal. Rapidly vibe-coded 
with Claude to help me start exploring the design space.

https://claude.ai/public/artifacts/7d521924-a6be-4cd4-acc0-1f8c82348db3
```

### Reception

**Immediate positive feedback from ResearchHub team:**
- Patrick Joyce: emoji reaction
- Ruslan Rust: emoji reaction

This was significant because the team "doesn't hand out positive feedback lightly — they are no nonsense."

The honest framing paid off — positioned as a "thinking tool" rather than a finished proposal, but the rigor showed through (real data calibration, multiple scenarios, surfacing uncomfortable truths).

---

## Token Talk Session

### ResearchHub 2026 Strategy (from call notes)

**Two main focuses:**

1. **Funding feature** — most successful revenue driver
   - First months: improve onboarding UX ("horrible and embarrassing")
   - Enable easy deposit: RSC, bank transfer, credit card, stablecoin
   - Volatility protection for traditional funders

2. **RSC token utility beyond current functionality**
   - Staking as leading contender
   - Stake RSC → receive "funding credits"
   - Credits must be spent on funding proposals
   - Functions like "decentralized endowment"
   - 2% burn continues when credits deployed

### Business Goals

- **$14-15 million** in funding needed to break even
- 7% fee structure generates revenue
- 10x increase from last year
- Achievable with 5-7 major funders

### Additional Revenue Experiments

1. **Prediction markets** tied to pre-registered proposals
2. **Crypto asset issuance** for funded projects (tokens/NFTs)
3. **Third-party lab recruitment** (separates design from execution)

### Key Outcomes

- ResearchHub expressed enthusiasm for collaboration
- Coordination with Tyler arranged
- Governance: 72-hour Discord discussion + Snapshot vote
- Technical preference: in-app implementation first (not smart contract)
- Allows tiered APY based on staking duration

### Convergences and Divergences

| Process Fidelity Model | Their Current Thinking |
|------------------------|------------------------|
| Stake on *proposals* with panel resolution | Stake RSC → receive *funding credits* |
| Panelists earn/get slashed | Stakers earn yield, must deploy to funding |
| Focus: honest peer review at scale | Focus: token lock-up + funding flywheel |

These aren't incompatible — they could layer. Their version creates lock-up and buy pressure. The process fidelity approach addresses *how funded proposals get evaluated*.

---

## The Decentralized Endowment Model

### Their Vision

```
Stake RSC → Earn Credits (APY) → Deploy to Proposals → 2% Burn
```

This is simpler than process fidelity staking but addresses same core issues:
- Creates lock-up
- Creates buy pressure (need RSC to stake)
- Burns on deployment (deflation)
- "Decentralized endowment" framing (you control where yield goes)

### Built Second ABM for Tyler Conversation

Scaffolded a "Decentralized Endowment ABM" with:
- 4 staking tiers (Flexible, 3mo, 6mo, 12mo)
- APY multipliers for longer locks
- Credit generation and deployment mechanics
- Design Questions tab surfacing open decisions

### Open Design Questions

1. **Success Criteria**: What determines if a funded proposal "succeeded"?
2. **Deployment Model**: Individual choice vs. pooled fund vs. hybrid?
3. **Failure Consequences**: What happens when proposals fail?
4. **Credit Expiry**: Do undeployed credits expire? (Use-it-or-lose-it?)
5. **Yield Source**: Emissions vs. platform revenue vs. hybrid?

### Flask/Mesa Migration

If serious interest in using ABM as design tool, Python/Flask migration planned:
- Proper statistical runs (100+ trials, confidence intervals)
- Sensitivity analysis (parameter sweeps)
- Better data persistence
- Integration with actual RSC on-chain data

**Package created:** `rsc-endowment-abm.zip` with:
- Mesa model architecture
- Flask REST API
- Batch runner for headless simulations
- pytest test suite
- Full documentation (README, CLAUDE.md, ARCHITECTURE.md)

---

## Technical Artifacts

### Files Created

| File | Description |
|------|-------------|
| `rsc_staking_abm_v7.jsx` | Process Fidelity Staking ABM (React, 1768 lines) |
| `rsc_endowment_abm_v1.jsx` | Decentralized Endowment ABM (React) |
| `rsc-endowment-abm.zip` | Flask/Mesa migration package |
| `rsc-project-orientation.md` | Claude context file |
| `rsc-staking-abm-v6-docs.md` | Technical documentation |
| `rsc-staking-proposal-final.md` | Mechanism proposal |
| `abm-prototyper-skill.zip` | Reusable Claude skill for future ABMs |

### ABM Prototyper Skill

Created reusable skill for building future agent-based models:
- YAML frontmatter for Claude.ai upload
- Design patterns document
- Template JSX with all standard features
- Uploaded to `/mnt/skills/user/abm-prototyper/`

### Public Artifact

Published simulation accessible at:
`https://claude.ai/public/artifacts/7d521924-a6be-4cd4-acc0-1f8c82348db3`

---

## Open Questions

### Mechanism Design

1. **Collusion modeling** — Current model doesn't capture coordinated panel attacks
2. **Appeals mechanism** — What happens with disputed resolutions?
3. **Stake governance** — How to adjust RSC stakes as price appreciates?
4. **Cross-hub judging** — How to handle interdisciplinary proposals?

### Stake Governance Proposal

Fixed RSC stakes become barriers as price appreciates:

| RSC Price | Adjusted Stake | USD Value |
|-----------|----------------|-----------|
| $0.14 | 5,000 RSC | $700 |
| $0.50 | 1,500 RSC | $750 |
| $1.00 | 750 RSC | $750 |
| $2.00 | 400 RSC | $800 |

Quarterly governance reviews 30-day average price and adjusts.

### Integration Questions

- How does staking compound with existing 2% fee burns?
- Integration with existing reputation system?
- Timeline for governance vote?

---

## Philosophical Context

### The Decoupling Question

**Can staking help RSC decouple from broader crypto market?**

**Partial yes.** The mechanism creates:
- **Forced demand** (researchers need RSC to participate)
- **Lock-ups** (can't panic sell staked tokens)
- **Burns** (failed proposals + slashing = permanent supply reduction)
- **Utility users** (platform users hold regardless of BTC)

Combined with existing fee burns, this creates a **demand floor** based on platform activity, not speculation.

Full decoupling is impossible (liquidity crises affect everything), but fundamental value can matter on the margin. A demand floor based on researchers needing RSC to participate is real utility.

### Why This Matters

> "Most token design is solving fake problems or just creating new speculation vehicles. This is different."

**The actual hard problem**: How do you create credible, scalable peer review without central authority?

- Traditional publishing is broken (publication bias, slow, captured)
- Pure reputation systems get gamed
- Pure pay-to-play creates conflicts

**Why staking might work**: You're importing the PoS insight — make honesty the economically dominant strategy — into a domain where "truth" is hard to define. Process fidelity sidesteps the "what is good science" question.

### The Hope

> "We might finally be at the point where [utility-driven tokens] are possible."

2017-2023 was infrastructure building. Now the rails exist:
- Fiat on-ramps that don't require a PhD
- Institutional custody
- Regulatory frameworks emerging
- Wallets that hide the blockchain

If researchers *must* stake to participate, and the UX is clean enough that they don't notice the blockchain... that's the play.

### Managing Speculators

When token goes up, speculators flood Discord. The classic tension: you want their liquidity, not their opinions.

**Mechanisms that take their money but not their voice:**
- REP-gated governance (token holdings don't vote)
- Time-locked voting (lock 6-12 months for governance power)
- Burn mechanics (give them "number go up" dopamine via deflation)
- Utility requirements (must actively use platform for certain benefits)

---

## Appendix: Chat Summary

### Chat 1: "rsc staking sim" (3 days ago)
- Initial brainstorming on crypto projects and RSC tokenomics
- Identified structural problems with RSC
- Developed Process Fidelity Staking concept
- Built ABM v1-v6 iteratively
- Created orientation doc and ABM prototyper skill
- Analyzed RSC burn data

### Chat 2: "Continuing RSC staking project work" (2 hours ago)
- Confirmed context transfer worked
- Fixed v7 with minRscForPanel and encoding
- Crafted Discord post
- Shared artifact publicly
- Received positive team feedback
- Discussed next steps and Python migration

### Chat 3: "Simulation project interrupted by chat limit" (1 hour ago)
- Built Decentralized Endowment ABM
- Chat limit hit during development

### Chat 4: "Chat limit reached with artifacts created" (43 minutes ago)
- Recovered artifacts from interrupted chat
- Began Flask/Mesa migration documentation

### Chat 5: "RSC Decentralized Endowment ABM migration to Flask/Mesa" (25 minutes ago)
- Completed Flask/Mesa package
- Created full project structure
- Generated rsc-endowment-abm.zip

---

*Document created January 14, 2026*
*For migration to local Claude Code environment*
