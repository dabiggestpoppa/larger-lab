"""
Macro Monthly DTB v2 — Using Real Daily Data from MT5
=====================================================
Uses actual D1 data (2912 bars = ~11 years) instead of M5-aggregated daily.
This gives us ~130 monthly samples per symbol instead of ~35.

Same morphism: N = W1 × Φ_WT × Ψ_MR × Ω_DL × Δ_D
"""
from __future__ import annotations
import json, time, uuid, warnings
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

warnings.filterwarnings("ignore")

LAB_DIR = Path(__file__).parent
MODEL_DIR = LAB_DIR / "models_macro_v2"
LOGS_DIR = LAB_DIR / "logs"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RAW_DATA_DIR = Path("quant-lab/data")

TRAIN_SYMBOLS = ["EURUSD", "USDCHF", "BTCUSD"]

# Try PRO suffix first, then bare
SYMBOL_FILES = {
    "EURUSD": ["EURUSD_PRO_D1.csv", "EURUSD_M5.csv"],
    "USDCHF": ["USDCHF_PRO_D1.csv", "USDCHF_M5.csv"],
    "BTCUSD": ["BTCUSD_D1.csv", "BTCUSD_M5.csv"],
}

MACRO_CHECKPOINTS = {"T0": 5, "T1": 8, "T2": 11, "T3": 13}
HARD_EXIT_DAY = 15

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
             "timestamp": pd.Timestamp.now().isoformat(),
             "elapsed_s": round(time.time() - self.t0, 1), **self.metrics}
        p = LOGS_DIR / f"run_{self.name}_{self.id}.json"
        p.write_text(json.dumps(m, indent=2, default=str), encoding="utf-8")
        print(f"  Logged: {p.name}")
        return m


def load_daily(symbol: str) -> pd.DataFrame:
    """Load daily data, preferring D1 CSV, falling back to M5 aggregation."""
    files = SYMBOL_FILES.get(symbol, [f"{symbol}_D1.csv", f"{symbol}_M5.csv"])

    for fname in files:
        p = RAW_DATA_DIR / fname
        if not p.exists():
            continue

        df = pd.read_csv(p)
        col_map = {}
        for c in df.columns:
            cl = c.lower().strip()
            if cl in ('date', 'datetime', 'time', 'timestamp'): col_map[c] = 'dt'
            elif cl in ('open', 'high', 'low', 'close'): col_map[c] = cl
            elif cl in ('volume', 'vol', 'tick_volume', 'tickvol'): col_map[c] = 'volume'
        df = df.rename(columns=col_map)

        if 'dt' not in df.columns:
            continue

        df['dt'] = pd.to_datetime(df['dt'], utc=True, errors='coerce')
        df = df.dropna(subset=['dt']).set_index('dt').sort_index()

        # If this is M5 data, aggregate to daily
        if 'M5' in fname:
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

        df['symbol'] = symbol
        return df

    return pd.DataFrame()


def macro_tier(w1_range_pips: float) -> Tuple[str, float]:
    for tier_name, (lo, hi, mult) in MACRO_TIERS.items():
        if lo <= w1_range_pips < hi:
            return tier_name, mult
    return "NO-GO", 0.0


def temporal_decay_days(days_remaining: int) -> float:
    if days_remaining <= 0:
        return 0.0
    return 1.0 / (1.0 + np.exp(-0.3 * (days_remaining - 4)))


def build_macro_features(
    daily: pd.DataFrame,
    symbol: str,
    checkpoint_day: int,
) -> Optional[Dict]:
    """Build features at a macro checkpoint using real daily data."""
    if len(daily) < checkpoint_day:
        return None

    daily = daily.sort_index()

    # Week 1 = first 5 trading days
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

    # Time features
    days_elapsed = checkpoint_day
    days_remaining = HARD_EXIT_DAY - checkpoint_day
    delta_d = temporal_decay_days(days_remaining)

    # Expansion phase: Day 6 to checkpoint
    expansion = daily.iloc[5:checkpoint_day]

    # Macro Regime
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

    # Distribution so far
    dist_data = daily.iloc[:checkpoint_day]
    dist_so_far = float((dist_data['high'].max() - dist_data['low'].min()) * 10000) if len(dist_data) > 0 else 0.0
    if np.isnan(dist_so_far) or np.isinf(dist_so_far):
        dist_so_far = 0.0

    vel_denom = max(checkpoint_day - 5, 1)
    velocity = dist_so_far / vel_denom
    if np.isnan(velocity) or np.isinf(velocity):
        velocity = 0.0

    # Day of week
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
        if not in_impulse and i > 0:
            if closes[i] > closes[i-1] * 1.001:
                in_impulse = True
                impulse_high = highs[i]
                impulse_low = lows[i]
            elif closes[i] < closes[i-1] * 0.999:
                in_impulse = True
                impulse_high = highs[i]
                impulse_low = lows[i]
        elif in_impulse:
            impulse_high = max(impulse_high, highs[i])
            impulse_low = min(impulse_low, lows[i])
            impulse_range = impulse_high - impulse_low
            if impulse_range > 0:
                retrace = (impulse_high - closes[i]) / impulse_range
                if 0.32 <= retrace <= 0.50:
                    loops += 1
                    in_impulse = False
    return loops


