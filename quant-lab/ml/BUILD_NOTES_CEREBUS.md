# CEREBUS Neuro-Symbolic Scanner — CC Build Notes
> **Created:** 2026-06-10 | **Agent:** CC (Claude Code) | **Status:** PLANNING → READY TO BUILD
> **Master Plan:** `CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md`
> **Source:** CEREBUS BUILD.txt (4-Step Architecture)

## What This Build Is

The **largest build yet** — a complete Neuro-Symbolic Scanner that reads market constraint-system physics and alerts when resolution probability exceeds 85%.

**NOT** a retail trading bot. No RSI, no MACD, no black-box guessing. Pure CEREBUS constraint-resolution physics mapped by AI.

## Architecture (4 Steps)

```
Step 1: Data Cleanup + Macro Feature Engine + Pattern Recognition + Labels
Step 2: Retrain XGBoost + Entry Scorer on FULL 30-feature set + Ironclad Rules
Step 3: RAG Oracle (ChromaDB vector store, smart PDF chunking, query engine)
Step 4: Guardian Alert Pipeline (live scanner + alignment + Telegram dispatch)
```

## Current Baseline

| Component | Status | Tests |
|-----------|--------|-------|
| Phase 1 (Data: CSV→Parquet, AR, K-Means) | ✅ Complete | 14/14 |
| Phase 2 (XGBoost, Entry Scorer) | ✅ Complete (on 8 features) | 18/18 |
| Phase 5 (Guardrails, Drift, Shadow) | ✅ Complete | 8/8 |
| **Total existing** | | **40/40** |
| Macro Feature Engine (MLR, Fib, 132%) | ❌ NOT BUILT | 0 |
| Pattern Recognition (Alpha/Beta/AB-CD) | ❌ NOT BUILT | 0 |
| Label Generator v2 (order-of-events) | ❌ NOT BUILT | 0 |
| RAG Oracle (ChromaDB + chunker) | ❌ NOT BUILT | 0 |
| Guardian Pipeline (live + Telegram) | ❌ NOT BUILT | 0 |
| Ironclad Rules Engine | ❌ NOT BUILT | 0 |

## PM's Data Extraction (INPUT to this build)

PM (Polymorph) has extracted:
- **99 files, 35MB** from Holy Grail Excel (97 sheets) + 55 PDFs
- `raw_data/`: 9 CSV files (EURUSD, ETH, OILUSD OHLCV)
- `stats/`: 84 CSV files (hit rates, Fib analysis, patterns, ILM zones)
- `unified/master_feature_store.json`: 1626 entries (586 tagged, 1040 UNKNOWN)
- `pdf_stats/pdf_master_stats.json`: 1101 stat entries from 55 PDFs

**Data quality issues to fix:**
1. 1040/1626 entries have `asset: UNKNOWN`
2. 1066/1626 entries have `pattern: UNKNOWN`
3. Raw CSVs have mixed column naming
4. No standardized UTC alignment across sources

## Execution Order

### Wave 1 (CC leads, PM2 supports)
1. **Data Cleanup** — Unify raw CSVs, fix UNKNOWN entries, produce clean dataset
2. **Macro Feature Engine** — MLR, Fib targets, 132% kill-switch, ILM states
3. **Label Generator v2** — Forward-looking labels with order-of-events tracking

### Wave 2 (OC2 leads, CC supports)
4. **RAG Oracle** — ChromaDB + smart chunking + query engine
5. **Retrain Models** — XGBoost + entry scorer on 30 features + ironclad rules

### Wave 3 (OC2 leads, AS supports)
6. **Guardian Pipeline** — Live scanner + alignment + Telegram dispatch
7. **Integration Tests** — End-to-end validation

## Dependencies to Add

```
chromadb>=0.4.0          # Vector database for RAG Oracle
sentence-transformers>=2.0  # Embeddings for ChromaDB
```

## Constitution (12 Rules — NON-NEGOTIABLE)

1. Python only
2. No Track A/B — ONE unified pipeline
3. Close-only SL — M5 CLOSE beyond OCC Extreme
4. Zero-buffer OCC — SL at exact impulse extreme
5. Gear Shift modifies TARGET ONLY
6. 12PM EST Hard Exit — no exceptions
7. No online learning — model frozen between quarterly re-trains
8. Fallback to hardcoded — confidence < 0.6 → manual tiers
9. No retail indicators — no RSI, MACD, BB in feature store
10. RAG purity — no LLM fine-tuning, only RAG
11. Time-series split only — never random split
12. Separation of church and state — Macro/Micro isolated

## Success Criteria

| Metric | Target |
|--------|--------|
| Clean dataset | 18 assets × 4 years, no NaN |
| Macro features | 12 new features per bar |
| XGBoost CV accuracy | ≥ 89% on 30 features |
| SHAP physics check | `dist_to_132_pct` in top 5 |
| RAG query latency | < 200ms |
| Guardian alert latency | < 5s candle→Telegram |
| Total tests | 80+ (40 existing + 40 new) |

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| PM extraction incomplete | HIGH | Audit all 99 files, fill gaps ourselves |
| 1040 UNKNOWN entries | MEDIUM | Regex + context classification |
| PDF OCR quality | MEDIUM | PyMuPDF first, flag low-confidence |
| XGBoost overfitting (30 features) | MEDIUM | Regularization + SHAP check |
