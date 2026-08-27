# 21 — INTEGRITY AUDIT

## Bugs Found and Corrected

### Bug 1: Multi-day return computation (CRITICAL)

**Location:** `lf_build_panel.py` line ~197, `lf_analysis_structure.py` lines ~85, ~220, ~310, ~383

**Error:** `cs_shift = groupby("cmc_id")["_logf"].transform(lambda s: s.shift(w))`

This shifts the **raw logf** (single-day log return) by w positions, then subtracts from the cumulative sum:

```
ret_wd = expm1(cumsum(t) - logf(t-w))  # WRONG
```

Should shift the **cumulative sum**:

```
ret_wd = expm1(cumsum(t) - cumsum(t-w))  # CORRECT
```

**Impact:** ALL multi-day returns (ret_3d, ret_7d, ret_14d, ret_30d, ret_60d) were incorrect across the entire panel. This affected Phases F, G, H of the structure analysis and all forward-return-dependent results.

**Fix:** Store cumsum as a column, shift the cumsum:

```python
df["_cs"] = df.groupby("cmc_id", sort=False)["_logf"].cumsum()
cs_shift = df.groupby("cmc_id")["_cs"].transform(lambda s: s.shift(w))
df[f"ret_{w}d"] = np.expm1(df["_cs"] - cs_shift)
```

### Bug 2: Rank velocity not grouped by asset (MODERATE)

**Location:** `lf_build_panel.py` line ~209, `lf_analysis_structure.py` lines ~94, ~229, ~315

**Error:** `df["rank"].transform(lambda s: s.shift(w) - s)`

This shifts the **entire DataFrame's rank column** by w positions, crossing asset boundaries. At each asset boundary, the first ~7 rows use a different asset's rank.

**Impact:** ~50,000 rows affected (first ~7 dates of each asset). Rank velocity values at asset boundaries are incorrect.

**Fix:** Group by cmc_id:

```python
df.groupby("cmc_id")["rank"].transform(lambda s: s.shift(w) - s)
```

## Corrected Results

After patching the panel and re-running all analyses:

### Momentum State Geometry (corrected vs buggy)

| Shape | Band | Buggy Extreme% | Corrected Extreme% |
|-------|------|---------------|-------------------|
| SHORT_HOT_MEDIUM_COLD | 1-25 | 5.9% | 15.1% |
| SHORT_HOT_MEDIUM_COLD | 1501-2000 | 31.2% | 32.0% |
| SHORT_HOT_MEDIUM_HOT | 1-25 | 5.0% | 21.4% |
| SHORT_HOT_MEDIUM_HOT | 1501-2000 | 23.4% | 36.5% |

The gradient is still present but less dramatic. The buggy code was inflating the baseline and compressing the range.

### Reversal Rates (corrected vs buggy)

| Event | Band | Buggy Reversal | Corrected Reversal |
|-------|------|---------------|-------------------|
| UP trailing-252d | 501-750 | 76.9% | 66.6% (1D), 71.7% (30D) |
| DOWN trailing-252d | 501-750 | 73.0% | 50.7% (1D), 33.7% (30D) |

The buggy code was showing uniformly high reversal. The corrected data shows asymmetric reversal: UP events reverse more strongly than DOWN events.

## Files Corrected

- `lf_build_panel.py`: Fixed ret_3d..60d and rank_vel computation
- `lf_analysis_structure.py`: Fixed canonical loading, forward features, rank velocity
- `lf_patch_features.py`: New script to patch existing panel without full rebuild
- All downstream results (10, 11, 12, plots) re-generated
