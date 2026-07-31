"""
Phase 3.1: Search Space Definition
====================================
Per-regime parameter search spaces for Bayesian optimization.
"""
from __future__ import typing


# Per-regime search spaces (can be tuned per asset class)
REGIME_SEARCH_SPACES = {
    "CONFIRMED": {
        "au_multiplier": (0.40, 0.65),
        "trigger_multiplier": (1.0, 1.3),
        "dz_lower_pct": (0.30, 0.40),
        "dz_upper_pct": (0.45, 0.60),
        "buffer_pips": (3.0, 15.0),
        "min_pullback_pct": (0.30, 0.40),
        "max_pullback_pct": (0.50, 0.60),
    },
    "CAUTION": {
        "au_multiplier": (0.35, 0.55),
        "trigger_multiplier": (1.1, 1.5),
        "dz_lower_pct": (0.25, 0.38),
        "dz_upper_pct": (0.45, 0.58),
        "buffer_pips": (5.0, 20.0),
        "min_pullback_pct": (0.25, 0.38),
        "max_pullback_pct": (0.50, 0.65),
    },
    "FAILED": {
        "au_multiplier": (0.35, 0.50),
        "trigger_multiplier": (1.2, 1.5),
        "dz_lower_pct": (0.25, 0.35),
        "dz_upper_pct": (0.45, 0.55),
        "buffer_pips": (8.0, 25.0),
        "min_pullback_pct": (0.25, 0.35),
        "max_pullback_pct": (0.50, 0.65),
    },
    "NO-GO": {
        "au_multiplier": (0.35, 0.45),
        "trigger_multiplier": (1.3, 1.5),
        "dz_lower_pct": (0.25, 0.35),
        "dz_upper_pct": (0.45, 0.55),
        "buffer_pips": (10.0, 35.0),
        "min_pullback_pct": (0.25, 0.35),
        "max_pullback_pct": (0.50, 0.65),
    },
}

# Asset-class specific overrides
ASSET_CLASS_OVERRIDES = {
    "forex_major": {
        "CONFIRMED": {"buffer_pips": (3.0, 10.0)},
    },
    "forex_cross": {
        "CONFIRMED": {"buffer_pips": (5.0, 18.0)},
    },
    "index": {
        "CONFIRMED": {"buffer_pips": (5.0, 30.0)},
    },
    "metal": {
        "CONFIRMED": {"buffer_pips": (5.0, 18.0)},
    },
    "crypto": {
        "CONFIRMED": {"buffer_pips": (10.0, 50.0)},
    },
}


def get_search_space(regime: str, asset_class: str = None) -> dict:
    """Get search space for a regime, optionally with asset-class overrides."""
    space = dict(REGIME_SEARCH_SPACES.get(regime, REGIME_SEARCH_SPACES["CAUTION"]))
    if asset_class and asset_class in ASSET_CLASS_OVERRIDES:
        overrides = ASSET_CLASS_OVERRIDES[asset_class].get(regime, {})
        space.update(overrides)
    return space
