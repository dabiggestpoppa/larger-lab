# HEARTBEAT.md - OC2 Operator

> **Policy:** Latest status + active delegations only. Archive history to logs/heartbeat-history/>.
Max 4000 chars.

## Current Status (2026-06-01 04:50 EDT)
- **PHASE 0 GROUND TRUTH MATRIX COMPLETE** ✅ — 19 assets, Nautilus locked physics
- **TRACK A CODE COMPLETE** ✅ — 7/7 deliverables written
- **DASHBOARD COMPLETE** ✅ — running at localhost:3001
- **OBSIDIAN VAULT ACTIVE** ✅
- **CONFIG FIX APPLIED** ✅ — 3 files fixed (ST strategy, P90 strategy, backtest runner)
- **RE-BACKTEST IN PROGRESS** — 4 groups spawned, Groups 1+2 complete, Groups 3+4 running
- **DEPRECATED SCRIPTS CLEANED** ✅ — 29 Python scripts removed from reports/
- **MODE: UNIFIED** | MEMORY: PERSISTENT | FIELD: STABILIZED
- **AWAITING GROUPS 3+4 COMPLETION → PHASE 1 DIRECTIVE**

## Hard Stop Rule (Post-May-31-2026 Incident)
**After ANY completed deliverable:**
1. Write status to HEARTBEAT
2. Report to MAD in plain text
3. WAIT. Do NOT spawn, fix, or continue until MAD explicitly says go.
4. If a subagent fails → REPORT failure to MAD. Do NOT retry without approval.

## Phase 0 Ground Truth Matrix (Nautilus, locked physics)

### Symmetry Trap — 17,119 trades | 85.3% avg WR
| Asset | Trades | WR | PnL |
|-------|--------|-----|-----|
| BTCUSD | 2,014 | 86.9% | +219,719 |
| EURUSD | 2,186 | 82.1% | +8,585 |
| GBPUSD | 2,234 | 83.5% | +11,751 |
| USDCHF | 2,050 | 81.6% | +7,756 |
| GBPAUD | 1,428 | 85.2% | +12,529 |
| GBPNZD | 1,410 | 85.0% | +13,936 |
| XAUUSD | 1,718 | 81.8% | +21,118 |
| GBPCHF | 1,161 | 89.9% | +7,981 |
| ETHUSD | 777 | 94.7% | +11,902 |
| AUDUSD | 1,249 | 87.8% | +5,329 |
| NZDUSD | 833 | 91.6% | +4,364 |
| FR40 | 56 | 96.4% | -329,031 ⚠️ |
| XAGUSD | 2 | 100% | +50 |
| US500 | 1 | 100% | +19 |
| CHFJPY | 0 | — | 0 |
| DE30 | 0 | — | 0 |
| GBPJPY | 0 | — | 0 |
| HK50 | 0 | — | 0 |
| USDJPY | 0 | — | 0 |

### P90 Kinetic — 6,088 trades | 55.8% avg WR | +3,233 pips
| Asset | Trades | WR | PnL |
|-------|--------|-----|-----|
| GBPUSD | 1,297 | 53.1% | +397 |
| EURUSD | 1,048 | 60.4% | +793 |
| GBPCHF | 980 | 59.7% | +674 |
| USDCHF | 841 | 57.4% | +259 |
| AUDUSD | 527 | 49.1% | -36 |
| NZDUSD | 457 | 54.0% | +215 |
| GBPAUD | 380 | 47.9% | +81 |
| GBPNZD | 255 | 48.6% | +134 |
| XAUUSD | 202 | 54.5% | +309 |
| ETHUSD | 99 | 83.8% | +391 |
| BTCUSD | 2 | 100% | +17 |
| Others | 0 | — | 0 |

### Critical Issues
1. **FR40**: -329,031 pips — pip calc broken on equity instrument type
2. **USDJPY, CHFJPY, GBPJPY**: 0 trades both strategies (dead)
3. **Indices (US500, DE30, HK50)**: near-zero trades (equity instrument workaround — unreliable)
4. **XAGUSD**: 2 trades only

### Key Finding
**Excluding FR40 anomaly: ST PnL ≈ +325,000+ pips across 18 assets. ST dominates P90 on every asset class.**

## Track A Deliverables — ALL COMPLETE
| # | File | Status |
|---|------|--------|
| 1 | crypto/CryptoAssetScanner.py (23.8KB) | ✅ Done |
| 2 | tradovate/CEREBUS_ST_NT8.cs (21.9KB) | ✅ Done |
| 3 | tradovate/CEREBUS_P90_NT8.cs (25.4KB) | ✅ Done |
| 4 | tradovate/CEREBUS_BacktestHarness.cs (12.4KB) | ✅ Done |
| 5 | tradovate/CEREBUS_DeployConfig.json (3.1KB) | ✅ Done |
| 6 | tradovate/CEREBUS_TradeCopier.cs (7.0KB) | ✅ Done |
| 7 | tradovate/CEREBUS_AssetPresets.cs (10.1KB) | ✅ Done |

## Cron Fleet (2 Active, 8 Disabled)
| Cron | Schedule | Status |
|------|----------|--------|
| CEREBUS Overnight Report | 5AM EST | ✅ Working |
| DRIFT Architecture | 6:45AM Sun/Wed/Sat | ✅ Working |

## Key Paths
| Path | Purpose |
|------|---------|
| `quant-lab/reports/nautilus_ground_truth_matrix.json` | Phase 0 master matrix |
| `quant-lab/reports/PHASE0_GROUND_TRUTH_REPORT.md` | Phase 0 report |
| `tradovate/` | All 7 Track A files |
| `quant-lab/engines/` | Python truth source (ST + P90) |
| `quant-lab/data/` | 24 CSV data files |
| `C:\Users\wifik\Downloads\o2c` | Obsidian vault (primary memory) |

_Last updated: 2026-06-01 03:53 EDT — PHASE 0 COMPLETE — AWAITING MAD REVIEW + PHASE 1 DIRECTIVE_
