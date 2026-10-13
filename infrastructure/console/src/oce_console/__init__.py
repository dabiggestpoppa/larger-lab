"""OCE console — client of the local OCE control plane (charter increment I-3).

B5-I4 (OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md section 12, row I-3):
the deterministic read path — a CLI status view over contract-validated
reads with fail-closed ``STACK_UNREACHABLE``. The console is a client and
never an authority: it holds no canonical state, mints nothing, writes
nothing, and can only GET routes declared in the frozen B5-I2 contract
pack against a loopback base URL. Stdlib only; no LLM; no provider.
"""
from __future__ import annotations

__version__ = "1.0.0"

CONSOLE_KIND = "oce-console-status"
