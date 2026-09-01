# G2R Evidence-Lineage Audit

**Scope:** G2R-02 (execution-grade evidence registry), G2R-03 (derived patch recurrence), G2R-05 (§5 non-scalar independence lineage), AMB-13 resolution representation.

## 1. Governed evidence registry (G2R-02)

Every scenario run constructs an `EvidenceRegistry` from its `observable_evidence.json` records **before the first adjudicated decision**. Accepted kinds: `OBSERVATION`, `DETERMINISTIC`, `AGENT_CLAIM`, `INDEPENDENT_CONFIRMATION`, `CONTRADICTION`, `PATCH_PRESSURE`, `INDEPENDENCE`, `AFFECTED_SURFACE`, `RESOLUTION` (reusing the canonical `EvidenceRecord` / `ContradictionRecord` / `PatchPressureRecord` / `AffectedSurface` / `IndependenceRecord` types — no parallel semantics).

Fail-closed behavior (each asserted in `tests/test_g2r_evidence_registry.py`):

| property | behavior |
|---|---|
| unknown evidence ref | `UnknownEvidenceRef` — observation parked, violation recorded, never applied |
| duplicate conflicting id | rejected at construction (`DuplicateEvidenceError`) |
| duplicate identical id | tolerated (canonical fingerprint unchanged) |
| phase transition citing phantom ref | rejected before a decision is formed |
| institutional action citing phantom ref | rejected before the action applies |
| provenance survival | registry ids + lineage survive into the transition audit |

## 2. Independence lineage — NON-SCALAR (G2R-05 / §5)

`LineageSummary` carries the raw vector: `raw_evidence_count`, `distinct_source_lineages`, `distinct_model_lineages`, `shared_allocator`, `shared_retrieval`. No authoritative effective-sample-size score is minted (AMB-03 open); a `derived_lineage_score` property exists but is labelled EXPERIMENTAL / NON-AUTHORITATIVE and carries no transition authority.

The policy's high-independence gates (`core.structural.contradiction`, `core.window.open`, reconsolidation, plural-model rules) require `lineage_min_distinct: 2`.

Metamorphic proof (`test_collapse_lineages_kills_independent_confirmation`): with every channel grade **identical**, collapsing `LINEAGE_B` into `LINEAGE_A` drops the distinct-lineage count from 2 to 1 — the high-independence gate stops believing independent confirmation and the review stalls at `ESCALATION_REVIEW` instead of reaching `TRANSFORMATION_CANDIDATE`.

Distinction guard (`test_s01_patch_pressure_is_not_an_independent_confirmation_claim`): S01's transformation fires through the **derived patch-pressure gate** (`core.structural.patch`) — a signature-recurrence topology that intentionally does not claim independent confirmation — so the S01 run retains `TRANSFORMATION_CANDIDATE` at `distinct_source_lineages=1`. This prevents a future reader from over-reading the S01 trace as an independence-lineage proof.

Derivation over claims (`test_registry_lineage_ignores_claim_when_evidence_disagrees`): an `INDEPENDENCE` record may claim 2 distinct lineages, but the registry derives support from the actual referenced evidence objects' lineages (1) — the claim is never trusted as truth.

## 3. Derived patch recurrence (G2R-03)

`PatchAccumulator` derives per-signature state from the **ordered** patch-event history:

- `derived_recurrence` / `recurrence` — exact-signature event count (caller-supplied value is overwritten; the caller's claim is preserved in `caller_supplied_recurrence` for the audit);
- `justified_level` — highest structural level observed for that signature;
- `override_total` — accumulated override burden.

`core.structural.patch` reads only derived values: `L3 <= justified_level <= L6` and `derived_recurrence >= 3`.

Proofs (`tests/test_g2r_lineage_patch.py`):

- one L3 event claiming `recurrence=99` → derived `1` → no structural escalation (audit shows `patch_derived_recurrence=1`);
- four same-signature L3 events each claiming `recurrence=1` → structural gate fires **only at derived count 4**;
- three *different* signatures at L3 (each lying `recurrence=99`) → no single signature reaches 3 → no escalation (raw patch count is insufficient);
- committed S03 pack: the unrelated `SIG_X` lying event never aggregates; only the `SIG_C` cluster (derived 8) fires at obs 11.

No semantic/ML clustering is implemented — AMB-11 remains OPEN; grouping is by explicitly supplied exact `causal_signature`.

## 4. Resolution representation (AMB-13)

`ResolutionCondition` (PROVISIONAL_TEST_OBJECT) resolves from the registry via `resolution_class` on evidence records: `REPLACEMENT_VALIDATED` (S01 → NEW_STABLE), `PLURAL_NON_DOMINATION` (S05 → PLURAL_MODEL_STATE). `core.resolution.new_stable` additionally requires unsullied prior structural history (`clean_labels: [DATA_QUALITY_DEFECT]`), so a quiet baseline or a data-quality-defective episode can never mint a NEW_STABLE. **AMB-13 stays OPEN for ratification review — no A-010 channel was added.**

## 5. Verdict

**PASS.** Evidence refs are execution-grade; independence is a non-scalar vector with a metamorphic proof; patch recurrence is derived, not trusted; resolution semantics are explicit without amending the architecture.