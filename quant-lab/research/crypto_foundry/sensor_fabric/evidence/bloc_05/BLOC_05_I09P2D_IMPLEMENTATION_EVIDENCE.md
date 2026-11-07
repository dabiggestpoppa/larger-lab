# SENSOR-B5-I09P2d - CUSTODY AUTHORITY, SCOPED VERIFICATION AND PIT FAIL-CLOSURE

**Checkpoint:** SENSOR-B5-I09P2d
**Starting HEAD:** `0f0b3195b43a47b88896ef8d1cfa49e2568a581e`
**Entering disposition:** `I09P2C_RATIFICATION_HOLD`
**Authoritative finding:** `BLOC_05_I09P2CR1_INDEPENDENT_AUDIT.md`
**Disposition:** `I09P2D_IMPLEMENTATION_PARTIAL`

---

## 1 - Scope

Four measured defects were repaired in the existing verification and authority
modules. Nothing else was widened:

* no real provider certification, and the production manifest still approves
  zero artifacts;
* no fabrication of provider documentation or evidence blobs;
* no liquidation transformation invented (the honest `False` is preserved);
* no ingestion application, no I11 ratification, no I12/I17 work, no program
  gate promotion;
* every synthetic approval, registry and blob in the tests is labelled
  synthetic and certifies nothing about a real venue.

Authorized production surfaces, all minimal:

| Path | Change |
|---|---|
| `src/crypto_sensor_fabric/normalization/authority/__init__.py` | adds `evidence_digest()` (+20 lines, CRLF preserved) |
| `src/crypto_sensor_fabric/normalization/sensors/verification.py` | custody protocol, scoped result, result laws, PIT closure (+218/-28) |
| `tests/.../test_b5_i09p2c_record_verification.py` | custody fixture holds BYTES instead of digests |
| `tests/.../test_b5_i10_scope_audit.py` | one disclosed authorized-prefix entry for the new suite |
| `tests/.../test_b5_i09p2d_custody_scope_pit.py` | new independent 40-test security suite |

---

## 2 - RED reproduction of the four findings

Measured against `0f0b3195b4` before the repair, with the synthetic P2c fixtures:

| Finding | Probe | Observed on `0f0b3195b4` |
|---|---|---|
| F-R1-01 | object with only `held_digest()` returning the approved digest | `custody_verified=True`, `downstream_trusted=True` |
| F-R1-02 | venue / instrument / contract / revision / acquisition substitution | `VERIFIED`, `downstream_trusted=True`, no statement of what stayed unauthenticated |
| F-R1-03 | `RecordVerification(downstream_trusted=True, custody_verified=False)` | constructed and serialized |
| F-R1-04 | approval with neither `available_at` nor `available_at_instant` | verified at an arbitrary earlier cutoff |

Each row now has a named test in the P2d suite (`SEC-D01`, `SEC-D15..D18`,
`SEC-D11..D13`, `SEC-D21`).

---

## 3 - Custody is bytes, not a self-report

`TrustedCustodyProvider` now requires

```
read_evidence(reference: str) -> bytes | None
```

and the verifier hashes what it receives through `authority.evidence_digest`,
which is the module that owns digest verification. The digest is therefore no
longer something a custody object can assert about itself: satisfying the
boundary requires the approved bytes, and producing them from other bytes is a
preimage search. The pure sensor layer still imports no `hashlib`.

`BlobStoreCustody.read_evidence` re-verifies the stored object and then reads
its bytes; `held_digest()` survives as an operator-inspection convenience that
hashes the bytes actually read, and the verifier never calls it.

Three claims are now separate, and the result says which one holds:

* `custody_verified` - the approved bytes were handed over and hash to the
  approved digest (`BLOB_INTEGRITY_VERIFIED`);
* `custody_source_authorized` - an independently controlled application owns
  that store. **Always `False` here**: this repository has no such initializer,
  so operational custody stays unearned;
