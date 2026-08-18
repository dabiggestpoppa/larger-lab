# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1 -- Protocol

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1-TRUTH-SYNC-AND-HANDOFF-SEAL
**Base:** 00bef1b5b52db63c22a29b3287799742631930db · **Parent:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING-R1-POSITION-SCALING-ACCOUNT-BOUNDARY-TRUTH-REPAIR
**Branch:** dabiggestpoppa/larger-lab · `capital-routing`

## Scope (narrow truth/handoff seal)

- Recompute accepted notional summary statistics DIRECTLY from the event-level
  `CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv` (status == ACCEPT_FULL). No prose
  summary is trusted.
- Audit every summary source (R1 decision audit_facts, R1 report, R1 progress
  file) against the canonical event-level stats; repair drift.
- Freeze cross-workstream authority SHAs (execution-runtime-foundation,
  tb-forward-engine) at checkpoint-verified heads (read-only).
- Repair the Capital Policy vs Translation boundary: H1, family classification,
  and model heat are immutable UPSTREAM inputs; Capital Translation Core never
  recomputes admission.
- Emit the frozen handoff schemas and the R1.1 nonregression lock.

## DO NOT

Change strategy science, A/B, 70/30, H1, f_total, 1R, pos, cost science,
optimize, clip exposure, add leverage caps, build Capital Translation Core,
connect a broker, place orders, or modify execution-runtime-foundation /
tb-forward-engine.

## Evidence chain

1. Sealed science: Block III scale seal R1 (fail-closed) at `40d23712`.
2. Position-scaling repair (R1) at `00bef1b5` — corrected formula
   N = E x f x pos x 1e4/RISK proven at machine precision.
3. This seal: canonical stats + drift audit + handoff boundary.
