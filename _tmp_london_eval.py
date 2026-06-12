"""
Focused evaluation: London session distribution prediction accuracy.
Uses the DTB v3 cascade T2 model (9AM checkpoint) to predict
remaining distribution from 9AM to 12PM EST (London session tail).
"""
import sys, os, json
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from pathlib import Path

sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

RAW_DATA_DIR = Path("quant-lab/data")
LAB_DIR = Path("quant-lab/ml/dtb_lab")

FX_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
    "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
    "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    "NZDJPY", "NZDCHF", "NZDCAD",
    "CADJPY", "CADCHF", "CHFJPY",
]

def load_m5_data(symbol):
    csv_path = RAW_DATA_DIR / f"{symbol}_M5.csv"
    if not csv_path.exists():
        for f in RAW_DATA_DIR.glob(f"*{symbol}*M5*.csv"):
            csv_path = f
            break
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ("date", "datetime", "time", "timestamp"): col_map[c] = "dt"
        elif cl in ("open", "high", "low", "close"): col_map[c] = cl
        elif cl in ("volume", "vol", "tick_volume", "tickvol"): col_map[c] = "volume"
    df = df.rename(columns=col_map)
    df["dt"] = pd.to_datetime(df["dt"], utc=True, errors="coerce")
    df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
    df["symbol"] = symbol
    if "volume" not in df.columns:
        df["volume"] = 0
    return df

def classify_tier(ar_pips):
    if ar_pips < 20: return "T1", ar_pips * 0.5, 52
    elif ar_pips < 30: return "T2", ar_pips * 0.5, 68
    elif ar_pips < 45: return "T3", ar_pips * 0.5, 94
    else: return "T4_NO_GO", 0.0, 999

def temporal_decay(minutes_to_exit):
    if minutes_to_exit <= 0: return 0.0
    k = 0.015
    return 1.0 / (1.0 + np.exp(-k * (minutes_to_exit - 120)))

def count_loops_vectorized(high, low, close, ah, al):
    if len(high) == 0 or ah <= 0: return 0
    above_ah = high > ah
    if not above_ah.any():
        below_al = low < al
        if not below_al.any(): return 0
        impulse_starts = np.where(below_al & ~np.roll(below_al, 1))[0]
        impulse_starts = impulse_starts[impulse_starts > 0]
        if len(impulse_starts) == 0: return 0
        count = 0
        for start in impulse_starts:
            seg_low = low[start:]; seg_close = close[start:]
            running_min = np.minimum.accumulate(seg_low)
            impulse_range = ah - running_min
            valid = impulse_range > 0
            if not valid.any(): continue
            retrace = (seg_close[valid] - running_min[valid]) / impulse_range[valid]
            if len(np.where((retrace >= 0.32) & (retrace <= 0.50))[0]) > 0: count += 1
        return count
    impulse_starts = np.where(above_ah & ~np.roll(above_ah, 1))[0]
    impulse_starts = impulse_starts[impulse_starts > 0]
    if len(impulse_starts) == 0: return 0
    count = 0
    for start in impulse_starts:
        seg_high = high[start:]; seg_close = close[start:]
        running_max = np.maximum.accumulate(seg_high)
        impulse_range = running_max - ah
        valid = impulse_range > 0
        if not valid.any(): continue
        retrace = (running_max[valid] - seg_close[valid]) / impulse_range[valid]
        if len(np.where((retrace >= 0.32) & (retrace <= 0.50))[0]) > 0: count += 1
    return count

def compute_volatility_features(df):
    df = df.copy()
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            np.abs(df["high"] - df["close"].shift(1)),
            np.abs(df["low"] - df["close"].shift(1))
        )
    )
    df["atr_14"] = df["tr"].rolling(14).mean()
    df["atr_50"] = df["tr"].rolling(50).mean()
    df["range"] = df["high"] - df["low"]
    agg_dict = {"daily_range": ("range", "max"), "daily_atr": ("atr_14", "last")}
    if "volume" in df.columns:
        agg_dict["daily_volume"] = ("volume", "sum")
    daily = df.groupby(df.index.date).agg(**agg_dict)
    daily.index = pd.to_datetime(daily.index)
    daily["range_expansion_5"] = daily["daily_range"] / daily["daily_range"].rolling(5).mean()
    daily["range_expansion_10"] = daily["daily_range"] / daily["daily_range"].rolling(10).mean()
    daily["atr_ratio"] = daily["daily_atr"] / daily["daily_atr"].rolling(20).mean()
    return daily

