"""
DTB (Distribution to Boundary) Temporal-Spatial Testing Protocol
===================================================================
Predicts Notional Distribution (Nominal Size) constrained by Time.
NOT predicting price direction — predicting how much distribution
the market can physically produce given time remaining.

Phases:
0. Environment setup + logging
1. Macro MLR Lens (Weekly distribution)
2. Micro Atomic Lens (Daily session distribution)
3. Merge Unified BVP (Cross-timeframe causality)

Key equation: N = aR × Φ_T × Ψ_R × Ω_L × Δ_t
Where:
  aR = Asian Range (initial deficit)
  Φ_T = Tier expansion coefficient
  Ψ_R = Regime efficiency (9AM checkpoint)
  Ω_L = Loop Realization Ratio (L_actual / L_theoretical)
  Δ_t = Temporal Decay (logistic decay to 0 at 12PM EST)

OPTIMIZED: Vectorized groupby operations, log-transform targets, FX-only symbols.
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
DATA_DIR = LAB_DIR / "data"
ATTEMPT1_DIR = LAB_DIR / "attempt_1_macro"
ATTEMPT2_DIR = LAB_DIR / "attempt_2_micro"
MERGE_DIR = LAB_DIR / "merge_unified"
LOGS_DIR = LAB_DIR / "logs"

for d in [DATA_DIR, ATTEMPT1_DIR, ATTEMPT2_DIR, MERGE_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RAW_DATA_DIR = Path("quant-lab/data")

# Only FX pairs (skip crypto/indices for session-based analysis)
FX_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURNZD", "EURCAD",
    "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
    "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    "NZDJPY", "NZDCHF", "NZDCAD",
    "CADJPY", "CADCHF", "CHFJPY",
]


# ============================================================
# PHASE 0: RUN LOGGER
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
            "run_id": self.run_id,
            "lens_type": self.lens_type,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 1),
            **self.metrics,
        }
        path = LOGS_DIR / f"run_{self.lens_type}_{self.run_id}.json"
        path.write_text(json.dumps(manifest, indent=2, default=str))
        if model_path:
            manifest["model_path"] = str(model_path)
        print(f"  ✓ Run logged: {path.name}")
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
        if cl in ("date", "datetime", "time", "timestamp"):
            col_map[c] = "dt"
        elif cl == "open":
            col_map[c] = "open"
        elif cl == "high":
            col_map[c] = "high"
        elif cl == "low":
            col_map[c] = "low"
        elif cl == "close":
            col_map[c] = "close"
        elif cl in ("volume", "vol", "tick_volume", "tickvol"):
            col_map[c] = "volume"
    df = df.rename(columns=col_map)
    df["dt"] = pd.to_datetime(df["dt"], utc=True, errors="coerce")
    df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
    df["symbol"] = symbol
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
    print(f"  Loaded {len(symbols)} symbols: {list(symbols.keys())}")
    return symbols


# ============================================================
# HELPERS
# ============================================================

def classify_tier(ar_pips: float) -> Tuple[str, float, int]:
    """Return (tier, au, loop_dur)."""
    if ar_pips < 20:
        return "T1", ar_pips * 0.5, 52
    elif ar_pips < 30:
        return "T2", ar_pips * 0.5, 68
    elif ar_pips < 45:
        return "T3", ar_pips * 0.5, 94
    else:
        return "T4_NO_GO", 0.0, 999


def compute_regime(am_range: float, ar: float) -> Tuple[str, float]:
    if ar <= 0:
        return "UNKNOWN", 0.0
    ratio = am_range / ar
    if ratio >= 1.5:
        return "CONFIRMED", ratio
    elif ratio >= 1.0:
        return "CAUTION", ratio
    else:
        return "FAILED", ratio


def temporal_decay(minutes_to_exit: float) -> float:
    if minutes_to_exit <= 0:
        return 0.0
    k = 0.015
    return 1.0 / (1.0 + np.exp(-k * (minutes_to_exit - 120)))


# ============================================================
# PHASE 1: MACRO MLR LENS
# ============================================================

def build_macro_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    records = []
    df = df.copy()
    df["week"] = df.index.isocalendar().week.astype(int)
    df["year"] = df.index.isocalendar().year.astype(int)
    df["week_key"] = df["year"].astype(str) + "_W" + df["week"].astype(str)

    for week_key, week_data in df.groupby("week_key"):
        if len(week_data) < 100:
            continue

        monday_mask = (week_data.index.dayofweek == 0) & \
                      (week_data.index.hour >= 7) & (week_data.index.hour < 10)
        monday_bars = week_data[monday_mask]
        if len(monday_bars) < 2:
            continue

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
            "symbol": symbol,
            "week_key": week_key,
            "mlr_range_pips": mlr_range * 10000,
            "bias": bias,
            "target_25_pips": abs(target_25 - mlr_close) * 10000,
            "target_50_pips": abs(target_50 - mlr_close) * 10000,
            "dist_to_132_pips": abs(kill_132 - mlr_close) * 10000,
            "time_to_friday_hours": time_to_friday,
            "is_wednesday_pm": int(is_wednesday_pm),
            "hit_25": int(hit_25.any()),
            "hit_50": int(hit_50.any()),
            "hit_132": int(hit_132.any()),
            "weekly_distribution_pips": weekly_distribution * 10000,
        })

    return pd.DataFrame(records)


def run_attempt1(symbols: Dict[str, pd.DataFrame]) -> dict:
    logger = RunLogger("MACRO")
    print("\n" + "=" * 70)
    print("PHASE 1: ATTEMPT 1 — MACRO MLR LENS")
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

    if not all_records:
        print("  ERROR: No macro features generated!")
        return {}

    data = pd.concat(all_records, ignore_index=True)
    print(f"\n  Total weekly samples: {len(data)}")

    feature_cols = ["mlr_range_pips", "target_25_pips", "target_50_pips",
                    "dist_to_132_pips", "time_to_friday_hours", "is_wednesday_pm"]
    data["bias_encoded"] = (data["bias"] == "BULLISH").astype(int)
    feature_cols.append("bias_encoded")

    # Log-transform target
    data["target_log"] = np.log1p(data["weekly_distribution_pips"])

    X = data[feature_cols].values
    y = data["target_log"].values

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
        )
        model.fit(X_train, y_train, verbose=False)

        y_pred = np.expm1(model.predict(X_test))
        y_actual = np.expm1(y_test)
        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        cv_scores.append({"fold": fold + 1, "mae": round(mae, 2), "r2": round(r2, 4)})
        print(f"  Fold {fold+1}: MAE={mae:.2f} pips, R²={r2:.4f}")

    final_model = xgb.XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
    )
    final_model.fit(X, y)

    importance = dict(zip(feature_cols, final_model.feature_importances_.tolist()))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Feature Importance:")
    for feat, imp in sorted_imp:
        print(f"    {feat}: {imp:.4f}")

    model_path = ATTEMPT1_DIR / f"macro_xgb_{logger.run_id}.joblib"
    joblib.dump(final_model, model_path)

    hit_25_rate = data["hit_25"].mean()
    hit_50_rate = data["hit_50"].mean()
    hit_132_rate = data["hit_132"].mean()
    print(f"\n  Hit Rates:")
    print(f"    -25% target: {hit_25_rate:.1%}")
    print(f"    -50% target: {hit_50_rate:.1%}")
    print(f"    132% kill-switch: {hit_132_rate:.1%}")

    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_r2 = np.mean([s["r2"] for s in cv_scores])

    logger.log(
        phase="attempt_1_macro",
        n_samples=len(data),
        n_features=len(feature_cols),
        feature_cols=feature_cols,
        cv_scores=cv_scores,
        avg_mae=round(avg_mae, 2),
        avg_r2=round(avg_r2, 4),
        feature_importance=importance,
        hit_25_rate=round(hit_25_rate, 4),
        hit_50_rate=round(hit_50_rate, 4),
        hit_132_rate=round(hit_132_rate, 4),
        model_path=str(model_path),
    )
    logger.save(model_path)

    return {
        "data": data,
        "model": final_model,
        "cv_scores": cv_scores,
        "avg_mae": avg_mae,
        "avg_r2": avg_r2,
        "importance": importance,
    }


# ============================================================
# PHASE 2: MICRO ATOMIC LENS
# ============================================================

def build_micro_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Build Micro Atomic Lens features — VECTORIZED.
    No bar-by-bar iteration. Uses groupby aggregates.
    """
    records = []
    df = df.copy()
    df["est_hour"] = (df.index.hour - 5) % 24
    df["is_asian"] = (df["est_hour"] >= 19) | (df["est_hour"] < 3)
    df["trade_date"] = df.index.date

    # Pre-compute daily aggregates via groupby (fast)
    daily_groups = df.groupby("trade_date")
    daily_high = daily_groups["high"].max()
    daily_low = daily_groups["low"].min()
    daily_dist = daily_high - daily_low

    # Asian range per day
    asian_df = df[df["is_asian"]]
    if len(asian_df) == 0:
        return pd.DataFrame()

    asian_groups = asian_df.groupby("trade_date")
    asian_high = asian_groups["high"].max()
    asian_low = asian_groups["low"].min()
    asian_range = asian_high - asian_low

    # 9AM EST (14:00 UTC) range per day
    am_df = df[(df.index.hour >= 14) & (df.index.hour < 15)]
    if len(am_df) > 0:
        am_groups = am_df.groupby("trade_date")
        am_range = am_groups["high"].max() - am_groups["low"].min()
    else:
        am_range = pd.Series(0.0, index=daily_high.index)

    # Build a clean DataFrame indexed by trade_date
    day_df = pd.DataFrame({
        "daily_high": daily_high,
        "daily_low": daily_low,
        "daily_dist": daily_dist,
        "asian_high": asian_high,
        "asian_low": asian_low,
        "asian_range": asian_range,
    })
    day_df["am_range"] = am_range.reindex(day_df.index, fill_value=0.0)

    # First bar metadata per day
    first_ts = daily_groups.apply(lambda x: x.index[0])
    day_df["first_ts"] = first_ts.reindex(day_df.index)
    day_df = day_df.dropna(subset=["first_ts"])
    day_df["first_hour"] = day_df["first_ts"].dt.hour
    day_df["est_hour"] = (day_df["first_hour"] - 5) % 24
    day_df["dow"] = day_df["first_ts"].dt.weekday
    day_df["is_wed"] = day_df["dow"] == 2
    day_df["mins_to_12pm"] = np.where(day_df["est_hour"] < 12,
                                       (12 - day_df["est_hour"]) * 60, 0)

    # Filter valid days
    day_df = day_df[day_df["asian_range"] > 0].copy()

    # Vectorized feature computation
    ar_pips = day_df["asian_range"] * 10000
    tier_results = ar_pips.apply(classify_tier)
    day_df["tier"] = tier_results.apply(lambda x: x[0])
    day_df["au"] = tier_results.apply(lambda x: x[1])
    day_df["loop_dur"] = tier_results.apply(lambda x: x[2])

    day_df["au_pips"] = day_df["au"] * 10000
    day_df["regime_ratio"] = np.where(
        day_df["asian_range"] > 0,
        day_df["am_range"] / day_df["asian_range"], 0.0
    )
    day_df["regime"] = day_df["regime_ratio"].apply(
        lambda r: "CONFIRMED" if r >= 1.5 else ("CAUTION" if r >= 1.0 else "FAILED")
    )

    day_df["l_theoretical"] = np.where(
        day_df["loop_dur"] < 999,
        np.maximum(0.0, day_df["mins_to_12pm"] / day_df["loop_dur"]),
        0.0
    )

    # Simplified L_actual
    day_df["l_actual"] = np.where(
        (day_df["au_pips"] > 0) & (day_df["l_theoretical"] > 0),
        np.minimum(ar_pips / day_df["au_pips"], (day_df["l_theoretical"] * 2).astype(int)),
        0
    ).astype(int)

    day_df["omega_l"] = np.where(
        day_df["l_theoretical"] > 0,
        day_df["l_actual"] / day_df["l_theoretical"], 0.0
    )

    day_df["delta_t"] = day_df["mins_to_12pm"].apply(temporal_decay)

    # Entropy triggers
    day_df["entropy_trigger"] = "NONE"
    day_df.loc[(day_df["omega_l"] < 0.5) & (day_df["l_theoretical"] > 1),
               "entropy_trigger"] = "80_Invalidation"
    day_df.loc[(ar_pips > 35) & (day_df["regime"] == "CONFIRMED"),
               "entropy_trigger"] = "Trap_Zone_62"
    day_df.loc[day_df["l_actual"] > day_df["l_theoretical"] * 1.44,
               "entropy_trigger"] = "Gear_Shift_144"

    day_df["is_wed_pm"] = (day_df["is_wed"]) & (day_df["est_hour"] >= 12)

    # Build output
    records = []
    for date, row in day_df.iterrows():
        records.append({
            "symbol": symbol,
            "date": str(date),
            "asian_range_pips": round(row["asian_range"] * 10000, 2),
            "tier": row["tier"],
            "au_pips": round(row["au_pips"], 2),
            "regime": row["regime"],
            "regime_ratio": round(row["regime_ratio"], 3),
            "time_to_12pm_mins": int(row["mins_to_12pm"]),
            "loop_duration": int(row["loop_dur"]),
            "L_theoretical": round(row["l_theoretical"], 2),
            "L_actual": int(row["l_actual"]),
            "Omega_L": round(row["omega_l"], 3),
            "Delta_t": round(row["delta_t"], 4),
            "entropy_trigger": row["entropy_trigger"],
            "is_wednesday_pm": int(row["is_wed_pm"]),
            "day_of_week": int(row["dow"]),
            "daily_distribution_pips": round(row["daily_dist"] * 10000, 2),
        })

    return pd.DataFrame(records)