* `source_lineage_verified` - never claimed; authorship is not integrity.

---

## 4 - Counterfeit and tamper results

| Case | Attack | Result |
|---|---|---|
| CUST-01 | object exposing only `held_digest()` | `TypeError` (not a custody provider) |
| CUST-02 | plain `{reference: digest}` dict | `TypeError` |
| CUST-03 | wrapper/subclass that cannot hash bytes | `CUSTODY_UNVERIFIED` |
| CUST-04 | `BlobStoreCustody` over a store claiming integrity for other bytes | `CUSTODY_UNVERIFIED` |
| CUST-05 | missing object | `CUSTODY_UNVERIFIED` |
| CUST-06 | mutated object, index unchanged | `CUSTODY_UNVERIFIED` |
| CUST-07 | index naming another present blob | `CUSTODY_UNVERIFIED` |
| CUST-08 | bytes belonging to another provider | `CUSTODY_UNVERIFIED` |
| CUST-09 | source document unavailable at the cutoff | unresolved: no acquisition availability exists to assert (see 7) |
| CUST-10 | approved synthetic bytes held by a separate test store | `custody_verified=True`, `custody_source_authorized=False` |

---

## 5 - Scoped verification result (Option A)

`downstream_trusted` is retained with one machine-enforced meaning,
`trust_scope = "ECONOMIC_FIELD_BINDING"`: the declared canonical field was
re-derived from the approved mapping, bound to the preserved native evidence,
found PIT-admissible, and its approved evidence bytes hash to the approved
digest.

Every verdict additionally carries `unverified_dimensions`, which on this
evaluator is always:

```
SOURCE_LINEAGE, VENUE_IDENTITY, INSTRUMENT_IDENTITY,
SOURCE_REVISION, ACQUISITION_LINEAGE, CUSTODY_SOURCE_AUTHORITY
```

The laws refuse a downstream verdict with an empty list, so silence can no
longer read as whole-record authentication. Positive claims are gated on proof
references (`lineage_proof`, `instrument_authentication_ref`,
`revision_authentication_ref`), none of which this evaluator can produce.

---

## 6 - Result laws

`RecordVerification._trust_laws` refuses, at construction and at validation:

* `downstream_trusted` without approved mapping, verified transformation,
  verified custody, PIT admissibility, or any verified field;
* `downstream_trusted` with an empty `unverified_dimensions`;
* a dimension claimed authentic while listed unverified;
* `source_lineage_verified`, `instrument_authenticated` or
  `source_revision_authenticated` without the corresponding proof reference;
* any `trust_scope` other than `ECONOMIC_FIELD_BINDING`.

`model_copy(update=...)` is a documented Pydantic bypass and can still stamp an
invalid state; `assert_trustworthy()` re-validates the object's own payload and
raises `CONTRADICTORY_VERIFICATION`. Verifier-produced results pass it
unchanged. Consumers that accept a copied result as final evidence must call it.

---

## 7 - PIT fail-closure

`_assert_intraday_pit` now refuses `PIT_AVAILABILITY_MISSING` when an approval
states neither `available_at` nor `available_at_instant`: an approval with no
availability is admissible at no instant. Precedence and inclusivity are
unchanged otherwise: an instant-precise availability is authoritative and is
admissible at equality; a date-only availability refuses every instant on its own
day and admits later days; naive cutoffs, naive instants and expired/revoked
approvals refuse through the existing vocabulary.

Evidence-acquisition availability does not exist in the record model, so no
acquisition PIT claim is made and `ACQUISITION_LINEAGE` stays in
`unverified_dimensions` rather than being invented.

---

## 8 - Liquidation and prior behaviour preserved

* coordinated record+admission rewrite: `semantic_mapping_approved=True`,
  `record_transformation_verified=False`, `downstream_trusted=False`;