def build_t2_features(df, symbol):
    """Build features at T2 (9AM EST = 14UTC) to predict remaining distribution."""
    records = []
    df = df.copy()
    df["est_hour"] = (df.index.hour - 5) % 24
    df["is_asian"] = (df["est_hour"] >= 19) | (df["est_hour"] < 3)
    df["trade_date"] = df.index.date

    vol_features = compute_volatility_features(df)
    day_grouped = {date: group for date, group in df.groupby("trade_date")}

    for date, day_bars in day_grouped.items():
        if len(day_bars) < 20: continue
        asian_bars = day_bars[day_bars["is_asian"]]
        if len(asian_bars) < 2: continue

        ah = asian_bars["high"].max()
        al = asian_bars["low"].min()
        ar = ah - al
        ar_pips = ar * 10000
        tier, au, loop_dur = classify_tier(ar_pips)
        if tier == "T4_NO_GO": continue

        # T2 = 9AM EST = 14 UTC
        cp_hour_utc = 14
        sink_hour_utc = 17
        cp_bars = day_bars[(day_bars.index.hour >= cp_hour_utc) & (day_bars.index.hour < sink_hour_utc)]
        if len(cp_bars) == 0:
            remaining_dist = 0.0
        else:
            remaining_dist = (cp_bars["high"].max() - cp_bars["low"].min()) * 10000

        pre_cp_bars = day_bars[day_bars.index.hour < cp_hour_utc]
        if len(pre_cp_bars) < 5: continue

        mins_to_12pm = (sink_hour_utc - cp_hour_utc) * 60
        delta_t = temporal_decay(mins_to_12pm)

        am_bars_pre = pre_cp_bars[(pre_cp_bars.index.hour >= 14) & (pre_cp_bars.index.hour < 15)]
        if len(am_bars_pre) > 0:
            am_range = am_bars_pre["high"].max() - am_bars_pre["low"].min()
            regime_ratio = am_range / ar if ar > 0 else 0
        else:
            regime_ratio = 0

        if regime_ratio >= 1.5: regime = "CONFIRMED"
        elif regime_ratio >= 1.0: regime = "CAUTION"
        else: regime = "FAILED"
        regime_map = {"CONFIRMED": 2, "CAUTION": 1, "FAILED": 0}

        h = pre_cp_bars["high"].values
        l = pre_cp_bars["low"].values
        c = pre_cp_bars["close"].values
        l_actual = count_loops_vectorized(h, l, c, ah, al)
        l_theoretical = max(0.0, mins_to_12pm / loop_dur) if loop_dur < 999 else 0.0
        omega_l = l_actual / l_theoretical if l_theoretical > 0 else 0.0

        dist_so_far = (pre_cp_bars["high"].max() - pre_cp_bars["low"].min()) * 10000
        mins_elapsed = (cp_hour_utc - 8) * 60
        velocity = dist_so_far / max(mins_elapsed, 1)

        first_bar = day_bars.index[0]
        est_hour = (first_bar.hour - 5) % 24
        dow = first_bar.weekday()
        is_wed = dow == 2
        is_wed_pm = is_wed and est_hour >= 12

        entropy_trigger = "NONE"
        if omega_l < 0.5 and l_theoretical > 1: entropy_trigger = "80_Invalidation"
        elif ar_pips > 35 and regime == "CONFIRMED": entropy_trigger = "Trap_Zone_62"
        elif l_actual > l_theoretical * 1.44: entropy_trigger = "Gear_Shift_144"
        entropy_map = {"NONE": 0, "80_Invalidation": 1, "Trap_Zone_62": 2, "Gear_Shift_144": 3}

        date_ts = pd.Timestamp(date)
        vol_row = vol_features.loc[vol_features.index == date_ts]
        if len(vol_row) > 0:
            range_exp_5 = vol_row["range_expansion_5"].values[0] if not pd.isna(vol_row["range_expansion_5"].values[0]) else 1.0
            range_exp_10 = vol_row["range_expansion_10"].values[0] if not pd.isna(vol_row["range_expansion_10"].values[0]) else 1.0
            atr_ratio = vol_row["atr_ratio"].values[0] if not pd.isna(vol_row["atr_ratio"].values[0]) else 1.0
        else:
            range_exp_5 = range_exp_10 = atr_ratio = 1.0

        regime_x_time = regime_map[regime] * mins_to_12pm
        regime_x_omega = regime_map[regime] * omega_l
        time_x_omega = mins_to_12pm * omega_l
        regime_x_loops = regime_map[regime] * l_actual
        velocity_x_regime = velocity * regime_map[regime]
        expansion_x_regime = range_exp_5 * regime_map[regime]

        records.append({
            "symbol": symbol, "date": str(date),
            "asian_range_pips": round(ar_pips, 2),
            "au_pips": round(au * 10000, 2),
            "regime_encoded": regime_map[regime],
            "regime_ratio": round(regime_ratio, 3),
            "time_to_12pm_mins": int(mins_to_12pm),
            "loop_duration": int(loop_dur),
            "L_theoretical": round(l_theoretical, 2),
            "L_actual": int(l_actual),
            "Omega_L": round(omega_l, 3),
            "Delta_t": round(delta_t, 4),
            "dist_so_far_pips": round(dist_so_far, 2),
            "velocity_pips_per_min": round(velocity, 4),
            "is_wednesday_pm": int(is_wed_pm),
            "day_of_week": int(dow),
            "entropy_encoded": entropy_map[entropy_trigger],
            "range_expansion_5": round(range_exp_5, 3),
            "range_expansion_10": round(range_exp_10, 3),
            "atr_ratio": round(atr_ratio, 3),
            "regime_x_time": round(regime_x_time, 2),
            "regime_x_omega": round(regime_x_omega, 4),
            "time_x_omega": round(time_x_omega, 4),
            "regime_x_loops": regime_x_loops,
            "velocity_x_regime": round(velocity_x_regime, 4),
            "expansion_x_regime": round(expansion_x_regime, 3),
            "remaining_dist_pips": round(remaining_dist, 2),
        })
    return pd.DataFrame(records)