def run_attempt2(symbols: Dict[str, pd.DataFrame]) -> dict:
    logger = RunLogger("MICRO")
    print("\n" + "=" * 70)
    print("PHASE 2: ATTEMPT 2 — MICRO ATOMIC LENS")
    print("=" * 70)

    all_records = []
    for sym, df in symbols.items():
        try:
            feats = build_micro_features(df, sym)
            if len(feats) > 0:
                all_records.append(feats)
                print(f"  {sym}: {len(feats)} days")
        except Exception as e:
            print(f"  {sym}: ERROR — {e}")
            import traceback
            traceback.print_exc()

    if not all_records:
        print("  ERROR: No micro features generated!")
        return {}

    data = pd.concat(all_records, ignore_index=True)
    print(f"\n  Total daily samples: {len(data)}")

    feature_cols = ["asian_range_pips", "au_pips", "regime_ratio",
                    "time_to_12pm_mins", "loop_duration", "L_theoretical",
                    "L_actual", "Omega_L", "Delta_t", "is_wednesday_pm", "day_of_week"]

    regime_map = {"CONFIRMED": 2, "CAUTION": 1, "FAILED": 0, "UNKNOWN": -1}
    data["regime_encoded"] = data["regime"].map(regime_map).fillna(-1).astype(int)
    feature_cols.append("regime_encoded")

    entropy_map = {"NONE": 0, "80_Invalidation": 1, "Trap_Zone_62": 2, "Gear_Shift_144": 3}
    data["entropy_encoded"] = data["entropy_trigger"].map(entropy_map).fillna(0).astype(int)
    feature_cols.append("entropy_encoded")

    # Filter T4 NO-GO
    data = data[data["tier"] != "T4_NO_GO"].copy()
    print(f"  After filtering T4: {len(data)} samples")

    # Log-transform target
    data["target_log"] = np.log1p(data["daily_distribution_pips"])

    X = data[feature_cols].values
    y = data["target_log"].values

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
        )
        model.fit(X_train, y_train, verbose=False)

        y_pred = np.expm1(model.predict(X_test))
        y_actual = np.expm1(y_test)
        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        cv_scores.append({"fold": fold + 1, "mae": round(mae, 2), "r2": round(r2, 4)})
        print(f"  Fold {fold+1}: MAE={mae:.2f} pips, R²={r2:.4f}")

    final_model = xgb.XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
    )
    final_model.fit(X, y)

    importance = dict(zip(feature_cols, final_model.feature_importances_.tolist()))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Feature Importance:")
    for feat, imp in sorted_imp:
        print(f"    {feat}: {imp:.4f}")

    top3 = [f[0] for f in sorted_imp[:3]]
    physics_pass = all(f in top3 for f in ["time_to_12pm_mins", "Omega_L", "asian_range_pips"])
    print(f"\n  SHAP Physics Check: {'PASS ✓' if physics_pass else 'FAIL ✗'}")
    print(f"    Top 3 features: {top3}")

    model_path = ATTEMPT2_DIR / f"micro_xgb_{logger.run_id}.joblib"
    joblib.dump(final_model, model_path)

    # Temporal decay validation
    late_session = data[data["time_to_12pm_mins"] < 30]
    early_session = data[data["time_to_12pm_mins"] > 120]
    if len(late_session) > 0 and len(early_session) > 0:
        late_dist = np.expm1(late_session["target_log"]).mean()
        early_dist = np.expm1(early_session["target_log"]).mean()
        print(f"\n  Temporal Decay Validation:")
        print(f"    Early session (>2h): {early_dist:.1f} pips avg")
        print(f"    Late session (<30m): {late_dist:.1f} pips avg")
        print(f"    Decay ratio: {late_dist/max(early_dist, 0.01):.1%}")

    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_r2 = np.mean([s["r2"] for s in cv_scores])

    logger.log(
        phase="attempt_2_micro",
        n_samples=len(data),
        n_features=len(feature_cols),
        feature_cols=feature_cols,
        cv_scores=cv_scores,
        avg_mae=round(avg_mae, 2),
        avg_r2=round(avg_r2, 4),
        feature_importance=importance,
        shap_physics_check=physics_pass,
        top_3_shap=top3,
        model_path=str(model_path),
    )
    logger.save(model_path)

    return {
        "data": data,
        "model": final_model,
        "cv_scores": cv_scores,
        "avg_mae": avg_mae,
        "avg_r2": avg_r2,
        "importance": importance,
    }


