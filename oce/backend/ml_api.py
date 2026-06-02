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

logger = logging.getLogger("oce.ml")

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

# ── Tier configs (from Phase 1 K-Means or manual fallback) ─

TIER_CONFIGS = {
    "EURUSD": {"T1": {"au": 10, "trig": 12}, "T2": {"au": 12, "trig": 15}, "T3": {"au": 15, "trig": 19}},
    "GBPUSD": {"T1": {"au": 13, "trig": 16}, "T2": {"au": 16, "trig": 19}, "T3": {"au": 20, "trig": 24}},
    "USDCHF": {"T1": {"au": 11, "trig": 13}, "T2": {"au": 15, "trig": 18}, "T3": {"au": 20, "trig": 24}},
    "USDJPY": {"T1": {"au": 16, "trig": 19}, "T2": {"au": 26, "trig": 31}, "T3": {"au": 44, "trig": 53}},
    "AUDUSD": {"T1": {"au": 10, "trig": 12}, "T2": {"au": 12, "trig": 15}, "T3": {"au": 15, "trig": 19}},
    "NZDUSD": {"T1": {"au": 10, "trig": 12}, "T2": {"au": 12, "trig": 15}, "T3": {"au": 15, "trig": 19}},
    "GBPJPY": {"T1": {"au": 19, "trig": 23}, "T2": {"au": 37, "trig": 44}, "T3": {"au": 71, "trig": 85}},
    "GBPAUD": {"T1": {"au": 14, "trig": 17}, "T2": {"au": 24, "trig": 29}, "T3": {"au": 42, "trig": 50}},
    "GBPNZD": {"T1": {"au": 15, "trig": 18}, "T2": {"au": 27, "trig": 32}, "T3": {"au": 51, "trig": 61}},
    "GBPCHF": {"T1": {"au": 13, "trig": 16}, "T2": {"au": 23, "trig": 28}, "T3": {"au": 44, "trig": 53}},
    "CHFJPY": {"T1": {"au": 14, "trig": 17}, "T2": {"au": 24, "trig": 29}, "T3": {"au": 42, "trig": 50}},
    "US500":  {"T1": {"au": 21, "trig": 25}, "T2": {"au": 39, "trig": 47}, "T3": {"au": 75, "trig": 90}},
    "DE30":   {"T1": {"au": 19, "trig": 23}, "T2": {"au": 37, "trig": 44}, "T3": {"au": 71, "trig": 85}},
    "FR40":   {"T1": {"au": 19, "trig": 23}, "T2": {"au": 37, "trig": 44}, "T3": {"au": 71, "trig": 85}},
    "XAUUSD": {"T1": {"au": 16, "trig": 19}, "T2": {"au": 29, "trig": 35}, "T3": {"au": 48, "trig": 58}},
    "XAGUSD": {"T1": {"au": 7,  "trig": 8.5},"T2": {"au": 12, "trig": 14.5},"T3": {"au": 21, "trig": 25}},
    "BTCUSD": {"T1": {"au": 205,"trig": 246},"T2": {"au": 545,"trig": 654},"T3": {"au": 1160,"trig": 1392}},
    "ETHUSD": {"T1": {"au": 35, "trig": 42}, "T2": {"au": 42, "trig": 52}, "T3": {"au": 52, "trig": 65}},
}


# ── Endpoints ──────────────────────────────────────────────

@router.get("/status", response_model=ModelStatus)
async def get_model_status():
    """Get current ML model status."""
    return ModelStatus(**_model_status)


@router.get("/regime/{symbol}", response_model=RegimePrediction)
async def get_regime(symbol: str):
    """
    Get current regime prediction for a symbol.
    Returns cached prediction or computes from tier config fallback.
    """
    symbol = symbol.upper().replace('.', '').replace('/', '')

    # Return cached prediction if available
    if symbol in _regime_predictions:
        return RegimePrediction(**_regime_predictions[symbol])

    # Fallback: return a default "loading" response
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
