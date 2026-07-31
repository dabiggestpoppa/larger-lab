"""
Macro Monthly DTB — Distribution to Boundary Cascade Predictor
===============================================================
Fractal-scaled version of DTB v4 for monthly predictions.

Same morphism equation, different time lens:
  Intraday: N = aR × Φ_T × Ψ_R × Ω_L × Δ_t  (M5, 8h window)
  Macro:    N = W1 × Φ_WT × Ψ_MR × Ω_DL × Δ_D  (Daily, 15-day window)

Checkpoints:
  T0 (Day 5 Close)  → Base prediction (Week 1 Range + Macro Tier)
  T1 (Day 8 Close)  → Velocity check (Daily Loop completion)
  T2 (Day 11 Close) → Regime lock (Macro Regime confirmed)
  T3 (Day 13)       → Temporal decay (80% threshold, variance → 0)

Manual rules:
  - W1 Range = High-Low of Trading Days 1-5
  - Activation: M5 close outside 5-Day band
  - 2-hour hold filter for false breakout rejection
  - Target: 2.0x extension of W1 Range (200% Fib alignment)
  - Invalidation: M5 close back inside 5-Day band (81.2% rule)
  - Hard exit: Day 15 close
  - NO-GO: W1 Range > 200 pips (exhaustion)
"""
from __future__ import annotations
import json, uuid, time, warnings
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

LAB_DIR = Path(__file__).parent
MODEL_DIR = LAB_DIR / "models_macro"
LOGS_DIR = LAB_DIR / "logs"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RAW_DATA_DIR = Path("quant-lab/data")

TRAIN_SYMBOLS = ["EURUSD", "USDCHF", "BTCUSD"]

# Macro checkpoints (trading days of month)
MACRO_CHECKPOINTS = {
    "T0": 5,   # Day 5 Close — Anchor
    "T1": 8,   # Day 8 Close — Velocity Check
    "T2": 11,  # Day 11 Close — Regime Lock
    "T3": 13,  # Day 13 — 80% Threshold / Temporal Decay
}
HARD_EXIT_DAY = 15  # Day 15 — Engine shutdown

# Macro Tier thresholds (Week 1 Range in pips)
# W-T1: <120p (2.95x), W-T2: 120-165p (2.55x), W-T3: >165p (2.15x), NO-GO: >200p
MACRO_TIERS = {
    "W-T1": (0, 120, 2.95),
    "W-T2": (120, 165, 2.55),
    "W-T3": (165, 200, 2.15),
    "NO-GO": (200, 99999, 0),
}


class RunLogger:
    def __init__(self, name):
        self.name = name
        self.id = str(uuid.uuid4())[:8]
        self.t0 = time.time()
        self.metrics = {}
    def log(self, **kw): self.metrics.update(kw)
    def save(self, path=None):
        m = {"run_id": self.id, "name": self.name,
             "timestamp": datetime.now().isoformat(),
             "elapsed_s": round(time.time() - self.t0, 1), **self.metrics}
        p = LOGS_DIR / f"run_{self.name}_{self.id}.json"
        p.write_text(json.dumps(m, indent=2, default=str), encoding="utf-8")
        print(f"  Logged: {p.name}")
        return m


