# A1-DEEPERS — RAW Namespace

Status: SEALED_AT_B1 (PFT-B1-SPECIFICATION-SEAL)

## Rule

RAW is the literal implementation of the frozen A1 v2.2 specification.

- RAW code lives under `a1_deepers_v2/raw/` and
  `strategy_foundry.pft.engine.*`.
- RAW never imports from `twins/` or `strategy_foundry.pft.twins.*`.
- RAW never silently substitutes an alternative algorithm (e.g. no
  pseudoinverse/ridge for the literal K3 OLS inverse).
- RAW parameters reference the parameter register; AUTHOR_CONSTANT values
  are frozen.
- RAW results are never overwritten by TWIN or ABLATION results.

## Fail-closed contract

Every unresolved implementation state has a deterministic fail-closed
behavior enumerated in the machine spec (`SPEC_A1_V2_2.json` ->
`fail_closed`). When a required condition cannot be computed safely the
affected kernel is marked invalid with a reason code and disabled for
that observation.
