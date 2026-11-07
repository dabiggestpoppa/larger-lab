# SENSOR-B5-I09P2b - TRUSTED INITIALIZATION, RECORD VERIFICATION, PIT PROVENANCE

**Status:** IMPLEMENTATION COMPLETE (BOUNDED) - HARD STOP, NOT RATIFIED
**Checkpoint:** `SENSOR-B5-I09P2b` (bounded authority boundary; `B5-I09b` real-provider
certification remains unauthorized and untouched)
**Custody base:** `fa758874ea766eebcb3a6d31ade09b7dece6f4ae`
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Prior:** I09P2a = `IMPLEMENTATION_COMPLETE`, ratification `I09P2A_RATIFICATION_HOLD`
(ledger sections 190-191). B5-I09a = OPERATOR_ACCEPTED; B5-I09b = DEFERRED; B5-I10 =
OPERATOR_ACCEPTED (bounded); B5-I11 = IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD.

---

## 1. Custody

```text
REPOSITORY   = dabiggestpoppa/larger-lab
BRANCH       = agent/crypto-sensor-fabric-build
HEAD         = fa758874ea766eebcb3a6d31ade09b7dece6f4ae  (= origin at start)
FROZEN PLAN  = 4bb677f9e0266f4dc48405181696019f359ae49f, untouched by this build
SCRATCH      = .bu_tmp/, evidence/bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md
               (2026-10-06), scripts/b5_i03_redteam_results.json (2026-10-09)
               -- untracked, pre-existing, never staged
SHIPPED ROOT = config/crypto_sensor_fabric/provider_semantics/approval_manifest.json,
               sha256 3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654,
               artifacts == {} (zero production approvals)
```

No reset, rebase, amend, squash or force-push. The delta is linear on `fa758874ea`.

## 2. RECONSTRUCT - the authority chain as it actually was

Read at source, not inferred from names:

* `manifest_bytes` and `artifact_bytes` were both supplied by the caller of
  `load_semantic_authority`; the loader verified their internal consistency only.
  Whoever supplied the artifact also supplied the approval of the artifact.
* No component in `src/` calls `load_semantic_authority` outside the authority
  package itself: this repository ships a normalization library, not an ingestion
  application. `src/crypto_sensor_fabric/` contains contracts, normalization,
  providers, registry, schemas, storage and probes only.
* `SemanticAuthority` guarantees: the artifact bytes hash to a digest an approval
  entry names, the entry's validity/revocation state, the registry version, and
  per-row coverage (methodology registered, evidence reference bound, declared
  native field, approved transformation, resolved blocking assumption).
* It does not guarantee that the manifest came from an independent actor, that
  the cited evidence documents exist, or that the approval was available at the
  instant the record is used.
* Records: `T1TradeRecord` carried no authority field at all; liquidation carried
  `admission_approval_id` + `admission_registry_digest` only, with no verifier.

## 3. RED - the contract that failed first

`tests/crypto_sensor_fabric/normalization/test_b5_i09p2b_trusted_root.py`
(24 tests, written before the implementation) failed first on exactly the gaps it
targets: no `load_trusted_authority`, no `MappingProvenance`, no
`verify_evidence_custody`, no `verify_mapping_provenance`, no `available_at`
enforcement, no `verify_liquidation_admission_provenance`, no
`authority_provenance` field on `T1TradeRecord`. They pass only against section 4.

## 4. IMPLEMENT - the trusted boundary

All new code lives in the already-authorized surfaces
`normalization/authority/__init__.py` and `normalization/sensors/trade.py`.

```text
TRUSTED_MANIFEST_RELPATH        config/crypto_sensor_fabric/provider_semantics/approval_manifest.json
TRUSTED_MANIFEST_SHA256         3d707c59...c7042654      (reviewed source constant)
TRUSTED_MANIFEST_SCHEMA_VERSION b5-i09p2a-1
load_trusted_authority(...)     -> SemanticAuthority, or TRUSTED_ROOT_MISMATCH
MappingProvenance               -> serialized audit trail (NOT authentication)
verify_mapping_provenance(...)  -> re-derives a trade record's admission
verify_liquidation_admission_provenance(...) -> same, for LiquidationSideAdmission
verify_evidence_custody(...)    -> evidence reference -> held blob digest
```

