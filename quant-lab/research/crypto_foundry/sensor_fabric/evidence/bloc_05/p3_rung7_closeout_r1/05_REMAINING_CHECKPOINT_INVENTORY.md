# 05 - Remaining Bloc 5 checkpoint inventory

Source of authority: `bloc_05/07_BLOC_05_FREEZE_MANIFEST.md` §10 (frozen future
implementation sequence), read together with `bloc_05/06_ACCEPTANCE_TESTS_AND_
STAGED_IMPLEMENTATION_COMMITS.md` §19 and the readiness assessments already on
record. Nothing here is new architecture or a new plan; it is the frozen
sequence with its measured state.

**Scope note.** These are the normalization checkpoints `I12`-`I23`. The storage
series with overlapping numbers (`test_i11_postgres_metadata`,
`test_i13_export_restore`, `test_i15r2_*`) belongs to the Bloc 4 storage track
and is not the same checkpoint set; it is reused, not renumbered.

**Current position.** `I01`-`I11` are implemented and evidenced
(`consumer/` is the P3 rung series, `sensors/` holds `trade.py` and
`liquidation.py`). `I12` has a frozen contract and a readiness assessment but no
code. `I13`-`I23` have contracts and schemas only. Per sensor, `sensors/`
contains no `oi.py`, `funding.py`, `book.py`, `positioning.py` or `basis.py`, and
`normalization/` has no `lineage/`, `duplicates/`, `query/` package.

**Gate state** (read from existing evidence, not re-measured):

| Gate | State | Blocking checkpoint |
| --- | --- | --- |
| `IDENTITY_GATE` | satisfied by `I01`-`I04` evidence | - |
| `TIME_GATE` | satisfied by `I05`-`I07` evidence | - |
| `SEMANTIC_GATE` | satisfied for trade/liquidation; open for remaining sensors | `I12`-`I15` |
| `UNIT_GATE` | primitives implemented; `B5_I08_UNITS_V1` not admitted in the PROVISIONAL methodology registry (I08 ratification L4) | `I12` for `oi_usd`, `I13` for rate-based USD |
| `LINEAGE_GATE` | not met | `I16` |
| `DUPLICATE_REVISION_GATE` | not met | `I17` |
| `REPLAY_SAFETY_GATE` | gate implemented at `I05`/`I06`; record-level binding contract deferred | `REPLAY_EVIDENCE_RECORD_BINDING_V1` |
| `GOLDEN_T0_T1_GATE` | not met | `I22` |

---

## I12 - OI normalizer

- **Current state.** Not implemented. Frozen contract `04` §4.1-§4.4, schema
  snapshot `MechanicalOpenInterest.schema.json`, readiness assessment
  `BLOC_05_I12_READINESS_ASSESSMENT.md` = `READY_TO_IMPLEMENT_WITH_BLOCKS`.
- **Dependencies.** `I09` `ProviderSemanticMapping` read from the registry with
  critical-use confidence (never caller-supplied); `I04B` conversion primitives;
  `I04` PIT contract terms; `I05` availability/replay gate; `B5_I08_UNITS_V1`
  methodology admission for `oi_usd`; provider evidence for native-unit
  semantics.
- **Remaining work.** Eight-field envelope; unit-honesty branches (contracts,
  base, quote, USD-native, provider-specific); map the `02` §4 classification
  into the five-member field vocabulary without merging the two enums; measured
  zero with coverage provenance admitted, defaulted or gap-filling zero refused;
  multi-venue aggregate never assigned to one venue; contract-denominated
  conversion requires PIT terms; the §9 refusal surface with named codes;
  I09-backed semantic admission (the `I11F1` pattern, **not** I11's Boolean
  side-certification); tests plus adversarial matrix.
- **Acceptance.** Scope-audit amendment for `I12`; mechanical republish of
  `python_files_scanned` after staging, never by hand; canonical run (serial,
  ~27 min at 4,968 nodes plus the new nodes); independent targeted reattack.
- **Parallel.** **Yes** with `I13` and `I15`. Coordinate only on
  `sensors/__init__.py` and the shared semantic-admission helper. `oi_usd` stays
  blocked, so it does not wait on I08 resolution.

## I13 - Funding normalizer

