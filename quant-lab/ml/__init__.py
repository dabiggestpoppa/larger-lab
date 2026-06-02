"""
CEREBUS ML — Regime-Adaptive Parameter Optimization Engine
==========================================================
3-Layer Architecture:
  Layer 1: XGBoost Regime Classifier (CONFIRMED/CAUTION/FAILED/NO-GO)
  Layer 2: XGBoost Entry Quality Scorer (0.0-1.0 continuous)
  Layer 3: Optuna Bayesian Parameter Optimizer (per-asset, per-regime)

Constitution: Python only. No NT8. No Track A/B. Close-only SL. Zero-buffer OCC.
"""