* canonical-only, admission-only and cross-field rewrites: refused;
* I10 (native trade evidence, Binance polarity, UNKNOWN aggressor, PIT
  conversions, `B5_I08_UNITS_V1` notional rule, no I17 collapse) and I11 (four
  side dimensions, per-field admission, contradiction quarantine, all-or-nothing
  promotion, five aggregation scopes, zero-versus-missing, count/identity
  coherence, linear and inverse PIT, maker/taker gating, unresolved USD
  methodology, unverified liquidation transforms) are unchanged, and their
  suites pass.

---

## 9 - Security suite

`tests/crypto_sensor_fabric/normalization/test_b5_i09p2d_custody_scope_pit.py`
adds 40 independent tests: custody identity and tampering (SEC-D01..D10), result
invariants, JSON reconstruction and copy bypass (SEC-D11..D14), unauthenticated
dimension reporting (SEC-D15..D18), liquidation economic uncertainty
(SEC-D19..D20), the PIT availability and timezone matrix including the DST
fall-back repeated hour (SEC-D21..D32), root emptiness and no new real-provider
approvals (SEC-D33..D34), determinism (SEC-D35) and sensor-layer hashing hygiene
(SEC-D36). No test skips or xfails a trust-boundary defect.

P2c's 43 tests still pass unchanged in substance; only the custody fixture was
ported from digests to bytes, because a digest-holding fixture would re-test the
defect.

---

## 10 - Historical custody and the pin cascade

* seven frozen Bloc 5 planning documents untouched;
* `authority/__init__.py` remains CRLF (0 bare LF); `verification.py`, the P2c
  and P2d suites remain LF; no wholesale reformatting;
* the I09 producer was regenerated in place because its declared inventory pins
  the authority module: artifact `845f1c660cd659dafc0e00503ce10264647eb0b9b85dd63db1b3ee6db77edde2`,
  35 rows, 35 pass, 0 fail, 3 unresolved (SEM-26/SEM-35 sequence unchanged);
* I05 `86/86/0` + scope `7/7` and I06 `14/14/0` + scope `8/8` reproduce without
  regeneration;
* the four `bloc_04` evidence side effects left by the whole-package suite were
  restored to their committed bytes and never staged;
* the production approval manifest is byte-identical: `artifacts == {}`, pin
  `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654`.

---

## 11 - Regression and static checks

Canonical suite: **4604 passed, 11 skipped, 0 failed across 11 file-partitioned chunks (4615 collected)**

Execution note: the canonical set was run as eleven file-partitioned chunks,
because single long invocations were terminated by the host mid-run (they
reached 74% without a summary). A first pass of the storage chunk recorded six
failures while a superseded run was still terminating; the same 31 files rerun
in isolation passed 462 with 4 skipped and no failure reproduced. The chunk
counts sum exactly to the 4615 collected tests.

Focused runs on the same tree: P2d 40 passed; P2c 43 passed; the `i09/i10/i11`
selection 532 passed / 5 skipped; governance binding 4 passed; ruff clean on the
four touched Python files; mypy reports only pre-existing provider/`numeric.py`
errors and nothing in the two production modules changed here.

---

## 12 - Acceptance matrix

