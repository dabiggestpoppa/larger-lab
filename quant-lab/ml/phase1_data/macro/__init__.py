"""
CEREBUS Macro Feature Engine
=============================
MLR (Monday London Range), Fibonacci targets, 132% kill-switch,
ILM states, and comprehensive pattern recognition.

These are the MACRO LENS features that complement the MICRO LENS
(Asian Range, AU, Density Zone) from the base feature matrix.

Per the CEREBUS v4 Manual:
- Macro and Micro lenses must remain ISOLATED in the feature store
- They operate on different temporal dimensions
- Bridging state variables connect them, NOT direct mapping

Pattern modules:
- 3-Leg: Alpha (72% retrace), Beta (61.8% retrace)
- AB-CD: Fibonacci extension pattern
- NY Sweep: 7-8 AM NY session sweep detection
- Gamma: Fibonacci-based gamma zone detection
- Rekey: 132% kill-switch breach + sequence tracking
- OCC: Order Close Confirmation extreme
- ILM Zone: Impulse Level Monitor zone
- Density Zone: Price concentration detection
- Wednesday Bifurcation: PM stress window
- Hard Exit: 12PM EST exit signal
- Gear Shift: Target modification signal
- Fib Levels: Retrace + extension level detection
- Micro-Macro Phase: Phase alignment detection
"""

from .mlr_engine import compute_mlr_features, compute_fib_targets, compute_friday_asian_anchor
from .kill_switch import compute_132_proximity, compute_rekey_state
from .ilm_detector import compute_ilm_state, compute_regime_ratio
from .pattern_recognizer import (
    detect_alpha_leg, detect_beta_leg, detect_abcd,
    detect_ny_sweep, detect_gamma, detect_rekey_132, detect_rekey_sequence,
    detect_occ_extreme, detect_ilm_zone, detect_density_zone,
    detect_wednesday_bifurcation, detect_hard_exit, detect_gear_shift,
    detect_fib_retrace_levels, detect_fib_extension_levels,
    detect_micro_macro_phase, detect_all_patterns,
)
from .macro_feature_builder import build_macro_feature_matrix

__all__ = [
    'compute_mlr_features',
    'compute_fib_targets',
    'compute_friday_asian_anchor',
    'compute_132_proximity',
    'compute_rekey_state',
    'compute_ilm_state',
    'compute_regime_ratio',
    'detect_alpha_leg',
    'detect_beta_leg',
    'detect_abcd',
    'detect_ny_sweep',
    'detect_gamma',
    'detect_rekey_132',
    'detect_rekey_sequence',
    'detect_occ_extreme',
    'detect_ilm_zone',
    'detect_density_zone',
    'detect_wednesday_bifurcation',
    'detect_hard_exit',
    'detect_gear_shift',
    'detect_fib_retrace_levels',
    'detect_fib_extension_levels',
    'detect_micro_macro_phase',
    'detect_all_patterns',
    'build_macro_feature_matrix',
]
