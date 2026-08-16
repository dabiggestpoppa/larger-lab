# MVE R0.5 — STATIC LEAKAGE AUDIT

> Checkpoint: MVE-R0.5-CAUSALITY-GATE · 2026-08-15
> Method: grep of the full `src/mve/` tree for future-leaning patterns
> (`.shift(-`, `iloc[i+`, `iloc[idx+`, `iloc[i + 1]`, centered rolling,
> whole-sample min/max in features). Every occurrence classified.

## Pattern inventory

### 1. `.shift(-1)` — forward returns (event-study labeling)
| Location | Class |
|---|---|
| `morphic_coordinates.py:334` (`analyze_coordinate_trends`) | EX_POST_ONLY |
| `sigma_states.py:317` (`analyze_event_trends`) | EX_POST_ONLY |
| `volatility.py` / `anchors.py` / `acceptance.py` / `rekey.py` / `regime.py` | none found (only `.shift(1)` past) |

Verdict: EX_POST_ONLY — allowed only for descriptive/event-study outcome
classification, never a live signal. SAFE with that restriction.

### 2. `iloc[i+1]` / `iloc[idx+1]` / `iloc[idx+horizon]` — forward access
| Location | Class |
|---|---|
| `acceptance.py:248` (`analyze_acceptance_forward_returns`) | EX_POST_ONLY |
| `acceptance.py:391,445` (regime/rebalancing effects) | EX_POST_ONLY |
| `regime.py:211,275` (regime-specific forward returns) | EX_POST_ONLY |
| `rekey.py:236,287,353` (rekey analyze forward returns) | EX_POST_ONLY |
| `sigma_states.py:278,569` (transition counting) | EX_POST_ONLY |
| `morphic_coordinates.py:300`, `regime.py:121,165,284` (transition matrices) | EX_POST_ONLY |
| ~~`signals.py:87,156,211`~~ **REMOVED (R0.5.1 repair)** — Models A/B/C no longer read bar i+1 to emit a signal at bar i; A/C emit at the confirmation bar i+1, B is realtime |

### 3. Pivot right-side lookahead (`i+1:i+window+1`)
| Location | Class |
|---|---|
| `anchors.py:129-130` (pivot high) | CAUSAL_DELAYED_CONFIRMATION — known at i+window; MUST be delayed before use |
| `anchors.py:157-158` (pivot low) | CAUSAL_DELAYED_CONFIRMATION — same |

### 4. RKEY-B future retest scan (`range(i + 1, min(i + 5, ...))`)
| Location | Class |
|---|---|
| `rekey.py` `_rekey_variant_b` | **REPAIRED (R0.5.1):** the retest scan still looks ahead, but the anchor is now scheduled and activated only AT the retest bar j (never at the scan-origin bar i) — CAUSAL_DELAYED_CONFIRMATION; verified diff 0.0 |

### 4b. Model E whole-sample scalar (new finding)
| Location | Class |
|---|---|
| `signals.py` `_calculate_state_progression_quality` (Q) — `(coords.diff().abs() > step).sum()/len` broadcast into every bar | **VIOLATION (BLOCKED)** — full-sample scalar repaints historical scores; Model E classified BLOCKED_LOGIC_SPEC and excluded from future scientific execution |

### 5. Trailing windows ending at i — all safe (CAUSAL_REALTIME)
- `acceptance.py:65` (occupancy `max(0, i - n_bars + 1):i + 1`)
- `anchors.py:181,188,211,218,244,279-280,310,341`
- `rekey.py:203` (RKEY-C `max(0, i - 2):i + 1`)
- `signals.py:223,434`

### 6. Whole-sample / full-history statistics
| Location | Class |
|---|---|
| `volatility.py:317-319` (estimator range/coverage in quality) | EX_POST_ONLY |
| `volatility.py:506`, `morphic_coordinates.py:204-205,261-262`, `acceptance.py:163-164,179-180,489-490` | EX_POST_ONLY (descriptive stats) |
| `frozen sigma` = first valid rolling vol (`volatility.py` `compare_volatility_fields`, `morphic_coordinates.py` `calculate_live_frozen_coordinates`) | CAUSAL_REALTIME — a series-prefix constant, not a whole-sample mean; invariant to future mutation (tested) |

### 7. Backtest evaluation internals
| Location | Class |
|---|---|
| `backtest.py:139,319,500` (drawdown via running max) | causal evaluation |
| `backtest.py:397-398` (walk-forward train slices) | causal (train = past) |

## Summary (post-R0.5.1-repair re-audit)

| Class | Count |
|---|---|
| CAUSAL_REALTIME (trailing/elementwise) | ~25 sites + repaired Models B |
| CAUSAL_DELAYED_CONFIRMATION | pivots (2) + RKEY-B + Models A/C |
| EX_POST_ONLY (whole-sample descriptive / forward-return labeling) | ~20 sites (unchanged, per R0.5.1-N) |
| **CAUSAL_VIOLATION (unresolved)** | **0 in code eligible for future scientific execution** |
| BLOCKED (excluded) | Model D (contradictory logic), Model E (Q whole-sample scalar) |

## Verdict

**No unresolved CAUSAL_VIOLATION remains in code eligible for future
scientific execution.** The four R0.5-gate violations were repaired with
human authorization (RKEY-B delayed activation; Models A/C confirmation-bar
known times; Model B cosmetic-read removal). Two components remain BLOCKED
and excluded per the R0.5.1 pass gate: Model D (ambiguous contradictory
conditions, audit in `MVE_R05_1_MODEL_D_AUDIT.md`) and Model E (whole-sample
Q component). The remaining forward-references in `src/mve/` are all
`EX_POST_ONLY` descriptive analyzers, preserved unchanged per R0.5.1-N.
