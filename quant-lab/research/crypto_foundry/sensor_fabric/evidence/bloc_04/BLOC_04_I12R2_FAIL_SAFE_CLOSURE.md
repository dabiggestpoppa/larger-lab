# SENSOR-B4-I12R2 — FAIL-SAFE CLOSURE (append-only correction narrative)

> Mandate: SENSOR-B4-I12R2 · Branch: `agent/crypto-sensor-fabric-build`
> Start HEAD: `76042ca4c4abf17884980fca84a7aa1ba2d680c6` · Research: FROZEN · I13+: UNAUTHORIZED

Operator review of the sealed I12 → I12R1 chain (PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED
= PENDING_OPERATOR_REVIEW) found two remaining blockers in source review. Both were
REPRODUCED failure-first, then repaired, then re-measured end-to-end through
`RawEvidenceQueryService.execute()`.

---

## 1. BLOCKER A — default ERROR_ON_AMBIGUITY bypassed the I06 authority

### Reproduction (failure-first, recorded before any repair)

Fixture: two acquisitions under ONE source identity (`request_fingerprint="fp-rev"`,
distinct bytes, strictly later `response_observed_at` for the second), one manifest
referencing both blobs. Service constructed with `manifest_repository`,
`acquisition_repository`, `blob_metadata_repository` only — `revision_registry=None`.

```
svc.execute(RawEvidenceQuery())   # default revision_policy=ERROR_ON_AMBIGUITY

DEFECT CONFIRMED: returned 1 result(s) with
  acquisition_ids=['acq-r1', 'acq-r2']
  (two revisions exist under one source key; ambiguity was NEVER raised)
```

The pre-I12R2 `execute()` gate refused an unwired service only when the query carried
an explicit non-default policy (or an exact revision number); the default policy was an
explicit pass-through — both revisions returned with no I06 authority consulted.

### Why it is a defect

ERROR_ON_AMBIGUITY is itself a revision-RESOLUTION policy. It cannot be honored
without the authority whose ambiguity it is supposed to detect. A fail-safe default
must refuse, not pass through.

### Exact repair

`RawEvidenceQueryService.execute()` (I12R2 §3):

```
if self._revision_registry is None:
    raise RevisionAuthorityUnavailable(...)
```

for EVERY policy — no default-policy exception, no compatibility switch
(`allow_unresolved_revisions` / `unsafe_revision_passthrough` / `legacy_mode` do not
exist on the public constructor; §5). Historical tests that constructed incomplete
services were repaired in the TEST HARNESS, never in runtime semantics.

### Typed failure choice (§7)

New narrow type `RevisionAuthorityUnavailable(QueryValidationError)` — preferred over
widening `RevisionPolicyInvalid`, so the R1 meaning of the latter stays unchanged.
The refusal is a service configuration/authority failure and is deliberately NOT
mapped to `StorageBackendUnavailable`, `NoMatchingEvidence` or `RevisionAmbiguity`.

### Post-fix measured behavior

See `BLOC_04_I12R2_AUTHORITY_REQUIRED_MATRIX.json`: unwired default/FIRST_SEEN/
EXACT/ALL all refuse with the same typed class; wired single-revision default
succeeds through registry resolution (`acq-s1`, revision_state STABLE); wired
two-revision default raises `RevisionAmbiguity` — the authority is actually
CONSULTED; `limit=1` cannot suppress it.

## 2. BLOCKER B — requested T0B silently disappeared (T0A fallback)

### Reproduction (failure-first, recorded before any repair)

Fixture: one blob/acquisition, committed projection `proj-1` (schema
`i12.test.projection`), manifest with `projection_refs=["proj-1"]`; fully wired service.

```
svc.execute(RawEvidenceQuery(
    include_t0a=True, include_t0b=True,
    projection_schema_ids=["nonmatching.schema"]))

DEFECT CONFIRMED: blob_refs=['53cf...'] (valid T0A returned)
  projection_refs=[] (requested T0B silently gone)
```

### Why it is a defect

`include_t0b=True` is an explicit caller requirement. A result with no T0B looks like
the complete query succeeded.

### Exact repair (representation-satisfaction law, §9-§13)

- `include_t0b=True` ⇒ every published result carries ≥1 eligible selected T0B
  projection; otherwise `ProjectionSchemaUnsupported` — for T0B-only AND
  both-representations queries (the I12R1 §10 option-A fallback is superseded).
- `projection_schema_ids=[]` + `include_t0b=True` still requires one otherwise-valid
  T0B projection; a nonempty filter requires a matching schema id.
- Publication-boundary structural assertion: `include_t0a=True` ⇒ nonempty
  `blob_refs`; `include_t0b=True` ⇒ nonempty `projection_refs`.
- No new partial-failure vocabulary was added to `RawEvidenceResult` (§9).
- No T0A fallback, no unrelated projection substitution.

### Post-fix measured behavior

See `BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json`: the full include-flag
truth table, both schema-mismatch refusals, no-projection refusal, lineage-broken
refusal (adversarial mutation), and §14 T0A-only wiring determinism.

## 3. Superseded I12R1 artifact row — append-only correction

The I12R1 `REPRESENTATION_SELECTION` matrix contained the row
`schema_mismatch_with_T0A_fallback_documented` measuring the option-A fallback as
accepted behavior. Operator review superseded that behavior (§12), so the SAME
accepted I12R1 builder now measures
`schema_mismatch_with_both_requested_fails_typed` = OK (`ProjectionSchemaUnsupported`).

- The I12R1 evidence MODULE changed only on that row; the artifact was regenerated
  mechanically by the accepted builder (`UPDATE_I12R1_EVIDENCE=1`), not hand-edited.
- All four other I12R1 matrices are byte-identical to the I12R1 publication.
- All original I12 artifacts are byte-identical.
- The superseded R1 test `test_projection_schema_mismatch_t0a_fallback_documented` was
  replaced by `test_projection_schema_mismatch_with_both_requested_fails_typed`.
- QueryOutcome doc corrected (§15): `execute()` RAISES `NoMatchingEvidence`; the
  `no_matching_evidence` flag is only True on success-with-no-results semantics.

## 4. Typed error mapping table (post-I12R2, crossing the I12 boundary)

| Origin (I06 / configuration) | I12 typed error | `__cause__` preserved |
|---|---|---|
| Service constructed without `revision_registry` (ANY policy) | `RevisionAuthorityUnavailable` | n/a (direct refusal) |
| `RevisionAmbiguityError` / `RevisionTemporalAmbiguity` | `RevisionAmbiguity` | yes |
| `RevisionNotFound` | `NoMatchingEvidence` | yes |
| `RevisionResolutionUnavailable` | `RevisionCanonicalUnavailable` | yes |
| `RevisionConfigurationError` / `SourceRevisionCatalogCorrupt` | `RevisionPolicyInvalid` | yes (FUTURE HARDENING: naming is imperfect but fail-closed; retained per §16) |
| T0B chain broken / lineage unreadable | `LineageIncomplete` | yes |
| No eligible T0B while `include_t0b=True` | `ProjectionSchemaUnsupported` | n/a |

Epistemic ambiguity ≠ backend unavailable; missing revision ≠ corruption;
registry corruption ≠ no-match; authority absence ≠ evidence content.

## 5. Counts

- I12R2 focused suite: 20 tests (authority 9, representation 8, T0A-wiring 2, outcome contract 1) — all passing, 0 skips.
- I12R2 matrices: AUTHORITY_REQUIRED 9 rows / 8 OK / 1 synthetic FAIL;
  REPRESENTATION_SATISFACTION 11 rows / 10 OK / 1 synthetic FAIL.
