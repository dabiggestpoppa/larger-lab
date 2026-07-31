"""
DTB v4 — London Distribution Predictor
========================================
Trains on EURUSD, USDCHF, BTCUSD only.
Predicts remaining London session distribution at 3 checkpoints:
  T0 (3AM EST) → Base prediction (Asian Range + Tier)
  T1 (6AM EST) → Cascade update (loop velocity check)
  T2 (9AM EST) → Final prediction (regime locked)

Formula: N = aR × Φ_T × Ψ_R × Ω_L × Δ_t
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
MODEL_DIR = LAB_DIR / "models_v4"
LOGS_DIR = LAB_DIR / "logs"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RAW_DATA_DIR = Path("quant-lab/data")

# ONLY these 3 pairs
TRAIN_SYMBOLS = ["EURUSD", "USDCHF", "BTCUSD"]

# Checkpoints (UTC hours)
CHECKPOINTS = {"T0": 8, "T1": 11, "T2": 14}  # 3AM, 6AM, 9AM EST
SINK_UTC = 17  # 12PM EST


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


def load_m5(symbol):
    p = RAW_DATA_DIR / f"{symbol}_M5.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    cm = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ("date","datetime","time","timestamp"): cm[c] = "dt"
        elif cl in ("open","high","low","close"): cm[c] = cl
        elif cl in ("volume","vol","tickvol"): cm[c] = "volume"
    df = df.rename(columns=cm)
    df["dt"] = pd.to_datetime(df["dt"], utc=True, errors="coerce")
    df = df.dropna(subset=["dt"]).set_index("dt").sort_index()
    if "volume" not in df.columns: df["volume"] = 0
    return df


def tier(ar_pct, symbol=""):
    """
    Tier classification using percentage-based thresholds.
    ar_pct = ar / mid_price * 100 (percentage move)
    T1: < 0.15% (tight Asian Range)
    T2: 0.15-0.35% (normal)
    T3: 0.35-0.70% (wide)
    T4: > 0.70% (extreme, skip)
    """
    if ar_pct < 0.15: return "T1", ar_pct * 50, 52
    if ar_pct < 0.35: return "T2", ar_pct * 50, 68
    if ar_pct < 0.70: return "T3", ar_pct * 50, 94
    return "T4", 0.0, 999


def dt_decay(mins):
    if mins <= 0: return 0.0
    return 1.0 / (1.0 + np.exp(-0.015 * (mins - 120)))


def count_loops(h, l, c, ah, al):
    if len(h) == 0 or ah <= 0: return 0
    above = h > ah
    if not above.any():
        below = l < al
        if not below.any(): return 0
        starts = np.where(below & ~np.roll(below, 1))[0]
        starts = starts[starts > 0]
        if not starts.size: return 0
        cnt = 0
        for s in starts:
            rm = np.minimum.accumulate(l[s:])
            ir = ah - rm; v = ir > 0
            if not v.any(): continue
            r = (c[s:][v] - rm[v]) / ir[v]
            if np.any((r >= 0.32) & (r <= 0.50)): cnt += 1
        return cnt
    starts = np.where(above & ~np.roll(above, 1))[0]
    starts = starts[starts > 0]
    if not starts.size: return 0
    cnt = 0
    for s in starts:
        rm = np.maximum.accumulate(h[s:])
        ir = rm - ah; v = ir > 0
        if not v.any(): continue
        r = (rm[v] - c[s:][v]) / ir[v]
        if np.any((r >= 0.32) & (r <= 0.50)): cnt += 1
    return cnt


def build_features_for_checkpoint(df, symbol, cp_hour_utc):
    """Build features at a specific checkpoint to predict remaining distribution."""
    records = []
    df = df.copy()
    df["est_hour"] = (df.index.hour - 5) % 24
    df["is_asian"] = (df["est_hour"] >= 19) | (df["est_hour"] < 3)
    df["trade_date"] = df.index.date

    for date, day_bars in df.groupby("trade_date"):
        if len(day_bars) < 20: continue
        ab = day_bars[day_bars["is_asian"]]
        if len(ab) < 2: continue

        ah = ab["high"].max(); al = ab["low"].min()
        ar = ah - al
        mid_price = (ah + al) / 2
        ar_pct = (ar / mid_price) * 100 if mid_price > 0 else 0
        t, au, ld = tier(ar_pct, symbol)
        if t == "T4": continue

        # Bars BEFORE checkpoint (no lookahead)
        pre = day_bars[day_bars.index.hour < cp_hour_utc]
        if len(pre) < 5: continue

        # Remaining distribution: checkpoint to sink
        cp_bars = day_bars[(day_bars.index.hour >= cp_hour_utc) & (day_bars.index.hour < SINK_UTC)]
        remaining = (cp_bars["high"].max() - cp_bars["low"].min()) * 10000 if len(cp_bars) > 0 else 0.0

        # Time
        mins_remaining = (SINK_UTC - cp_hour_utc) * 60
        mins_elapsed = max((cp_hour_utc - 8) * 60, 1)
        delta_t = dt_decay(mins_remaining)

        # Regime (from pre-checkpoint bars only)
        am = pre[(pre.index.hour >= 14) & (pre.index.hour < 15)]
        amr = (am["high"].max() - am["low"].min()) if len(am) > 0 else 0.0
        rr = amr / ar if ar > 0 else 0.0
        reg = 2 if rr >= 1.5 else (1 if rr >= 1.0 else 0)

        # Loops
        la = count_loops(pre["high"].values, pre["low"].values, pre["close"].values, ah, al)
        lt = max(0.0, mins_remaining / ld) if ld < 999 else 0.0
        ol = la / lt if lt > 0 else 0.0

        # Distribution so far
        dsf = (pre["high"].max() - pre["low"].min()) * 10000
        vel = dsf / mins_elapsed

        # Metadata
        fb = day_bars.index[0]
        dow = fb.weekday()
        iw = dow == 2 and (fb.hour - 5) % 24 >= 12

        # Entropy
        ent = 0
        if ol < 0.5 and lt > 1: ent = 1
        elif ar_pct > 0.5 and reg == 2: ent = 2
        elif la > lt * 1.44: ent = 3

        records.append({
            "symbol": symbol, "date": str(date), "checkpoint": cp_hour_utc,
            "ar_pct": round(ar_pct, 4), "au": round(au, 4),
            "regime": reg, "regime_ratio": round(rr, 3),
            "mins_remaining": mins_remaining, "mins_elapsed": mins_elapsed,
            "L_theoretical": round(lt, 2), "L_actual": la, "Omega_L": round(ol, 3),
            "delta_t": round(delta_t, 4), "dist_so_far": round(dsf, 2),
            "velocity": round(vel, 4), "is_wed_pm": int(iw), "dow": dow,
            "entropy": ent, "remaining_pips": round(remaining, 2),
        })
    return pd.DataFrame(records)


def train_checkpoint_model(symbols, cp_hour_utc, cp_name):
    """Train XGBoost for a specific checkpoint."""
    logger = RunLogger(f"v4_{cp_name}")
    print(f"\n{'='*60}")
    print(f"Training {cp_name} ({cp_hour_utc}UTC) model")
    print(f"{'='*60}")

    all_data = []
    for sym in symbols:
        df = load_m5(sym)
        if len(df) < 1000: continue
        feats = build_features_for_checkpoint(df, sym, cp_hour_utc)
        if len(feats) > 0:
            all_data.append(feats)
            print(f"  {sym}: {len(feats)} samples")

    if not all_data:
        print("  NO DATA!"); return None, {}

    data = pd.concat(all_data, ignore_index=True)
    print(f"  Total: {len(data)} samples")

    feature_cols = [
        "ar_pct", "au", "regime", "regime_ratio",
        "mins_remaining", "mins_elapsed", "L_theoretical", "L_actual",
        "Omega_L", "delta_t", "dist_so_far", "velocity",
        "is_wed_pm", "dow", "entropy",
    ]

    X = data[feature_cols].values
    y = np.log1p(data["remaining_pips"].values)

    # TimeSeriesSplit CV
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []

    for fold, (ti, te) in enumerate(tscv.split(X)):
        m = xgb.XGBRegressor(
            n_estimators=200, max_depth=6, lr=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
        )
        m.fit(X[ti], y[ti], verbose=False)
        pred = np.expm1(m.predict(X[te]))
        act = np.expm1(y[te])
        mae = mean_absolute_error(act, pred)
        r2 = r2_score(act, pred)
        cv_scores.append({"fold": fold+1, "mae": round(mae, 2), "r2": round(r2, 4)})
        print(f"  Fold {fold+1}: MAE={mae:.2f}, R2={r2:.4f}")

    # Final model
    final = xgb.XGBRegressor(
        n_estimators=300, max_depth=6, lr=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42, n_jobs=-1,
    )
    final.fit(X, y)

    imp = dict(zip(feature_cols, final.feature_importances_.tolist()))
    print(f"\n  Feature Importance:")
    for f, v in sorted(imp.items(), key=lambda x: x[1], reverse=True):
        print(f"    {f}: {v:.4f}")

    path = MODEL_DIR / f"v4_{cp_name}.joblib"
    joblib.dump(final, path)
    print(f"  Saved: {path.name}")

    avg_mae = np.mean([s["mae"] for s in cv_scores])
    avg_r2 = np.mean([s["r2"] for s in cv_scores])
    logger.log(cp=cp_name, n=len(data), cv_scores=cv_scores,
               avg_mae=round(avg_mae, 2), avg_r2=round(avg_r2, 4),
               features=feature_cols, model_path=str(path))
    logger.save(path)

    return final, {"data": data, "scores": cv_scores, "mae": avg_mae, "r2": avg_r2}


def run_cascade_simulation(models, symbols):
    """Simulate T0→T1→T2 cascade on test data."""
    print(f"\n{'='*60}")
    print("CASCADE SIMULATION — 3 Predictions Per Day")
    print(f"{'='*60}")

    results = {}
    for cp_name, cp_hour in CHECKPOINTS.items():
        if cp_name not in models or models[cp_name] is None:
            continue

        all_data = []
        for sym in symbols:
            df = load_m5(sym)
            if len(df) < 1000: continue
            feats = build_features_for_checkpoint(df, sym, cp_hour)
            if len(feats) > 0:
                all_data.append(feats)

        if not all_data: continue
        data = pd.concat(all_data, ignore_index=True)

        feature_cols = [
            "ar_pct", "au", "regime", "regime_ratio",
            "mins_remaining", "mins_elapsed", "L_theoretical", "L_actual",
            "Omega_L", "delta_t", "dist_so_far", "velocity",
            "is_wed_pm", "dow", "entropy",
        ]

        X = data[feature_cols].values
        y_actual = data["remaining_pips"].values
        y_pred = np.expm1(models[cp_name].predict(X))

        mae = mean_absolute_error(y_actual, y_pred)
        r2 = r2_score(y_actual, y_pred)
        bias = y_pred.mean() - y_actual.mean()

        results[cp_name] = {
            "mae": round(mae, 2), "r2": round(r2, 4),
            "actual_mean": round(y_actual.mean(), 1),
            "pred_mean": round(y_pred.mean(), 1),
            "bias": round(bias, 1), "n": len(data),
        }

        print(f"\n  {cp_name} ({cp_hour}UTC):")
        print(f"    MAE={mae:.2f}, R2={r2:.4f}")
        print(f"    Actual={y_actual.mean():.1f}, Pred={y_pred.mean():.1f}, Bias={bias:+.1f}")
        print(f"    Samples: {len(data)}")

        # Hit rates
        for tol in [3, 5, 8, 10, 15]:
            w = np.abs(y_actual - y_pred) <= tol
            print(f"    +/-{tol:2d} pips: {w.mean():.1%}")

        # By symbol
        for sym in sorted(data["symbol"].unique()):
            mask = data["symbol"] == sym
            if mask.sum() < 20: continue
            s_mae = mean_absolute_error(y_actual[mask], y_pred[mask])
            s_r2 = r2_score(y_actual[mask], y_pred[mask])
            print(f"    {sym}: MAE={s_mae:.2f}, R2={s_r2:+.4f} (n={mask.sum()})")

    # Cascade trend
    if len(results) >= 2:
        cp_order = ["T0", "T1", "T2"]
        maes = [results.get(cp, {}).get("mae") for cp in cp_order]
        maes = [m for m in maes if m is not None]
        r2s = [results.get(cp, {}).get("r2") for cp in cp_order]
        r2s = [r for r in r2s if r is not None]
        if len(maes) >= 2:
            shrinking = all(maes[i] >= maes[i+1] for i in range(len(maes)-1))
            print(f"\n  MAE trend: {' -> '.join(f'{m:.1f}' for m in maes)}")
            print(f"  R2 trend:  {' -> '.join(f'{r:.3f}' for r in r2s)}")
            print(f"  Variance compression: {'YES' if shrinking else 'NO'}")

    return results


def main():
    print("=" * 60)
    print("DTB v4 — London Distribution Predictor")
    print("=" * 60)
    print(f"Symbols: {TRAIN_SYMBOLS}")
    print(f"Checkpoints: {CHECKPOINTS}")

    # Train 3 models (one per checkpoint)
    models = {}
    for cp_name, cp_hour in CHECKPOINTS.items():
        model, metrics = train_checkpoint_model(TRAIN_SYMBOLS, cp_hour, cp_name)
        models[cp_name] = model

    # Run cascade simulation
    cascade_results = run_cascade_simulation(models, TRAIN_SYMBOLS)

    # Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"\n  3 predictions per day (London session):")
    for cp in ["T0", "T1", "T2"]:
        r = cascade_results.get(cp, {})
        if r:
            print(f"    {cp}: MAE={r['mae']:.2f} pips, R2={r['r2']:.4f}, "
                  f"Bias={r['bias']:+.1f}, n={r['n']}")

    print(f"\n  Models saved to: {MODEL_DIR}")
    print(f"  Logs saved to: {LOGS_DIR}")


if __name__ == "__main__":
    main()
