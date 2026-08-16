# MVE P6.5 — MINIMAL SURVIVING MVE CORE

> **Checkpoint:** MVE-P6.5-STRUCTURAL-PRUNING-SEAL
> **Status:** SEAL — definitional document, no new science

---

## 1. The core

The minimum scientifically surviving MVE architecture after P4 (acceptance)
and P6 (rekey) are removed as independent predictive layers is:

```
price (OHLCV, canonical H1)
  → causal anchors (trailing extremes; P4_TRAILING_WINDOW=50, shifted)
  → causal volatility (close-to-close rolling estimator)
  → morphic coordinates (x = signed ln(price/anchor)/vol)
  → sigma states (S_t = sign(x) · floor(|x|/step))
  → model-specific decision logic (Models A/B/C, pending falsification)
```

Every layer in this chain is:

- causally executable (all CAUSAL_REALTIME or CAUSAL_DELAYED_CONFIRMATION in
  the sealed R0.5.2 matrix; perturbation 0.0, truncation PASS),
- independent of the pruned acceptance/rekey predictive layers,
- independent of the blocked Model D/E logic.

## 2. What is explicitly excluded from the core

| Layer | Role after P6.5 |
|---|---|
| Acceptance (P4 family) | **DESCRIPTIVE_ONLY** — may appear as a descriptive control in future analyses; never an alpha feature |
| RKEY-A / RKEY-B | **PRUNED** — no predictive credit; not required for coordinate maintenance (the executed field uses trailing-extreme anchors, rekey.py is never consumed by coordinate construction) |
| RKEY-C | **ARCHIVED_INSUFFICIENT_N** — not promoted, not a P7 input |
| Model D | **BLOCKED_LOGIC_SPEC** |
| Model E | **BLOCKED_LOGIC_SPEC** |
| generate_all_signals | **BLOCKED_AGGREGATE** (calls Model E) |

## 3. The core question that remains

The MVE hypothesis has been reduced to one falsifiable claim:

> **The morphic coordinate/sigma-state field itself carries structural
> information about downstream state behavior — beyond raw distance,
> volatility state, and momentum — and Models A/B/C are candidate
> transformations of that field worth testing against simple baselines.**

P4 and P6 established that *acceptance* and *rekey* do NOT add independent
information beyond coordinate distance and sigma state. P6.5 does not claim
the coordinate field itself is validated — that is precisely what P7 must
falsify.

## 4. Rekey as state maintenance: settled

P6.5 examined whether rekey is mechanically required for coordinate
construction. **It is not.** The executed P4/P6 field builds anchors as
trailing prior-N-bar extremes (`.rolling(P4_TRAILING_WINDOW).max().shift(1)`
and the min mirror) and computes coordinates directly from them. `rekey.py`
is never imported or consumed by the coordinate pipeline. Rekey therefore
receives no role in the minimal core — neither predictive nor maintenance.

## 5. What the core does NOT contain

- No trade targets, stops, exits, sizing, or PnL.
- No acceptance/rekey alpha features.
- No Model D/E logic.
- No 2026 data (FINAL_HOLDOUT_PENDING).
- No ML.

## 6. Consequence for P7

P7 (if human-authorized) must falsify Models A/B/C against the simple
baselines recorded in `MVE_P65_BASELINE_CROSSWALK.csv`:

1. coordinate-only (distance) baseline,
2. sigma-only baseline,
3. coordinate + sigma baseline,
4. simple breakout,
5. volatility-normalized breakout,
6. simple momentum,
7. simple mean reversion (if relevant),
8. persistence baseline (if relevant).

A model receives credit only if it adds information beyond its closest
simple equivalent.
