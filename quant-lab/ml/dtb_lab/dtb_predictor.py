"""
DTB v4 Cascade Predictor — Integration Module
================================================
Provides London Distribution predictions to the Trade Orchestrator.

3 predictions per day:
  T0 (3AM EST) → Base prediction (Asian Range + Tier)
  T1 (6AM EST) → Cascade update (loop velocity check)
  T2 (9AM EST) → Final prediction (regime locked)

Formula: N = aR × Φ_T × Ψ_R × Ω_L × Δ_t

Usage:
    from dtb_lab.dtb_predictor import DTBPredictor
    predictor = DTBPredictor()
    prediction = predictor.predict_remaining(session_bars, symbol)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

MODEL_DIR = Path(__file__).parent / "models_v4"


@dataclass
class DTBPrediction:
    """A single DTB prediction at a checkpoint."""
    checkpoint: str          # "T0", "T1", "T2"
    remaining_pips: float    # Predicted remaining distribution (pips)
    confidence: float        # 0-1 confidence based on time remaining
    regime: str              # "CONFIRMED", "CAUTION", "FAILED"
    ar_pct: float            # Asian Range as percentage
    tier: str                # "T1", "T2", "T3"
    omega_l: float           # Loop Realization Ratio
    l_actual: int            # Loops completed
    l_theoretical: float     # Max loops possible
    delta_t: float           # Temporal decay factor


@dataclass
class DTBCascadeResult:
    """Full cascade result — 3 predictions for one day."""
    symbol: str
    date: str
    t0: Optional[DTBPrediction] = None
    t1: Optional[DTBPrediction] = None
    t2: Optional[DTBPrediction] = None

    @property
    def best_prediction(self) -> Optional[DTBPrediction]:
        """Return the most confident (latest) prediction."""
        if self.t2: return self.t2
        if self.t1: return self.t1
        return self.t0

    @property
    def variance_compression(self) -> Optional[float]:
        """Ratio of T2 MAE to T0 MAE (lower = better compression)."""
        if self.t0 and self.t2 and self.t0.remaining_pips > 0:
            return self.t2.remaining_pips / self.t0.remaining_pips
        return None


class DTBPredictor:
    """
    DTB v4 Cascade Predictor.
    Loads 3 XGBoost models (T0, T1, T2) and provides
    London Distribution predictions to the trade orchestrator.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or MODEL_DIR
        self.models = {}
        self._load_models()

    def _load_models(self):
        """Load the 3 checkpoint models."""
        for cp in ["T0", "T1", "T2"]:
            path = self.model_dir / f"v4_{cp}.joblib"
            if path.exists():
                self.models[cp] = joblib.load(path)
                print(f"  DTB {cp} model loaded: {path.name}")
            else:
                print(f"  WARNING: DTB {cp} model not found at {path}")

    def predict_remaining(
        self,
        bars: pd.DataFrame,
        symbol: str,
        checkpoint: str = "T2",
    ) -> Optional[DTBPrediction]:
        """
        Predict remaining London distribution at a checkpoint.

        Args:
            bars: M5 OHLCV DataFrame with DatetimeIndex (UTC)
            symbol: Symbol string (e.g., "EURUSD")
            checkpoint: "T0" (3AM), "T1" (6AM), or "T2" (9AM)

        Returns:
            DTBPrediction or None if insufficient data
        """
        if checkpoint not in self.models:
            return None

        model = self.models[checkpoint]
        features = self._build_features(bars, symbol, checkpoint)
        if features is None:
            return None

        # Predict (model outputs log-transformed)
        X = np.array([list(features.values())])
        pred_log = model.predict(X)[0]
        remaining = np.expm1(pred_log)

        return DTBPrediction(
            checkpoint=checkpoint,
            remaining_pips=max(0, remaining),
            confidence=self._confidence(checkpoint, features),
            regime=features.get("regime", "UNKNOWN"),
            ar_pct=features.get("ar_pct", 0),
            tier=features.get("tier", "T1"),
            omega_l=features.get("omega_l", 0),
            l_actual=features.get("l_actual", 0),
            l_theoretical=features.get("l_theoretical", 0),
            delta_t=features.get("delta_t", 0),
        )

    def predict_cascade(
        self,
        bars: pd.DataFrame,
        symbol: str,
    ) -> DTBCascadeResult:
        """
        Run full T0→T1→T2 cascade prediction.

        Returns:
            DTBCascadeResult with up to 3 predictions
        """
        result = DTBCascadeResult(
            symbol=symbol,
            date=str(bars.index[0].date()) if len(bars) > 0 else "",
        )

        for cp in ["T0", "T1", "T2"]:
            pred = self.predict_remaining(bars, symbol, cp)
            if pred:
                setattr(result, cp.lower(), pred)

        return result

    def _build_features(
        self,
        bars: pd.DataFrame,
        symbol: str,
        checkpoint: str,
    ) -> Optional[Dict]:
        """Build feature vector for a specific checkpoint."""
        if len(bars) < 20:
            return None

        # Determine checkpoint hour in UTC
        cp_hours = {"T0": 8, "T1": 11, "T2": 14}
        cp_hour_utc = cp_hours[checkpoint]
        sink_utc = 17

        # Asian Range (19:00-03:00 EST = 00:00-08:00 UTC)
        bars = bars.copy()
        bars["est_hour"] = (bars.index.hour - 5) % 24
        bars["is_asian"] = (bars["est_hour"] >= 19) | (bars["est_hour"] < 3)

        asian_bars = bars[bars["is_asian"]]
        if len(asian_bars) < 2:
            return None

        ah = asian_bars["high"].max()
        al = asian_bars["low"].min()
        ar = ah - al
        mid = (ah + al) / 2
        ar_pct = (ar / mid) * 100 if mid > 0 else 0

        # Tier
        if ar_pct < 0.15:
            t, au, ld = "T1", ar_pct * 50, 52
        elif ar_pct < 0.35:
            t, au, ld = "T2", ar_pct * 50, 68
        elif ar_pct < 0.70:
            t, au, ld = "T3", ar_pct * 50, 94
        else:
            return None  # T4 — skip

        # Pre-checkpoint bars
        pre = bars[bars.index.hour < cp_hour_utc]
        if len(pre) < 5:
            return None

        # Time features
        mins_remaining = (sink_utc - cp_hour_utc) * 60
        mins_elapsed = max((cp_hour_utc - 8) * 60, 1)
        delta_t = self._temporal_decay(mins_remaining)

        # Regime (from pre-checkpoint bars)
        am = pre[(pre.index.hour >= 14) & (pre.index.hour < 15)]
        amr = (am["high"].max() - am["low"].min()) if len(am) > 0 else 0.0
        rr = amr / ar if ar > 0 else 0.0
        reg = 2 if rr >= 1.5 else (1 if rr >= 1.0 else 0)

        # Loops
        h = pre["high"].values
        l = pre["low"].values
        c = pre["close"].values
        la = self._count_loops(h, l, c, ah, al)
        lt = max(0.0, mins_remaining / ld) if ld < 999 else 0.0
        ol = la / lt if lt > 0 else 0.0

        # Distribution so far
        dsf = (pre["high"].max() - pre["low"].min()) * 10000
        vel = dsf / mins_elapsed

        # Metadata
        fb = bars.index[0]
        dow = fb.weekday()
        iw = dow == 2 and (fb.hour - 5) % 24 >= 12

        # Entropy
        ent = 0
        if ol < 0.5 and lt > 1: ent = 1
        elif ar_pct > 0.5 and reg == 2: ent = 2
        elif la > lt * 1.44: ent = 3

        return {
            "ar_pct": round(ar_pct, 4),
            "au": round(au, 4),
            "regime": reg,
            "regime_ratio": round(rr, 3),
            "mins_remaining": mins_remaining,
            "mins_elapsed": mins_elapsed,
            "L_theoretical": round(lt, 2),
            "L_actual": la,
            "Omega_L": round(ol, 3),
            "delta_t": round(delta_t, 4),
            "dist_so_far": round(dsf, 2),
            "velocity": round(vel, 4),
            "is_wed_pm": int(iw),
            "dow": dow,
            "entropy": ent,
            "tier": t,
            "l_actual": la,
            "l_theoretical": round(lt, 2),
            "omega_l": round(ol, 3),
        }

    @staticmethod
    def _temporal_decay(mins):
        if mins <= 0: return 0.0
        return 1.0 / (1.0 + np.exp(-0.015 * (mins - 120)))

    @staticmethod
    def _count_loops(h, l, c, ah, al):
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

    @staticmethod
    def _confidence(checkpoint: str, features: Dict) -> float:
        """Estimate prediction confidence based on checkpoint and features."""
        # Later checkpoints = more data = higher confidence
        cp_conf = {"T0": 0.5, "T1": 0.8, "T2": 0.95}
        base = cp_conf.get(checkpoint, 0.5)

        # Adjust by regime
        regime = features.get("regime", 0)
        if regime == 2:  # CONFIRMED
            base *= 1.1
        elif regime == 0:  # FAILED
            base *= 0.7

        # Adjust by delta_t (temporal decay)
        dt = features.get("delta_t", 0.5)
        base *= (0.5 + 0.5 * dt)

        return min(1.0, max(0.0, base))


def get_dtb_predictor() -> DTBPredictor:
    """Singleton accessor for the DTB predictor."""
    if not hasattr(get_dtb_predictor, "_instance"):
        get_dtb_predictor._instance = DTBPredictor()
    return get_dtb_predictor._instance