def build_training_data(symbol: str, checkpoint_day: int) -> pd.DataFrame:
    """Build labeled training data using real daily data."""
    daily = load_daily(symbol)
    if len(daily) < 15:
        return pd.DataFrame()

    daily = daily.sort_index()
    daily['year_month'] = daily.index.to_period('M')

    records = []
    for ym, month_data in daily.groupby('year_month'):
        if len(month_data) < 15:
            continue

        month_data = month_data.sort_index()

        w1 = month_data.iloc[:5]
        w1_high = w1['high'].max()
        w1_low = w1['low'].min()
        w1_range = w1_high - w1_low
        w1_range_pips = w1_range * 10000

        tier_name, phi_wt = macro_tier(w1_range_pips)
        if tier_name == "NO-GO":
            continue

        features = build_macro_features(month_data, symbol, checkpoint_day)
        if features is None:
            continue

        # Label: MFE from Day 5 band edge to Day 15 extreme
        checkpoint_idx = min(checkpoint_day - 1, len(month_data) - 1)
        day15_idx = min(14, len(month_data) - 1)

        remaining_data = month_data.iloc[checkpoint_idx:day15_idx + 1]
        if len(remaining_data) < 1:
            continue

        remaining_high = remaining_data['high'].max()
        remaining_low = remaining_data['low'].min()

        if pd.isna(remaining_high) or pd.isna(remaining_low):
            continue

        # MFE from breakout direction
        day6_close = month_data.iloc[5]['close'] if len(month_data) > 5 else (w1_high + w1_low) / 2
        if pd.isna(day6_close):
            continue

        if day6_close > w1_high:  # LONG
            mfe = float((remaining_high - w1_high) * 10000)
        elif day6_close < w1_low:  # SHORT
            mfe = float((w1_low - remaining_low) * 10000)
        else:
            mfe = float((remaining_high - remaining_low) * 10000)

        if np.isnan(mfe) or np.isinf(mfe) or mfe < 0:
            continue

        features['mfe_pips'] = round(mfe, 2)
        features['remaining_pips'] = round(float((remaining_high - remaining_low) * 10000), 2)
        features['breakout_direction'] = 1 if day6_close > w1_high else (-1 if day6_close < w1_low else 0)

        records.append(features)

    df = pd.DataFrame(records)
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
    logger = RunLogger(f"macro_v2_{cp_name}")
    print(f"\n{'='*60}")
    print(f"Training Macro v2 {cp_name} (Day {checkpoint_day}) model")
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

    X = data[feature_cols].values
    mfe = data['mfe_pips'].values
    mfe = np.maximum(mfe, 0.0)
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

    path = MODEL_DIR / f"macro_v2_{cp_name}.joblib"
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
    print("MACRO v2 CASCADE SIMULATION — 4 Predictions Per Month")
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

        # Filter NaN
        mask = ~(np.isnan(y_actual) | np.isnan(y_pred))
        y_actual = y_actual[mask]
        y_pred = y_pred[mask]

        if len(y_actual) == 0:
            continue

        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        bias = y_pred.mean() - y_actual.mean()

        print(f"\n  {cp_name} (Day {cp_day}):")
        print(f"    MAE={mae:.2f}, R2={r2:.4f}, Bias={bias:+.1f}")
        print(f"    Actual MFE: {y_actual.mean():.1f}p, Pred: {y_pred.mean():.1f}p")
        print(f"    Samples: {len(y_actual)}")

        # By symbol
        for sym in sorted(data["symbol"].unique()):
            sym_mask = mask & (data["symbol"] == sym)
            if sym_mask.sum() < 3: continue
            s_mae = mean_absolute_error(y_actual[sym_mask], y_pred[sym_mask])
            s_r2 = r2_score(y_actual[sym_mask], y_pred[sym_mask])
            print(f"      {sym}: MAE={s_mae:.2f}, R2={s_r2:+.4f} (n={sym_mask.sum()})")

        # By tier
        for tier in ['W-T1', 'W-T2', 'W-T3']:
            tier_mask = mask & (data['macro_tier'] == tier)
            if tier_mask.sum() < 3: continue
            t_mae = mean_absolute_error(y_actual[tier_mask], y_pred[tier_mask])
            t_r2 = r2_score(y_actual[tier_mask], y_pred[tier_mask])
            print(f"      {tier}: MAE={t_mae:.2f}, R2={t_r2:+.4f} (n={tier_mask.sum()})")

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
                mask = ~(np.isnan(y_actual) | np.isnan(y_pred))
                if mask.sum() > 0:
                    maes.append(mean_absolute_error(y_actual[mask], y_pred[mask]))

    if len(maes) >= 2:
        print(f"\n  MAE trend: {' -> '.join(f'{m:.1f}' for m in maes)}")
        shrinking = all(maes[i] >= maes[i+1] for i in range(len(maes)-1))
        print(f"  Variance compression: {'YES' if shrinking else 'NO'}")


def main():
    print("=" * 60)
    print("Macro Monthly DTB v2 — Real Daily Data")
    print("=" * 60)
    print(f"Symbols: {TRAIN_SYMBOLS}")
    print(f"Checkpoints: {MACRO_CHECKPOINTS}")
    print(f"Hard Exit: Day {HARD_EXIT_DAY}")
    print(f"\nFormula: N = W1 × Φ_WT × Ψ_MR × Ω_DL × Δ_D")

    run_macro_cascade(TRAIN_SYMBOLS)

    print(f"\n{'='*60}")
    print("MACRO DTB v2 COMPLETE")
    print(f"{'='*60}")
    print(f"\nModels saved to: {MODEL_DIR}")
    print(f"Logs saved to: {LOGS_DIR}")


if __name__ == "__main__":
    main()
