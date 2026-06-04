# quant-lab/engines/README.md

## Engines Directory

| Engine | File | Type | Status |
|--------|------|------|--------|
| P90 Kinetic Engine | `p90_engine.py` | Kinetic (Engine A) | ✅ Live |
| Symmetry Trap Engine | `symmetry_trap.py` | Structural (Engine B) | ✅ Live |
| DMR Resolution Engine | `dmr_resolution.py` | Hybrid | 🔄 Paused |
| **Prop Firm Sniper** | `prop_firm_sniper.py` | Capital Allocation | 🟡 New |

---

## Prop Firm Match & Capital Deployment Engine

### Core Metric: Prop Exploit Score (PES)

```
PES = (Effective Leverage × Win Rate Edge × Payout Frequency Factor)
      ÷ (Account Cost + Consistency Drag + Scaling Friction + Opportunity Cost of Live Capital)
```

### Philosophy
Props are **options on your own edge**. The upfront fee is the premium. Payout latency is the time decay. Consistency rules are the strike price adjustment. The Capital Velocity Singularity is the crossover where live capital becomes mathematically superior per unit of risk-adjusted return.

### Architecture
```
prop_firm_sniper.py          → PES calculator + Capital Deployer
prop_firm_data.py            → Firm database + live scraper
prop_firm_monitor.py         → Frontier tracking + crossover detection
```

### MAD Directives
1. Multiple small accounts > fewer large accounts (up to crossover) — independent consistency windows
2. New listings = temporary alpha (looser rules → PES spike → decay)
3. Promos = mispriced options (recalculate PES at promo pricing)
4. Crossover is **dynamic** — recalculate weekly as edge changes

---
_Last updated: 2026-05-30_
