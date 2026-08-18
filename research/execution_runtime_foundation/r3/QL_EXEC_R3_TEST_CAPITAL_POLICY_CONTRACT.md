# QL-EXEC-R3 — Test Capital Policy Contract

`PassThroughCapitalPolicyAdapter` (runtime/adapters.py) is SIMULATION ONLY.

- `admit()` deterministically ADMITS (default) or REJECTS (`reject=True`) a
  fixture event; it produces an idempotent `decision_id` + `reservation_id`.
- NO A/B, NO 70/30, NO H1, NO pos_t, NO 1R, NO notional formula.
- `release()`, `reconstruct_reservations()`, `shared_heat_state()` are stubs.

`CapitalPolicyAdapter` remains the only capital authority boundary; the generic
runtime performs NO sizing math.
