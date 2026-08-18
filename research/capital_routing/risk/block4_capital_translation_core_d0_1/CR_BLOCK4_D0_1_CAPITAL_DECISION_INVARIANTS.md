# CR-BLOCK4-D0.1 -- CapitalDecision Invariants

CapitalDecision is IMMUTABLE upstream truth. The core never recomputes H1 /
family / model heat; it only REJECTS internally contradictory decisions
(CapitalDecisionConsistencyError) — it never silently repairs them.

## Rejected events (REJECT_HEAT_CAP)
- admitted_f_pct == 0 within 1e-09 (a rejected event has ZERO admitted
  exposure; a contradictory nonzero admitted_f is REJECTED, never overwritten)
- after validation -> NO_EXPOSURE: zero budget, zero notional, zero price move
- no H1 reconsideration, no exposure leakage

## Accepted events (ACCEPT_FULL)
- admitted_f_pct > 0
- frozen family-f contract (science R1.1):
    A: requested_f == 0.70 AND admitted_f == 0.70
    B: requested_f == 0.30 AND admitted_f == 0.30
  (a 100x unit error, e.g. 70 instead of 0.70, fails the contract)
- model_heat_after <= 1.0 + 1e-09 (H1-1.00-REJ cap)

## Model heat
- model_heat_before / model_heat_after: finite, >= -1e-09 (the sealed
  ledger carries fp noise down to -2.2e-16 on pre-heat; the bound uses the
  documented tolerance, it is not a hardcoded 0)
- for REJECT_HEAT_CAP the after-value is the pre-existing heat (the rejected
  event adds none); no stronger invariant is invented

## Policy / config identity
- policy_id non-empty, configuration_hash non-empty (policy IDs are
  generation-dependent; the frozen literal name is not hardcoded into the
  core — the harness binds H1-1.00-REJ + its configuration hash upstream)

## Numeric finiteness (all fields)
pos_t, risk_unit_bps, requested_f_pct, admitted_f_pct, model_heat_before,
model_heat_after, equity_at_admission: math.isfinite required; NaN / +inf /
-inf -> InvalidNumericInputError. (`not value` guards alone do NOT catch NaN:
bool(float("nan")) is True.)
