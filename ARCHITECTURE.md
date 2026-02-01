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
        ES[EndowmentStaker]
        EP[EndowmentProposal]
        DC[DataCollector]
        CT[Constants & Archetypes]
    end

    UI -->|fetch /api/*| API
    API -->|JSON response| UI
    API --> EM
    EM --> ES
    EM --> EP
    EM --> DC
    CT --> ES
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

    U->>D: Click Run 1 Year
    D->>S: POST /api/run {steps: 52}
    loop Each step
        S->>M: model.step()
        Note over M: Credit generation
        Note over M: Deployment decisions
        Note over M: Proposal resolution
        Note over M: Satisfaction + churn
    end
    S-->>D: {state, events, history}
    D->>D: Render grid, charts, metrics
```

## Behavioral Model: B = f(P, E)

```mermaid
graph LR
    subgraph Person["Person Attributes"]
        MA[Mission Alignment]
        RT[Risk Tolerance]
        EN[Engagement]
        PS[Price Sensitivity]
    end

    subgraph Environment
        APY[Yield Rate]
        SR[Success Rate]
        DP[Deploy Probability]
        SAT[Satisfaction History]
        CP[Credit Pressure]
    end

    subgraph Behavior
        DEP[Deploy?]
        SEL[Select Proposal]
        CHR[Churn?]
    end

    MA --> DEP
    EN --> DEP
    CP --> DEP
    SAT --> DEP
    DP --> DEP

    MA --> SEL
    RT --> SEL

    SAT --> CHR
    PS --> CHR
    RT --> CHR
```

## Deployment Decision (_should_deploy)

```mermaid
graph TD
    A[Credits > 0?] -->|No| Z[Don't deploy]
    A -->|Yes| B[base_prob = engagement * 0.6]
    B --> C[pressure_boost = sigmoid of credit accumulation]
    C --> D[sat_factor = 0.3 + 0.7 * satisfaction]
    D --> E["deploy_scale = deploy_probability / 0.3"]
    E --> F["final_prob = (base + pressure) * sat * scale"]
    F --> G{random < final_prob?}
    G -->|Yes| Y[Deploy credits]
    G -->|No| Z
```

## Archetypes

```mermaid
graph TD
    subgraph Believer["Believer (25%)"]
        B1[Mission: 0.7-1.0]
        B2[Risk: 0.6-0.9]
        B3[Engagement: 0.7-1.0]
        B4[Price Sens: 0.0-0.3]
    end

    subgraph YieldSeeker["Yield Seeker (30%)"]
        Y1[Mission: 0.2-0.5]
        Y2[Risk: 0.3-0.6]
        Y3[Engagement: 0.5-0.8]
        Y4[Price Sens: 0.5-0.9]
    end

    subgraph Governance["Governance (20%)"]
        G1[Mission: 0.5-0.8]
        G2[Risk: 0.3-0.5]
        G3[Engagement: 0.6-0.9]
        G4[Price Sens: 0.2-0.5]
    end

    subgraph Speculator["Speculator (25%)"]
        S1[Mission: 0.0-0.3]
        S2[Risk: 0.7-1.0]
        S3[Engagement: 0.2-0.5]
        S4[Price Sens: 0.7-1.0]
    end
```

## Dashboard Layout

```mermaid
graph TB
    subgraph Sidebar
        direction TB
        P[Parameters<br/>Yield / Deploy Rate / Success / Stakers]
        AM[Archetype Mix<br/>Linked sliders sum=100%]
        ST[Staking Tiers<br/>Distribution bar]
        ADV[Advanced<br/>Burn Rate / Expiry / Failure / Min Stake]
        SC[Scenarios<br/>Save / Compare]
        HW[How It Works]
        DQ[Design Questions]
    end

    subgraph Main["Main Area"]
        direction TB
        KPI[Pinned KPIs: Staked / Satisfaction / Churned]
        subgraph Tabs
            AF[Agent Field<br/>Grid + archetype cards]
            TS[Time Series<br/>Staked/Credits/Burned]
            PF[Proposals & Funding<br/>Status + progress]
            AI[Agent Inspector<br/>Individual deep-dive]
        end
    end

    P --> Main
    AM --> Main
    ADV --> Main
```

## Agent Field Grid Encoding

Each cell in the Agent Field grid encodes three dimensions:

| Visual Property | Data | Meaning |
|----------------|------|---------|
| Color | Archetype | Green=Believer, Gold=Yield Seeker, Purple=Governance, Red=Speculator |
| Opacity | Satisfaction | 1.0=fully satisfied, fading=losing satisfaction |
| Glow | Credit pressure | Bright edge=credits piling up, needs to deploy |
| Grey | Churned | Agent has left the system |

## Parameter Flow (Slider to Backend)

```mermaid
graph LR
    subgraph Dashboard["Dashboard Sliders"]
        SY[Yield 1-25%]
        SD[Deploy Rate 0-100%]
        SS[Success 20-100%]
        SN[Stakers 20-500]
        SB[Burn Rate 0.5-10%]
        SA[Archetype Mix]
    end

    subgraph Transform["JS getSliderParams()"]
        T1[/ 100]
        T2[parseInt]
        T3[/ 100 per arch]
    end

    subgraph Backend["EndowmentModel"]
        base_apy
        deploy_probability
        success_rate
        num_stakers
        burn_rate
        archetype_mix
    end

    SY --> T1 --> base_apy
    SD --> T1 --> deploy_probability
    SS --> T1 --> success_rate
    SN --> T2 --> num_stakers
    SB --> T1 --> burn_rate
    SA --> T3 --> archetype_mix
```

## Credit Lifecycle

```mermaid
graph LR
    STAKE[RSC Staked] -->|yield * tier_mult / 52| CREDITS[Credits Generated]
    CREDITS -->|behavioral decision| DEPLOY[Credits Deployed]
    DEPLOY -->|fund proposal| PROP[Proposal]
    DEPLOY -->|burn_rate %| BURN[RSC Burned]
    PROP -->|success_rate| COMPLETE[Completed]
    PROP -->|1 - success_rate| FAIL[Failed]
    COMPLETE -->|+satisfaction| SAT[Satisfaction]
    FAIL -->|−satisfaction| SAT
    SAT -->|low + unlocked| CHURN[Churn]
```
