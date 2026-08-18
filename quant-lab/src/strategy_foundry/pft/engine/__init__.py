"""PFT A1 v2.2 engine — pre-economic math & causality conformance.

Implements the frozen formulas (A1.F01-F19) exactly as specified,
computes features/kernel weights/state ONLY, and stops before any PnL.
Drawdown and per-leg-stop overlays are implemented as pure, fixture-
tested state machines (synthetic NAV only) and are NOT run against real
data in pre-economic mode.
"""