- **Current state.** Not implemented. Schema snapshot
  `MechanicalFunding.schema.json`; frozen decisions `F14`, `F20`.
- **Dependencies.** `I05` interval/time registry and availability; `I08` rate and
  basis-point primitives; `I09` semantic admission; provider funding-interval and
  cap semantics from the probe registry.
- **Remaining work.** Native vs predicted vs effective vs realized funding kept
  separate and never collapsed; interval length and `interval_end_at` carried;
  rate applied to a named notional without inventing a USD figure while
  `B5_I08_UNITS_V1` is unadmitted; refusal of a funding row carrying flow or PnL
  semantics; tests plus adversarial matrix.
- **Acceptance.** As `I12` - scope audit, mechanical inventory republish,
  canonical run, targeted reattack.
- **Parallel.** **Yes** with `I12`/`I15`; no shared code with them beyond the
  admission helper.

## I14 - Book / book-metric normalizer

- **Current state.** Not implemented. Schema snapshots
  `MechanicalBookSnapshot.schema.json`, `MechanicalBookMetric.schema.json`; frozen
  decision `F21` (book reconstruction fails on sequence gaps).
- **Dependencies.** Book-depth source data with sequence numbers; `I05` interval
  and availability; `I09` semantics; `I04B` for any notional conversion.
- **Remaining work.** Snapshot normalizer; sequence-gap detection that fails
  closed instead of interpolating; derived metrics (spread, depth, imbalance)
  each carrying methodology and lineage; refusal of a metric computed across a
  gap; tests plus adversarial gap matrix.
- **Acceptance.** As `I12`, with the added requirement that the sequence-gap
  adversarial matrix is part of the acceptance evidence, not an optional extra.
- **Parallel.** **Partly** - the module can be authored alongside `I12`/`I13`/
  `I15`, but acceptance needs book fixtures with controllable sequence gaps, so
  expect it to finish in the second wave.

## I15 - Positioning and basis normalizers

- **Current state.** Not implemented. Schema snapshots
  `MechanicalPositioning.schema.json`, `MechanicalBasis.schema.json`; frozen
  decisions `F22` (population definition) and `F23` (basis reference identity and
  units).
- **Dependencies.** `I09` semantic admission; `I04B` units; the frozen five-type
  reference-price vocabulary with `market_available_at <= cutoff`;
  `F24` no cross-venue synthesis at T1.
- **Remaining work.** Positioning with explicit long/short population
  definition; basis carrying reference instrument identity, units and PIT price
  lineage; refusal of a type-substituted or late reference price; refusal of any
  cross-venue synthesis; tests plus adversarial matrix.
- **Acceptance.** As `I12`.
- **Parallel.** **Yes** with `I12`/`I13`; two independent modules, one scope
  audit.

## I16 - Lineage and deterministic T1 IDs

- **Current state.** Not implemented. No `normalization/lineage/` package; frozen
  decisions `F25`, `F29`; `LINEAGE_GATE` not met.
- **Dependencies.** Complete T0 lineage carried by every implemented T1 row
  (`I10`/`I11` today, `I12`-`I15` for full coverage); `I05` evidence models.
- **Remaining work.** Lineage graph with completeness assertions; deterministic
  content-addressed T1 IDs stable across runs and machines; immutability law for
  published generations; tests including a re-run-identical-IDs property.
- **Acceptance.** `LINEAGE_GATE` PASS over every implemented T1 row; scope audit;
  canonical run; targeted reattack focused on ID stability and lineage
  completeness.
- **Parallel.** **Partly** - author the module in wave 1 against `I10`/`I11`, but
  gate closure must wait for `I12`-`I15` or the gate would pass on a partial
  sensor set.

## I17 - Duplicate and revision engine

- **Current state.** Not implemented. No `normalization/duplicates/` package;
  frozen decisions `F26`-`F29`; `DUPLICATE_REVISION_GATE` not met.
- **Dependencies.** `I16` deterministic IDs (**hard** - dedupe keys on identity);
  `I07` revision policies (`revision_policies.yaml` exists); storage dedupe
  primitives from the Bloc 4 track.
- **Remaining work.** Hard-duplicate vs soft-candidate strength classes; the law
  that cross-venue events are never deduped by similarity; append-only revisions;
  immutable generations; refusal paths for contradiction.
