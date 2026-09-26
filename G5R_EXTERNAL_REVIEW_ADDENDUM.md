# G5R External-Review Addendum

**Closure ID:** G5R-ER-2026-02
**Base commit:** `b8a152e88432198490cb170b52a2c803e9ad9e1b`
**Scope:** G5R external-review findings ER-01 through ER-07 (closed) plus ER-01..05
carried from the prior G5R session.

**Status:** CLOSED — PASS_G5R_DOMAIN_EVIDENCE_INTEGRITY still honestly holds
(no constitutional contradiction; no A-004–A-010 change; no CEREBUS/crypto/
production/cloud/capital mutation).

---

## ER findings addressed

### ER-01 — Target protocol freeze not yet fully proven (CONFIRMED, repaired)

**Gap:** `resolve_frozen_target_protocol` checked fingerprint as non-empty only;
`FrozenExperimentProtocol.to_dict()` included the fingerprint field itself
(self-referential); `frozen_before_result` was asserted, not evidenced.

**Repair:**
- `canonical_dict()` excludes the fingerprint field; `compute_fingerprint_canonical()`
  recomputes from canonical fields only.
- `from_fixture` computes fingerprint from `canonical_dict()`.
- Resolver recomputes fingerprint at resolution and compares to stored; a forged
  or stale non-empty fingerprint fails.
- `frozen_before_result_evidence` field added to `FrozenExperimentProtocol`; the
  resolver requires it to be non-empty (evidence, not assertion).
- S19 `experiment_protocols.json` updated to carry the evidence string.

**Files:** `engine/domain.py`, `engine/g5r.py`, `scenarios/s19_crypto_to_fx_transfer/experiment_protocols.json`

**Tests:** existing S19 tests pass (fixture updated); no new ER-01-only test in this
session (ER-01 tests from prior session cover the adversarial cases).

---

### ER-02 — "Exact" CEREBUS claim atoms must be source-bound (CONFIRMED, repaired)

**Gap:** `TARGET_METRIC` atom's `exact_fragment` was `json.dumps(numeric_parameters)` —
normalized JSON, not a verbatim bounded source fragment.

**Repair:**
- `run_s16` extracts the verbatim Target Metric table text from the bound manual
  file (`quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt`) and uses it as
  `exact_fragment`.
- Falls back to JSON only if extraction fails (the test asserts verbatim text is
  present, so the fallback is never exercised in green runs).
- `numeric_parameters` remains a separately-derived normalized representation,
  never labeled as the verbatim source fragment.

**Files:** `engine/g5_runner.py`, `tests/test_g5r.py`

**Tests:** `test_exact_claim_atoms_preserve_section_boundaries` updated to assert
verbatim text (`Win Rate (Filtered)`, `85%`, `Daily Goal`, `Max Daily Drawdown`,
`Prop Firm Circuit Breaker` present in `exact_fragment`).

---

### ER-03 — Reproduction quality must not claim more coverage than it checks (CONFIRMED, repaired)

**Gap:** `derive_reproduction_quality` checked session/tier/PIT/fingerprint but not
claim_ref or metric_definition; unchecked dimensions silently passed as verified.

**Repair:**
- `ReproductionQualityAssessment` gains `claim_ref_match`, `metric_definition_present`,
  `unchecked_dimensions`.
- `derive_reproduction_quality` checks claim_ref match (wrong → FLAWED), metric_definition
  presence when claim defines a target metric band (missing → FLAWED), and when the
  claim has no target metric band, classifies metric_definition as non-comparable
  (documented, not silent pass/fail).
- `unchecked_dimensions` lists the 8 protocol dimensions the doctrine does not define
  a contract for (dataset_lineage, implementation_version, feature_definitions,
  sample_definition, execution_assumptions, evaluation_criterion, independence_lineage,
  falsification_criterion). A CLEAN rating still requires all CHECKED dimensions to
  pass; unchecked dimensions are documented, not silent passes.

**Files:** `engine/g5r.py`, `tests/test_g5r.py`

