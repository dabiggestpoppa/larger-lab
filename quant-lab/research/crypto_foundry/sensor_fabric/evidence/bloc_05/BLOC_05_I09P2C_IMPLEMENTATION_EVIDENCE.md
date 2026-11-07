# BLOC_05 — SENSOR-B5-I09P2c — IMPLEMENTATION EVIDENCE

**Starting HEAD:** `9d9380631e1aa577b880de9be382be943185de50` (== remote)
**Branch:** `agent/crypto-sensor-fabric-build`
**Entering disposition:** `I09P2B_RATIFICATION_HOLD` (P2B-18/19 FAIL, P2B-11/12/13/17 PARTIAL)
**Disposition after this checkpoint:** `I09P2C_IMPLEMENTATION_PARTIAL`

Bounded production repair of record verification, custody and intraday PIT. No
provider approval was added, no venue certified, no provider document fabricated,
no ingestion application invented, no program gate promoted, I11 not ratified.

---

## 1. THE DEFECTS REPRODUCED BEFORE ANY EDIT

The R1 audit's three measured holes were re-proven as tests first. The P2c suite
(`tests/crypto_sensor_fabric/normalization/test_b5_i09p2c_record_verification.py`)
fails at collection against the unrepaired tree:

```
$ PYTHONPATH=src python -m pytest tests/.../test_b5_i09p2c_record_verification.py -q
E   ImportError: cannot import name 'verify_trade_record' ...
1 error in 1.22s          RED_EXIT=2
```

Against the R1 behaviour (recorded in §3 of `BLOC_05_I09P2BR1_INDEPENDENT_AUDIT.md`):

| Hole | Source anchor | R1 observed |
|---|---|---|
| F1 record-blind verification | `authority/__init__.py::verify_mapping_provenance(provenance, ...)` | flipped `aggressor_side=BUY` verified clean |
| F2 liquidation not record/provider bound | `verify_liquidation_admission_provenance` | row chosen by uniqueness, provider absent |
| F3 custody self-attestation | `verify_evidence_custody(authority, custody: dict)` | forged map passing; no bytes read |
| F4 same-day PIT leakage | `load_semantic_authority` `.date()` truncation | 09:00 / 15:00 admitted on the availability date |

---

## 2. WHAT CHANGED, AND WHAT DID NOT

