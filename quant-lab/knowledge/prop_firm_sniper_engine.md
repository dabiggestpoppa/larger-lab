# Prop Firm Sniper Engine — Full System Architecture
> Source: MAD + Architect responses 2026-05-30
> Format: Q&A Ontology + Implementation Spec
> Layer: Capital Allocation Optimization (NOT trading)

---

## Q1: What is the fundamental insight about prop firms?

**A:** This is NOT a trading problem. It's a **capital allocation optimization problem**.

Prop firms sell **risk bandwidth**, not capital. The upfront fee is the premium. Payout latency is the time decay. Consistency rules are the strike price adjustment.

Most traders treat props as "free leverage" but fail to model that **payout latency + consistency rules + scaling friction** act as a compounding drag that eventually makes live capital with raw leverage mathematically superior per unit of risk-adjusted return.

This is identical to LP staking yield curves, bond duration matching, or inventory turnover in supply chain finance. Same math, different field.

---

## Q2: What is the Prop Exploit Score (PES)?

**A:** Custom alpha metric — ranks firms by **risk-adjusted capital velocity per dollar deployed**, accounting for ALL hidden friction.

### THE META EQUATION:
```
Ω = (E × L × V) / (C × T × R)

Where:
E = executable exposure (D × λ — DD × leverage multiplier)
L = leverage efficiency
V = capital velocity
C = acquisition cost
T = payout latency
R = restriction drag
```

### THE FORMULA:
```
PES = (Effective Leverage × Win Rate Edge × Payout Frequency Factor)
      ÷ (Account Cost + Consistency Drag + Scaling Friction + Opportunity Cost of Live Capital)
```

### Variables:

| Variable | Definition | How to Calculate |
|----------|-----------|-----------------|
| **Effective Leverage** | Notional exposure per $1 risk AFTER max daily loss limits, trailing DD compression, consistency caps | Account size / (account_size × max_daily_loss_pct) adjusted for trailing DD |
| **Win Rate Edge** | Your engine's expected WR on that firm's specific rule set | Run your engine's WR through the firm's rule constraints |
| **Payout Frequency Factor** | 1 / (payout cycle days + buffer days) | Biweekly (14 days) = 0.071. Monthly = 0.033 |
| **Account Cost** | Upfront fee amortized over expected payout cycles to breakeven | cost / expected_payouts |
| **Consistency Drag** | Math penalty from consistency rules (max day <30% of total reduces compounding ~22%) | Derived from rule set |
| **Scaling Friction** | Time delay + cost to scale up, modeled as lost compounding periods | From firm rules |
| **Opportunity Cost** | What $X in live account at Y:1 leverage generates in same timeframe with no drag | Direct calculation |

### Capital Velocity (Vc):
```
Vc = P / Δt
Where:
P = extractable payout
Δt = payout cycle time
```

### Alpha (deepest layer):
```
α = Extractable Capital Flow / Constraint Surface
= how efficiently you extract liquidity through imposed rule geometry
```

---

## Q3: What is the Capital Velocity Singularity (Crossover Point)?

**A:** The exact mathematical threshold where prop firm leverage CEASES to be an alpha generator and BECOMES a velocity tax.

```
IF PES(prop_N_accounts) < PES(live_capital_at_equivalent_risk)
→ PROPS ARE NOW A VELOCITY TAX
→ DEPLOY LIVE CAPITAL INSTEAD
```

**Validated Example:**
- 10 × $1K accounts @ 5% risk = $50 risk each = $500 total risk
- Cost: 10 × $10 = $100 upfront
- Payout: Biweekly, but consistency rule caps max day at 30% → effective compounding rate reduced ~22%
- Equivalent live: $500 risk @ 100:1 leverage = $50,000 notional, NO consistency drag, instant withdrawal
- **Crossover Point: At ~$8K-$12K total prop AUM, consistency drag + payout latency makes live capital superior PER UNIT OF RISK**

### Why Small Accounts Beat Large Accounts (up to crossover):
```
Setup              Cost   Max DD   Effective Exposure
1 × $10K          $120   $500     Centralized
10 × $1K          $100   $500     Distributed

10×1K gives:
- Better survivability distribution
- Payout fragmentation
- Rule bypass flexibility
- Lower correlation failure
- Parallel extraction
```

### Portfolio Survival Equation:
```
S = 1 - (1-p)^n
Where:
p = success probability per account
n = account count
→ More accounts = exponentially higher extraction survivability
```

