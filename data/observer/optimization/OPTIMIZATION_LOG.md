# OPTIMIZATION LOG — Tuning History + Next Steps
> Linked: `[[BACKTEST_RESULTS]]` | `[[ACTIVE_STRATEGIES]]` | `[[FAILURE_INDEX]]`

---

## Completed Backtest Phases

| Phase | Description | Status | Date |
|-------|-------------|--------|------|
| 1 | 19 individual asset reports + MC | ✅ | 2026-05-31 |
| 2 | 4 group reports (Majors/Crosses/MetalsCrypto/Indices) | ✅ | 2026-05-31 |
| 3 | Multi-asset combined (12,488 pooled trades) | ✅ | 2026-05-31 |
| 4 | Master INDEX linking all reports | ✅ | 2026-05-31 |
| 5 | Top 5 + Major 6 deep-dive re-runs | ✅ | 2026-05-31 |

---

## Known Issues

| Issue | Priority | Status | Details |
|-------|----------|--------|---------|
| XAGUSD config | 🔴 HIGH | OPEN | Only 2 trades — tier thresholds incompatible with silver |
| BTC concentration | 🟡 MEDIUM | OPEN | 55% of multi-asset pool PnL from single asset |
| Crypto correlation | 🟡 MEDIUM | OPEN | BTC+ETH = 58.5% of pool, correlated drawdown risk |
| NAS100 missing | 🟡 MEDIUM | BLOCKED | No MT5 data available |

---

## Metrics to Add for Future Optimization

Current reports track: WR, PF, Sharpe, MaxDD, Avg Win, Avg Loss, Consec Wins/Losses, MC ruin

**Needed for prop firm models:**
- Max drawdown duration (time spent in DD)
- Time in average drawdown (recovery speed)
- Per-session PnL distribution
- Slippage impact estimation

---

## Future Optimization Angles

### Prop Firm Models
1. **High-risk model**: Larger AU, wider stops, fewer trades, higher per-trade PnL
2. **Consistency model**: Tighter tiers, more trades, smoother equity curve
3. **Prop firm specific**: Calibrate to max DD limits (10% total, 5% daily)
4. **Scaling model**: Increase lots only after N consecutive winners

### Phase Backlog
| Phase | Description | Priority |
|-------|-------------|----------|
| 6 | P90 multi-asset backtest | Next |
| 7 | Dual-engine convergence (P90 + ST) | High |
| 8 | Nautilus cross-validation | High |
| 9 | Live deployment expansion | Medium |

---

## Calibration Principles (from MAD)
1. AU is the anchor — calibrate AU first, tiers cascade from AU
2. Trigger thresholds scale with asset volatility — compare relative to AU, not absolute
3. Zero-Buffer OCC is default SL method unless manual specifies otherwise
4. 80% close invalidation is absolute
5. No look-ahead bias — all calculations use only data available at decision time
6. 12PM cutoff is by design — never extend
