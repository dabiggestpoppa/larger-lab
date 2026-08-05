# 📊 CONTENT ENGINE — DATA SOURCES MASTER INDEX

> **Last Updated:** 2026-06-14
> **Purpose:** Every data source the content engine can pull from for content creation.

---

## 🔴 TIER 1: PRIMARY DATA (Highest Content Value)

### 1. QUANTLAB BIBLE — Locked Parameters
- **File:** `quant-lab/QUANTLAB_BIBLE.md`
- **Contents:** 20 calibrated assets, locked AU values, K-Factors, T1 triggers
- **Key Stats:**
  - EURUSD: K=0.46, T1=12p
  - GBPUSD: K=0.52, T1=14p
  - BTCUSD: K=0.35, T1=500
  - ETHUSD: K=0.36, T1=12
  - XAUUSD: K=0.38, T1=180p
- **Content Use:** "We calibrated 20 assets. Here's exactly what the math says."

### 2. CEREBUS ONTOLOGY — Strategy Philosophy
- **File:** `quant-lab/CEREBUS_ONTOLOGY.md`
- **Contents:** MAD's definitions, AU math, time windows, tier logic
- **Key Concepts:**
  - AU = 50% of K-Means centroid (NOT pips, NOT Fibonacci)
  - Zero-Buffer OCC = SL at exact impulse extreme
  - 12PM EST = full state reset
  - 80% Rule = close invalidation (absolute, close-only)
- **Content Use:** "Here's why everyone gets AU wrong."

### 3. SWEEP MATRIX — Accuracy-Frequency Curve
- **File:** `quant-lab/reports/SWEEP_MATRIX.md` + `SWEEP_MATRIX_V2.md`
- **Contents:** Full sweep results across 28 pairs
- **Key Stats:**
  - Floor (max trades): ~158,375 trades | 81.1% WR | PF 11.5
  - Ceiling (max accuracy): 29,438 trades | 90.8% WR | PF 20+
- **Content Use:** "We swept 28 pairs. Here's the accuracy-frequency curve."

### 4. TRIGGER SWEEP RESULTS — Per-Asset Accuracy
- **Files:** `quant-lab/reports/trigger_sweep_*.json` (20+ files)
- **Contents:** Per-pair trigger optimization results
- **Key Stats:** Best trigger values per pair, win rates, profit factors
- **Content Use:** "EURUSD optimal trigger is 12 pips. Here's the proof."

### 5. MANUAL ONTOLOGY — Deep Domain Knowledge
- **File:** `quant-lab/ontology/manual_ontology.md`
- **Contents:** 55 Q&As on market physics, strategy, edge
- **Content Use:** Educational content, myth-busting, deep dives

---

## 🟡 TIER 2: BACKTEST RESULTS

### 6. Symmetry Trap — Full Backtest (19 Assets)
- **File:** `quant-lab/reports/INDEX.md` + `reports/per-asset/`
- **Contents:** Per-asset backtest results
- **Key Stats:**
  - ETHUSD: 96.9% WR, PF 50.34, 547 trades
  - HK50: 94.0% WR, PF 40.30, 385 trades
  - BTCUSD: 92.6% WR, PF 26.52, 801 trades
  - Combined: 12,488 trades, 81.2% WR, PF 26.58
- **Content Use:** "96.9% win rate on ETHUSD. 547 trades. Not a backtest fantasy."

### 7. DTB Training Pipeline — Distribution Predictions
- **File:** `quant-lab/ml/dtb_lab/MASTER_LAB_REPORT.md`
- **Contents:** 3-phase training results
- **Key Stats:**
  - Intraday T2: MAE=1.95 pips, R²=0.97
  - Macro T3: MAE=6.2 pips, R²=0.975
  - Hit rates: -25%=94.8%, -50%=90.3%, 132%=67.6%
- **Content Use:** "We trained AI to predict price boundaries. 97% accuracy at T2."

### 8. Pattern Recognizer — 18 Patterns
- **File:** `quant-lab/ml/pattern_recognition.py` + reports
- **Contents:** 18 pattern detectors with accuracy data
- **Key Stats:** Pattern detection rates, formation frequencies
- **Content Use:** "We detect 18 patterns. Here's how often each one fires."

