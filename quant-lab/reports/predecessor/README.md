# CEREBUS Predecessor Data — Summary for CC Planning

> **Compiled:** 2026-06-08 by PM2
> **Source:** 60+ PDF files + 3 Excel files from MAD's archive
> **Purpose:** Prepare data context for CC to make official integration plan
> **Status:** 28 PDFs extracted to text, Excel pending processing

---

## 📁 FILES PROCESSED

### PDFs (extracted to quant-lab/reports/predecessor/)
| File | Size | Content |
|------|------|---------|
| CEREBUS_FX_v4_Complete_Manual (1).pdf | 18.6 MB | Main manual (214 pages) — Fibonacci-based trading system |
| CEREBUS v18.2.5 master scroll (1).pdf | 18.5 MB | Multi-market Fibonacci model (33 pages) — EUR/USD, OIL/USD, ETH/USD |
| cerebus dual incomplete bydatry (1).pdf | 18.5 MB | Dual-engine incomplete analysis (27 pages) |
| CEREBUS GJ PHASE 6 PLAYBOOK.pdf | Small | GJ Phase 6 playbook |
| CEREBUS GJ PHASE 1-2.pdf | Small | GJ Phase 1-2 analysis |
| CEREBUS GJ DARA.pdf | Small | GJ DARA analysis |
| Crypto Fibonacci Trading Model - BTC & ETH Complete Manual.pdf | Small | Crypto-specific Fibonacci model (11 pages) |
| CROSS ASSET MASTER FILE 3 FINAL FORM.pdf | Small | Cross-asset master file |
| cerebus cross asset master file FINAL FORM 1.pdf | Small | Cross-asset master file v1 |
| CEREBUS CROSS ASSET MASTER FILE 3.2.pdf | Small | Cross-asset master file v3.2 |
| Phase 1B OILUSD Session Bifurcation Analysis.pdf | Small | Oil bifurcation analysis (16 pages) |
| Phase 1B Cross-Asset Analysis_ EURUSD vs OILUSD.pdf | Small | Cross-asset analysis (15 pages) |

### Excel (not yet processed — too large, needs special handling)
| File | Size | Content |
|------|------|---------|
| cerebus 3 market hoily grail (3).xlsx | 10.5 MB | **THE HOLY GRAIL** — 100 sheets, 20k data points, raw price CSV |

---

## 🔑 KEY FINDINGS

### 1. The Fibonacci Approach (Predecessor System)

**Core Formula:**
```
Range A = Asian Session Range (7PM-3AM EST, 8 hours, H1 candles)
T+0 Anchor = Friday 05:00 EST Close

Fibonacci Targets (in direction of bias):
  -25% = T+0 ± (Range A × 0.25)
  -50% = T+0 ± (Range A × 0.50)
  -100% = T+0 ± (Range A × 1.00)
  -168% = T+0 ± (Range A × 1.68)

Invalidation (opposite direction):
  132% = T+0 ∓ (Range A × 1.32)

Tolerance: ±0.025 (adjust for asset volatility)
```

**Directional Bias:**
- Bullish: T+0 Close > Range A Midpoint
- Bearish: T+0 Close < Range A Midpoint

**Regime Detection (Crypto):**
- FAST: Range A > 1.5× 20-week SMA → 89.3% hit rate
- NORMAL: Range A 0.8-1.5× SMA → 89.0% hit rate
- SLOW: Range A < 0.8× SMA → 68.3% hit rate (avoid)

**Key Validation Results:**
- EUR/USD: 100% hit rate at -25% and -50% levels (±0.025 tolerance)
- ETH/USD: 100% hit rate at -25% level across all bias conditions
- 132% invalidation: 70-75% violation rate across all markets (universal)
- OIL/USD: 98% hit rate on 132% realignment trigger during bifurcation

### 2. The 132% Realignment Trigger (Oil Bifurcation Analysis)

**Finding:** When Asian Range ≠ London Open (51.5% of days = bifurcation):
- 98% of bifurcated days see at least one session's 132% level violated
- London 132% hits first 63.3% of the time
- Asian 132% hits first 34.7% of the time
- Only 2.0% of days see neither violated (rare consolidation)

**This is the foundation of the Kill-Switch State in the CEREBUS engine.**

### 3. Cross-Asset Universal Patterns

**Validated across EUR/USD, OIL/USD, ETH/USD:**
1. 132% invalidation is universal (70-75% violation rate)
2. -25% and -50% targets are highly reliable (>89% hit rate)
3. Asian Open Range has 77.4% containment rate
4. Monday London weekly bias: 55% reach -168% by Friday
5. When Asian and London align: -25% and -50% targets cluster within 10 pips 100% of time

### 4. Session Definitions (EST)