The bootstrap anchor is a constant in reviewed source, so no manifest can
authenticate itself with a hash it contains. No second configuration file was
added (the I10 "no non-manifest file" custody rule is intact) and the frozen
empty manifest still admits nothing: `artifacts == {}` refuses with `NO_APPROVAL`
inside the delegated loader.

Deployment assumption, stated plainly: the constant is only as strong as review
of the commit that changes it. This is a data boundary inside one process; it is
not a signature scheme and does not resist code running with the application's
privileges. No operator identity, signing key or approval history was invented.

## 5. G7 - exported record provenance

`T1TradeRecord.authority_provenance` is populated only when the canonical side
was admitted through an issued authority, carrying approval id, registry digest,
artifact id, provider, native field, canonical field, canonical sensor,
methodology id/version, evidence reference, semantic confidence and the approval
and availability instants.

A consumer calls `verify_mapping_provenance(record.authority_provenance, ...)`
with the independently held root, artifact bytes and evaluation instant. The
verifier reloads the authority under the pinned root and refuses
`PROVENANCE_MISSING` / `PROVENANCE_MISMATCH` rather than believing the record's
declared digest.

Liquidation reuses `LiquidationSideAdmission`: its approval id and registry
digest must equal the trusted root's, and the row must resolve uniquely by
(canonical field, provider field, methodology, version). Ambiguity refuses.

**Limit:** serialized provenance is an audit trail, not a signature. Nothing in
the stored envelope proves a field was genuinely read from the provider; that
remains an external source-lineage limitation and an operator review obligation.

## 6. Storage-blob evidence binding

`ApprovedArtifact.evidence_blobs` binds every approved evidence reference to the
SHA-256 of the source document held under custody, and its construction law
refuses a blob key that is not already bound in `evidence`. `verify_evidence_custody`
refuses a missing blob, a swapped digest, and a reference that no approval covers.

**Limit (disclosed, not papered over):** the repository holds no evidence-blob
store, so the custody map is supplied by the deploying process's storage
inventory. The binding is enforceable and independently checkable; it does not
ship a warehouse. Custody proves existence and integrity, never provider
authorship. No venue is certified by this checkpoint.

## 7. PIT authority revision

`available_at` is an approval-entry field; `load_semantic_authority` refuses
`APPROVAL_NOT_YET_AVAILABLE` when the evaluation instant precedes it and
`EVALUATION_TIME_REQUIRED` when an availability-bearing approval is applied
without one. The loader never reads a wall clock.

**Limit (disclosed):** availability is ISO `YYYY-MM-DD` and comparisons are
date-granular. Sub-day and timezone-bearing instants are not accepted, so no
timestamp is silently reinterpreted. Event time, observation time, acquisition
time, approval time and knowledge cutoff remain distinct fields; none is
substituted for another.

## 8. I10 and I11 nonregression

No behavior changed in either sensor. I10 keeps provisional Binance side without
approved mapping, canonical aggressor UNKNOWN when unadmitted, native and I04B
conversions untouched, USD notional still blocked on `B5_I08_UNITS_V1`, no I17
collapse. I11 keeps four-way side separation, per-field admission, contradiction
quarantine, five aggregation scopes, count/event identity, zero-vs-missing, PIT
arithmetic, maker/taker gating and USD refusal. The full I10/I11 suites pass
unchanged. No fixture was rewritten to accommodate this build.

## 9. Adversarial results

```text
FIXTURE (all synthetic, labelled)            EXPECTED                    OBSERVED
untrusted manifest through trusted entry     TRUSTED_ROOT_MISMATCH       refused
same-actor artifact + manifest (low loader)  issues authority (residual) documented
changed pin / other generation               TRUSTED_ROOT_MISMATCH       refused
empty production manifest                    NO_APPROVAL                 refused
evidence blob missing / swapped              EVIDENCE_BLOB_UNVERIFIED    refused
unbound blob key declared in manifest        MALFORMED_MANIFEST          refused
approval used before available_at            APPROVAL_NOT_YET_AVAILABLE  refused
availability without evaluation instant      EVALUATION_TIME_REQUIRED    refused
record without provenance                    PROVENANCE_MISSING          refused
mutated approval id / registry digest /       PROVENANCE_MISMATCH        refused
  canonical field / confidence /                                          (6 cases)
  methodology / evidence reference
liquidation admission without identity       PROVENANCE_MISSING          refused
mutated liquidation registry digest          PROVENANCE_MISMATCH         refused
```

## 10. Tests actually executed in this checkpoint

