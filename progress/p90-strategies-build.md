# P90 Strategies Build — Progress

## Status: ✅ COMPLETE (2026-05-29)

### Scope (MAD directive)
Reconstruct ALL P90 strategies from the manual/ontology, following the DMR pattern.
These are Model A (P90 Kinetic Engine) variants.

### File
`quant-lab/engines/p90_engine.py`

### Implemented
1. ✅ `P90Engine` class — handles ALL Model A variants in one engine
2. ✅ `P90Variant` enum: INITIAL, CASCADE, STALL_HARVEST, EWS
3. ✅ P90 detection: body >= per-hour threshold (calibrated)
4. ✅ Elastic vs Plastic deformation filter (cerebus_p90.md Section II)
5. ✅ Entry: immediate close of P90 candle (NO pullback, NO OCC)
6. ✅ SL: 80% of P90 body (Initial/Stall) or 168% of body (Cascade)
7. ✅ Targets: TP1 = -25% AR, TP2 = -50% AR (Initial/Cascade/Stall variants)
8. ✅ Cascade detection: same-dir P90 within 120 min of last exit
9. ✅ Stall-Harvest: P90 at 168% AR zone, binary reversion target
10. ✅ EWS: Opposite P90 at target = force-close exit signal, NOT reversal
11. ✅ Calibration function: `calibrate_p90()` from historical M5 data
12. ✅ Per-hour P90 thresholds (EUR/USD reference values)
13. ✅ Session management, state reset, hard exit
14. ✅ Engine isolation: P90 mechanics never mix with Symmetry Trap

### Variant Details

#### Base 80 / Initial P90
- First P90 breach of Asian Range boundary
- Entry: close of P90 candle
- SL: 80% of P90 candle body
- TP1: -25% of Asian Range
- TP2: -50% of Asian Range

#### Cascade P90
- 2nd/3rd same-direction P90 within 120 min of SL/TP exit
- Entry: close of cascade P90 candle
- SL: 168% of NEW P90 body
- TP1: -25% AR, TP2: -50% AR

#### Stall-Harvest
- P90 prints at/near 168% AR Stall Zone
- Entry: close of P90 candle
- SL: 80% of P90 body
- TP1: reversion to AR boundary
- TP2: -25% AR extension

#### EWS (Early Warning System)
- Opposite-direction P90 prints at/after TP target reached
- NOT an entry — it's an EXIT signal
- Force-close any remaining position immediately

### Verification
- ✅ SYNTAX OK
- ✅ IMPORT OK (module loads, all classes instantiate)
- ✅ Session initialization works
- ✅ Variant enum complete (4 variants)
- ✅ P90 thresholds load correctly

### Sources Cited
- cerebus_p90.md: Sections I-VIII (full P90 ontology)
- cerebus_dual_engine.md: Section I (Great Demarcation), Section II (Target Interplay)
- cerebus_unified_topology.md: Section II (Model A table), Section III (5 Axioms)
- cerebus_qa_recap.md: Target hierarchy, regime-behavior matrix
- cerebus_forward.md: Prime Directive, single state, computable invariants
- manual_ontology.md: Sections 1-4, Computable Mechanics

### Next Steps (for later)
- [ ] Backtest: wrap p90 engine in MT5 backtest following DMR pattern (`dmr_multi_pair_v2.py`)
- [ ] Live executor: wrap p90 engine in MT5 live executor following DMR pattern (`dmr_executor.py`)
- [ ] Per-pair P90 calibration (`p90_scanner.py` — may already exist)
- [ ] Dual-engine convergence detection (P90 + Symmetry Trap overlap)
- [ ] Option A / Blind Chain mode for Symmetry Trap (layer on top of base)
- [ ] Extended TP ladder for Symmetry Trap (-25% AR, -50% AR, Deep State)