- **Acceptance.** `DUPLICATE_REVISION_GATE` PASS; scope audit; canonical run;
  targeted reattack on the cross-venue non-dedup law specifically.
- **Parallel.** **No** - strictly after `I16`. Running it earlier would key
  duplicates on provisional identity.

## I18 - T1 generation writer, manifests and atomic publish

- **Current state.** Not implemented for T1 generations. Bloc 4 storage
  primitives that it will reuse are implemented and evidenced: blob store,
  catalog, checksums, compression, atomic publication, concurrent-publication
  guards, export/restore.
- **Dependencies.** `I16` + `I17`; the reviewed generation-manifest schema from
  `I09`; storage primitive contracts.
- **Remaining work.** Generation writer, manifest hashing and pinning, atomic
  publish, immutability enforcement, failure-rollback behaviour; tests reusing
  the storage adversarial suite rather than duplicating it.
- **Acceptance.** Generation reproducibility evidence plus storage-level
  adversarial tests; scope audit; canonical run; targeted reattack.
- **Parallel.** **No** - after `I17`.

## I19 - Canonical T1 query and strict research/replay filters

- **Current state.** Not implemented. No `normalization/query/` package; frozen
  decision `F30` (canonical research query boundary is mandatory).
- **Dependencies.** `I18` generation manifests; `I05`/`I06` replay eligibility and
  `AS_KNOWN_THEN` policy.
- **Remaining work.** The canonical query boundary, strict filters, and the law
  that research cannot reach T1 outside it; leakage tests proving a later
  revision cannot be returned for an earlier cutoff.
- **Acceptance.** Replay/leakage matrix; scope audit; canonical run; targeted
  reattack on leakage specifically.
- **Parallel.** **No** - after `I18`.

## I20 - Provider golden semantic fixtures

- **Current state.** Not started as a corpus. Provider documentation briefs
  (`BLOC_05_I06_PROVIDER_DOCUMENTATION_COLLECTION_BRIEF.md`) and the probe
  registry exist.
- **Dependencies.** `I09` registry rows; the normalizers the fixtures exercise
  (`I10`-`I15`); provider documentation.
- **Remaining work.** Checksum-pinned offline fixtures covering at least three
  providers, BTC plus an alt, linear plus inverse contracts, and each sensor
  family; each fixture states what semantic claim it proves.
- **Acceptance.** Fixtures ratified as golden evidence with pinned checksums -
  this is where a provider semantics claim becomes admissible, so it needs
  operator-visible review, not only a green suite.
- **Parallel.** **Yes** for authoring across waves 1-2; **ratification** waits
  for `I12`-`I15`.

## I21 - PIT, leakage, property and regression tests

- **Current state.** Partially present as per-checkpoint tests; not yet the
  cross-cutting suite the sequence calls for.
- **Dependencies.** Every normalizer (`I10`-`I15`); `I16`-`I19` for end-to-end
  properties.
- **Remaining work.** PIT/leakage properties, invariant properties (native value
  survival, non-destruction, refusal determinism), and a regression corpus that
  pins the refusal surface.
- **Acceptance.** Contributes to `TIME_GATE`, `LINEAGE_GATE`,
  `DUPLICATE_REVISION_GATE` and the replay gate; no gate closes on it alone.
- **Parallel.** **Yes**, continuously alongside every wave.

## I22 - T0→T1 golden replay slice and checksum evidence

- **Current state.** Not started. `GOLDEN_T0_T1_GATE` not met.
- **Dependencies.** `I18` writer, `I19` query boundary, `I20` fixtures, `I21`
  properties.
- **Remaining work.** One checksum-pinned end-to-end offline T0→T1 slice with
  reproduction instructions, exercising the fixture matrix from the freeze
  manifest §12.
- **Acceptance.** `GOLDEN_T0_T1_GATE` PASS; canonical run; independent
  reproduction of the checksum.
- **Parallel.** **No** - near-terminal, after `I19`/`I20`.

## I23 - Acceptance report and Bloc 6 handoff

- **Current state.** Not started.
- **Dependencies.** All of `I01`-`I22`.
- **Remaining work.** The Bloc 5 acceptance report and the Bloc 6 handoff, in the
  shape of the existing operator ratification packages.
- **Acceptance.** Operator decision. This checkpoint cannot be closed by the
  producer alone.