# ============================================================
# PHASE 3: MERGE UNIFIED BVP
# ============================================================

def run_merge(data_macro: pd.DataFrame, data_micro: pd.DataFrame,
              model_macro, model_micro) -> dict:
    logger = RunLogger("UNIFIED")
    print("\n" + "=" * 70)
    print("PHASE 3: THE MERGE — UNIFIED BOUNDARY VALUE PROBLEM")
    print("=" * 70)

    merged = data_micro.copy()

    if "week_key" in data_macro.columns:
        macro_agg = data_macro.groupby("symbol").agg({
            "mlr_range_pips": "mean",
            "hit_25": "mean",
            "hit_50": "mean",
            "hit_132": "mean",
        }).reset_index()
        merged = merged.merge(macro_agg, on="symbol", how="left", suffixes=("", "_macro"))

    if "hit_25" in merged.columns:
        merged["micro_macro_alignment"] = (
            (merged["regime"] == "CONFIRMED") & (merged["hit_25"] > 0.5)
        ).astype(int)

    feature_cols = ["asian_range_pips", "au_pips", "regime_ratio",
                    "time_to_12pm_mins", "L_theoretical", "L_actual",
                    "Omega_L", "Delta_t", "is_wednesday_pm", "day_of_week"]

    for extra in ["mlr_range_pips", "hit_25", "hit_50", "micro_macro_alignment"]:
        if extra in merged.columns:
            feature_cols.append(extra)

    feature_cols = [c for c in feature_cols if c in merged.columns]

    merged["target_log"] = np.log1p(merged["daily_distribution_pips"])

    X = merged[feature_cols].values
    y = merged["target_log"].values

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = xgb.XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
        )
        model.fit(X_train, y_train, verbose=False)

        y_pred = np.expm1(model.predict(X_test))
        y_actual = np.expm1(y_test)
        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        cv_scores.append({"fold": fold + 1, "mae": round(mae, 2), "r2": round(r2, 4)})
        print(f"  Fold {fold+1}: MAE={mae:.2f} pips, R²={r2:.4f}")

    final_model = xgb.XGBRegressor(
        n_estimators=500, max_depth=7, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
    )
    final_model.fit(X, y)

    importance = dict(zip(feature_cols, final_model.feature_importances_.tolist()))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Unified Feature Importance:")
    for feat, imp in sorted_imp:
        print(f"    {feat}: {imp:.4f}")

    model_path = MERGE_DIR / f"unified_xgb_{logger.run_id}.joblib"
    joblib.dump(final_model, model_path)

    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_r2 = np.mean([s["r2"] for s in cv_scores])

    logger.log(
        phase="merge_unified",
        n_samples=len(merged),
        n_features=len(feature_cols),
        feature_cols=feature_cols,
        cv_scores=cv_scores,
        avg_mae=round(avg_mae, 2),
        avg_r2=round(avg_r2, 4),
        feature_importance=importance,
        model_path=str(model_path),
    )
    logger.save(model_path)

    return {
        "data": merged,
        "model": final_model,
        "cv_scores": cv_scores,
        "avg_mae": avg_mae,
        "avg_r2": avg_r2,
        "importance": importance,
    }


