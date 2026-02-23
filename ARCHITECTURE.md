# Architecture

## System Overview

```mermaid
graph TB
    subgraph Browser["Browser (index.html)"]
        UI[Dashboard UI]
        JS[JavaScript Engine]
    end

    subgraph Server["Flask Server (server.py)"]
        API[REST API]
    end

    subgraph Model["Mesa ABM (src/)"]
        EM[EndowmentModel]
        EH[EndowmentHolder]
        EP[EndowmentProposal]
        DC[DataCollector]
        CT[Constants & Archetypes]
    end

    UI -->|fetch /api/*| API
    API -->|JSON response| UI
    API --> EM
    EM --> EH
    EM --> EP
    EM --> DC
    CT --> EH
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant S as Flask Server
    participant M as EndowmentModel

    U->>D: Adjust sliders + click Apply & Reset
    D->>S: POST /api/init {params}
    S->>M: EndowmentModel(**params)
    M-->>S: Model initialized
    S-->>D: {state, events}

    U->>D: Click Go (or +1 wk / +10 wk / +1 yr)
    D->>S: POST /api/run {steps: N}
    loop Each step (1 week)
        S->>M: model.step()
        Note over M: weekly_emission() = E(t)/52
        Note over M: Earn credits (dilution-based)
        Note over M: Deployment decisions
        Note over M: Proposal resolution
        Note over M: Exit decisions (yield vs threshold)
        Note over M: Spawn new entrants (if APY attractive)
    end
    S-->>D: {state, events, history}
    D->>D: Render grid, charts, metrics
```

## Emissions Engine

```mermaid
graph LR
    T[Step count t] --> YR[t_years = t / 52]
    YR --> AE["annual_emission = 9,500,000 / 2^(t_years/64)"]
    AE --> WE[weekly_emission = annual / 52]
    WE --> SHARE[× my_effective_share]
    SHARE --> CREDITS[Credits earned this week]
```

## Yield & Participation Rate

```mermaid
graph LR
    HELD[Total RSC held in RH] --> APY["current_apy = annual_emission / total_rsc_held"]
    CS[Circulating supply] --> PR["participation_rate = total_rsc_held / circulating"]
    APY --> EXIT{APY < yield_threshold?}
    EXIT -->|Yes| EXITHOLDER[Holder exits]
    EXIT -->|No| STAY[Holder stays]
    EXITHOLDER --> HELD
    APY --> ENTRY{APY > entry_threshold?}
    ENTRY -->|Yes| SPAWN[New yield seeker enters]
    SPAWN --> HELD
```

## Self-Balancing Mechanic

```mermaid
graph LR
    HP[High participation] --> LAPY[Low APY]
    LAPY --> EXITYS[Yield Seekers exit]
    EXITYS --> LP[Lower participation]
    LP --> HAPY[Higher APY]
    HAPY --> ENTRANTS[New entrants spawn]
    ENTRANTS --> HP

    BELIEVERS[Believers + Institutions] -->|Never exit| EQ[Stable floor]
```

## Behavioral Model: B = f(P, E)

```mermaid
graph LR
    subgraph Person["Person Attributes (P)"]
        MA[Mission Alignment]
        EN[Engagement]
        PS[Price Sensitivity]
        HH[Hold Horizon]
        YT[Yield Threshold]
    end

    subgraph Environment["Environment (E)"]
        APY[Current APY]
        WE[Weekly Emission]
        TRSW[Total Effective RSC]
        DP[Deploy Probability]
        CP[Credit Pressure]
    end

    subgraph Behavior["Behavior (B)"]
        DEP[Deploy credits?]
        SEL[Select proposal]
        EXIT[Exit? Pull RSC?]
    end

    MA --> DEP
    EN --> DEP
    CP --> DEP
    DP --> DEP

    MA --> SEL

    APY --> EXIT
    YT --> EXIT
    PS --> EXIT
    HH --> EXIT
```

## Deployment Decision (_should_deploy)

```mermaid
graph TD
    A[Credits > 0?] -->|No| Z[Don't deploy]
    A -->|Yes| B[base_prob = engagement * 0.6]
    B --> C[pressure_boost = sigmoid of credit accumulation]
    C --> D["deploy_scale = deploy_probability / 0.3"]
    D --> F["final_prob = (base + pressure) * scale"]
    F --> G{random < final_prob?}
    G -->|Yes| Y[Deploy credits]
    G -->|No| Z
```

## Exit Decision (_consider_exit)

```mermaid
graph TD
    A[current_apy >= yield_threshold?] -->|Yes| STAY[Stay, no exit pressure]
    A -->|No| GAP["gap = (threshold - apy) / threshold"]
    GAP --> EP["exit_prob = gap × price_sensitivity × 0.15"]
    EP --> HH["exit_prob × (1 - hold_horizon × 0.8)"]
    HH --> R{random < exit_prob?}
    R -->|Yes| EXIT[Agent exits]
    R -->|No| STAY
```

## Archetypes