| Path | Change | Reason |
|---|---|---|
| `normalization/sensors/verification.py` (new, 841 lines) | `verify_trade_record`, `verify_liquidation_record`, `TrustedAuthorityContext`, `TrustedCustodyProvider`, `BlobStoreCustody`, `RecordVerification`, `RecordVerificationRefusal` | the full-record boundary |
| `normalization/sensors/side_maps.py` (+42) | `apply_declared_side_transformation` | an EXECUTABLE transformation, not prose |
| `normalization/authority/__init__.py` (+73) | `available_at_instant` field + offset-aware PIT gate + `manifest_digest` | instant-precise availability; hashing stays in the trust module |
| `tests/.../test_b5_i09p2c_record_verification.py` (new, 982) | 43 adversarial tests | REC-01..REC-24 families |
| `tests/.../test_b5_i10_scope_audit.py`, `test_b5_i11_scope_audit.py` (+4, +10) | named module-set entry + P2c suite prefix | lawful scope-audit amendment |
| `evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | `python_files_scanned` 1092 → 1094 | mechanical republish: two new tracked `.py` files |
| `evidence/bloc_05/bloc_05_semantic_validation.json` | one inventory hash | mechanical republish: `authority/__init__.py` changed |

Untouched, deliberately: `config/.../provider_semantics/approval_manifest.json`
(still `artifacts == {}`), the frozen bloc_05 plan, every provider approval, I10's
polarity, I11's four side meanings, I12/I17, all program gates.

---

## 3. THE TRUST CHAIN, END TO END

| Transition | Enforced by | State after P2c |
|---|---|---|
| raw bytes → source revision + evidence refs | upstream T0A store (I03) | unchanged |
| native value → canonical value (trade) | `apply_declared_side_transformation` (re-executed at verification) | **enforced** |
| native value → canonical value (liquidation) | admission identity only | **not executable** (declared) |
| approved row → approval (`attests`) | `SemanticAuthority.attests` | enforced |
| approval → reviewed root | `TRUSTED_MANIFEST_SHA256` pin + `TrustedAuthorityContext` | enforced (integrity, not process) |
| evidence reference → held bytes | `TrustedCustodyProvider` | **enforced when supplied**, operator index `INTEGRATION_REQUIRED` |
| approval availability → knowledge cutoff | instant compare, else same-day refusal | **enforced** |
| record → trusted consumer | `downstream_trusted` conjunction | trade: attainable; liquidation: never claimed |

---

## 4. TRADE RECORD VERIFICATION (`verify_trade_record`)

Signature: `(record, *, trusted_context, artifact_bytes, methodology_registry,
knowledge_cutoff, custody=None)`. It takes the WHOLE `T1TradeRecord`.

Checks, in evidence-chain order: provenance present; the named approval re-derived
under the pinned root; the approved row resolves to the same canonical field,
methodology, version, evidence reference and confidence; `attests(row)`; the
record's `provider` equals the row's provider; the record's preserved
`native_side_field` equals the row's `provider_field`; the preserved native
boolean exists; the canonical side is present; the DECLARED transformation of that
native boolean equals the canonical side; the provisional mapping names the same
`(provider, field, methodology)` and maps to the same side; the cutoff is
admissible; custody holds the approved blob.

Executable transformations are the frozen rules only
(`BINANCE_USDM/isBuyerMaker`, methodology `AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1`).
A row whose family, canonical field, methodology or native type has no declared
rule returns `TRANSFORMATION_UNVERIFIABLE` — the prose `transformation` string is
never interpreted, and no other venue's polarity is borrowed.

`downstream_trusted` requires custody. `source_lineage_verified` is always
`False`, with the reason stated in the result: a byte-identical forged record is
indistinguishable by serialization alone.

---

## 5. LIQUIDATION RECORD VERIFICATION (`verify_liquidation_record`)

Each canonical claim must have its OWN admitted `LiquidationSideAdmission`. The
admission is then re-resolved with the RECORD's provider — not by row uniqueness
across venues — and must authorize exactly that canonical field with the same
methodology, version, evidence reference, confidence and approving identity. The
preserved native field must be the admitted field and the native value must be
present. The canonical value must equal the admitted reading. The contradiction
law (`LONG`+`BUY`, `SHORT`+`SELL`) is re-applied.

`record_transformation_verified` stays `False` and `downstream_trusted` is
`False`: the repository declares no executable liquidation transformation, so a
posteriori mutation of BOTH the record and its admission is outside this
boundary. That is stated in the result, not hidden.

---

## 6. TRUSTED CUSTODY (`TrustedCustodyProvider`)

`held_digest(reference) -> str | None` must read bytes it holds. A plain dict is
refused with `TypeError` (measured: `test_rec_20`). `BlobStoreCustody` re-reads the
immutable blob store and re-hashes it, so a mutated object is refused even when
the index still names the original digest (`test_rec_21`).

The INDEX is the residual: if an untrusted actor supplies both the reference and
the digest it should resolve to, the boundary is decorative. The operator-owned
catalog that would supply it is `INTEGRATION_REQUIRED`, so gate 14 is PARTIAL and
a production warehouse is NOT claimed.

---

## 7. INTRADAY PIT

Two lawful mechanisms, both implemented:

1. `available_at_instant` (offset-aware ISO-8601) on the approval; when present it
   is authoritative over the date and is compared as an instant. A naive value is
   refused at parse (`MALFORMED_MANIFEST`); a cutoff before it is refused
   (`APPROVAL_NOT_YET_AVAILABLE`).
2. Date-only approvals are fail-closed for point-in-time use: `verify_*_record`
   refuses any cutoff whose date is not strictly later than `available_at`
   (`INTRADAY_PIT_AMBIGUOUS`). Measured at 09:00, 12:00, 15:00 and 23:00.

A missing or naive cutoff is refused before any authority is derived
(`PIT_CUTOFF_REQUIRED`). The loader's existing date-granular behaviour is
unchanged for date-granular callers, so I05/I06 availability semantics are
untouched.

Limitation, disclosed: offsets exercised are UTC; sub-hour offsets rely on
`datetime.fromisoformat` offset arithmetic and were not separately asserted.

---

## 8. SECURITY MATRIX

| Case | Attack | Expected | Test | Observed |
|---|---|---|---|---|
| REC-01 | authorized record | verify | `test_rec_01_authorized_trade_record_verifies` | PASS, `downstream_trusted=True` |
| REC-02 | canonical side flipped | refuse | `test_rec_02_flipped_canonical_side_is_refused` | `CANONICAL_VALUE_MISMATCH` |
| REC-03 | provider substituted | refuse | `test_rec_03_provider_substitution_is_refused` | `PROVIDER_MISMATCH` |
| REC-04 | instrument substituted | bounded | `test_rec_04_instrument_substitution_is_outside_mapping_authority` | verifies, `instrument_authenticated=False` |
| REC-05 | native field substituted | refuse | `test_rec_05_native_field_substitution_is_refused` | `NATIVE_FIELD_MISMATCH` |
| REC-06 | native value substituted | refuse | `test_rec_06_native_value_substitution_is_refused` | `CANONICAL_VALUE_MISMATCH` |
| REC-07 | unapproved transformation | refuse | `test_rec_07_unapproved_transformation_is_refused`, `..._no_executable_transformation_for_liquidation_fields` | `TRANSFORMATION_NOT_APPROVED`; liquidation transform `None` |
| REC-08 | approval id changed | refuse | `test_rec_08_to_11_mutated_provenance_identity_is_refused` | `PROVENANCE_MISMATCH` |
| REC-09 | registry digest changed | refuse | same | `PROVENANCE_MISMATCH` |
| REC-10 | methodology/version changed | refuse | same | `PROVENANCE_MISMATCH` |
| REC-11 | evidence reference changed | refuse | same | `PROVENANCE_MISMATCH` |
| REC-12 | source revision changed | bounded | `test_rec_12_source_revision_is_preserved_not_authenticated` | `source_revision_authenticated=False` |
| REC-13 | cutoff manipulated | refuse | `test_rec_13_a_later_day_is_admissible` | later day admissible; same day refused |
| REC-14 | liquidation position side | refuse | `test_rec_14_position_side_substitution_is_refused` | `CANONICAL_VALUE_MISMATCH` |
| REC-15 | liquidation execution side | refuse | `test_rec_15_execution_side_substitution_is_refused` | `CANONICAL_VALUE_MISMATCH` |
| REC-16 | liquidation aggressor side | refuse | `test_rec_16_aggressor_side_without_an_admission_is_refused` | `ADMISSION_MISSING` |
| REC-17 | maker/taker role | refuse | `test_rec_17_maker_taker_role_substitution_is_refused` | `ADMISSION_MISSING` |
| REC-18 | wrong-provider admission | refuse | `test_rec_18_wrong_provider_liquidation_record_is_refused` | `PROVIDER_MISMATCH` |
| REC-19 | missing blob | refuse | `test_rec_19_missing_blob_is_refused` | `CUSTODY_UNVERIFIED` |
| REC-20 | untrusted custody dict | refuse | `test_rec_20_a_caller_dictionary_is_not_a_custody_provider` | `TypeError` |
| REC-21 | source blob mutated | refuse | `test_rec_21_a_mutated_source_blob_is_refused` | `CUSTODY_UNVERIFIED` |
| REC-22 | intraday same-day ambiguity | refuse | `test_rec_13_rec_22_same_day_intraday_cutoff_is_refused` (09/12/15/23) | `INTRADAY_PIT_AMBIGUOUS` |
| REC-23 | valid timestamped authority | verify | `test_rec_23_an_instant_precise_availability_is_honoured` | admissible at 15:05, refused at 14:55 |
| REC-24 | no trusted initializer | bounded | `test_rec_24_*`, `INTEGRATION_STATE` | `INTEGRATION_REQUIRED`; actor manifest → `TRUSTED_CONTEXT_MISMATCH` |

Extras: forged model-validated construction refused; record without provenance
refused; determinism (identical `model_dump` twice); no provider-package import;
wrong record kind refused; verifier signature carries `record`.

43 tests, all passing.

---

## 9. ACCEPTANCE GATES P2C-01…P2C-24

| Gate | Frozen clause | Expected | Observed | Test/probe | Result | Limitation |
|---|---|---|---|---|---|---|
| P2C-01 | repository custody | clean, linear | HEAD `9d9380631e` == remote, linear | `git rev-parse`/`ls-remote` | PASS | — |
| P2C-02 | frozen plan integrity | unchanged | no plan path in diff | `git diff HEAD -- bloc_05` empty | PASS | — |
| P2C-03 | trusted-root integrity | pin == bytes | pin matched, manifest untouched | `test_rec_24_the_reviewed_production_root...`, P2b suite | PASS | pin strength = review of the committing change |
| P2C-04 | empty production approvals | `artifacts == {}` | empty | same test + `cat` | PASS | — |
| P2C-05 | full trade-record verification | record in scope | record verified end to end | REC-01..12 | PASS | — |
| P2C-06 | full liquidation-record verification | record in scope | per-field, provider-bound | REC-14..18 | PASS | canonical value checked against admission, not a transform |
| P2C-07 | canonical economic-value coherence | re-derived | trade re-executed; liquidation admitted-reading | REC-02/06/14/15 | PARTIAL | no executable liquidation transform |
| P2C-08 | provider/venue binding | bound | provider bound by row; venue preserved | REC-03/18 | PARTIAL | the mapping framework carries no venue field |
| P2C-09 | native field/value binding | bound | field + boolean/value compared | REC-05/06 | PASS | — |
| P2C-10 | contract/instrument binding | bound | preserved; PIT-term contradiction refused by normalize | REC-04 | PARTIAL | no approval surface for instrument identity |
| P2C-11 | methodology + evidence identity | bound | row identity + attester | REC-08..11 | PASS | — |
| P2C-12 | source revision consistency | bound | preserved only | REC-12 | PARTIAL | no revision-authentication mechanism exists |
| P2C-13 | intraday PIT fail-closed | refuse ambiguity | same-day refused; instant honoured | REC-13/22/23 | PASS | UTC offsets exercised |
| P2C-14 | trusted custody interface | byte-reading boundary | protocol + adapter; dict refused | REC-19/20/21 | PARTIAL | operator catalog `INTEGRATION_REQUIRED` |
| P2C-15 | evidence-blob integrity | mutation refused | tampered blob refused | REC-21 | PASS | — |
| P2C-16 | no caller self-approval | manifest can't be self-supplied | context refuses non-pinned bytes | REC-24 | PASS | in-process boundary only |
| P2C-17 | no direct-record trust bypass | forged record refused | model-valid forgery refused | forged-construction test | PASS | — |
| P2C-18 | I10 nonregression | unchanged | 1167 normalization tests | subset + scope audits | PASS | — |
| P2C-19 | I11 nonregression | unchanged | four sides, all-or-nothing, counts | subset + scope audits | PASS | — |
| P2C-20 | deterministic verification | byte-identical | identical `model_dump`; producers `--check` exit 0 | determinism test + I05/I06/I09 | PASS | — |
| P2C-21 | historical custody and pins | preserved | I05 86/0, I06 14/0, I09 35/0 regenerated | producer runs | PASS | one inventory hash changed by design |
| P2C-22 | full canonical regression | 4522/14 baseline | 4565 passed, 14 skipped, exit 0 (1266.84 s) = baseline +43 | `python -m pytest -q` from the worktree root | PASS | newly executed |
| P2C-23 | no program-gate promotion | none | none touched | diff surface | PASS | — |
| P2C-24 | fast-forward Git custody | linear | fast-forward from `9d9380631e`; local == remote | `git push` receipt | PASS | recorded at push |

---

## 10. BLAST RADIUS AND PIN CASCADE

- Authorized surface: 6 source/test paths + 2 mechanically regenerated artifacts.
- `authority/__init__.py`: 894 CRLF lines → 967 CRLF lines, **0 bare LF** (no
  line-ending churn; numstat 73/0).
- I09 artifact regenerated: inventory hash for `authority/__init__.py`
  `91451a16…` → `fb71f7b2…`; artifact digest `8b3dbd3f…` → `567716a4…`; rows
  35, pass 35, fail 0, unresolved 3 (unchanged).
- I06 `P2B_DISCLOSED_SHA256` block untouched; predecessor pins byte-preserved.
- Governance `python_files_scanned` 1092 → 1094, republished through the documented
  `UPDATE_I11R2_EVIDENCE=1` mechanism **after staging**, not hand-edited.
- Scope audits amended only to name the new module and suite, each with its own
  DISCLOSED entry; no predicate was relaxed.

---

## 11. VERIFICATION EXECUTED

| Check | Result |
|---|---|
| P2c security suite | 43 passed |
| `tests/crypto_sensor_fabric/normalization` | 1167 passed (1124 + 43) |
| Governance binding audit | 4 passed (republished, then verified) |
| `b5_i05_time.py --check` | 86 rows, 0 fail; scope audit 7/7 |
| `b5_i06_replay_safety.py --check` | 14 rows, 0 fail; scope audit 8/8 |
| `b5_i09_semantics.py --check` | 35 rows, 0 fail, 3 unresolved, `567716a4…` |
| ruff (changed files) | clean |
| mypy (changed modules) | clean |
| compileall (changed modules) | exit 0 |
| Full canonical suite (`python -m pytest -q`, worktree root) | 4565 passed, 14 skipped, exit 0 (1266.84 s) |

---

## 12. GOVERNANCE

NO PROGRAM GATE PROMOTED. B5-I09a = OPERATOR_ACCEPTED; B5-I09b = DEFERRED;
B5-I10 = OPERATOR_ACCEPTED (bounded); B5-I11 = IMPLEMENTATION_PARTIAL /
RATIFICATION_HOLD; B5-I09P2A/B = NOT RATIFIED; B5-I09P2C =
IMPLEMENTATION_PARTIAL; BLOC_05 = INCOMPLETE; all eight gates NOT_YET_EARNED;
B5-I12+/I17/BLOC_06 UNAUTHORIZED; RESEARCH = FROZEN.

Remaining external dependencies: an operator-owned evidence catalog (custody
index), a trusted application initializer, and real provider evidence for any
nonempty approval.
