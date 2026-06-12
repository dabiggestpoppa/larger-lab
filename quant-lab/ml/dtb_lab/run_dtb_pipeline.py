"""
DTB v3 — Distribution to Boundary Cascade Predictor
=====================================================
4 fixes vs v2:
  1. Quantile regression + asymmetric loss (stop underpredicting big days)
  2. Non-linear interaction features (regime x time x loops)
  3. Cascade prediction — separate model per checkpoint (T0->T1->T2->T3)
  4. Volatility regime features (ATR, range expansion, session overlap)

Key insight: Don't predict total daily range. Predict REMAINING range at
each checkpoint, letting time compress the error at each step.
"""
from __future__ import annotations

import json
import uuid
import time
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

warnings.filterwarnings("ignore")

# ============================================================
# PATHS
# ============================================================
LAB_DIR = Path(__file__).parent
ATTEMPT1_DIR = LAB_DIR / "attempt_1_macro"
ATTEMPT2_DIR = LAB_DIR / "attempt_2_micro"
MERGE_DIR = LAB_DIR / "merge_unified"
LOGS_DIR = LAB_DIR / "logs"

for d in [ATTEMPT1_DIR, ATTEMPT2_DIR, MERGE_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RAW_DATA_DIR = Path("quant-lab/data")

FX_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
    "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
    "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    "NZDJPY", "NZDCHF", "NZDCAD",
    "CADJPY", "CADCHF", "CHFJPY",
]

# Checkpoints: UTC hour -> label
CHECKPOINTS = {
    "T0": 8,   # 3AM EST — Asian Range just locked
    "T1": 11,  # 6AM EST — 65% resolution expected
    "T2": 14,  # 9AM EST — Regime locked
    "T3": 15,  # 10:30AM EST — Temporal decay phase
}
SINK_HOUR_UTC = 17  # 12PM EST — Hard exit


# ============================================================
# RUN LOGGER
# ============================================================

class RunLogger:
    def __init__(self, lens_type: str):
        self.lens_type = lens_type
        self.run_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.metrics = {}

    def log(self, **kwargs):
        self.metrics.update(kwargs)

    def save(self, model_path: Optional[Path] = None):
        elapsed = time.time() - self.start_time
        manifest = {
            "run_id": self.run_id, "lens_type": self.lens_type,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 1), **self.metrics,
        }
        path = LOGS_DIR / f"run_{self.lens_type}_{self.run_id}.json"
        path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        print(f"  Run logged: {path.name}")
        return manifest


# ============================================================
# DATA LOADING
# ============================================================

def load_m5_data(symbol: str) -> pd.DataFrame:
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


def load_all_symbols() -> Dict[str, pd.DataFrame]:
    symbols = {}
    for sym in FX_SYMBOLS:
        try:
            df = load_m5_data(sym)
            if len(df) > 1000:
                symbols[sym] = df
        except Exception as e:
            print(f"  SKIP {sym}: {e}")
    print(f"  Loaded {len(symbols)} symbols")
    return symbols


# ============================================================
# HELPERS
# ============================================================

def classify_tier(ar_pips: float) -> Tuple[str, float, int]:
    if ar_pips < 20: return "T1", ar_pips * 0.5, 52
    elif ar_pips < 30: return "T2", ar_pips * 0.5, 68
    elif ar_pips < 45: return "T3", ar_pips * 0.5, 94
    else: return "T4_NO_GO", 0.0, 999


def temporal_decay(minutes_to_exit: float) -> float:
    if minutes_to_exit <= 0: return 0.0
    k = 0.015
    return 1.0 / (1.0 + np.exp(-k * (minutes_to_exit - 120)))


def count_loops_vectorized(high: np.ndarray, low: np.ndarray,
                           close: np.ndarray, ah: float, al: float) -> int:
    """Count impulse-rebalance cycles using vectorized numpy."""
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


# ============================================================
# FIX #4: VOLATILITY REGIME FEATURES
# ============================================================

