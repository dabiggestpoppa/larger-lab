# Nautilus Backtest Results — Fixed Configs (2026-05-31 22:10 EDT)

## Summary: Crypto/Commodity Now Working ✅

| Strategy | Symbol | Trades | WR | PnL (pips) | Status |
|----------|--------|--------|-----|------------|--------|
| Symmetry Trap | BTCUSD | 2,014 | 86.9% | +219,718 | ✅ |
| Symmetry Trap | ETHUSD | 777 | 94.7% | +11,902 | ✅ |
| Symmetry Trap | XAUUSD | 1,718 | 81.8% | +21,118 | ✅ |
| P90 | BTCUSD | 2 | 100.0% | +17 | ⚠️ Low count (24/7) |

## Cross-Validation vs Python Ground Truth

| Symbol | Python ST WR | Nautilus ST WR | Delta |
|--------|-------------|----------------|-------|
| BTCUSD | 92.6% | 86.9% | -5.7% |
| ETHUSD | 96.9% | 94.7% | -2.2% |
| XAUUSD | 84.4% | 81.8% | -2.6% |

## Root Cause of Previous Zero-Trade Bug
1. Nautilus strategies used hardcoded EURUSD tier configs for all symbols
2. BTCUSD pip_divisor was 10000 (forex default) → all AR values tiny → always NO-GO
3. Fix: pip_divisor=1.0 for crypto + correct tier configs from asset_configs.py

## Files Modified
- `quant-lab/strategies/symmetry_trap_strategy.py` — added BTC/ETH/XAU configs + symbol key normalization
- `quant-lab/strategies/p90_strategy.py` — same fixes
- `quant-lab/backtests/run_cerebus_backtest_fixed.py` — new runner with per-asset config loading

## Next Steps
1. Add ALL asset configs to SYMBOL_TIER_CONFIGS (not just BTC/ETH/XAU)
2. Replace run_cerebus_backtest.py with fixed version
3. Run full 19-asset Nautilus cross-validation campaign
4. Focus on NT8 REST API approach for prop firm execution

---
*Logged: 2026-05-31 22:10 EDT*