# ============================================================
# MAIN EVALUATION
# ============================================================
print("=" * 70)
print("LONDON SESSION DISTRIBUTION PREDICTION ACCURACY")
print("=" * 70)
print("\nUsing DTB v3 Cascade T2 model (9AM checkpoint)")
print("Target: Remaining distribution from 9AM to 12PM EST")
print("Training data: 9AM-12PM window (London session tail)")

# Load the T2 cascade model
model_files = sorted(LAB_DIR.glob("attempt_2_micro/cascade_T2_*.joblib"))
if not model_files:
    print("ERROR: No T2 model found!")
    sys.exit(1)

latest_model = model_files[-1]
print(f"\nModel: {latest_model.name}")
model = joblib.load(latest_model)

# Build features for all symbols
all_features = []
skipped = []
for sym in FX_SYMBOLS:
    df = load_m5_data(sym)
    if len(df) < 1000:
        skipped.append(sym)
        continue
    feats = build_t2_features(df, sym)
    if len(feats) > 0:
        all_features.append(feats)

data = pd.concat(all_features, ignore_index=True)
print(f"\nTotal samples: {len(data)}")
print(f"Symbols with data: {data['symbol'].nunique()}")
print(f"Symbols skipped (no data): {skipped}")

# Features
feature_cols = [
    "asian_range_pips", "au_pips", "regime_encoded", "regime_ratio",
    "time_to_12pm_mins", "loop_duration", "L_theoretical", "L_actual",
    "Omega_L", "Delta_t", "dist_so_far_pips", "velocity_pips_per_min",
    "is_wednesday_pm", "day_of_week", "entropy_encoded",
    "range_expansion_5", "range_expansion_10", "atr_ratio",
    "regime_x_time", "regime_x_omega", "time_x_omega",
    "regime_x_loops", "velocity_x_regime", "expansion_x_regime",
]