```text
new P2b suite                    24 passed (exit 0)
normalization package sweep    1124 passed (exit 0)
  includes P2a loader 32, I05/I06/I09, I10, I11 E1/R1/F1, I04B,
  scope audits, unauthorized-module probes and custody rows
I05 producer                   86 rows, 0 fail (artifact byte-identical)
I06 producer                   14 rows, 0 fail (artifact regenerated, pin disclosed)
I09 producer                   35 rows, 0 fail, --check exit 0 (artifact regenerated)
ruff / mypy                    clean on changed production
```

The full canonical regression is recorded in ledger section 192.

## 11. Custody and pin cascade

```text
test_b5_i10_scope_audit.py     allowlist extended by one named entry
                               (test_b5_i09p2b_), disclosed inline
b5_i06_replay_safety.py        P2B_DISCLOSED_SHA256 appended; P2A/I08/I09/I10
                               pins preserved unmodified, P2B merged last
bloc_05_time_validation.json   unchanged (its inventory does not name I10)
bloc_05_replay_safety_validation.json  regenerated (own inventory line)
bloc_05_semantic_validation.json       regenerated (authority module inventoried)
```

Producers ran in dependency order (I05 -> I06 -> I09). No sealed assertion was
weakened and no historical pin was rewritten. I11R2 governance counts were
republished only after staging.

## 12. P2B-01 .. P2B-24

```text
GATE    EXPECTED                         OBSERVED                                 RESULT   LIMITATION
P2B-01  clean tree at fa758874ea          HEAD == origin at start                  PASS
P2B-02  frozen plan untouched             no plan file in the delta                PASS
P2B-03  root independent of manifest      pin constant in reviewed source          PASS     review-dependent
P2B-04  zero shipped approvals            artifacts == {}, admits nothing          PASS
P2B-05  manifest/artifact separated       two objects, no shared proof             PASS
P2B-06  caller self-approval refused      TRUSTED_ROOT_MISMATCH                    PASS
P2B-07  approval integrity enforced       digest/revocation/validity in loader     PASS
P2B-08  registry version compatible       schema pin + registry version check      PASS
P2B-09  methodology binding               unregistered methodology refused         PASS
P2B-10  provider/evidence binding         declared native field + evidence ref     PASS
P2B-11  evidence blobs under custody      ref -> sha256, missing/swap refused      PARTIAL  custody map supplied by deployer
P2B-12  PIT revision admissible           available_at gate before digest          PARTIAL  date granularity only
P2B-13  trusted initialization            load_trusted_authority interface         PARTIAL  no application in repo
P2B-14  I10 consumer safety               I10 suites unchanged                    PASS
P2B-15  I11 consumer safety               I11 suites unchanged                    PASS
P2B-16  trade-record provenance           authority_provenance populated           PASS
P2B-17  liquidation-record provenance     approval id + digest + unique row        PASS     provider resolved by row identity
P2B-18  downstream verification           both verifiers re-derive under root      PASS
P2B-19  forged-record mutation refusal    10 mutation cases refuse                 PASS
P2B-20  historical evidence custody       predecessor pins preserved                PASS
P2B-21  determinism                       producer --check exit 0, repeats equal   PASS
P2B-22  full canonical regression         see ledger section 192                   PASS
P2B-23  no program-gate promotion         all eight gates unchanged                PASS
P2B-24  fast-forward Git custody          linear commit, local == remote           PASS
```

## 13. Disposition

`I09P2B_IMPLEMENTATION_PARTIAL`.

The mechanical layer is real: an untrusted actor cannot self-approve, records
carry a provenance a consumer re-derives rather than believes, evidence
references bind to held bytes, and PIT availability is enforced. Three gates stay
partial for disclosed, structural reasons, and none of them can be closed by
writing more code in this checkpoint:

1. P2B-11 - the repository holds no evidence-blob store, so custody is verified
   against the deploying process's inventory.
2. P2B-12 - availability is date-granular by the accepted I05/I06 conventions.
3. P2B-13 - no production application or ingestion initializer exists in this
   repository, so the trusted entry point is an interface plus integration
   contract, not a wired end-to-end boundary.

Calling this a PASS would assert a trusted application integration that does not
exist in the tree, which the directive forbids. Nothing here certifies a venue,
resolves the USD methodology, implements I12, collapses I17 or promotes a
program gate. I09P2a and I11 remain NOT OPERATOR_ACCEPTED and NOT RATIFIED.

Independent ratification follows.
