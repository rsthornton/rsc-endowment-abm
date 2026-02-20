# RH Endowment Reference Files

These 5 files describe ResearchHub's actual 2026 Endowment mechanism. They are the ground truth for
the redesigned simulation model.

---

## Files

### `ResearchHub Endowments [RHF Community].docx.md` / `.pdf`
**What it is**: Community-facing overview document. Describes the endowment concept, goals, and
high-level mechanism for the ResearchHub Foundation community.

**Key concepts for model**:
- Endowments allow RSC holders to earn yield by keeping RSC in RH accounts
- No lockups — time-weighted multipliers reward long-term holding
- Yield is dilution-based, not fixed APY

### `ResearchHub Endowment - Product Doc [RHF Community].docx.md` / `.pdf`
**What it is**: Technical product specification. The primary source for simulation parameters.

**Key mechanisms**:
- **Yield formula**: `(your RSC / total RH RSC) × annual emissions`
- **Time-weight multipliers**: 1.0x (new, <4 weeks), 1.15x (holder, 4wk–1yr), 1.20x (long-term, >1yr)
- **Emission schedule**: `E(t) = 9,500,000 / 2^(t/64)` — halves every 64 years
- **Burn trigger**: 2% on RH Foundation transactions
- **Participation is passive**: RSC in account auto-earns, no staking action required

**Design questions being explored**:
1. What participation rate equilibrates in the market?
2. How do multipliers affect long-term holding vs. churning?
3. What does the ecosystem look like with different holder mixes?
4. How quickly does yield self-balance after participation shifts?
5. Year-over-year yield trajectories at different equilibrium participation rates?

### `ResearchHub Endowment Yield Model [RHF Community] - Yearly returns over 10 years.csv`
**What it is**: Spreadsheet model built by RH team showing expected yearly returns across
different participation scenarios (15%, 30%, 70% of circulating supply).

**Key parameters extracted**:
- Total RSC supply: 1,000,000,000
- Year 0 circulating supply: 134,157,343
- Year 0 annual emission: 9,500,000 RSC
- Emission half-life: 64 years

**Use for model verification**: Compare APY outputs at 15%/30%/70% participation against CSV ground truth.

---

## Model-to-Reference Mapping

| Model Component | Source |
|---|---|
| `EMISSION_PARAMS` | Product Doc + CSV |
| `TIME_WEIGHT_MULTIPLIERS` | Product Doc |
| `ARCHETYPES` | Product Doc (holder types described) |
| APY formula in `model.py` | Product Doc yield formula |
| Participation rate KPI | Product Doc design questions |
| CSV scenario lines in dashboard | CSV file |