| GATE | FROZEN_CLAUSE | EXPECTED | OBSERVED | TEST | RESULT | LIMITATION |
|---|---|---|---|---|---|---|
| P2D-01 | Git custody | start at `0f0b3195b4`, linear, no rewrite | local == remote at start | `git rev-parse` / `ls-remote` | PASS | none |
| P2D-02 | Frozen plan integrity | planning docs byte-identical | unchanged | `git diff` | PASS | none |
| P2D-03 | Reproduce four findings | each defect measurable pre-repair | all four reproduced | probes, then SEC-D01/D11/D21 | PASS | synthetic root |
| P2D-04 | Fake custody provider refusal | no trust from `held_digest()` alone | `TypeError` / `CUSTODY_UNVERIFIED` | SEC-D01..D04 | PASS | none |
| P2D-05 | Storage-handle authorization | an application-owned handle is required | not available; result reports `custody_source_authorized=False` | SEC-D10 | PARTIAL | no initializer exists in this tree |
| P2D-06 | Blob-integrity verification | verifier hashes the bytes itself | digest computed in `authority.evidence_digest` | SEC-D04/D06/D07 | PASS | none |
| P2D-07 | Scoped trust verdict | one declared scope, machine-enforced | `ECONOMIC_FIELD_BINDING` only | SEC-D10/D14 | PASS | none |
| P2D-08 | Unverified-dimension reporting | out-of-scope dimensions enumerated | six dimensions on every verdict | SEC-D15..D18 | PASS | none |
| P2D-09 | Result-model invariants | contradictory states unrepresentable | `ValueError` on construction | SEC-D11 | PASS | direct dict payloads |
| P2D-10 | JSON round-trip | reconstruction re-runs the laws | refused | SEC-D12 | PASS | none |
| P2D-11 | Direct-construction bypass | copy bypass detectable | `CONTRADICTORY_VERIFICATION` | SEC-D13 | PASS | consumer must call the guard |
| P2D-12 | No false lineage claims | lineage never asserted | `False` + note | SEC-D15..D18 | PASS | authorship unverifiable |
| P2D-13 | No false instrument/venue claims | preserved, not authenticated | `instrument_authenticated=False` | SEC-D15/D16 | PASS | approval names no instrument |
| P2D-14 | No false revision claims | revision data is not authentication | `False` | SEC-D17 | PASS | none |
| P2D-15 | Liquidation uncertainty | mapping may be approved, economics not verified | `downstream_trusted=False` | SEC-D19/D20 | PASS | no executable transform |
| P2D-16 | PIT missing availability | refuse | `PIT_AVAILABILITY_MISSING` | SEC-D21 | PASS | none |
| P2D-17 | PIT timezone/DST | instants ordered, DST honoured | correct refusals and admissions | SEC-D22..D30 | PASS | none |
| P2D-18 | I10 nonregression | accepted behaviour preserved | suites pass | I10 selections | PASS | none |
| P2D-19 | I11 nonregression | accepted behaviour preserved | suites pass | I11 selections | PASS | none |
| P2D-20 | Root and manifest integrity | pinned root, empty approvals | unchanged digest, `artifacts == {}` | SEC-D33/D34 | PASS | bootstrap is a review fact |
| P2D-21 | Historical evidence custody | producers reproduce; pins declared | I05/I06/I09 exact | producer `--check` | PASS | I09 regenerated lawfully |
| P2D-22 | Full canonical regression | no new failure | awaiting single-invocation summary | canonical run | — | host truncates long invocations |
| P2D-23 | No program-gate promotion | no phase advance | none attempted | inspection | PASS | none |
| P2D-24 | Local/remote equality | fast-forward only | HEAD == remote after push | `git ls-remote` | PASS | none |

---

## 13 - Disposition

`I09P2D_IMPLEMENTATION_PARTIAL`.

The four measured defects are repaired and empirically attacked: counterfeit
custody no longer earns trust, an unauthenticated record dimension can no longer
ride an unqualified verdict, contradictory results cannot be constructed
silently, and an approval without availability admits nothing. What remains
unearned is deliberately unearned: no application owns the custody store, so
`custody_source_authorized` is always `False`, `INTEGRATION_STATE` is still
`INTEGRATION_REQUIRED`, and liquidity economics remain unverified.

P2c is **not** ratified by this build; I11 and I09b are untouched.

---

## 14 - Outstanding prerequisites

1. An application-owned initializer that reads the reviewed manifest and holds
   the custody store, so `custody_source_authorized` can become a real claim.
2. Evidence acquisition timestamps in the record model, before any acquisition
   PIT assertion is made.
3. An executable liquidation transformation backed by provider documentation,
   before liquidation economics can be verified.
4. An independent `P2dR1` audit of this repair. **Not executed.**
