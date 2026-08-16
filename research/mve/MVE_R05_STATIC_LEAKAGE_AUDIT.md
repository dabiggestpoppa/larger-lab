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
| **`signals.py:87,156,211` (`next_coord = morphic_coordinates.iloc[i+1]`)** | **CAUSAL_VIOLATION** — Models A/B/C gate the signal AT bar i on bar i+1's coordinate (backdated confirmation) |

### 3. Pivot right-side lookahead (`i+1:i+window+1`)
| Location | Class |
|---|---|
| `anchors.py:129-130` (pivot high) | CAUSAL_DELAYED_CONFIRMATION — known at i+window; MUST be delayed before use |
| `anchors.py:157-158` (pivot low) | CAUSAL_DELAYED_CONFIRMATION — same |

### 4. RKEY-B future retest scan (`range(i + 1, min(i + 5, ...))`)
| Location | Class |
|---|---|
| `rekey.py` `_rekey_variant_b` (`for j in range(i + 1, ...)` then `rekey_anchor = current_coord`) | **CAUSAL_VIOLATION** — anchor at bar i decided by bars i+1..i+4; historical rekey moves with future data (measured diff 1.033) |

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

## Summary

| Class | Count |
|---|---|
| CAUSAL_REALTIME (trailing/elementwise) | ~25 sites |
| CAUSAL_DELAYED_CONFIRMATION | 2 (pivot high/low) |
| EX_POST_ONLY (whole-sample descriptive / forward-return labeling) | ~20 sites |
| **CAUSAL_VIOLATION** | **4 (RKEY-B; signal Models A/B/C)** |
| BLOCKED (crash/NameError) | 2 (RKEY-C `int(NaN)`, Model E undefined `n`) |

## Verdict

**No unresolved critical violation in the causal research infrastructure**
(loader, resampler, volatility, coordinates, sigma states, occupancy,
acceptance, regime labeling, runner, persistence). All 4 violations live in
`BLOCKED_SCIENTIFIC_IMPLEMENTATION` scientific stubs that no phase executes.
They are recorded as blockers for P6 (rekey) and P7 (signals), not repaired —
per the immutable-rule STOP/escalate protocol, repairing them requires human
authorization (`SCIENTIFIC_LOGIC_CHANGE_REQUIRED`).