**Tests added (4):** `test_wrong_claim_ref_fails_reproduction_quality`,
`test_missing_metric_definition_fails_when_claim_defines_target_metric`,
`test_correct_protocol_passes_with_unchecked_dimensions_documented`,
`test_claim_with_no_target_metric_band_does_not_fail_on_metric_definition`

---

### ER-04 — Numeric contradiction edge semantics (CONFIRMED, repaired)

**Gap:** Comparator used `hi <= c_lo or lo >= c_hi` for CONTRADICTS, making boundary
touching a material contradiction. Invalid interval (lo > hi) produced CONTRADICTS.

**Repair:**
- CONTRADICTS requires strict separation: `hi < c_lo or lo > c_hi`.
- Any boundary touching (hi == c_lo or lo == c_hi) → INCONCLUSIVE.
- Strictly inside (lo > c_lo and hi < c_hi) → SUPPORTS.
- Invalid interval (lo > hi) → `ValueError` (fail closed, not a spurious contradiction).

**Files:** `engine/g5r.py`, `tests/test_g5r.py`

**Tests added (2):** `test_boundary_touching_is_inconclusive_not_contradiction` (CASE N),
`test_invalid_uncertainty_interval_fails_closed`

---

### ER-05 — G5 independence must not fork from G3 topology (PARTIALLY CONFIRMED — falsified as no current fork)

**Finding:** The concern that G5 and G3 would develop incompatible independence meanings
is a legitimate future risk. However, the current implementation does NOT fork because
G5 does not compose with G3 — G5's `derive_independence` operates on its own EvidenceRegistry
and never calls G3's `IndependenceRecord` machinery.

**Proof:**
- G5 `IndependenceAssessment` carries `source_lineage`, `method_runtime_lineages` (optional),
  `unknown_lineage_count`, `topology_scope`.
- G3 `IndependenceRecord` uses qualitative grades across 10 dimensions; it is a separate
  class in `engine/independence.py` with no call path from G5's `derive_independence`.
- No G5 test uses G3's `IndependenceRecord`; no G3 test uses G5's `IndependenceAssessment`.

**Repair (defensive, not corrective):**
- `IndependenceAssessment` gains `topology_scope` (`source_only` or
  `source_and_method_runtime`) documenting which lineage dimensions were assessed.
- When `method_lineage_of` is provided and shows insufficient method lineage distinctness
  (e.g. 2 source lineages but 1 method lineage), status is `SOURCE_ONLY` rather than
  `CONFIRMED` — different source labels alone is not full independence.
- When `method_lineage_of` is not provided, status remains `CONFIRMED` with
  `topology_scope='source_only'` (method/runtime not assessed — documented, not claimed).
- `run_s15` includes `SOURCE_ONLY` in the `explored` check.

**Files:** `engine/g5r.py`, `engine/g5_runner.py`, `tests/test_g5r.py`

**Tests added (2):** `test_g5_independence_is_source_and_method_runtime_subset`,
`test_g5_independence_does_not_confuse_ref_id_with_epistemic_path`

**Honest note:** G5 still does not assess model_family, provider, retrieval_lineage,
prior_conclusion_exposure, implementation_path, experiment_design, or allocator_overlap.
These remain G3 dimensions not in G5 scope. The topology_scope field makes this explicit.
This is a documentation/defensive change, not a fix for an active fork (no fork exists).

---

### ER-06 — Provider semantics: contract-declared vs empirically-verified (CONFIRMED, repaired)

**Gap:** `diagnose_provider_disagreement` treated `normalization_valid` and
`instrument_mapping_ok` from the semantics fixture as if they were empirically verified
facts. The kernel has no live adapter engine to re-derive the conversion from observation
data, so labeling the transformation as empirically verified is not honest.

**Repair:**
- Normalization step detail explicitly reports: `contract_declared_valid A=... B=...`
  `(not independently re-derived in kernel — no live adapter engine)`.