### Effective Exposure Calculation:
```
X = D × λ
Where:
D = allowed drawdown (REAL capital)
λ = leverage multiplier

Example: $100K prop @ 5% DD = $5K effective exposure
Everything above that = synthetic notional illusion
```

### Venue Comparison Table:
| Structure | Capital | Leverage | Effective Exposure |
|-----------|---------|----------|-------------------|
| Prop | $150 fee | 5K DD synthetic | Limited |
| Live | $5K | 1:100 direct | Full |
| Futures | Lower margin | Centralized high | Full |
| Crypto perp | Isolated margin | Variable continuous | Full |

---

## Q4: What is the architectural separation?

**A:** The system lives in 4 layers. The trading physics NEVER touches the venue.

| Layer | Function | Fragility | Adaptation |
|-------|----------|-----------|------------|
| **Physics Engine** | Impulse → Rebalance → Continuation | ZERO | Never changes. Universal law. |
| **Execution Engine** | Entry/SL/TP logic per asset | Low | Config tweak (AU, Trigger, Buffer). |
| **OC2 Intelligence** | Capital deployment topology | Medium | Re-runs when platform rules change. |
| **Venue/Platform** | Liquidity/Rules/Payouts | HIGH | Treated as disposable input variable. |

⚠️ **CRITICAL:** The OC2 engine does NOT trade. It outputs a **Deployment Config** (YAML/JSON) that tells the Execution Engine how much risk bandwidth to allocate and across how many synthetic instruments.

### OC2 as Config Generator — ChatGPT Math → CEREBUS Config Mapping:
| Math Concept | CEREBUS Config Output | Execution Impact |
|-------------|----------------------|-----------------|
| Effective Exposure (D×λ) | risk_per_trade parameter | Scales position sizing per account |
| Capital Velocity (P/Δt) | account_count & firm_mix | Determines parallel extraction topology |
| Restriction Drag (R) | consistency_buffer multiplier | Adjusts daily loss limits in config |
| Correlation Risk | max_correlated_exposure | Caps combined EU+CHF or XAU+XAG |
| Ban Probability | firm_diversification_min | Minimum firms required in deployment |
| Scaling Curve | diminishing_return_threshold | Triggers shift from props → live/futures |

### The Config Assembly Pattern:
```yaml
deployment_config:
  generated_at: "2026-05-30T11:00:00Z"
  crossover_threshold_usd: 10000
  firm_mix:
    - firm: "FirmA"
      accounts: 10
      size: 1000
      promo_applied: "SAVE20"
      true_cost: 8.0
    - firm: "FirmB"
      accounts: 5
      size: 2000
      promo_applied: null
      true_cost: 22.0
  risk_parameters:
    risk_per_trade: 0.05
    max_correlated_exposure: 3
    consistency_buffer: 0.78
```

### The Adaptation Cycle (when platforms change):
1. OC2 Re-evaluates: Re-runs Ω and Vc with new constraints
2. Config Regenerated: New YAML with adjusted account_distribution, risk_parameters, firm_mix
3. Execution Engine Unchanged: Same physics, same entry logic. Only allocation changes.
4. Zero Downtime: No strategy rewrite. No backtest rerun. Config swap only.

---

## Q5: What is the F&F (Friends & Family) Acquisition Protocol?

**A:** Structural Arbitrage — exploiting the gap between prop firms' compliance assumption (1 user = 1 account) and your operational reality (1 operator = N accounts).

### The F&F Multiplier:
```
Standard User:  Pays full price for Account #2, #3, #4. Cost basis rises linearly.
OC2 F&F Protocol: Applies "New Customer" promo rate to Account #2, #3, #4 via distinct identities. Cost basis stays flat at the discounted floor.

True Cost Basis = (Promo Price / Account Size) × Risk Multiplier
```

### The Data Pipeline:
| Step | Action | Source | Purpose |
|------|--------|--------|---------|
| **SCAN** | Scrape top-ranked futures firms + active promo codes | PropFirmMatch /futures | Baseline pricing & offers |
| **VERIFY** | Cross-reference code on official firm checkout page | Firm Official Site | Confirm validity, expiration, "New Customer Only" tags |
| **FILTER** | Apply F&F Multiplier Logic | Internal Config | Determine if promo applies to your acquisition method |
| **CALCULATE** | Compute True Cost Per Contract | Formula above | Establish real ROI denominator |

