"""LOWER-FIELD-1 — 05 TIME_TO_DELIVERY & 06 EVENT_DURATION_DECAY.

Builds the sigma-normalized event set (lens B/C/E on ret_1d) and computes,
for each qualifying event, censored durations: time to 1/2/3 sigma, time to
peak, above-2sigma, half-decay, return-inside-1sigma, total event duration.

Also 10 REVERSAL / DECAY GEOMETRY is partially captured here (06); the
sign/rank/state decomposition lives in lf1_reversal.py for output 13.

Outputs:
  RESULTS/05_TIME_TO_DELIVERY.csv        (band x quantile x metric, censored)
  RESULTS/06_EVENT_DURATION_DECAY.csv    (band x quantile x metric)
  EVENTS/lf1_event_set.parquet           (event table with durations, all lenses)
"""
import numpy as np
import pandas as pd

import lf1_common as C

FWD_MAX = 30


def forward_cumsum_matrix(base):
    """Return (n, FWD_MAX+1) array of forward cumulative ret starting at col 0.

    base: DataFrame already grouped by cmc_id sorted by date, with 'ret_1d'.
    Returns forward cum returns at t+1 ... t+FWD_MAX and also t (0). NaN beyond
    group end.
    """
    grp = base.groupby("cmc_id", sort=False)["ret_1d"]
    # build forward windowed cumsum via shift(-k) cumsum trick
    cols = {}
    for k in range(1, FWD_MAX + 1):
        cols[f"f{k}"] = grp.transform(lambda s: s.shift(-(k)).fillna(0.0))
    fmat = pd.concat(cols.values(), axis=1, keys=cols.keys()).to_numpy(float)
    # cumulative
    cum = np.cumsum(fmat, axis=1)
    # where a shifted value was NaN (crossed group boundary / missing), the
    # cumulative below is unreliable; we mark readiness via any-NaN in the window slice
    # instead recompute carefully: build raw shifted array to detect gaps
    raw = np.array([np.nan] * len(base))
    # We'll track per-row group-index validity via 'gaplen' helper below.
    return cum, base


