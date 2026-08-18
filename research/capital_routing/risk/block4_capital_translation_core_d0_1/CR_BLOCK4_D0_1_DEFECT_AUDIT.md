# CR-BLOCK4-D0.1 -- Defect Audit

## Defects repaired (all verified THROUGH the repaired core)
| # | defect | repair | verified |
|---|---|---|---|
| 1 | risk_unit_bps argument ignored by arithmetic | arithmetic uses explicit risk_unit_bps; frozen R enforced at boundary | True / True |
| 2 | translation_id not account/snapshot bound | canonical JSON id binds account/portfolio/profile/snapshot | True / True |
| 3 | PORTFOLIO_MASTER not enforced | role gate + portfolio_group_id required | True / True / True |
| 4 | decision consistency unvalidated | REJECT->f=0, ACCEPT->family-f contract, heat bounds, NaN/inf fail closed | True / True / True |
| 5 | known_time not causal | max(event, decision, snapshot) on aware timestamps | True |

All adversarial facts pass: **True** (32/32).

## Evidence
Every row in the adversarial truth table below was produced by calling the
repaired `translate()` / pure helpers with the hostile input and asserting the
exact fail-closed error class:

```json
{
  "helper_uses_risk_unit_argument": true,
  "translate_rejects_non_frozen_risk_unit": true,
  "nan_risk_unit_rejected": true,
  "inf_risk_unit_rejected": true,
  "nan_pos_rejected": true,
  "inf_pos_rejected": true,
  "nan_equity_rejected": true,
  "inf_equity_rejected": true,
  "nan_admitted_f_rejected": true,
  "inf_admitted_f_rejected": true,
  "rejected_nonzero_admitted_f_blocked": true,
  "accepted_zero_admitted_f_blocked": true,
  "A_requested_f_mismatch_blocked": true,
  "A_admitted_f_mismatch_blocked": true,
  "B_requested_f_mismatch_blocked": true,
  "B_admitted_f_mismatch_blocked": true,
  "exclusive_master_blocked": true,
  "follower_blocked": true,
  "portfolio_master_accepted": true,
  "empty_portfolio_group_blocked": true,
  "translation_id_binds_account": true,
  "translation_id_binds_profile": true,
  "translation_id_binds_equity_snapshot": true,
  "translation_id_binds_portfolio_group": true,
  "translation_id_binds_configuration": true,
  "translation_id_binds_event_decision": true,
  "translation_id_stable_for_same_inputs": true,
  "canonical_serialization_no_delimiter_collision": true,
  "known_time_is_max_causal_input": true,
  "malformed_timestamp_fails_closed": true,
  "rejected_maps_to_zero_exposure": true
}
```