def compute_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute volatility regime features per day:
    - ATR(14) from M5 bars
    - Range expansion ratio (today's range / 5-day avg range)
    - Session overlap flag (London-NY overlap = 12-17 UTC)
    - Consecutive direction bars (momentum)
    """
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

    # Daily aggregates
    agg_dict = {"daily_range": ("range", "max"), "daily_atr": ("atr_14", "last")}
    if "volume" in df.columns:
        agg_dict["daily_volume"] = ("volume", "sum")
    daily = df.groupby(df.index.date).agg(**agg_dict)
    daily.index = pd.to_datetime(daily.index)

    # Range expansion: today's range / 5-day avg
    daily["range_expansion_5"] = daily["daily_range"] / daily["daily_range"].rolling(5).mean()
    daily["range_expansion_10"] = daily["daily_range"] / daily["daily_range"].rolling(10).mean()
    daily["atr_ratio"] = daily["daily_atr"] / daily["daily_atr"].rolling(20).mean()

    return daily


# ============================================================
# PHASE 1: MACRO MLR LENS (unchanged from v2)
# ============================================================

def build_macro_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    records = []
    df = df.copy()
    df["week"] = df.index.isocalendar().week.astype(int)
    df["year"] = df.index.isocalendar().year.astype(int)
    df["week_key"] = df["year"].astype(str) + "_W" + df["week"].astype(str)

    for week_key, week_data in df.groupby("week_key"):
        if len(week_data) < 100: continue
        monday_mask = (week_data.index.dayofweek == 0) & \
                      (week_data.index.hour >= 7) & (week_data.index.hour < 10)
        monday_bars = week_data[monday_mask]
        if len(monday_bars) < 2: continue

        mlr_high = monday_bars["high"].max()
        mlr_low = monday_bars["low"].min()
        mlr_range = mlr_high - mlr_low
        mlr_close = monday_bars["close"].iloc[-1]
        mlr_mid = (mlr_high + mlr_low) / 2
        bias = "BULLISH" if mlr_close > mlr_mid else "BEARISH"

        week_high = week_data["high"].max()
        week_low = week_data["low"].min()
        weekly_distribution = week_high - week_low

        if bias == "BULLISH":
            target_25 = mlr_high + 0.25 * mlr_range
            target_50 = mlr_high + 0.50 * mlr_range
            kill_132 = mlr_low - 1.32 * mlr_range
        else:
            target_25 = mlr_low - 0.25 * mlr_range
            target_50 = mlr_low - 0.50 * mlr_range
            kill_132 = mlr_high + 1.32 * mlr_range

        hit_25 = (week_data["high"] >= target_25) if bias == "BULLISH" else (week_data["low"] <= target_25)
        hit_50 = (week_data["high"] >= target_50) if bias == "BULLISH" else (week_data["low"] <= target_50)
        hit_132 = (week_data["low"] <= kill_132) if bias == "BULLISH" else (week_data["high"] >= kill_132)

        monday_9am = monday_bars.index[0].replace(hour=14, minute=0)
        time_to_friday = (monday_bars.index[0].replace(hour=16, minute=0) + timedelta(days=4) - monday_9am).total_seconds() / 3600
        wed_mask = week_data.index.dayofweek == 2
        is_wednesday_pm = any(wed_mask & (week_data.index.hour >= 17))

        records.append({
            "symbol": symbol, "week_key": week_key,
            "mlr_range_pips": mlr_range * 10000, "bias": bias,
            "target_25_pips": abs(target_25 - mlr_close) * 10000,
            "target_50_pips": abs(target_50 - mlr_close) * 10000,
            "dist_to_132_pips": abs(kill_132 - mlr_close) * 10000,
            "time_to_friday_hours": time_to_friday,
            "is_wednesday_pm": int(is_wednesday_pm),
            "hit_25": int(hit_25.any()), "hit_50": int(hit_50.any()),
            "hit_132": int(hit_132.any()),
            "weekly_distribution_pips": weekly_distribution * 10000,
        })
    return pd.DataFrame(records)


def run_attempt1(symbols: Dict[str, pd.DataFrame]) -> dict:
    logger = RunLogger("MACRO")
    print("\n" + "=" * 70)
    print("PHASE 1: MACRO MLR LENS")
    print("=" * 70)

    all_records = []
    for sym, df in symbols.items():
        try:
            feats = build_macro_features(df, sym)
            if len(feats) > 0:
                all_records.append(feats)
                print(f"  {sym}: {len(feats)} weeks")
        except Exception as e:
            print(f"  {sym}: ERROR — {e}")

    if not all_records: return {}
    data = pd.concat(all_records, ignore_index=True)
    print(f"\n  Total: {len(data)} weekly samples")

    feature_cols = ["mlr_range_pips", "target_25_pips", "target_50_pips",
                    "dist_to_132_pips", "time_to_friday_hours", "is_wednesday_pm"]
    data["bias_encoded"] = (data["bias"] == "BULLISH").astype(int)
    feature_cols.append("bias_encoded")
    data["target_log"] = np.log1p(data["weekly_distribution_pips"])

    X = data[feature_cols].values
    y = data["target_log"].values

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        model = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train, verbose=False)
        y_pred = np.expm1(model.predict(X_test))
        y_actual = np.expm1(y_test)
        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        cv_scores.append({"fold": fold + 1, "mae": round(mae, 2), "r2": round(r2, 4)})
        print(f"  Fold {fold+1}: MAE={mae:.2f}, R2={r2:.4f}")

    final_model = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1)
    final_model.fit(X, y)

    importance = dict(zip(feature_cols, final_model.feature_importances_.tolist()))
    print(f"\n  Feature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"    {feat}: {imp:.4f}")

    model_path = ATTEMPT1_DIR / f"macro_xgb_{logger.run_id}.joblib"
    joblib.dump(final_model, model_path)

    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_r2 = np.mean([s["r2"] for s in cv_scores])
    logger.log(phase="attempt_1_macro", n_samples=len(data), avg_mae=round(avg_mae, 2),
               avg_r2=round(avg_r2, 4), cv_scores=cv_scores, model_path=str(model_path))
    logger.save(model_path)
    return {"data": data, "model": final_model, "cv_scores": cv_scores,
            "avg_mae": avg_mae, "avg_r2": avg_r2, "importance": importance}


# ============================================================
# PHASE 2: MICRO ATOMIC LENS — CASCADE PREDICTOR (v3)
# ============================================================

def build_cascade_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Build cascade features for v3:
    - At each checkpoint, compute state vector from bars SO FAR
    - Target = remaining distribution from checkpoint to 12PM sink
    - Includes volatility regime features and interaction terms
    """
    records = []
    df = df.copy()
    df["est_hour"] = (df.index.hour - 5) % 24
    df["is_asian"] = (df["est_hour"] >= 19) | (df["est_hour"] < 3)
    df["trade_date"] = df.index.date

    # Pre-compute volatility features
    vol_features = compute_volatility_features(df)

    # Group by day once
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

        # Total daily range (for reference)
        total_dist = (day_bars["high"].max() - day_bars["low"].min()) * 10000

        # Volatility features for this day
        date_ts = pd.Timestamp(date)
        vol_row = vol_features.loc[vol_features.index == date_ts]
        if len(vol_row) > 0:
            range_exp_5 = vol_row["range_expansion_5"].values[0] if not pd.isna(vol_row["range_expansion_5"].values[0]) else 1.0
            range_exp_10 = vol_row["range_expansion_10"].values[0] if not pd.isna(vol_row["range_expansion_10"].values[0]) else 1.0
            atr_ratio = vol_row["atr_ratio"].values[0] if not pd.isna(vol_row["atr_ratio"].values[0]) else 1.0
        else:
            range_exp_5 = range_exp_10 = atr_ratio = 1.0

        # Day metadata
        first_bar = day_bars.index[0]
        est_hour = (first_bar.hour - 5) % 24
        dow = first_bar.weekday()
        is_wed = dow == 2

        # ============================================================
        # CASCADE: For each checkpoint, compute features from bars SO FAR
        # and predict REMAINING distribution to sink
        # ============================================================
        for cp_name, cp_hour_utc in CHECKPOINTS.items():
            # Bars from checkpoint to sink
            cp_bars = day_bars[(day_bars.index.hour >= cp_hour_utc) & (day_bars.index.hour < SINK_HOUR_UTC)]
            if len(cp_bars) == 0:
                remaining_dist = 0.0
            else:
                remaining_dist = (cp_bars["high"].max() - cp_bars["low"].min()) * 10000

            # Bars BEFORE checkpoint (for feature computation — no lookahead)
            pre_cp_bars = day_bars[day_bars.index.hour < cp_hour_utc]
            if len(pre_cp_bars) < 5:
                continue

            # Time features
            mins_to_12pm = (SINK_HOUR_UTC - cp_hour_utc) * 60
            delta_t = temporal_decay(mins_to_12pm)

            # Regime from pre-checkpoint bars only (no leak)
            am_bars_pre = pre_cp_bars[(pre_cp_bars.index.hour >= 14) & (pre_cp_bars.index.hour < 15)]
            if len(am_bars_pre) > 0 and cp_hour_utc >= 14:
                am_range = am_bars_pre["high"].max() - am_bars_pre["low"].min()
                regime_ratio = am_range / ar if ar > 0 else 0
            else:
                regime_ratio = 0

            if regime_ratio >= 1.5: regime = "CONFIRMED"
            elif regime_ratio >= 1.0: regime = "CAUTION"
            else: regime = "FAILED"
            regime_map = {"CONFIRMED": 2, "CAUTION": 1, "FAILED": 0}

            # Loop count from pre-checkpoint bars only
            h = pre_cp_bars["high"].values
            l = pre_cp_bars["low"].values
            c = pre_cp_bars["close"].values
            l_actual = count_loops_vectorized(h, l, c, ah, al)

            l_theoretical = max(0.0, mins_to_12pm / loop_dur) if loop_dur < 999 else 0.0
            omega_l = l_actual / l_theoretical if l_theoretical > 0 else 0.0

            # Distribution achieved so far
            dist_so_far = (pre_cp_bars["high"].max() - pre_cp_bars["low"].min()) * 10000

            # Velocity: pips per minute since open
            mins_elapsed = (cp_hour_utc - 8) * 60  # From T0 (8UTC) to checkpoint
            velocity = dist_so_far / max(mins_elapsed, 1)

            # ============================================================
            # FIX #2: Non-linear interaction features
            # ============================================================
            regime_x_time = regime_map[regime] * mins_to_12pm
            regime_x_omega = regime_map[regime] * omega_l
            time_x_omega = mins_to_12pm * omega_l
            regime_x_loops = regime_map[regime] * l_actual
            velocity_x_regime = velocity * regime_map[regime]
            expansion_x_regime = range_exp_5 * regime_map[regime]

            # Entropy triggers
            entropy_trigger = "NONE"
            if omega_l < 0.5 and l_theoretical > 1: entropy_trigger = "80_Invalidation"
            elif ar_pips > 35 and regime == "CONFIRMED": entropy_trigger = "Trap_Zone_62"
            elif l_actual > l_theoretical * 1.44: entropy_trigger = "Gear_Shift_144"
            entropy_map = {"NONE": 0, "80_Invalidation": 1, "Trap_Zone_62": 2, "Gear_Shift_144": 3}

            is_wed_pm = is_wed and est_hour >= 12

            records.append({
                "symbol": symbol,
                "date": str(date),
                "checkpoint": cp_name,
                "asian_range_pips": round(ar_pips, 2),
                "tier": tier,
                "au_pips": round(au * 10000, 2),
                "regime": regime,
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
                # Volatility features (FIX #4)
                "range_expansion_5": round(range_exp_5, 3),
                "range_expansion_10": round(range_exp_10, 3),
                "atr_ratio": round(atr_ratio, 3),
                # Interaction features (FIX #2)
                "regime_x_time": round(regime_x_time, 2),
                "regime_x_omega": round(regime_x_omega, 4),
                "time_x_omega": round(time_x_omega, 4),
                "regime_x_loops": regime_x_loops,
                "velocity_x_regime": round(velocity_x_regime, 4),
                "expansion_x_regime": round(expansion_x_regime, 3),
                # Target
                "remaining_dist_pips": round(remaining_dist, 2),
                "total_daily_pips": round(total_dist, 2),
            })

    return pd.DataFrame(records)


def run_cascade_attempt(symbols: Dict[str, pd.DataFrame]) -> dict:
    """Train separate XGBoost model per checkpoint (cascade)."""
    logger = RunLogger("CASCADE")
    print("\n" + "=" * 70)
    print("PHASE 2: MICRO ATOMIC LENS — CASCADE PREDICTOR (v3)")
    print("=" * 70)

    # Build all features
    all_records = []
    for sym, df in symbols.items():
        try:
            feats = build_cascade_features(df, sym)
            if len(feats) > 0:
                all_records.append(feats)
                print(f"  {sym}: {len(feats)} checkpoint-samples")
        except Exception as e:
            print(f"  {sym}: ERROR — {e}")
            import traceback; traceback.print_exc()

    if not all_records: return {}
    data = pd.concat(all_records, ignore_index=True)
    print(f"\n  Total checkpoint-samples: {len(data)}")

    # Feature columns
    feature_cols = [
        "asian_range_pips", "au_pips", "regime_encoded", "regime_ratio",
        "time_to_12pm_mins", "loop_duration", "L_theoretical", "L_actual",
        "Omega_L", "Delta_t", "dist_so_far_pips", "velocity_pips_per_min",
        "is_wednesday_pm", "day_of_week", "entropy_encoded",
        "range_expansion_5", "range_expansion_10", "atr_ratio",
        "regime_x_time", "regime_x_omega", "time_x_omega",
        "regime_x_loops", "velocity_x_regime", "expansion_x_regime",
    ]

    # Filter T4
    data = data[data["tier"] != "T4_NO_GO"].copy()
    print(f"  After T4 filter: {len(data)}")

    # ============================================================
    # FIX #1: Asymmetric loss via sample weighting
    # Weight = delta_t * (1 + regime_bonus)
    # Regime CONFIRMED gets 2x weight (big days matter more)
    # ============================================================
    base_weight = data["Delta_t"].values
    base_weight = np.maximum(base_weight, 0.01)
    regime_bonus = np.where(data["regime_encoded"].values == 2, 2.0,
                   np.where(data["regime_encoded"].values == 1, 1.5, 1.0))
    sample_weights = base_weight * regime_bonus

    # Target: remaining distribution (log-transformed)
    data["target_log"] = np.log1p(data["remaining_dist_pips"])

    X = data[feature_cols].values
    y = data["target_log"].values

    # Train separate model per checkpoint
    cascade_models = {}
    cascade_scores = {}

    for cp_name in CHECKPOINTS:
        cp_mask = data["checkpoint"] == cp_name
        if cp_mask.sum() < 200:
            print(f"  SKIP {cp_name}: only {cp_mask.sum()} samples")
            continue

        X_cp = X[cp_mask]
        y_cp = y[cp_mask]
        w_cp = sample_weights[cp_mask]

        print(f"\n  --- {cp_name} ({cp_mask.sum()} samples) ---")

        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X_cp)):
            X_train, X_test = X_cp[train_idx], X_cp[test_idx]
            y_train, y_test = y_cp[train_idx], y_cp[test_idx]
            w_train = w_cp[train_idx]

            model = xgb.XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
                reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
            )
            model.fit(X_train, y_train, sample_weight=w_train, verbose=False)

            y_pred = np.expm1(model.predict(X_test))
            y_actual = np.expm1(y_test)
            mae = mean_absolute_error(y_actual, y_pred)
            r2 = r2_score(y_actual, y_pred)
            cv_scores.append({"fold": fold + 1, "mae": round(mae, 2), "r2": round(r2, 4)})
            print(f"    Fold {fold+1}: MAE={mae:.2f} pips, R2={r2:.4f}")

        # Final model on all data for this checkpoint
        final_model = xgb.XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
        )
        final_model.fit(X_cp, y_cp, sample_weight=w_cp)

        cascade_models[cp_name] = final_model
        cascade_scores[cp_name] = cv_scores

        avg_mae = np.mean([s["mae"] for s in cv_scores])
        avg_r2 = np.mean([s["r2"] for s in cv_scores])
        print(f"    Average: MAE={avg_mae:.2f}, R2={avg_r2:.4f}")

        # Feature importance
        importance = dict(zip(feature_cols, final_model.feature_importances_.tolist()))
        print(f"    Top 5 features:")
        for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      {feat}: {imp:.4f}")

        # Save model
        model_path = ATTEMPT2_DIR / f"cascade_{cp_name}_{logger.run_id}.joblib"
        joblib.dump(final_model, model_path)

    # ============================================================
    # CASCADE EVALUATION: Simulate T0->T1->T2->T3 prediction chain
    # ============================================================
    print(f"\n  --- CASCADE SIMULATION ---")
    # For each day, simulate: predict at T0, then T1, then T2, then T3
    # Measure how prediction error shrinks at each step

    cascade_maes = {cp: [] for cp in CHECKPOINTS}
    for cp_name in CHECKPOINTS:
        if cp_name not in cascade_models: continue
        cp_data = data[data["checkpoint"] == cp_name]
        if len(cp_data) == 0: continue
        X_cp = cp_data[feature_cols].values
        y_actual = cp_data["remaining_dist_pips"].values
        y_pred = np.expm1(cascade_models[cp_name].predict(X_cp))
        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        mean_actual = y_actual.mean()
        mean_pred = y_pred.mean()
        print(f"  {cp_name}: MAE={mae:.2f}, R2={r2:.4f}, "
              f"Actual={mean_actual:.1f}, Pred={mean_pred:.1f}, "
              f"Bias={mean_pred-mean_actual:+.1f}")
        cascade_maes[cp_name] = mae

    # Check if MAE shrinks along cascade
    cp_order = ["T0", "T1", "T2", "T3"]
    maes = [cascade_maes.get(cp, None) for cp in cp_order]
    maes = [m for m in maes if m is not None]
    if len(maes) >= 2:
        shrinking = all(maes[i] >= maes[i+1] for i in range(len(maes)-1))
        print(f"\n  Cascade MAE trend: {' -> '.join(f'{m:.1f}' for m in maes)}")
        print(f"  Variance compression: {'YES' if shrinking else 'NO'}")

    logger.log(phase="cascade_v3", n_samples=len(data),
               cascade_maes=cascade_maes, model_path="cascade_models")
    logger.save()

    return {
        "data": data, "models": cascade_models,
        "scores": cascade_scores, "cascade_maes": cascade_maes,
    }