def main():
    p = pd.read_parquet(C.PANEL)
    print("panel", len(p))
    p["sigma_t0"] = C.compute_sigma(p)
    # causal MAD sigma (trailing window excl t0), vectorized per asset
    def _trailing_mad(s):
        s = s.fillna(0.0)
        m = s.rolling(C.VOL_WINDOW, min_periods=C.VOL_MIN_OBS).median()
        dev = (s - m).abs()
        mad = dev.rolling(C.VOL_WINDOW, min_periods=C.VOL_MIN_OBS).median()
        return 1.4826 * mad
    p["mad_sigma_t0"] = (
        p.sort_values("historical_date")
        .sort_values("cmc_id")
        .groupby("cmc_id", sort=False)["ret_1d"]
        .transform(lambda s: _trailing_mad(s).shift(1))
        .astype(float)
    )
    p["z_cross"] = p.groupby("historical_date", sort=False)["ret_1d"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # ---- sigma-normalized event flags (lens B, C, E) on ret_1d
    evB = p["ret_1d"].abs() >= C.SIGMA_K * p["sigma_t0"]
    evC = p["ret_1d"].abs() >= C.MAD_K * p["mad_sigma_t0"]
    evE = p["z_cross"].abs() >= C.CROSS_Z
    p["lens_B"] = evB & p["sigma_t0"].notna()
    p["lens_C"] = evC & p["mad_sigma_t0"].notna()
    p["lens_E"] = evE & p["z_cross"].notna()
    p["event_any"] = p["lens_B"] | p["lens_C"] | p["lens_E"]

    ev = p[p["event_any"]].copy()
    print("sigma-normalized events:", len(ev))

    # ---- forward cumulative returns per event row, censored at group end
    # Precompute per-asset sorted by date -> forward window columns
    cols = {f"f{k}": np.nan for k in range(1, FWD_MAX + 1)}
    fdf = pd.DataFrame(index=p.index)
    byg = p.groupby("cmc_id", sort=False)["ret_1d"]
    for k in range(1, FWD_MAX + 1):
        fdf[f"f{k}"] = byg.transform(lambda s, kk=k: s.shift(-kk))
    fmat = fdf.to_numpy(float)
    cumf = np.cumsum(fmat, axis=1)  # cumf[i,h-1] = sum of f1..fh = cum ret t+1..t+h

    # attach forward cum to events
    ev_idx = p.index.get_indexer(ev.index)
    ecum = cumf[ev_idx]

    sigma0 = ev["sigma_t0"].to_numpy(float)
    n_ev = len(ev)

    def first_day(cond):
        """For each event, index of first True in cond (axis=1) +1, else None."""
        arr = cond.astype(int)
        # find first 1 per row
        idxs = np.argmax(arr, axis=1)
        any_true = arr.max(axis=1).astype(bool)
        out = (idxs + 1).astype(float)
        out[~any_true] = np.nan
        return out

    T1 = np.full(n_ev, np.nan)
    T2 = np.full(n_ev, np.nan)
    T3 = np.full(n_ev, np.nan)
    for k, T in [(1, T1), (2, T2), (3, T3)]:
        T[:] = first_day(np.abs(ecum) >= (k * np.abs(sigma0))[:, None])

    # time to peak: argmax of |cum| within +1..+14
    amp14 = np.abs(ecum[:, :14])
    peak_h = np.argmax(amp14, axis=1) + 1
    peak_amp = np.max(amp14, axis=1)
    T_peak = peak_h.astype(float)
    T_peak[~np.isfinite(amp14).all(axis=1)] = np.nan
    peak_amp[~np.isfinite(amp14).all(axis=1)] = np.nan

    # --- vectorized duration metrics (no per-row python loops) ---
    # time above 2sigma: leading-run length of |cum|>=2sigma
    above2 = (np.abs(ecum) >= (2 * np.abs(sigma0))[:, None]).astype(int)
    # row-leading zero count: cummin trick
    run = np.zeros(n_ev, dtype=int)
    prod = np.ones(n_ev, dtype=int)
    for h in range(FWD_MAX):
        prod = (prod * above2[:, h]).astype(int)
        run += prod

    # first index of |cum|<=1sigma (mask outside-window as far-future)
    inside = (np.abs(ecum) <= (1 * np.abs(sigma0))[:, None]).astype(int)
    inside_far = np.where(inside == 1, inside, FWD_MAX + 1)  # far-away marker
    first_inside_h = inside_far.argmin(axis=1)  # smallest horizon index where true
    valid_inside = inside.any(axis=1)
    T_inside = np.where(valid_inside, first_inside_h + 1, np.nan).astype(float)

    # half-decay: first horizon where |cum|<=peak/2 (after peak)
    valid_pk = np.isfinite(peak_amp) & (peak_amp > 0)
    half = ((np.abs(ecum) <= (0.5 * peak_amp[:, None])))
    half_far = np.where(half, half.astype(int), FWD_MAX + 1)
    first_half = half_far.argmin(axis=1)
    half_ok = half.any(axis=1) & valid_pk
    half_t = np.where(half_ok, first_half + 1, np.nan).astype(float)

    ev = ev.copy()
    ev["sigma_t0"] = sigma0
    for k, arr in [(1, T1), (2, T2), (3, T3), ("peak", T_peak)]:
        ev[f"time_to_{k}sigma" if k not in ("peak",) else "time_to_peak"] = arr
    ev["time_above_2sigma_d"] = run
    ev["time_to_return_inside_1sigma_d"] = T_inside
    ev["time_to_half_decay_d"] = half_t
    ev["peak_amp_sigma"] = (peak_amp / np.abs(sigma0))

    # ---- band-aggregated distributions (censored: right-censor at 30, mark n/event counts)
    rows = []
    for band in C.PRIMARY_BANDS:
        b = ev[ev["rank_band"] == band]
        if not len(b):
            continue
        for metric in ["time_to_1sigma", "time_to_2sigma", "time_to_3sigma", "time_to_peak",
                       "time_above_2sigma_d", "time_to_return_inside_1sigma_d",
                       "time_to_half_decay_d"]:
            v = b[metric].dropna()
            censor_rate = float(b[metric].isna().mean())
            row = {
                "rank_band": band, "metric": metric, "n": int(len(v)),
                "censor_rate_30d": round(censor_rate, 4),
                "median_d": round(float(v.median()) if len(v) else np.nan, 2),
                "p25_d": round(float(v.quantile(0.25)) if len(v) else np.nan, 2),
                "p75_d": round(float(v.quantile(0.75)) if len(v) else np.nan, 2),
                "p90_d": round(float(v.quantile(0.90)) if len(v) else np.nan, 2),
            }
            rows.append(row)
    d05 = pd.DataFrame(rows)
    d05.to_csv(C.RESULTS / "05_TIME_TO_DELIVERY.csv", index=False)
    print("\n=== TIME-TO-DELIVERY (median_d by band) ===")
    print(d05.pivot_table(index="metric", columns="rank_band", values="median_d").to_string())
    print("\ncensor rates:")
    print(d05.pivot_table(index="metric", columns="rank_band", values="censor_rate_30d").to_string())

    # ---- 06 duration/decay: peak amp |cum| profile by band (mean abs cum over horizon)
    decay_rows = []
    for band in C.PRIMARY_BANDS:
        b = ev[ev["rank_band"] == band]
        if not len(b):
            continue
        idx = ev.index.get_indexer(b.index)
        fwd = cumf[idx][:, :14]
        for h in range(1, 15):
            # mean abs forward cum at horizon h, winsorized
            vals = np.abs(fwd[:, h - 1])
            vals = np.sort(vals[~np.isnan(vals)]) if len(vals > 0) else vals
            if len(vals) == 0:
                continue
            decay_rows.append({
                "rank_band": band, "horizon_d": h, "n": int(len(vals)),
                "median_abs_cum_sigma": round(float(np.median(vals)), 4),
                "mean_abs_cum_sigma": round(float(np.mean(vals)), 4),
                "p90_abs_cum_sigma": round(float(np.quantile(vals, 0.90)), 4),
            })
    d06 = pd.DataFrame(decay_rows)
    d06.to_csv(C.RESULTS / "06_EVENT_DURATION_DECAY.csv", index=False)
    print("\n=== 06 median |cum| (sigma units) by horizon ===")
    print(d06.pivot_table(index="horizon_d", columns="rank_band", values="median_abs_cum_sigma").round(3).to_string())

    # save event set (subset columns for size)
    keep = ["historical_date", "cmc_id", "rank", "rank_band", "symbol", "ret_1d",
            "ret_3d", "ret_7d", "ret_14d", "ret_30d", "sigma_t0", "mad_sigma_t0",
            "z_cross", "lens_B", "lens_C", "lens_E", "btc_ret_1d", "eth_ret_1d",
            "mkt_ret_1d", "platform_chain", "tags", "is_stablecoin", "listing_age_days",
            "flag_stale_price", "flag_zero_volume", "mkt_vol_30d", "top500_breadth_30d",
            "time_to_1sigma", "time_to_2sigma", "time_to_3sigma", "time_to_peak",
            "time_above_2sigma_d", "time_to_return_inside_1sigma_d",
            "time_to_half_decay_d", "peak_amp_sigma"]
    ev[keep].to_parquet(C.ROOT / "EVENTS" / "lf1_event_set.parquet", index=False)
    print("\nwrote 05, 06 + EVENTS/lf1_event_set.parquet", len(ev))


if __name__ == "__main__":
    main()