### Operational Security Rules:
- NEVER use the same payout wallet/crypto address across F&F accounts
- NEVER execute from the same IP/device simultaneously without VPS isolation
- NEVER use identical KYC metadata patterns where avoidable

### Promo Verification Checklist (agent mandatory gate):
```python
promo_valid = (
    code_exists_on_prop_firm_match AND
    code_valid_on_official_site AND
    (NOT new_customer_only OR ff_access_confirmed) AND
    NOT expired AND
    NOT patch_signal_detected
)
```

### Patch Signal Detection:
| Signal | Severity | Action |
|--------|----------|--------|
| Promo code rejected at checkout for new identity | LOW | Temporary glitch or expired. Re-verify in 24h. |
| Mandatory video KYC with liveness check linked to previous accounts | HIGH | PATCH DETECTED. Mark firm as restricted for F&F. |
| Device fingerprinting warning during onboarding | MEDIUM | Use fresh VPS/browser profile. Proceed with caution. |
| Payout rejection due to "related accounts" | CRITICAL | BACKDOOR CLOSED. Immediate cessation of F&F scaling. |
| Terms update explicitly banning multi-accounting | HIGH | Update compliance database. Re-evaluate risk/reward. |

### Firm Database Status Field — Extended:
| Status | Meaning |
|--------|---------|
| ACTIVE | Operating normally, standard terms |
| PROMO | Active promotional pricing verified |
| NEW | Newly listed, temporary alpha window |
| ARBITRAGE | F&F backdoor confirmed open |
| PATCHED | F&F backdoor closed, use standard pricing only |
| SUSPENDED | Firm inactive or banned |

---

## Q6: What is the database schema?

### Table: `prop_firms`
| Field | Type | Description |
|-------|------|-------------|
| firm_id | UUID | Unique identifier |
| name | STRING | Firm name |
| website | URL | Official site |
| account_sizes | JSON | [1000, 5000, 10000, ...] |
| cost_per_size | JSON | {1000: 10, 5000: 45, ...} |
| promo_active | JSON | {code, discount_pct, new_customer_only, verified_at, expires_at} |
| max_daily_loss_pct | FLOAT | e.g., 0.05 |
| max_trailing_dd_pct | FLOAT | e.g., 0.06 |
| consistency_rule | JSON | {max_day_pct_of_total: 0.30, min_trading_days: 5} |
| payout_cycle_days | INT | 14, 30, etc. |
| payout_buffer_days | INT | Days between request and receipt |
| payout_method | ENUM | Crypto, Bank, PayPal |
| scaling_rules | JSON | {min_profit_to_scale: 0.08, scale_delay_days: 30} |
| allowed_instruments | LIST | ["EURUSD", "XAUUSD", ...] |
| news_restrictions | BOOLEAN | |
| ff_status | ENUM | ARBITRAGE, PATCHED, STANDARD, UNTESTED |
| patch_signals | JSON | [{signal_type, detected_at, severity}] |
| last_updated | TIMESTAMP | |
| status | ENUM | ACTIVE, PROMO, SUSPENDED, NEW |

### Table: `capital_deployments`
| Field | Type | Description |
|-------|------|-------------|
| deployment_id | UUID | |
| firm_id | FK | |
| account_size | INT | |
| quantity | INT | Number of accounts at this size |
| total_cost | FLOAT | quantity × cost_per_size (after promo discount) |
| total_risk_capital | FLOAT | quantity × account_size × max_daily_loss_pct |
| pes_score | FLOAT | Calculated PES at time of deployment |
| effective_exposure | FLOAT | D × λ |
| capital_velocity | FLOAT | P / Δt |
| crossover_threshold | FLOAT | AUM at which props < live for this deployment |
| equivalent_live_leverage | FLOAT | Computed crossover comparison |
| deployed_at | TIMESTAMP | |
| status | ENUM | ACTIVE, PAUSED, LIQUIDATED, GRADUATED |
| config_version | INT | Links to config file version |

### Table: `pes_snapshots`
| Field | Type | Description |
|-------|------|-------------|
| snapshot_date | DATE | |
| firm_id | FK | |
| account_size | INT | |
| pes_score | FLOAT | |
| effective_leverage | FLOAT | |
| consistency_drag | FLOAT | |
| velocity_factor | FLOAT | |
| opportunity_cost_live | FLOAT | |
| is_optimal | BOOLEAN | Is this the current best deployment? |
| notes | STRING | Promo, new listing, rule change, etc. |

---

## Q7: What is the `oc2 scope` workflow?

**A:** When triggered, the engine executes:

1. **SCAN** all active firms + new listings (last 7 days) + active promos from PropFirmMatch
2. **VERIFY** top promos against official firm sites, apply F&F override where applicable
3. **CALCULATE** PES for every (firm, account_size) combination using YOUR engine's WR and risk parameters
4. **RANK** by PES descending
5. **IDENTIFY** the top exploit spot: highest PES with sufficient liquidity
6. **COMPUTE** crossover threshold: at what total AUM does this stop being optimal vs. live capital?
7. **OUTPUT:**
```
🎯 BEST EXPLOIT: [Firm] $[Size] × [Qty]
   PES: [score] | Effective Lev: [X]:1 | Velocity: [factor]
   Total Risk Capital: $[amount] | Cost: $[cost] (promo: [code])
   Crossover Threshold: $[AUM] (beyond this → go live)
   F&F Status: ARBITRAGE / STANDARD
   Edge Degradation: [consistency drag %]
   Notes: [promo/new/rule change if applicable]
```

---

## Q8: What are the key strategic insights?

**A:**
1. **Props are options on your own edge.** Premium = upfront fee. Time decay = payout latency. Strike adjustment = consistency rules.
2. **Multiple small accounts > fewer large accounts (up to crossover).** Consistency drag scales NON-LINEARLY. Independent windows beat correlated exposure.
3. **New listings are temporary alpha.** Looser rules at launch. PES spikes. Decays. Track it.
4. **Promos are mispriced options.** Recalculate PES at promo pricing. Often the highest PES temporarily. Verify "New Customer Only" with F&F override.
5. **The live capital crossover is dynamic.** Higher WR → props stay optimal longer. Degrading edge → crossover comes sooner. **Recalculate weekly.**
6. **The backdoor is open until proven closed.** F&F access = structural arbitrage. Monitor patch signals continuously.
7. **The system lives above the venue.** Physics don't change. Only the config changes when houses burn.

---

## Q9: How does this connect to CEREBUS?

**A:**
The Prop Firm Sniper Engine is a **capital allocation decision layer** ABOVE the CEREBUS trading engines.

- CEREBUS (P90 Kinetic + Symmetry Trap Structural) = the **edge generator**
- Prop Firm Sniper = the **capital optimizer** that tells you WHERE to deploy that edge

**Metrics flow CEREBUS → Sniper:**
| CEREBUS Output | Sniper Input |
|---------------|--------------|
| Win Rate (per strategy) | Win Rate Edge variable in PES |
| Max Drawdown | Trailing DD risk modeling |
| Trade frequency | Consistency window pacing |
| Instrument compatibility | Allowed instruments filter |
| Sharpe / PF | Edge degradation modeling |

**The feedback loop:**
```
CEREBUS edge degrades → PES recalculates → Crossover comes sooner → Deploy live capital
CEREBUS edge improves → PES recalculates → Props stay optimal longer → More aggressive funding
Venue rules change → OC2 re-runs → New config generated → Execution engine reads new config → Zero downtime
```

---

## Implementation Priority

1. **PES Calculator** — Core math engine (Ω, Vc, X, S)
2. **Firm Database** — SQLite with the 3 tables above, seeded from PropFirmMatch
3. **Promo Scanner** — Web scrape PropFirmMatch + verify against official sites
4. **Scope Workflow** — The `oc2 scope` command (scan → verify → calculate → rank → output)
5. **Config Generator** — YAML output for execution engine
6. **F&F Arbitrage Module** — Promo override logic + patch signal tracking
7. **Deployment Tracker** — Live monitoring of active deployments
8. **Dynamic Recalculation** — Weekly PES updates as edge changes
9. **Crossover Alerts** — Notify when approaching velocity tax threshold

---

## The Quant Lab Bible — Two Books:
- **Book 1: Physics** (Impulse → Rebalance → Continuation). Immutable. Lives in execution engine. Never touched when platforms change.
- **Book 2: Deployment Topology** (OC2 Intelligence). Mutable. Regenerated when venues change. Outputs config only.

**The engine lives above the house. The house can burn. The physics persist.** 🔥

---

_Stored: 2026-05-30 11:09 EDT — Full conversation ontology (MAD + Architect + ChatGPT + Architect final + MAD F&F protocol + Architect acquisition module)_
_Source file: PROP_SNIPER_PLAN---04c41864-af2a-4794-bf9b-2c26a5169740.txt_
_Next: Awaiting MAD's signal to begin build_