X = data[feature_cols].values
y_actual = data["remaining_dist_pips"].values

# Predict
y_pred = np.expm1(model.predict(X))

# ============================================================
# OVERALL METRICS
# ============================================================
print("\n" + "=" * 70)
print("OVERALL LONDON SESSION PREDICTION ACCURACY")
print("=" * 70)

mae = mean_absolute_error(y_actual, y_pred)
rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
r2 = r2_score(y_actual, y_pred)
mape = np.mean(np.abs((y_actual - y_pred) / np.maximum(y_actual, 1))) * 100

from scipy.stats import spearmanr
pearson = np.corrcoef(y_actual, y_pred)[0, 1]
spearman, _ = spearmanr(y_actual, y_pred)

print(f"  MAE:              {mae:.2f} pips")
print(f"  RMSE:             {rmse:.2f} pips")
print(f"  R²:               {r2:.4f}")
print(f"  MAPE:             {mape:.1f}%")
print(f"  Pearson:          {pearson:.4f}")
print(f"  Spearman:         {spearman:.4f}")
print(f"  Mean Actual:      {y_actual.mean():.1f} pips")
print(f"  Mean Predicted:   {y_pred.mean():.1f} pips")
print(f"  Bias:             {y_pred.mean() - y_actual.mean():+.1f} pips")

# ============================================================
# HIT RATES
# ============================================================
print("\n" + "=" * 70)
print("HIT RATE ANALYSIS")
print("=" * 70)

for tol in [3, 5, 8, 10, 15, 20]:
    within = np.abs(y_actual - y_pred) <= tol
    print(f"  Within ±{tol:2d} pips: {within.mean():.1%} ({within.sum()}/{len(y_actual)})")

# ============================================================
# ACCURACY BY SYMBOL
# ============================================================
print("\n" + "=" * 70)
print("ACCURACY BY SYMBOL")
print("=" * 70)

symbol_stats = []
for sym in data["symbol"].unique():
    mask = data["symbol"] == sym
    if mask.sum() < 30: continue
    sym_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
    sym_r2 = r2_score(y_actual[mask], y_pred[mask])
    sym_actual = y_actual[mask].mean()
    sym_pred = y_pred[mask].mean()
    symbol_stats.append({
        "symbol": sym, "n": mask.sum(), "mae": sym_mae, "r2": sym_r2,
        "actual": sym_actual, "pred": sym_pred, "bias": sym_pred - sym_actual
    })

symbol_stats.sort(key=lambda x: x["n"], reverse=True)
print(f"  {'Symbol':8s} {'N':>5s} {'MAE':>7s} {'R²':>7s} {'Actual':>8s} {'Pred':>8s} {'Bias':>7s}")
print(f"  {'-'*8:8s} {'-'*5:>5s} {'-'*7:>7s} {'-'*7:>7s} {'-'*8:>8s} {'-'*8:>8s} {'-'*7:>7s}")
for s in symbol_stats:
    print(f"  {s['symbol']:8s} {s['n']:5d} {s['mae']:7.2f} {s['r2']:+7.4f} "
          f"{s['actual']:8.1f} {s['pred']:8.1f} {s['bias']:+7.1f}")

# ============================================================
# ACCURACY BY REGIME
# ============================================================
print("\n" + "=" * 70)
print("ACCURACY BY REGIME")
print("=" * 70)

