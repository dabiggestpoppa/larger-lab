# A1-DEEPERS — TWINS Namespace

Status: SEALED_AT_B1 (PFT-B1-SPECIFICATION-SEAL)

## Rule

TWINs are separately registered, mathematically consistent alternative
interpretations of A1.

- TWIN code lives under `a1_deepers_v2/twins/` (and mirrors in
  `strategy_foundry.pft.twins.*`).
- Every TWIN is registered with its own experiment id and parameter
  register entries (`TWIN_PARAMETER` class).
- TWIN results never overwrite RAW results; they are reported as
  evidence classes in `comparative/twins/`.
- TWIN parameters are never referenced by RAW code.

## Examples of TWIN candidates (preregistered, not authorized to build yet)

- K3 OLS with pseudoinverse / ridge / regularization.
- Alternative DMD solver or phase estimator.
- Any reinterpretation of a frozen v2.2 constant.

No TWIN is built during B0-B3; this namespace exists to enforce
isolation before any experiment exists.