- **Parallel.** **No** - final.

---

## Deferred integration contract A - `REPLAY_EVIDENCE_RECORD_BINDING_V1`

- **Current state.** Named, guarded, **not implemented**.
  `REPLAY_RECORD_BINDING_ESTABLISHED = False`; unbound evidence terminates in
  `INTEGRATION_REQUIRED` naming the contract; `replay_status = "NOT_BOUND"` is
  explicit, never an implicit pass.
- **Dependencies.** The I05 replay **producer** must mint a versioned schema that
  carries `record_id`, `provider`, `record_kind`, `artifact_id` and the artifact
  evidence digest; the operator must approve that schema version. The consumer
  must not infer these from the record under test.
- **Remaining work.** Mint the schema; implement binding in
  `TrustConsumerPolicy._bind_replay`; retire `NOT_BOUND` and
  `UNRESOLVED_REPLAY_BINDING`; flip `REPLAY_RECORD_BINDING_ESTABLISHED`; re-run
  the five reconciled positive controls as the acceptance gate.
- **Acceptance.** One positive control (evidence minted for this record,
  provider, kind and artifact, all known at the cutoff) and six negatives, each
  refusing with a named code: a row copied from another record of the same
  provider; the same record under a different provider; the same artifact under a
  different kind; a row from another artifact; matching record id with a
  mismatched artifact digest; evidence missing any new field.
- **Parallel.** **Yes** - independent of `I12`-`I15`, and should not be bundled
  with a sensor release. It spans one producer schema and one consumer
  implementation, so it is one reviewed contract, not a background change.

## Deferred integration contract B - `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1`

- **Current state.** Unresolved and **unimplemented**. No field exists for a
  custody source in `ApprovalManifest` or `ApprovedArtifact`; every input,
  including a synthetic complete approval, derives `INTEGRATION_REQUIRED`.
- **Dependencies.** An operator-signed record type held at the same authority
  level as the manifest and bound to it by `manifest_sha256`, naming the source,
  the store, the operating entity, the record kinds and providers it covers, and
  its validity window.
- **Remaining work.** Define the record; extend the derivation path and the
  policy's composition step; keep the empty-manifest path as the default; add
  tests that no configuration flag, environment variable or test seam can
  synthesize the record.
- **Acceptance.** One positive (authorized source, authorized kind and provider,
  inside its validity window, approved artifact, matching identity digest) and
  seven negatives, each refusing rather than downgrading: unlisted source; listed
  source outside its granted kinds; provider outside its grant; revoked or
  expired record; approved artifact with an unauthorized source; matching source
  bound to a different `manifest_sha256`; an `AUTHORIZED` derivation whose
  `identity_sha256` disagrees with the identity the policy built.
- **Parallel.** **Yes** in principle, but the record is operator-authored: no
  amount of engineering can complete it, and engineering must not approximate it.

---

## Suggested continuation order after D1

| Wave | Work | Why this order |
| --- | --- | --- |
| 1 | `I12`, `I13`, `I15` in parallel; author `I16` against `I10`/`I11`; start `I20` fixture authoring; continue `I21` | Independent sensor modules over existing primitives; no cross-dependency |
| 2 | `I14` acceptance with sequence-gap fixtures; close `I16` once `I12`-`I15` are in; ratify `I20` | `I16`'s gate must not pass on a partial sensor set |
| 3 | `I17`, then `I18`, then `I19` | Hard chain: identity -> dedupe -> generation -> query |
| 4 | `I22`, then `I23` | End-to-end evidence, then the acceptance report |
| Parallel lane | Contract A, then Contract B | Independent of the sensor waves; both are authority acts, not releases |

**Host constraint.** Implementation branches can proceed in parallel, but
canonical verification on this host is serial only: one worker, 5,400 s
partition timeout, ~27 minutes for the current 4,968 nodes before the new
checkpoints add more. Four workers produced a truncated bundle and 42 concurrency
artifacts in an earlier attempt and remain unsupported. Budget one canonical run
per merged checkpoint, not one per branch.

**Parallelism that is not available.** No checkpoint in this list may be merged
with another for review convenience: the freeze manifest forbids squashing during
staged review, and each checkpoint needs its own scope audit and inventory
republish.
