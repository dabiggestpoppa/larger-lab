# G5R NEW ALPHA / INDEPENDENCE AUDIT — S15 evidence-path integrity

Scope: G5R-01 (independence must be proven from paths), G5R-02 (evidence-bound cluster
membership), G5R-03 (disposition-gated mechanism admission). Core law:
**CLAIMED INDEPENDENCE != VERIFIED INDEPENDENCE.**

## 1. The defect (pre-G5R)

`UnresolvedPatternRecord` carried `evidence_lineages: int` and `run_s15` used
`evidence_lineages >= 2` to produce `independence_status=CONFIRMED` — a caller could mint
epistemic independence with an integer. Anomaly clustering used
`sum(max(evidence_lineages, 1) for members)`, which converted ZERO declared lineages into
ONE independent observation. Mechanism cards were loaded whenever the fixture file
existed, regardless of the pattern's epistemic disposition.

## 2. Replacement (G5R)

`engine/g5r.py`:

- **`derive_independence(pattern, registry)`** resolves the pattern's explicit
  `independence_evidence_refs` through the governed EvidenceRegistry and derives:
  raw evidence paths, distinct source lineages, distinct method/runtime lineages (via the
  optional `method_lineage_of` mapping), unknown lineage count, verified distinct lineage
  count. No effective-sample-size scalar is produced. Fail-closed rules:
  - unregistered ref → counted as UNKNOWN lineage, never favorable;
  - two registered refs on the SAME lineage → ONE lineage;
  - zero refs → zero verified observations (never becomes one);
  - CONFIRMED requires ≥ 2 verified distinct lineages AND zero unknowns;
    SUPPORTED = ≥2 refs all on a single lineage; else UNRESOLVED.
- **`cluster_verified_observation_paths(members, registry)`** — cluster
  `independent_observations` = unique REGISTERED evidence paths across members. A repeated
  pattern record referencing the same underlying observation cannot inflate the cluster.
- **`decide_mechanism_admission(card, dispositions)`** — only
  `ONTOLOGY_EXPLORATION_CANDIDATE` yields `ADMITTED_MECHANISM_FOR_EXPERIMENT`;
  `UNRESOLVED_PATTERN` / `DATA_BLOCKED` / `POLICY_HOLD` keep the card
  `PROPOSED_MECHANISM` and NO frozen protocol is emitted.

The runner (`run_s15`) now derives every pattern's independence from the registry built
from the scenario's `evidence.json` (IND_1..IND_3, distinct estimator lineages
L1/L2/L3) and feeds the derived status (not the integer) into the shared policy.

`evidence_lineages` remains on the record as a LEGACY DISPLAY field; no code path reads it
for decisions (grep-verified in the runner).

## 3. Regression coverage (`tests/test_g5r.py`)

| Required test | What it enforces |
|---|---|
| `test_raw_integer_cannot_mint_independence` | CASE A: `evidence_lineages=99`, 0 registered refs → NOT independent, end-to-end UNRESOLVED_PATTERN |
| `test_zero_lineage_does_not_become_one` | zero refs → zero verified observations |
| `test_duplicate_lineage_not_independent` | E1+E2 on lineage L1 → one lineage, not CONFIRMED |
| `test_two_verified_distinct_lineages_support_exploration` | 3 refs / 3 lineages → CONFIRMED |
| `test_unknown_lineage_does_not_count_favorably` | registered-with-lineage + registered-without-lineage → unknown ≥ 1, never CONFIRMED |
| `test_duplicate_pattern_same_evidence_dedupes` | two identical patterns → cluster counts unique paths |
| `test_same_signature_distinct_evidence_counts_separately` | distinct evidence on same signature counts separately |
| `test_similarity_does_not_imply_independence` | grouping never upgrades per-pattern independence (runner-level too) |
| `test_data_quality_failed_pattern_not_admitted_to_mechanism` | quality-failed host → card PROPOSED, no protocol |
| `test_single_lineage_pattern_not_admitted` | one verified lineage → UNRESOLVED + card PROPOSED |
| `test_data_blocked_pattern_not_admitted` | sensor-dependent host → DATA_BLOCKED + card PROPOSED |
| `test_qualified_pattern_can_admit_mechanism` | ONTOLOGY_EXPLORATION_CANDIDATE → ADMITTED_MECHANISM_FOR_EXPERIMENT |

## 4. Changed G5 assertions (documented upgrades, §29 discipline)

| Old assertion | Why invalid | Replacement | Location |
|---|---|---|---|
| `test_control_b_single_lineage_remains_unresolved` mutated `evidence_lineages=1` | the integer held decision authority pre-G5R — exactly the defect closed | reduce REGISTERED evidence refs to a single lineage (`independence_evidence_refs=["IND_1"]`) | tests/test_g5.py |

## 5. Result

`S15 EVIDENCE INDEPENDENCE: PASS — derived from governed evidence paths; zero never becomes one; clusters evidence-bound; mechanism admission disposition-gated.`
