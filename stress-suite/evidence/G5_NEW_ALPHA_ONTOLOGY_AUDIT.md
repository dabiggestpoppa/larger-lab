# G5 — NEW ALPHA ONTOLOGY AUDIT (S15)

## Required path (enforced)
```
UNRESOLVED_PATTERN -> anomaly cluster -> ontology-exploration review
-> candidate MechanismCard -> frozen experiment protocol -> B7 validation
```
Exit condition: a NEW mechanism hypothesis exists without forcing a known label and without creating a tradable strategy prematurely.

## Object semantics
- **UnresolvedPatternRecord:** observations, conditions, data-quality results, known-family fit attempts (`trend`, `mean-reversion`, `carry`, `microstructure` all tested and rejected), residual behavior, independence, falsifiers, what remains unexplained. `UNKNOWN_FAMILY` is a legal, first-class value — nearest-family classification is prohibited.
- **MechanismCard:** proposed mechanism, observable inputs, constraints, state-transition hypothesis, realization/failure conditions, domain, evidence refs, alternative explanations, falsifiers. Card ≠ strategy.
- **FrozenExperimentProtocol:** dataset, time range, features, labels, metrics, falsification criteria, holdout, cost/execution assumptions, promotion criteria — all frozen before result evaluation; post-hoc threshold change prohibited.

## Controls
- **A:** residual disappears after data-quality correction → no new family (`data_quality_failure` rule → unresolved disposition).
- **B:** residual survives but only one evidence lineage → remains unresolved / requests independent confirmation.
- **C:** residual survives multiple lineages but required sensor missing → routes to DATA_BLOCKED (S18), not forced ontology.

## Forbidden transition
`UNRESOLVED_PATTERN -> StrategySpec/Signal/ExecutionPlan` is tested as an explicit failure. No execution artifact was produced by the S15 pack (asserted in `test_g5.py`).

## Status
**PASS** — new-family discovery without label forcing or premature strategy creation; MechanismCard precedes strategy; protection holds under all three controls.