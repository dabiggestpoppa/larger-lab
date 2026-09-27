# G5 — B7 VALIDATION AUDIT

## Authority source
Read-only ingestion of `OCE_BLOCK_07_QUANT_FOUNDATION_PLAN_v1.0.md` (and B8 Quant Lab/Watch plan). B7 is the validation authority for quantitative strategy promotion; QUANT WATCH/B8 is a research/discovery surface, not execution authority. `B7ValidationGate` in `engine/domain.py` is a fixture derived from that doctrine, not a parallel fake quant stack.

## Gate vector (preserved, not collapsed to a score)
- PIT integrity
- data lineage
- execution realism
- cost model
- parameter/family multiplicity
- OOS/holdout
- walk-forward
- sensitivity/stress
- mechanism plausibility
- reproducibility

No `B7_SCORE = 82`-style scalar authority: a material hard failure blocks promotion regardless of other surfaces.

## S14 evidence
- **PIT:** critical feature has `availability_time > decision_time` while the naive pipeline consumes it — detected from observable timestamps (no hidden-truth shortcut).
- **Execution:** condensed fills contain impossible-spread and fills-before-signal-availability defects.
- **Terminal:** promotion `REJECTED` while research priority `PRIORITY_HIGH` (priority ≠ promotion; S14/S18 requirement).
- **FailureAtoms emitted:** `LOOKAHEAD_LEAKAGE`, `UNREALISTIC_FILL_MODEL` — reusable, with reopen conditions: PIT-correct reconstruction AND realistic execution model passing frozen validation.
- **Controls:** A) fix lookahead only → still reject (execution impossible); B) fix fills only → still reject (lookahead remains); C) moderate PnL with clean PIT/fills/OOS → progresses farther than huge fake alpha.

## Metamorphic (profit cannot buy promotion)
Same defective strategy at PnL 50% / 500% / 5000%: terminal state identical (`REJECTED_NEGATIVE_KNOWLEDGE`); research priority may rise. Enforced as a policy rule, not prose.

## Status
**PASS** — material-gate rejection is artifact-driven, vector-preserving, and PnL-invariant. No test asserts a scalar score.