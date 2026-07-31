# DEPLOYMENT STATUS — What's Live Right Now
> Linked: `[[ACTIVE_STRATEGIES]]` | `[[ENGINES_INDEX]]`

## Live Executors

| Executor | Symbol | Strategy | Magic | Lots | Account |
|----------|--------|----------|-------|------|---------|
| ST Executor | EURUSD.PRO | Symmetry Trap | 20260531 | 0.03 | 650898 LIVE |
| P90 Executor | USDCHF.PRO | P90 CASCADE | 20260532 | 0.01 | 650898 LIVE |

## Broker
- Ox Securities MetaTrader 5
- Account: 650898 LIVE

## Rules
⚠️ DO NOT TOUCH `quant-lab/mt5/` without MAD approval — live executors running

## Deployment History
- ST Executor EURUSD.PRO: Deployed 2026-05-31
- P90 CASCADE USDCHF.PRO: Deployed 2026-05-31
- Previous DMR executors: DEPRECATED (merged into P90 engine)

## Expansion Plan
1. Add GBPUSD.PRO + AUDUSD.PRO (pending backtest confirmation)
2. Multi-asset live deployment after Phase 6 P90 backtest
3. Prop firm deployment (calibrate to 10% max DD, 5% daily loss limits)