```mermaid
graph TD
    subgraph Believer["Believer (25%)"]
        B1[Mission: 0.7-1.0]
        B3[Engagement: 0.7-1.0]
        B4[Price Sens: 0.0-0.3]
        B5[Hold Horizon: 0.7-1.0]
        B6[Threshold: mean - 0.03]
    end

    subgraph YieldSeeker["Yield Seeker (30%)"]
        Y1[Mission: 0.2-0.5]
        Y3[Engagement: 0.5-0.8]
        Y4[Price Sens: 0.5-0.9]
        Y5[Hold Horizon: 0.2-0.6]
        Y6[Threshold: mean + 0.05]
    end

    subgraph Institution["Institution (20%)"]
        G1[Mission: 0.6-0.9]
        G3[Engagement: 0.4-0.7]
        G4[Price Sens: 0.1-0.4]
        G5[Hold Horizon: 0.8-1.0]
        G6[Threshold: mean - 0.04]
        G7["RSC: 5K-50K"]
    end

    subgraph Speculator["Speculator (25%)"]
        S1[Mission: 0.0-0.3]
        S3[Engagement: 0.2-0.5]
        S4[Price Sens: 0.7-1.0]
        S5[Hold Horizon: 0.0-0.3]
        S6[Threshold: mean + 0.08]
    end
```

## Time-Weight Multipliers

```mermaid
graph LR
    W0[weeks_held = 0] --> NEW[New: 1.00x < 4 weeks]
    NEW --> HOLD[Holder: 1.15x 4wk–1yr]
    HOLD --> LT[LongTerm: 1.20x > 1yr]

    MY[my_effective_rsc = rsc × multiplier] --> SHARE["share = my_eff / total_eff"]
    SHARE --> YIELD["credits = weekly_emission × share"]
```

## Dashboard Layout

```mermaid
graph TB
    subgraph Top["Framing Strip"]
        FS[What is this? / Self-balancing math / DeFi death spiral / Sources]
    end

    subgraph Hero["Calculator Hero"]
        DI[Dollar input]
        SC[Scenario cards: Conservative 15% / Expected 30% / High 70%]
        EC[Endowment comparison table: Cash Donation vs RSC Endowment]
    end

    subgraph Controls["Sim Controls"]
        SU[Setup]
        ST[+1 wk · +10 wk · +1 yr]
        GO[Go / Stop toggle]
        TC[Tick counter Wk / Yr]
    end

    subgraph KPIs["Pinned KPIs"]
        PR[Participation Rate]
        APY[Current APY]
        EX[Exited]
        BC[Burn Coverage %]
    end

    subgraph TwoCol["Two-Column Main"]
        subgraph Left["Left: Charts"]
            AC[Archetype Composition<br/>Stacked RSC by holder type]
            SF[Science Funding vs Protocol Cost<br/>Credits deployed + Emissions vs Burns]
        end
        subgraph Right["Right: Endowment Projection"]
            EP[Year 1 credits / 10-yr total / Year 10 APY]
            SP[10-year sparkline]
        end
    end

    subgraph Bottom["Agent Grid + Accordions"]
        AG[Agent Field — every dot is a holder]
        ACC[Adjust Scenario / Advanced / Data Tables / Time Series]
    end

    Top --> Hero --> Controls --> KPIs --> TwoCol --> Bottom
```

## Agent Field Grid Encoding

Each cell in the Agent Field grid encodes three dimensions:

| Visual Property | Data | Meaning |
|----------------|------|---------|
| Color | Archetype | Green=Believer, Gold=Yield Seeker, Purple=Institution, Red=Speculator |
| Opacity | Holding duration | 0.35=New (< 4wk), 0.65=Holder (4wk–1yr), 0.95=LongTerm (> 1yr) |
| Glow | Credit pressure | Bright edge = credits accumulating, needs to deploy |
| Grey | Exited | Holder pulled RSC from RH account |

## Parameter Flow (Slider to Backend)

```mermaid
graph LR
    subgraph Dashboard["Dashboard Sliders"]
        SY[Yield Threshold 1-25%]
        SD[Deploy Rate 0-100%]
        SS[Success 20-100%]
        SN[Holders 20-500]
        SB[Burn Rate 0.5-10%]
        SA[Archetype Mix]
    end

    subgraph Transform["JS getSliderParams()"]
        T1[/ 100]
        T2[parseInt]
        T3[/ 100 per arch]
    end

    subgraph Backend["EndowmentModel"]
        yield_threshold_mean
        deploy_probability
        success_rate
        num_holders
        burn_rate
        archetype_mix
    end

    SY --> T1 --> yield_threshold_mean
    SD --> T1 --> deploy_probability
    SS --> T1 --> success_rate
    SN --> T2 --> num_holders
    SB --> T1 --> burn_rate
    SA --> T3 --> archetype_mix
```

## Credit Lifecycle

```mermaid
graph LR
    RSC[RSC held in RH] -->|× time_weight_mult| EFF[Effective RSC share]
    EFF -->|× weekly_emission| CREDITS[Credits Generated]
    CREDITS -->|behavioral decision| DEPLOY[Credits Deployed]
    DEPLOY -->|fund proposal| PROP[Proposal]
    DEPLOY -->|burn_rate %| BURN[RSC Burned]
    PROP -->|success_rate| COMPLETE[Completed]
    PROP -->|1 - success_rate| FAIL[Failed]
    APY[APY < threshold] -->|probabilistic| EXIT[Holder Exits]
    EXIT --> LESSPILE[Less total RSC]
    LESSPILE --> HIGHERAPY[Higher APY for remaining]
```
