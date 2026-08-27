# LOWER-FIELD-2 INTEGRITY REPAIR AUDIT

**Decision node:** `INTEGRITY_PASS_REQUIRED = TRUE`
**Gate cleared.** No cross-rank section is DATA_BLOCKED.

Two distinct corruption classes were found and repaired before any scientific
interpretation advanced.

---

## BUG 1 — Top-500 multi-day return corruption (FIXED)

**Location:** `lower_field_1/scripts/lf1_common.py :: canonical_upper_bands()`

**Broken expression:**
```
cs      = groupby(cmc_id)[log_ret].cumsum()     # cumulative log return
cs_shift= groupby(cmc_id)[log_ret].transform(lambda s: s.shift(w))   # shifts the DAILY log-return
ret_wd  = expm1(cs - cs_shift)                  # ??? not a w-day return
```

`cs_shift` shifted the **daily log-return** `_logf` (not the cumulative sum),
so `cs - cs_shift` = "cumulated log return minus a single earlier daily
log-return", which is **not** a w-day return. It inflated `ret_3d..ret_30d`
by roughly the accumulated-history factor (~50x). Because the normalized
amplitude used `|ret_h| / sigma_t0`, the comparison bands showed impossible
values — e.g. **26-100 3D median normalized move ≈ 181σ**.

**Correct expression (matches the proven LF0 501-2000 panel exactly):**
```
cs      = groupby(cmc_id)[log_ret].cumsum()
cs_shift= groupby(cmc_id)[cs].transform(lambda s: s.shift(w))   # shift the CUMSUM
ret_wd  = expm1(cs - cs_shift)
```

Returns are computed on the **full continuous per-asset series (ranks 1-500)
BEFORE band filtering**, so rank migration across a band boundary keeps
continuity (mirrors LF0 `merge_canonical_series`).

**Verification:**
- Median |3D| move: corrected 4.6% (broken 233%); 3D p99: 50% (broken 5e6+).
- Parity vs LF0 algorithm: **max |diff| = 0.0** across 1,043,100 rows and all
  horizons (1D/3D/7D/14D/30D).

**Impact:** only outputs `03`/`04` (amplitude and cross-rank sigma comparisons)
used the corrupted comparison bands. The lower-field 501-2000 results (05-30 of
LOWER-FIELD-1) were NOT affected because LF0's `add_causal_features()` was
already correct. The 26-100/101-250/251-500 comparison rows are now repaired.

---

## BUG 2 — Sigma band-truncation artifact (AVOIDED)

**Observation:** computing the trailing-63d sigma on a **band-filtered slice**
(dist vs the full continuous panel) changed the unconditional 1D `>=3σ` rate
from ~2.5% to ~8%, purely because band-filtering truncates migrated assets'
series and distorts the rolling window.

**Rule enforced across LF2:** sigma (and all rolling/cumulative state) is
computed on the **full per-asset series before any band filter**, then rows are
assigned to bands by their PIT rank. `lf2_load.build()` implements this; scripts
must call `L.load()` and never re-derive sigma on a band slice.

**consequence check:** with the continuous definition, `P(|ret_1d| >= 3σ) =
2.25%` unconditional — consistent with the LF1 `04` value and with the known
"~2.4-2.5%" rate. The earlier "8%" was our own contamination artifact.

---

## Event-count reconciliation (the "329k / 10% >=3σ" claim)

LOWER-FIELD-1's summary conflated the **union-of-lenses event count** with the
`>=3σ` count. Reconciliation (continuous causal sigma, full primary panel):

| metric | value |
|---|---|
| rows ranks 501-2000 | 3,290,806 |
| rows with finite 1D sigma | 2,989,851 |
| **unconditional 1D >=3σ** | **2.25%** |
| unconditional 1D >=2σ | 5.4% |
| unconditional 1D >=4σ | 1.2% |
| rows passing sigma>=3 lens | 73,881 |
| rows passing raw>=15% lens | 280,060 |
| union (sigma>=3 OR raw>=15%) | 186,521 |
| rows passing BOTH lenses | 58,611 |
| share of union genuinely >=3σ | ~40% |

**Resolution:** the "~329k events" figure is the **union of event lenses**,
dominated by the far-more-lenient raw `>=15%` and cross-sectional lenses. The
true `>=3σ` population is ~74k, and the unconditional 1D `>=3σ` rate is ~2.3%,
**not 10%**. The 329k/10% framing is **DISSOLVED**. The meaningful
high-tail statistical population is the `>=3σ` lens.

---

## Sanity of corrected cross-rank sigma (output 03)

All bands now diffuse correctly — `3D median ≈ sqrt(3) x 1D`, `14D ≈ sqrt(14) x
1D`, no `impossible_median_ratio` anywhere:

| band | 1D med | 3D med | 14D med | p99 3D |
|---|---|---|---|---|
| 26-100 | 0.51 | 0.90 | 2.09 | 6.29 |
| 101-250 | 0.48 | 0.86 | 2.07 | 6.52 |
| 251-500 | 0.46 | 0.81 | 1.95 | 6.33 |
| 501-750 | 0.42 | 0.76 | 1.87 | 7.32 |
| 751-1000 | 0.42 | 0.76 | 1.86 | 6.83 |
| 1001-1500 | 0.40 | 0.72 | 1.75 | 6.74 |
| 1501-2000 | 0.36 | 0.66 | 1.59 | 6.33 |

The 1D median normalized move declines monotonically with depth — this is a
real normalization-coordinate gradient (denominator, not a fattened tail) and
is documented for the displacement workstream.

---

## Required test checklist

- [x] no impossible median sigma ratios (verified all bands)
- [x] denominator strictly pre-event (compute_sigma uses shift(1) rolling)
- [x] no zero/near-zero sigma leakage (sigma min 40 obs, MAD guarded)
- [x] cumulative-return unit parity vs LF0 (max diff 0.0)
- [x] random-sample manual forward reconstruction (max diff 8.9e-16)
- [x] parity between independent calculation paths

**INTEGRITY_PASS_REQUIRED = TRUE.** All cross-rank work proceeds on corrected
features with continuous causal sigma.