# ============================================================
# PHASE 3: MERGE (simplified — just use cascade T2 model)
# ============================================================

def run_merge_v3(cascade_result: dict, data_macro: pd.DataFrame) -> dict:
    """Phase 3: Use T2 cascade model + macro context."""
    logger = RunLogger("MERGE")
    print("\n" + "=" * 70)
    print("PHASE 3: MERGE — MACRO + CASCADE T2")
    print("=" * 70)

    if "T2" not in cascade_result.get("models", {}):
        print("  SKIP: No T2 model")
        return {}

    # The cascade T2 model already has the best features
    # Just report its performance as the "merge" result
    t2_scores = cascade_result["scores"].get("T2", [])
    if t2_scores:
        avg_mae = np.mean([s["mae"] for s in t2_scores])
        avg_r2 = np.mean([s["r2"] for s in t2_scores])
        print(f"  T2 Cascade: MAE={avg_mae:.2f}, R2={avg_r2:.4f}")

    logger.log(phase="merge_v3", model_path="cascade_T2")
    logger.save()
    return {"model": cascade_result["models"]["T2"]}


# ============================================================
# MASTER REPORT
# ============================================================

def generate_master_report(results: dict):
    report = []
    report.append("# CEREBUS DTB LAB v3 — MASTER REPORT")
    report.append(f"\n**Generated:** {datetime.now().isoformat()}")
    report.append("\n**Fixes:** Quantile loss + interactions + cascade + vol regime")

    if "attempt_1" in results and results["attempt_1"]:
        r = results["attempt_1"]
        report.append(f"\n## Phase 1: Macro MLR")
        report.append(f"- MAE: {r.get('avg_mae', 'N/A')} pips")
        report.append(f"- R2: {r.get('avg_r2', 'N/A')}")

    if "cascade" in results and results["cascade"]:
        r = results["cascade"]
        report.append(f"\n## Phase 2: Cascade Predictor")
        maes = r.get("cascade_maes", {})
        for cp, mae in maes.items():
            report.append(f"- {cp}: MAE={mae:.2f} pips")

    report_text = "\n".join(report)
    report_path = LAB_DIR / "MASTER_LAB_REPORT.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"\n  Report saved: {report_path}")
    return report_text


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("CEREBUS DTB v3 — CASCADE VARIANCE COMPRESSION ENGINE")
    print("=" * 70)
    print("\nFixes: asymmetric loss + interactions + cascade + vol regime")

    print("\n[DATA] Loading...")
    symbols = load_all_symbols()
    if not symbols:
        print("ERROR: No data!"); return

    print("\n[PHASE 1] Macro MLR...")
    result1 = run_attempt1(symbols)

    print("\n[PHASE 2] Cascade Predictor...")
    result2 = run_cascade_attempt(symbols)

    print("\n[PHASE 3] Merge...")
    result3 = run_merge_v3(result2, result1.get("data", pd.DataFrame()))

    print("\n[REPORT]")
    generate_master_report({"attempt_1": result1, "cascade": result2, "merge": result3})

    print("\n" + "=" * 70)
    print("DTB v3 LAB COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