### 9. CEREBUS Scanner — Wave 1-3 Results
- **File:** `quant-lab/ml/BUILD_NOTES_CEREBUS.md`
- **Contents:** Full scanner build results, 120 tests
- **Key Stats:** Feature engine (41 features), XGBoost (87.1% CV), SHAP importance
- **Content Use:** "41 features. 87% cross-val accuracy. Here's what matters."

---

## 🟢 TIER 3: RESEARCH & ANALYSIS

### 10. Research Mesh — Paper Synthesis
- **Location:** `core/research/` + `O2C-VAULT/research/`
- **Contents:** Synthesized papers from OpenAlex + arXiv + S2
- **Example:** Geopolitical Risk + GBS Airlock theory (5 papers, 1847 words, 0.72 confidence)
- **Content Use:** "We analyzed 5 papers on geopolitical risk. Here's the unified theory."

### 11. Horizon News Radar
- **Location:** `core/research/horizon/`
- **Contents:** AI-powered news monitoring (HN, Reddit, Twitter, RSS)
- **Content Use:** Timely content based on trending topics

### 12. CONTENT FUEL — Holy Grail Data
- **File:** `content-engine/knowledge/CONTENT_FUEL.md`
- **Contents:** 1,626 stat entries, top-tier stats, Fibonacci truth bombs
- **Key Stats:**
  - 90.3% hit rate across 132 sessions
  - 25% Fib level: 73.9% exact hit rate
  - 221 failure events analyzed
  - 72.6% of "failures" are actually restarts
- **Content Use:** Pre-packaged stat bombs for social media

---

## 📁 Key File Locations

| Data Source | File Path |
|-------------|-----------|
| Quant Bible | `quant-lab/QUANTLAB_BIBLE.md` |
| Quant Bible (alt) | `quant-lab/QUANT_BIBLE.md` |
| CEREBUS Ontology | `quant-lab/CEREBUS_ONTOLOGY.md` |
| Manual Ontology | `quant-lab/ontology/manual_ontology.md` |
| Sweep Matrix | `quant-lab/reports/SWEEP_MATRIX.md` |
| Trigger Sweeps | `quant-lab/reports/trigger_sweep_*.json` |
| Backtest Results | `quant-lab/reports/INDEX.md` |
| DTB Results | `quant-lab/ml/dtb_lab/MASTER_LAB_REPORT.md` |
| Pattern Recognizer | `quant-lab/ml/pattern_recognition.py` |
| CEREBUS Build | `quant-lab/ml/BUILD_NOTES_CEREBUS.md` |
| Content Fuel | `content-engine/knowledge/CONTENT_FUEL.md` |
| Research Papers | `O2C-VAULT/research/` |
| Horizon News | `core/research/horizon/` |

---

## 🔄 Data Flow for Content Creation

```
[Quant Lab Reports] ──→ [CONTENT_FUEL.md] ──→ [Content Creator Agent]
[CEREBUS Ontology]   ──→ [Brand Voice]     ──→ [Templates]
[Sweep Results]      ──→ [Stat Bombs]      ──→ [Social Media]
[Research Papers]    ──→ [Deep Dives]      ──→ [Long-form]
[Horizon News]       ──→ [Timely Takes]    ──→ [Threads]
```

---

## 📊 Quick Stats for Content (Verified)

| Stat | Value | Source |
|------|-------|--------|
| Overall hit rate | 90.3% | 132 sessions |
| ETHUSD WR | 96.9% | 547 trades |
| BTCUSD WR | 92.6% | 801 trades |
| Combined WR | 81.2% | 12,488 trades |
| Combined PF | 26.58 | Multi-asset |
| DTB T2 R² | 0.97 | 15,570 days |
| XGBoost CV | 87.1% | 5.3M samples |
| Fib 25% hit | 73.9% | EURUSD Asian |
| Failure restart rate | 72.6% | 221 events |
| Live trades | 25,540+ | All assets |
| Calibrated assets | 20 | Per-pair sweep |
