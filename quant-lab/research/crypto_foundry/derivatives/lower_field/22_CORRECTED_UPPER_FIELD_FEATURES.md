# 22 — CORRECTED UPPER FIELD FEATURES

## Canonical Upper-Band (1-500) Feature Construction

The canonical Top-500 panel (ALT_DATA_1_1) is loaded in `lf_analysis_structure.py` via `load_canonical_upper()` and `lf_analysis_events.py` via `load_panels()`.

### Multi-day Returns (CORRECTED)

```python
# Correct algorithm:
can["_logf"] = np.where(ok, np.log1p(can["ret_1d"].clip(lower=-0.9999)), np.nan)
can["_cs"] = can.groupby("cmc_id", sort=False)["_logf"].cumsum()
for w in [3, 7, 14, 30, 60]:
    cs_shift = can.groupby("cmc_id")["_cs"].transform(lambda s: s.shift(w))
    can[f"ret_{w}d"] = np.expm1(can["_cs"] - cs_shift)
```

This computes: `ret_wd(t) = exp(Σ log(1+r) from t-w+1 to t) - 1`

Which is the cumulative product of daily returns over the w-day window.

### Rank Velocity (CORRECTED)

```python
# Correct algorithm:
can[f"rank_vel_{w}d"] = can.groupby("cmc_id")["rank"].transform(
    lambda s: s.shift(w) - s)
```

This computes: `rank_vel_wd(t) = rank(t-w) - rank(t)`

Positive = improving rank (moving toward rank 1).

### Other Features (UNCHANGED)

- `ret_1d`: Computed from price ratio (correct)
- `mkt_ret_1d`: Cap-weighted Top-500 return from total_mcap (correct)
- `btc_ret_1d`, `eth_ret_1d`: From terrain file (correct)
- `vol_accel`: Volume / trailing 7d median (correct)
- `listing_age_days`: Days since CMC dateAdded (correct)

## Events Script Canonical Loading

The events script (`lf_analysis_events.py`) loads canonical with only basic columns and computes `ret_1d` from price. It does NOT compute multi-day returns or rank velocity for canonical data — it only uses `ret_1d` and `mkt_ret_1d`. Therefore the events script was NOT affected by these bugs.
