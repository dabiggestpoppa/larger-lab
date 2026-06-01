# Phase A2: NT8 Backtest Validation

> **Prerequisite:** Phase A1 complete (CEREBUS_ST_NT8.cs + CEREBUS_P90_NT8.cs written)
> **Goal:** Validate C# translation against Python baseline

## Validation Pipeline

### Step 1: Futures Asset Configs
Create YAML configs for the 4 key futures instruments:

| Instrument | Symbol | Tick Size | Tick Value | Point Value |
|-----------|--------|-----------|------------|-------------|
| E-mini S&P 500 | ES | 0.25 | $12.50 | $50 |
| E-mini NASDAQ-100 | NQ | 0.25 | $5.00 | $20 |
| Gold Futures | GC | 0.10 | $10.00 | $100 |
| Crude Oil | CL | 0.01 | $10.00 | $1000 |

For each, derive tier thresholds from the Python asset_configs.py pattern:
- Use percentage-based AUs relative to average range
- T1 = low volatility day, T2 = medium, T3 = high
- NO-GO = extreme volatility (skip the day)

### Step 2: NT8 Configuration Checklist
Document exact NT8 settings needed:
- Calculate: OnBarClose (CRITICAL)
- Session template: 3:00 AM – 12:00 PM EST
- Spread: Instrument actual (NOT zero)
- Slippage: 1 tick
- Commission: Per-side actual
- Data: Tick Replay required
- Bars required: ≥ 2 years

### Step 3: Metric Gate Thresholds (from Python baseline)

| Metric | Python Baseline (EUR/USD) | NT8 Target Range | Failure Threshold |
|--------|--------------------------|-------------------|-------------------|
| Win Rate | 88.4% | 86-90% | < 85% |
| Profit Factor | 4.18 | 3.5-4.5 | < 2.5 |
| Max DD | 3.8% | ≤ 6.0% | > 6.0% |
| Avg R-Multiple | 1.18R | ≥ 1.0R | < 1.0R |
| Trade Count (2yr) | 3,842 | ≥ 200 | < 200 |

### Step 4: Debug Diagnostic Tree
If gates fail, check in order:
1. Session times match Python?
2. SL = OCC Extreme exact? (no buffer)
3. Bar indexing = close only? (Calculate.OnBarClose)
4. Tier thresholds match Manual?
5. Spread/slippage settings realistic?

## Output Files
- `quant-lab/tradovate/configs/futures_configs.yaml` — per-instrument tier/AU configs
- `quant-lab/tradovate/VALIDATION_PROTOCOL.md` — step-by-step NT8 backtest procedure
- `quant-lab/tradovate/NT8_CONFIG_CHECKLIST.md` — exact NT8 settings to use