def load_daily(symbol: str) -> pd.DataFrame:
    """Load daily OHLCV data. Falls back to M5 aggregated to daily."""
    # Try daily CSV first
    for suffix in ["_D1.csv", "_daily.csv"]:
        p = RAW_DATA_DIR / f"{symbol}{suffix}"
        if p.exists():
            df = pd.read_csv(p)
            return _parse_daily(df, symbol)

    # Aggregate from M5
    p = RAW_DATA_DIR / f"{symbol}_M5.csv"
    if not p.exists():
        return pd.DataFrame()

    df = pd.read_csv(p)
    df['dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['dt']).set_index('dt').sort_index()
    df['trade_date'] = df.index.date

    daily = df.groupby('trade_date').agg(
        open=('open', 'first'),
        high=('high', 'max'),
        low=('low', 'min'),
        close=('close', 'last'),
        volume=('volume', 'sum'),
    )
    daily.index = pd.to_datetime(daily.index)
    daily['symbol'] = symbol
    return daily


def _parse_daily(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Parse daily CSV with standard column names."""
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ('date', 'datetime', 'time', 'timestamp'): col_map[c] = 'dt'
        elif cl in ('open', 'high', 'low', 'close'): col_map[c] = cl
        elif cl in ('volume', 'vol'): col_map[c] = 'volume'
    df = df.rename(columns=col_map)
    df['dt'] = pd.to_datetime(df['dt'], utc=True, errors='coerce')
    df = df.dropna(subset=['dt']).set_index('dt').sort_index()
    df['symbol'] = symbol
    return df


def macro_tier(w1_range_pips: float) -> Tuple[str, float]:
    """
    Macro tier classification based on Week 1 Range.
    Returns (tier_name, expansion_multiplier).
    """
    for tier_name, (lo, hi, mult) in MACRO_TIERS.items():
        if lo <= w1_range_pips < hi:
            return tier_name, mult
    return "NO-GO", 0.0


def temporal_decay_days(days_remaining: int) -> float:
    """Logistic decay — approaches 0 as days_remaining approaches 0."""
    if days_remaining <= 0:
        return 0.0
    k = 0.3  # Steeper than intraday (days vs hours)
    return 1.0 / (1.0 + np.exp(-k * (days_remaining - 4)))


def build_macro_features(
    daily: pd.DataFrame,
    symbol: str,
    checkpoint_day: int,
) -> Optional[Dict]:
    """
    Build features at a macro checkpoint.

    Uses daily bars from Day 1 through the checkpoint to predict
    remaining distribution from checkpoint to Day 15.
    """
    if len(daily) < checkpoint_day:
        return None

    # Week 1 = Trading Days 1-5
    w1 = daily.iloc[:5]
    if len(w1) < 5:
        return None

    w1_high = w1['high'].max()
    w1_low = w1['low'].min()
    w1_range = w1_high - w1_low
    w1_range_pips = w1_range * 10000

    tier_name, phi_wt = macro_tier(w1_range_pips)
    if tier_name == "NO-GO":
        return None

    # Days elapsed and remaining
    days_elapsed = checkpoint_day
    days_remaining = HARD_EXIT_DAY - checkpoint_day
    delta_d = temporal_decay_days(days_remaining)

    # Daily bars from Day 5 to checkpoint (the expansion phase)
    # For T0 (Day 5), expansion is empty — use W1-only features
    expansion = daily.iloc[5:checkpoint_day] if checkpoint_day > 5 else pd.DataFrame()

    # Macro Regime: Did Days 6-checkpoint expand cleanly?
    if len(expansion) >= 1 and w1_range > 0:
        exp_range = expansion['high'].max() - expansion['low'].min()
        exp_ratio = float(exp_range / w1_range)
        if np.isnan(exp_ratio) or np.isinf(exp_ratio):
            exp_ratio = 0.0
        macro_regime = 2 if exp_ratio >= 1.5 else (1 if exp_ratio >= 1.0 else 0)
    else:
        macro_regime = 0
        exp_ratio = 0.0

    # Daily Loops
    daily_loops = _count_daily_loops(expansion) if len(expansion) >= 2 else 0
    theoretical_loops = max(1, len(expansion))
    omega_dl = float(daily_loops) / theoretical_loops if theoretical_loops > 0 else 0.0

    # Distribution achieved so far
    dist_data = daily.iloc[:checkpoint_day]
    if len(dist_data) > 0:
        dist_so_far = float((dist_data['high'].max() - dist_data['low'].min()) * 10000)
    else:
        dist_so_far = float(w1_range_pips)
    if np.isnan(dist_so_far) or np.isinf(dist_so_far):
        dist_so_far = 0.0

    # Velocity
    vel_denom = max(checkpoint_day - 5, 1)
    velocity = float(dist_so_far) / vel_denom
    if np.isnan(velocity) or np.isinf(velocity):
        velocity = 0.0

    # Day of week for the checkpoint
    checkpoint_date = daily.index[min(checkpoint_day - 1, len(daily) - 1)]
    dow = checkpoint_date.weekday()

    def _s(v, d=0.0):
        if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
            return d
        return v

    return {
        "symbol": symbol,
        "date": str(checkpoint_date.date()),
        "checkpoint": f"T{checkpoint_day}",
        "w1_range_pips": _s(round(w1_range_pips, 2)),
        "macro_tier": tier_name,
        "phi_wt": _s(phi_wt),
        "days_elapsed": _s(days_elapsed, 5),
        "days_remaining": _s(days_remaining, 10),
        "delta_d": _s(round(delta_d, 4)),
        "macro_regime": _s(macro_regime, 0),
        "exp_ratio": _s(round(exp_ratio, 3)),
        "daily_loops": _s(daily_loops, 0),
        "theoretical_loops": _s(theoretical_loops, 1),
        "omega_dl": _s(round(omega_dl, 3)),
        "dist_so_far_pips": _s(round(dist_so_far, 2)),
        "velocity_pips_per_day": _s(round(velocity, 2)),
        "dow": _s(dow, 0),
    }


def _count_daily_loops(expansion: pd.DataFrame) -> int:
    """
    Count daily impulse-rebalance cycles.
    A loop = daily close in one direction, then next day retraces 32-50%.
    """
    if len(expansion) < 2:
        return 0

    closes = expansion['close'].values
    highs = expansion['high'].values
    lows = expansion['low'].values

    loops = 0
    in_impulse = False
    impulse_high = 0.0
    impulse_low = 999999.0

    for i in range(len(expansion)):
        if not in_impulse:
            # Start impulse if close is at extreme
            if i > 0:
                prev_close = closes[i - 1]
                if closes[i] > prev_close * 1.001:  # Bullish impulse
                    in_impulse = True
                    impulse_high = highs[i]
                    impulse_low = lows[i]
                elif closes[i] < prev_close * 0.999:  # Bearish impulse
                    in_impulse = True
                    impulse_high = highs[i]
                    impulse_low = lows[i]
        else:
            impulse_high = max(impulse_high, highs[i])
            impulse_low = min(impulse_low, lows[i])
            impulse_range = impulse_high - impulse_low

            if impulse_range > 0:
                retrace = (impulse_high - closes[i]) / impulse_range
                if 0.32 <= retrace <= 0.50:
                    loops += 1
                    in_impulse = False

    return loops


def build_training_data(
    symbol: str,
    checkpoint_day: int,
) -> pd.DataFrame:
    """
    Build labeled training data for a macro checkpoint.

    For each month in the data:
    1. Compute W1 Range (Days 1-5)
    2. Compute features at checkpoint
    3. Label = actual remaining distribution (checkpoint to Day 15 extreme)
    """
    daily = load_daily(symbol)
    if len(daily) < 15:
        return pd.DataFrame()

    # Group by month
    daily['year_month'] = daily.index.to_period('M')

    records = []
    for ym, month_data in daily.groupby('year_month'):
        if len(month_data) < 15:
            continue

        # Sort by date
        month_data = month_data.sort_index()

        # Week 1 = first 5 trading days
        w1 = month_data.iloc[:5]
        w1_high = w1['high'].max()
        w1_low = w1['low'].min()
        w1_range = w1_high - w1_low
        w1_range_pips = w1_range * 10000

        tier_name, phi_wt = macro_tier(w1_range_pips)
        if tier_name == "NO-GO":
            continue

        # Checkpoint features
        features = build_macro_features(month_data, symbol, checkpoint_day)
        if features is None:
            continue

        # Label: remaining distribution from checkpoint to Day 15
        checkpoint_idx = min(checkpoint_day - 1, len(month_data) - 1)
        day15_idx = min(14, len(month_data) - 1)

        remaining_data = month_data.iloc[checkpoint_idx:day15_idx + 1]
        if len(remaining_data) < 1:
            continue

        remaining_high = remaining_data['high'].max()
        remaining_low = remaining_data['low'].min()

        # Skip if NaN
        if pd.isna(remaining_high) or pd.isna(remaining_low):
            continue

        remaining_range = (remaining_high - remaining_low) * 10000

        # Also compute MFE (Maximum Favorable Excursion) from breakout direction
        w1_mid = (w1_high + w1_low) / 2
        if len(month_data) > 5:
            day6_close = month_data.iloc[5]['close']
            if pd.isna(day6_close):
                day6_close = w1_mid
        else:
            day6_close = w1_mid

        if day6_close > w1_high:  # LONG breakout
            mfe = (remaining_high - w1_high) * 10000
        elif day6_close < w1_low:  # SHORT breakout
            mfe = (w1_low - remaining_low) * 10000
        else:  # No breakout
            mfe = remaining_range

        # Skip if any critical value is NaN
        if np.isnan(remaining_range) or np.isnan(mfe):
            continue

        features['remaining_pips'] = round(remaining_range, 2)
        features['mfe_pips'] = round(mfe, 2)
        features['breakout_direction'] = 1 if day6_close > w1_high else (-1 if day6_close < w1_low else 0)

        records.append(features)

    df = pd.DataFrame(records)
    # Drop any rows with NaN in feature or target columns
    if len(df) > 0:
        feature_cols = [
            "w1_range_pips", "phi_wt", "days_elapsed", "days_remaining",
            "delta_d", "macro_regime", "exp_ratio", "daily_loops",
            "omega_dl", "dist_so_far_pips", "velocity_pips_per_day", "dow",
        ]
        df = df.dropna(subset=feature_cols + ['mfe_pips'])
    return df


def train_macro_checkpoint(symbols: List[str], checkpoint_day: int, cp_name: str):
    """Train XGBoost for a specific macro checkpoint."""
    logger = RunLogger(f"macro_{cp_name}")
    print(f"\n{'='*60}")
    print(f"Training Macro {cp_name} (Day {checkpoint_day}) model")
    print(f"{'='*60}")

    all_data = []
    for sym in symbols:
        data = build_training_data(sym, checkpoint_day)
        if len(data) > 0:
            all_data.append(data)
            print(f"  {sym}: {len(data)} monthly samples")

    if not all_data:
        print("  NO DATA!"); return None, {}

    data = pd.concat(all_data, ignore_index=True)
    print(f"  Total: {len(data)} monthly samples")

    feature_cols = [
        "w1_range_pips", "phi_wt", "days_elapsed", "days_remaining",
        "delta_d", "macro_regime", "exp_ratio", "daily_loops",
        "omega_dl", "dist_so_far_pips", "velocity_pips_per_day", "dow",
    ]

    # Target: MFE (Maximum Favorable Excursion) — the real edge
    X = data[feature_cols].values
    mfe = data['mfe_pips'].values
    mfe = np.maximum(mfe, 0.0)  # Floor at 0 — no negative MFE
    y = np.log1p(mfe)

    tscv = TimeSeriesSplit(n_splits=3)
    cv_scores = []

    for fold, (ti, te) in enumerate(tscv.split(X)):
        m = xgb.XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
        )
        m.fit(X[ti], y[ti], verbose=False)
        pred = np.expm1(m.predict(X[te]))
        act = np.expm1(y[te])
        # Filter out any remaining NaN
        mask = ~(np.isnan(act) | np.isnan(pred))
        if mask.sum() < 5:
            cv_scores.append({"fold": fold + 1, "mae": 0, "r2": 0})
            continue
        mae = mean_absolute_error(act[mask], pred[mask])
        r2 = r2_score(act[mask], pred[mask])
        cv_scores.append({"fold": fold + 1, "mae": round(mae, 2), "r2": round(r2, 4)})
        print(f"  Fold {fold+1}: MAE={mae:.2f}, R2={r2:.4f}")

    final = xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
    )
    final.fit(X, y)

    imp = dict(zip(feature_cols, final.feature_importances_.tolist()))
    print(f"\n  Feature Importance:")
    for f, v in sorted(imp.items(), key=lambda x: x[1], reverse=True):
        print(f"    {f}: {v:.4f}")

    path = MODEL_DIR / f"macro_{cp_name}.joblib"
    joblib.dump(final, path)
    print(f"  Saved: {path.name}")

    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_r2 = np.mean([s["r2"] for s in cv_scores])
    logger.log(cp=cp_name, n=len(data), cv_scores=cv_scores,
               avg_mae=round(avg_mae, 2), avg_r2=round(avg_r2, 4),
               model_path=str(path))
    logger.save(path)

    return final, {"data": data, "scores": cv_scores, "mae": avg_mae, "r2": avg_r2}


def run_macro_cascade(symbols: List[str]):
    """Train all 4 macro checkpoint models and run cascade simulation."""
    models = {}
    for cp_name, cp_day in MACRO_CHECKPOINTS.items():
        model, metrics = train_macro_checkpoint(symbols, cp_day, cp_name)
        models[cp_name] = model

    # Cascade simulation
    print(f"\n{'='*60}")
    print("MACRO CASCADE SIMULATION — 4 Predictions Per Month")
    print(f"{'='*60}")

    for cp_name, cp_day in MACRO_CHECKPOINTS.items():
        if cp_name not in models or models[cp_name] is None:
            continue

        all_data = []
        for sym in symbols:
            data = build_training_data(sym, cp_day)
            if len(data) > 0:
                all_data.append(data)

        if not all_data:
            continue

        data = pd.concat(all_data, ignore_index=True)
        feature_cols = [
            "w1_range_pips", "phi_wt", "days_elapsed", "days_remaining",
            "delta_d", "macro_regime", "exp_ratio", "daily_loops",
            "omega_dl", "dist_so_far_pips", "velocity_pips_per_day", "dow",
        ]

        X = data[feature_cols].values
        y_actual = data['mfe_pips'].values
        y_pred = np.expm1(models[cp_name].predict(X))

        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        bias = y_pred.mean() - y_actual.mean()

        print(f"\n  {cp_name} (Day {cp_day}):")
        print(f"    MAE={mae:.2f}, R2={r2:.4f}, Bias={bias:+.1f}")
        print(f"    Actual MFE: {y_actual.mean():.1f}p, Pred: {y_pred.mean():.1f}p")
        print(f"    Samples: {len(data)}")

        # By symbol
        for sym in sorted(data['symbol'].unique()):
            mask = data['symbol'] == sym
            if mask.sum() < 3: continue
            s_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
            s_r2 = r2_score(y_actual[mask], y_pred[mask])
            print(f"      {sym}: MAE={s_mae:.2f}, R2={s_r2:+.4f} (n={mask.sum()})")

        # By tier
        for tier in ['W-T1', 'W-T2', 'W-T3']:
            mask = data['macro_tier'] == tier
            if mask.sum() < 3: continue
            t_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
            t_r2 = r2_score(y_actual[mask], y_pred[mask])
            print(f"      {tier}: MAE={t_mae:.2f}, R2={t_r2:+.4f} (n={mask.sum()})")

    # Compression trend
    cp_order = ["T0", "T1", "T2", "T3"]
    maes = []
    for cp in cp_order:
        if cp in models and models[cp] is not None:
            all_data = []
            for sym in symbols:
                data = build_training_data(sym, MACRO_CHECKPOINTS[cp])
                if len(data) > 0:
                    all_data.append(data)
            if all_data:
                data = pd.concat(all_data, ignore_index=True)
                feature_cols = [
                    "w1_range_pips", "phi_wt", "days_elapsed", "days_remaining",
                    "delta_d", "macro_regime", "exp_ratio", "daily_loops",
                    "omega_dl", "dist_so_far_pips", "velocity_pips_per_day", "dow",
                ]
                X = data[feature_cols].values
                y_actual = data['mfe_pips'].values
                y_pred = np.expm1(models[cp].predict(X))
                maes.append(mean_absolute_error(y_actual, y_pred))

    if len(maes) >= 2:
        print(f"\n  MAE trend: {' -> '.join(f'{m:.1f}' for m in maes)}")
        shrinking = all(maes[i] >= maes[i+1] for i in range(len(maes)-1))
        print(f"  Variance compression: {'YES' if shrinking else 'NO'}")


def main():
    print("=" * 60)
    print("Macro Monthly DTB — Fractal Cascade Predictor")
    print("=" * 60)
    print(f"Symbols: {TRAIN_SYMBOLS}")
    print(f"Checkpoints: {MACRO_CHECKPOINTS}")
    print(f"Hard Exit: Day {HARD_EXIT_DAY}")
    print(f"\nFormula: N = W1 × Φ_WT × Ψ_MR × Ω_DL × Δ_D")

    run_macro_cascade(TRAIN_SYMBOLS)

    print(f"\n{'='*60}")
    print("MACRO DTB COMPLETE")
    print(f"{'='*60}")
    print(f"\nModels saved to: {MODEL_DIR}")
    print(f"Logs saved to: {LOGS_DIR}")


if __name__ == "__main__":
    main()
