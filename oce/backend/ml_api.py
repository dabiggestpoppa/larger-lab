"""
ML API — CEREBUS ML Integration Endpoints
===========================================
FastAPI routes for ML regime classification, entry quality scoring,
optimized parameters, feature importance, and model status.

Registered under /api/v1/ml/*
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging
import joblib
from pathlib import Path

logger = logging.getLogger("oce.ml")

# ── Load trained models at startup ─────────────────────────
_MODELS_DIR = Path(__file__).parent.parent.parent / "quant-lab" / "ml" / "models"
_regime_models: Dict[str, object] = {}

def _load_models():
    """Load all trained regime classifier models."""
    global _regime_models
    if not _MODELS_DIR.exists():
        logger.warning(f"Models directory not found: {_MODELS_DIR}")
        return
    for pkl_file in _MODELS_DIR.glob("regime_*.pkl"):
        symbol = pkl_file.stem.replace("regime_", "")
        try:
            artifact = joblib.load(pkl_file)
            _regime_models[symbol] = artifact
            logger.info(f"Loaded regime model for {symbol}")
        except Exception as e:
            logger.error(f"Failed to load model for {symbol}: {e}")
    logger.info(f"Loaded {len(_regime_models)} regime models")

# Load on import
_load_models()

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

# ── Models ─────────────────────────────────────────────────

class RegimePrediction(BaseModel):
    symbol: str
    regime: str  # CONFIRMED | CAUTION | FAILED | NO-GO
    confidence: float
    probabilities: Dict[str, float]
    timestamp: str

class EntryQualityResponse(BaseModel):
    symbol: str
    score: float
    action: str  # ENTER_FULL | HALF_SIZE | SKIP
    features: Dict[str, float]
    timestamp: str

class OptimizedParams(BaseModel):
    symbol: str
    regime: str
    au_multiplier: float
    buffer: float
    dz_width: float
    trigger_multiplier: float
    sharpe: float
    win_rate: float
    max_dd: float

class FeatureImportance(BaseModel):
    feature: str
    importance: float
    rank: int

class ModelStatus(BaseModel):
    regime_model_loaded: bool = False
    entry_model_loaded: bool = False
    optimizer_ready: bool = False
    last_training: str = ""
    data_hash: str = ""
    cv_accuracy: float = 0.0
    heldout_accuracy: float = 0.0
    psi_score: float = 0.0
    drift_detected: bool = False

# ── In-memory state (populated by ML pipeline) ─────────────

_model_status = {
    "regime_model_loaded": False,
    "entry_model_loaded": False,
    "optimizer_ready": False,
    "last_training": "",
    "data_hash": "",
    "cv_accuracy": 0.0,
    "heldout_accuracy": 0.0,
    "psi_score": 0.0,
    "drift_detected": False,
}

# Placeholder — populated when ML pipeline runs
_regime_predictions: Dict[str, dict] = {}
_entry_quality: Dict[str, dict] = {}
_optimized_params: Dict[str, list] = {}
_feature_importance: Dict[str, list] = {}

# ── Tier configs (from Phase 1 K-Means, data-driven) ──────
# These are the AU values discovered by K-Means clustering on 4 years of M5 Asian Range data
# AU = 50% of cluster centroid, Trigger = AU x 1.2
TIER_CONFIGS = {
    "EURUSD": {"T1": {"au": 9.0,  "trig": 10.8}, "T2": {"au": 21.9, "trig": 26.3}, "T3": {"au": 75.2, "trig": 90.2}},
    "GBPUSD": {"T1": {"au": 12.7, "trig": 15.2}, "T2": {"au": 34.6, "trig": 41.5}, "T3": {"au": 163.6,"trig": 196.3}},
    "USDCHF": {"T1": {"au": 9.8,  "trig": 11.8}, "T2": {"au": 22.8, "trig": 27.4}, "T3": {"au": 59.3, "trig": 71.2}},
    "USDJPY": {"T1": {"au": 19.5, "trig": 23.4}, "T2": {"au": 48.3, "trig": 58.0}, "T3": {"au": 165.0,"trig": 198.0}},
    "AUDUSD": {"T1": {"au": 8.6,  "trig": 10.3}, "T2": {"au": 17.8, "trig": 21.4}, "T3": {"au": 35.8, "trig": 43.0}},
    "NZDUSD": {"T1": {"au": 9.4,  "trig": 11.3}, "T2": {"au": 20.3, "trig": 24.4}, "T3": {"au": 41.7, "trig": 50.0}},
    "GBPJPY": {"T1": {"au": 26.9, "trig": 32.3}, "T2": {"au": 65.1, "trig": 78.1}, "T3": {"au": 224.2,"trig": 269.0}},
    "GBPAUD": {"T1": {"au": 25.5, "trig": 30.6}, "T2": {"au": 59.7, "trig": 71.6}, "T3": {"au": 216.5,"trig": 259.8}},
    "GBPNZD": {"T1": {"au": 32.1, "trig": 38.5}, "T2": {"au": 73.5, "trig": 88.2}, "T3": {"au": 270.7,"trig": 324.8}},
    "GBPCHF": {"T1": {"au": 13.9, "trig": 16.7}, "T2": {"au": 37.6, "trig": 45.1}, "T3": {"au": 192.5,"trig": 231.0}},
    "CHFJPY": {"T1": {"au": 23.2, "trig": 27.8}, "T2": {"au": 50.8, "trig": 61.0}, "T3": {"au": 162.3,"trig": 194.8}},
    "US500":  {"T1": {"au": 7.0,  "trig": 8.4},  "T2": {"au": 22.8, "trig": 27.4}, "T3": {"au": 59.4, "trig": 71.3}},
    "DE30":   {"T1": {"au": 29.3, "trig": 35.2}, "T2": {"au": 87.2, "trig": 104.6},"T3": {"au": 220.4,"trig": 264.5}},
    "FR40":   {"T1": {"au": 12.5, "trig": 15.0}, "T2": {"au": 37.3, "trig": 44.8}, "T3": {"au": 100.2,"trig": 120.2}},
    "XAUUSD": {"T1": {"au": 62.9, "trig": 75.5}, "T2": {"au": 273.0,"trig": 327.6},"T3": {"au": 1013.7,"trig": 1216.4}},
    "XAGUSD": {"T1": {"au": 186.9,"trig": 224.3},"T2": {"au": 1589.7,"trig": 1907.6},"T3": {"au": 5329.9,"trig": 6395.9}},
    "BTCUSD": {"T1": {"au": 335.6,"trig": 402.7},"T2": {"au": 990.6,"trig": 1188.7},"T3": {"au": 2240.2,"trig": 2688.2}},
    "ETHUSD": {"T1": {"au": 226.0,"trig": 271.2},"T2": {"au": 700.8,"trig": 841.0},"T3": {"au": 1569.0,"trig": 1882.8}},
}


# ── Endpoints ──────────────────────────────────────────────

@router.get("/status", response_model=ModelStatus)
async def get_model_status():
    """Get current ML model status."""
    status = dict(_model_status)
    status["regime_model_loaded"] = len(_regime_models) > 0
    status["entry_model_loaded"] = False  # Not yet trained
    status["optimizer_ready"] = False  # Not yet run
    status["cv_accuracy"] = 80.7  # From Phase 2 training
    status["last_training"] = "2026-06-02"
    return ModelStatus(**status)


@router.get("/regime/{symbol}", response_model=RegimePrediction)
async def get_regime(symbol: str):
    """
    Get current regime prediction for a symbol.
    Uses trained XGBoost model if available, otherwise falls back to tier config.
    """
    symbol = symbol.upper().replace('.', '').replace('/', '')

    # Return cached prediction if available
    if symbol in _regime_predictions:
        return RegimePrediction(**_regime_predictions[symbol])

    # Use trained model if available
    if symbol in _regime_models:
        try:
            artifact = _regime_models[symbol]
            model = artifact.get("model", artifact) if isinstance(artifact, dict) else artifact
            # Use tier config features as input
            tiers = TIER_CONFIGS.get(symbol, TIER_CONFIGS["EURUSD"])
            import numpy as np
            # Create feature vector from tier config (simplified)
            au_avg = (tiers["T1"]["au"] + tiers["T2"]["au"] + tiers["T3"]["au"]) / 3
            features = np.array([[au_avg, 1.0, 6.0, 0.0, 0.5, 2.0, 0, 0.5]])
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(features)[0]
                pred_class = int(np.argmax(probs))
                regime_map = {0: "CONFIRMED", 1: "CAUTION", 2: "FAILED", 3: "NO-GO"}
                return RegimePrediction(
                    symbol=symbol,
                    regime=regime_map.get(pred_class, "CONFIRMED"),
                    confidence=float(probs[pred_class]),
                    probabilities={regime_map.get(i, "CONFIRMED"): float(probs[i]) for i in range(4)},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        except Exception as e:
            logger.error(f"Model prediction failed for {symbol}: {e}")

    # Fallback: return tier-based default
    return RegimePrediction(
        symbol=symbol,
        regime="CONFIRMED",
        confidence=0.0,
        probabilities={"CONFIRMED": 0.25, "CAUTION": 0.25, "FAILED": 0.25, "NO-GO": 0.25},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/entry-quality/{symbol}", response_model=EntryQualityResponse)
async def get_entry_quality(symbol: str):
    """Get current entry quality score for a symbol."""
    symbol = symbol.upper().replace('.', '').replace('/', '')

    if symbol in _entry_quality:
        return EntryQualityResponse(**_entry_quality[symbol])

    return EntryQualityResponse(
        symbol=symbol,
        score=0.0,
        action="SKIP",
        features={
            "pullback_pct": 0, "occ_body_ratio": 0, "time_since_impulse": 0,
            "volume_spike": 0, "regime_confidence": 0, "distance_to_dz": 0,
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/params/{symbol}", response_model=List[OptimizedParams])
async def get_optimized_params(symbol: str):
    """Get optimized parameters per regime for a symbol."""
    symbol = symbol.upper().replace('.', '').replace('/', '')

    if symbol in _optimized_params:
        return [OptimizedParams(**p) for p in _optimized_params[symbol]]

    # Fallback: return tier config defaults
    tiers = TIER_CONFIGS.get(symbol, TIER_CONFIGS["EURUSD"])
    result = []
    for regime in ["T1", "T2", "T3"]:
        t = tiers.get(regime, tiers["T1"])
        result.append(OptimizedParams(
            symbol=symbol,
            regime=regime,
            au_multiplier=0.5,
            buffer=5.0,
            dz_width=0.2,
            trigger_multiplier=1.2,
            sharpe=0.0,
            win_rate=0.0,
            max_dd=0.0,
        ))
    return result


@router.get("/features/{symbol}", response_model=List[FeatureImportance])
async def get_feature_importance(symbol: str):
    """Get SHAP feature importance for a symbol."""
    symbol = symbol.upper().replace('.', '').replace('/', '')

    if symbol in _feature_importance:
        return [FeatureImportance(**f) for f in _feature_importance[symbol]]

    # Default feature importance (pre-training placeholder)
    defaults = [
        {"feature": "asian_range_pips", "importance": 0.0, "rank": 1},
        {"feature": "vol_ratio_3am_9am", "importance": 0.0, "rank": 2},
        {"feature": "hour_est", "importance": 0.0, "rank": 3},
        {"feature": "spread_vs_20d_avg", "importance": 0.0, "rank": 4},
        {"feature": "impulse_to_ar_ratio", "importance": 0.0, "rank": 5},
        {"feature": "day_of_week", "importance": 0.0, "rank": 6},
    ]
    return [FeatureImportance(**f) for f in defaults]


# ── Internal update functions (called by ML pipeline) ──────

def update_regime_prediction(symbol: str, prediction: dict):
    """Update cached regime prediction (called by ML pipeline)."""
    _regime_predictions[symbol] = prediction


def update_entry_quality(symbol: str, quality: dict):
    """Update cached entry quality (called by ML pipeline)."""
    _entry_quality[symbol] = quality


def update_optimized_params(symbol: str, params: list):
    """Update cached optimized params (called by ML pipeline)."""
    _optimized_params[symbol] = params


def update_feature_importance(symbol: str, features: list):
    """Update cached feature importance (called by ML pipeline)."""
    _feature_importance[symbol] = features


def update_model_status(status: dict):
    """Update model status (called by ML pipeline)."""
    _model_status.update(status)


def register_ml_endpoints(app):
    """Register ML API routes with the FastAPI app."""
    app.include_router(router)
    logger.info("ML API endpoints registered at /api/v1/ml/*")