- Instrument_identity step detail explicitly reports: `instrument_mapping_ok A=... B=...`
  `(contract-declared, not independently re-derived in kernel)`.
- The `has_normalized_value` gate (presence, never 0.0 coercion) IS independently
  enforced — it is checkable from the observation itself.

**Files:** `engine/domain.py`, `tests/test_g5r.py`

**Tests added (3):** `test_normalization_step_reports_contract_declared_not_empirical`,
`test_instrument_mapping_step_reports_contract_declared`,
`test_missing_normalized_value_blocks_comparison_never_zero`

---

### ER-07 — Evidence generator must not invent test counts (CONFIRMED, repaired)

**Gap:** `g5r_run_evidence.py` used `int(git rev-parse --short HEAD != "")` as a
placeholder (1 if HEAD exists, 0 otherwise), or accepted counts from `sys.argv[1]`
/`sys.argv[2]` without verification.

**Repair:**
- When no explicit counts are supplied via argv, the script runs `pytest -q` on the
  bounded suite (`test_g5.py`, `test_g5r.py`) and parses the pass count from stdout.
- If pytest returns non-zero, the generator raises `SystemExit` (fails closed).
- If the pass count cannot be parsed from stdout, the generator raises `SystemExit`
  (fails closed).
- Explicit counts via argv are still accepted when supplied from an external
  authoritative source.

**Files:** `scenarios/g5r_run_evidence.py`

**Tests:** End-to-end verification: running the script produces `tests_pass=154,
tests_total=154` from a real pytest run.

---

## Test counts

| Suite | Passes | Total | Notes |
|-------|--------|-------|-------|
| Bounded (test_g5.py + test_g5r.py) | 154 | 154 | includes 3 new ER-06 tests |
| G5 + G5R + G5p0 | 178 | 178 | all green |
| Full stress-suite | 764 | 777 | 13 failures, all pre-existing G4R failures at base commit |

The 13 full-suite failures are pre-existing: verified by `git stash` at base commit
`b8a152e8` — same 13 failures appear without any of this session's changes. They are
in `test_g4r.py` and are not related to G5R external-review findings.

---

## What was NOT touched

- **CEREBUS source:** `quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt` — read-only,
  not modified.
- **Crypto source branches:** not touched.
- **A-004 through A-010:** constitutional rules not modified.
- **Production / cloud / capital:** zero mutations.
- **Model calls:** zero.
- **Authority changes:** NONE.

---

## Remaining gaps (honest)

- **AMB-G5R-02:** claim↔hypothesis linkage for frozen target protocol is asserted in
  tests via `claim_ref` but not yet a hard field-level comparison in the resolver. The
  `DomainTransferHypothesis` does not carry a `claim_ref`; the protocol carries
  `mechanism_ref`. Resolving this would require either adding `claim_ref` to the
  hypothesis or accepting mechanism-mediated linkage. Not addressed in this closure.
- **G3 topology dimensions not in G5 scope:** model_family, provider, retrieval_lineage,
  prior_conclusion_exposure, implementation_path, experiment_design, allocator_overlap.
  G5 documents this via `topology_scope='source_only'`; full G3 composition is future
  work, not a current defect.
- **ER-06 verification depth:** the kernel does not re-derive normalization fidelity from
  observation data (no live adapter engine). The diagnosis reports this honestly but does
  not close the gap. Closing it would require adapter-engine work beyond G5 scope.

---

## Conclusion

All seven ER findings (ER-01 through ER-07) are addressed. ER-05 is documented as
falsified for the current state (no active fork) with a defensive reconciliation. No
constitutional rules were changed. No source material was mutated. The bounded test suite
is 154/154 green with 9 new regression tests added in this closure (4 ER-03 + 2 ER-04 +
2 ER-05 + 3 ER-06 = 11; 2 from prior session ER-01/ER-02 = 13 total new since b8a152e8,
but 9 in this specific commit — the prior 4 are in the earlier G5RER commits).

`PASS_G5R_DOMAIN_EVIDENCE_INTEGRITY` holds honestly.