for rv, rn in [(2, "CONFIRMED"), (1, "CAUTION"), (0, "FAILED")]:
    mask = data["regime_encoded"] == rv
    if mask.sum() < 30: continue
    reg_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
    reg_r2 = r2_score(y_actual[mask], y_pred[mask])
    reg_actual = y_actual[mask].mean()
    reg_pred = y_pred[mask].mean()
    print(f"  {rn:10s} ({mask.sum():5d}): MAE={reg_mae:6.2f}, R²={reg_r2:+.4f}, "
          f"Actual={reg_actual:6.1f}, Pred={reg_pred:6.1f}, Bias={reg_pred-reg_actual:+6.1f}")

# ============================================================
# ACCURACY BY DAY OF WEEK
# ============================================================
print("\n" + "=" * 70)
print("ACCURACY BY DAY OF WEEK")
print("=" * 70)

dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
for dow_val in range(5):
    mask = data["day_of_week"] == dow_val
    if mask.sum() < 30: continue
    d_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
    d_r2 = r2_score(y_actual[mask], y_pred[mask])
    d_actual = y_actual[mask].mean()
    d_pred = y_pred[mask].mean()
    print(f"  {dow_names[dow_val]:4s} ({mask.sum():5d}): MAE={d_mae:6.2f}, R²={d_r2:+.4f}, "
          f"Actual={d_actual:6.1f}, Pred={d_pred:6.1f}")

# ============================================================
# TRADE FILTERING EDGE
# ============================================================
print("\n" + "=" * 70)
print("TRADE FILTERING EDGE")
print("=" * 70)
print("  'Only trade when predicted remaining distribution > threshold'")
print()

for thresh in [15, 20, 25, 30, 35, 40, 50]:
    mask = y_pred >= thresh
    if mask.sum() < 30: continue
    f_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
    f_r2 = r2_score(y_actual[mask], y_pred[mask])
    f_actual = y_actual[mask].mean()
    f_pred = y_pred[mask].mean()
    pct = mask.mean() * 100
    improvement = (mae - f_mae) / mae * 100
    print(f"  Pred >= {thresh:2d} pips ({mask.sum():5d}/{len(y_actual)} = {pct:4.0f}%): "
          f"MAE={f_mae:6.2f} ({improvement:+5.1f}%), R²={f_r2:+.4f}, "
          f"Actual={f_actual:6.1f}, Pred={f_pred:6.1f}")

# ============================================================
# LONDON SESSION SPECIFIC: 9AM-12PM window analysis
# ============================================================
print("\n" + "=" * 70)
print("LONDON SESSION WINDOW ANALYSIS (9AM-12PM EST)")
print("=" * 70)

# How much of total daily range happens in 9AM-12PM?
# We need total daily range for this
total_daily = []
for sym in data["symbol"].unique():
    df = load_m5_data(sym)
    if len(df) < 1000: continue
    df["trade_date"] = df.index.date
    daily_ranges = df.groupby("trade_date").apply(
        lambda x: (x["high"].max() - x["low"].min()) * 10000
    )
    for date, dr in daily_ranges.items():
        total_daily.append({"symbol": sym, "date": str(date), "total_range": dr})

td_df = pd.DataFrame(total_daily)
data_with_total = data.merge(td_df, on=["symbol", "date"], how="left")

valid = data_with_total.dropna(subset=["total_range"])
if len(valid) > 0:
    valid["london_pct"] = valid["remaining_dist_pips"] / valid["total_range"] * 100
    print(f"  London session (9AM-12PM) accounts for:")
    print(f"    Mean:   {valid['london_pct'].mean():.1f}% of total daily range")
    print(f"    Median: {valid['london_pct'].median():.1f}%")
    print(f"    Min:    {valid['london_pct'].min():.1f}%")
    print(f"    Max:    {valid['london_pct'].max():.1f}%")
    print(f"\n  London session absolute range:")
    print(f"    Mean:   {valid['remaining_dist_pips'].mean():.1f} pips")
    print(f"    Median: {valid['remaining_dist_pips'].median():.1f} pips")
    print(f"    Std:    {valid['remaining_dist_pips'].std():.1f} pips")

print("\n" + "=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)