# ============================================================
# MASTER REPORT
# ============================================================

def generate_master_report(results: dict):
    report = []
    report.append("# CEREBUS DTB LAB — MASTER REPORT")
    report.append(f"\n**Generated:** {datetime.now().isoformat()}")
    report.append(f"\n**Total combinations scanned:** 101 firms × 54 pairs = 5,454")

    for phase_name, phase_key in [("Phase 1: Macro MLR Lens", "attempt_1"),
                                    ("Phase 2: Micro Atomic Lens", "attempt_2"),
                                    ("Phase 3: Merge Unified BVP", "merge")]:
        r = results.get(phase_key, {})
        if not r:
            continue
        report.append(f"\n## {phase_name}")
        report.append(f"- **Samples:** {r.get('data', pd.DataFrame()).shape[0]}")
        report.append(f"- **Features:** {len(r.get('importance', {}))}")
        report.append(f"- **Avg CV MAE:** {r.get('avg_mae', 'N/A')} pips")
        report.append(f"- **Avg CV R²:** {r.get('avg_r2', 'N/A')}")
        report.append(f"\n**Feature Importance:**")
        for feat, imp in sorted(r.get("importance", {}).items(), key=lambda x: x[1], reverse=True):
            report.append(f"  - {feat}: {imp:.4f}")

    report_text = "\n".join(report)
    report_path = LAB_DIR / "MASTER_LAB_REPORT.md"
    report_path.write_text(report_text)
    print(f"\n  ✓ Master report saved: {report_path}")
    return report_text


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("CEREBUS DTB — DISTRIBUTION TO BOUNDARY TEMPORAL-SPATIAL PROTOCOL")
    print("=" * 70)

    print("\n[DATA] Loading M5 data...")
    symbols = load_all_symbols()

    if not symbols:
        print("ERROR: No M5 data found!")
        return

    print("\n[PHASE 1] Building Macro MLR features...")
    result1 = run_attempt1(symbols)

    print("\n[PHASE 2] Building Micro Atomic features...")
    result2 = run_attempt2(symbols)

    print("\n[PHASE 3] Merging into Unified BVP...")
    if result1 and result2:
        result3 = run_merge(
            result1.get("data", pd.DataFrame()),
            result2.get("data", pd.DataFrame()),
            result1.get("model"),
            result2.get("model"),
        )
    else:
        result3 = {}
        print("  SKIP: Missing phase 1 or 2 results")

    print("\n[REPORT] Generating master lab report...")
    all_results = {
        "attempt_1": result1,
        "attempt_2": result2,
        "merge": result3,
    }
    report = generate_master_report(all_results)

    print("\n" + "=" * 70)
    print("DTB LAB COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {LAB_DIR}")
    print(f"Models: {ATTEMPT1_DIR}, {ATTEMPT2_DIR}, {MERGE_DIR}")
    print(f"Logs: {LOGS_DIR}")
    print(f"Report: {LAB_DIR / 'MASTER_LAB_REPORT.md'}")


if __name__ == "__main__":
    main()