| Session | Time | Duration | Purpose |
|---------|------|----------|---------|
| Asian Range | 7:00 PM - 3:00 AM | 8 hours | Full Asian session |
| London Open | 2:00 AM - 6:00 AM | 4 hours | Formation window |
| Asian Open Range | 6:00 PM - 9:30 PM | 3.5 hours | Predictive window |
| Monday London | 3:00 AM - 11:00 AM | 8 hours | Weekly bias formation |
| NY-AM | 6:00 AM - 9:00 AM | 3 hours | Morning session |
| NY-PM | 9:00 AM - 11:00 AM | 2 hours | Afternoon session |
| Black Zone | 12:00 PM - 7:00 PM | 7 hours | Avoid trading |

### 5. The Overlay: Fibonacci ↔ Atomic Structure

**MAD's insight:** The atomic structure (ST/P90) is a more precise model of the same underlying physics as the Fibonacci approach.

**Mapping:**
| Fibonacci Level | Atomic Structure Equivalent |
|----------------|---------------------------|
| -25% target | Partial rebalance (32-50% DZ) |
| -50% target | Full AU completion |
| -100% target | 2× AU cascade |
| -168% target | 3× AU cascade (Deep State) |
| 132% invalidation | Kill-Switch State |
| Range A | Asian Range Deficit |
| T+0 Anchor | Session activation point |

**Why both matter:**
- Fibonacci: Simple, human-executable, works across all assets
- Atomic Structure: More precise, better for automation, tighter stops
- Together: Fibonacci gives the roadmap, atomic structure gives the precision

### 6. Multi-Market Model (Master Scroll)

**EUR/USD Model:**
- 281 weeks validated (Jan 2020 - May 2025)
- Monday London Range anchor (06:00 UTC)
- 1,401 sessions analyzed

**OIL/USD Model:**
- 281 weeks validated (benchmark model)
- Same Monday London Range anchor

**ETH/USD Model:**
- 215 weeks validated (Jan 2021 - Dec 2025)
- Friday Asian Range anchor (00:00-07:00 UTC)
- 948 Fibonacci hits confirmed

**Performance:**
- 12-24 trades/week across all markets
- 87-94% hit rate (depending on conditions)
- +42-54R weekly expected

---

## 📊 DATA IN EXCEL (Not Yet Processed)

The Excel file (`cerebus 3 market hoily grail (3).xlsx`, 10.5 MB) contains:
- 100 sheets
- 20,000+ data points
- Raw price CSV data
- The actual trading data that generated the PDF reports

**This is the source of truth.** The PDFs are just reader-friendly extracts from this Excel.

**Next step for CC:** Process the Excel to extract:
1. Raw price data per asset
2. Range A calculations per session
3. Fibonacci target hits/misses
4. 132% invalidation events
5. Session bifurcation data
6. Cross-asset correlation data

---

## 🎯 WHAT CC NEEDS TO PLAN

### Immediate Tasks
1. **Process the Excel file** — Extract all data, validate against PDF results
2. **Build the distribution tracker** — Already started in `quant-lab/distribution/tracker.py`
3. **Integrate Fibonacci + Atomic approaches** — Use Fibonacci as the roadmap, atomic structure for precision
4. **Update the Quant Bible** — Add the predecessor data and overlay mapping

### Key Questions for CC
1. Should the distribution tracker be a standalone module or integrated into the bridge?
2. Do we need to re-run backtests using the Fibonacci approach for comparison?
3. Should we add the 132% realignment trigger as a separate signal in the bridge?
4. How do we handle the Excel data — process it all or just extract key sheets?

### Files CC Should Read First
1. `quant-lab/reports/predecessor/crypto_fibonacci.txt` — Crypto Fibonacci model (clearest explanation)
2. `quant-lab/reports/predecessor/oilusd_bifurcation.txt` — 132% realignment trigger
3. `quant-lab/reports/predecessor/cross_asset_analysis.txt` — Cross-asset validation
4. `quant-lab/reports/predecessor/cerebus_master_scroll.txt` — Multi-market model
5. `quant-lab/ontology/manual_ontology.md` — Current ontology (already read)
6. `quant-lab/QUANT_BIBLE.md` — Current bible (already read)

---

## ⚠️ CRITICAL NOTES

1. **The Excel is the holy grail** — All PDF data comes from it. Process it carefully.
2. **Two approaches, one physics** — Don't treat them as separate systems. They're the same thing at different precision levels.
3. **The 132% trigger is universal** — 98% hit rate during bifurcation. This is the most important finding.
4. **Session timing is critical** — All times are EST. Wrong timing = wrong results.
5. **Asset-specific adjustments needed** — Crypto needs tighter stops (115% vs 132%), compressed delivery windows.

---

*Prepared by PM2 for CC planning. All data extracted from MAD's archive.*
