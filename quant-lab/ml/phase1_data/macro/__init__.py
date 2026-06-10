"""
CEREBUS Macro Feature Engine
=============================
MLR (Monday London Range), Fibonacci targets, 132% kill-switch,
ILM states, and Alpha/Beta pattern recognition.

These are the MACRO LENS features that complement the MICRO LENS
(Asian Range, AU, Density Zone) from the base feature matrix.

Per the CEREBUS v4 Manual:
- Macro and Micro lenses must remain ISOLATED in the feature store
- They operate on different temporal dimensions
- Bridging state variables connect them, NOT direct mapping
"""

from .mlr_engine import compute_mlr_features, compute_fib_targets
from .kill_switch import compute_132_proximity, compute_rekey_state
from .ilm_detector import compute_ilm_state, compute_regime_ratio
from .pattern_recognizer import detect_alpha_leg, detect_beta_leg, detect_abcd
from .macro_feature_builder import build_macro_feature_matrix

__all__ = [
    'compute_mlr_features',
    'compute_fib_targets',
    'compute_132_proximity',
    'compute_rekey_state',
    'compute_ilm_state',
    'compute_regime_ratio',
    'detect_alpha_leg',
    'detect_beta_leg',
    'detect_abcd',
    'build_macro_feature_matrix',
]
