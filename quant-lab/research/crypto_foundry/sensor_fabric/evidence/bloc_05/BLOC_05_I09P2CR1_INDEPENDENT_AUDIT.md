# BLOC_05 — SENSOR-B5-I09P2cR1 — INDEPENDENT FULL-RECORD SECURITY AUDIT

**Audited HEAD:** `3a732e18878e96adbc192731c4b4a2ded30379ea` (local == remote)
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Entering disposition:** `I09P2C_IMPLEMENTATION_PARTIAL`
**Audit disposition:** `I09P2C_RATIFICATION_HOLD`

Read-only audit. No production file, test file, historical artifact or frozen plan
was modified. The three preserved scratch paths (`.bu_tmp/`,
`BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`, `b5_i03_redteam_results.json`)
are untouched and unstaged. Probes are disposable and live only in `.bu_tmp/`.

---

## 1. REALITY LOCK

| Check | Observed |
|---|---|
| HEAD == remote | `3a732e1887` == `3a732e1887` |
| Branch | `agent/crypto-sensor-fabric-build`, linear on `9d9380631e` |
| Tracked tree | clean (only the three scratch paths untracked) |
| P2c commit surface | exactly the 10 disclosed paths, +2298/−5 |
| Seven frozen Bloc 5 documents | byte-identical since `dafcd86a02` (`git diff --stat` empty) |
| I09a/I10 acceptance | intact (`TEST_OR_PROBE` pins unchanged, scope audits pass) |
| I11 | still `IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD` |
| Production manifest | `artifacts == {}`, sha `3d707c59…`, pin == bytes `True` |
| Intervening commits | none between `9d9380631e` and HEAD except P2c |

No reset, rebase, amend, squash or force-push was performed.

---

## 2. TRUST CHAIN, RECONSTRUCTED FROM THE MODULES

Ten properties, kept distinct on purpose:

| Property | Established by | Reality at this HEAD |
|---|---|---|
| structural model validity | pydantic contracts | enforced on construction |
| mapping approval | `SemanticAuthority` + `attests` | enforced, pinned root |
| transformation verification | `apply_declared_side_transformation` | **trade only** |
| provider identity | record.provider == approved row | enforced |
| venue identity | record.venue | **preserved, never checked** |
| instrument / contract identity | native_instrument, contract_instance_id | **preserved, never checked** |
| source revision authenticity | source_revision_id | **preserved, never checked** |
| evidence-blob custody | `TrustedCustodyProvider` | **interface only; see F-R1-01** |
| source acquisition authenticity | acquisition_refs | **preserved, never checked** |
| PIT admissibility | instant compare / same-day refusal | enforced |
| downstream verdict | conjunction in `RecordVerification` | **overstates; see F-R1-02/R1-03** |

---

## 3. INDEPENDENT TRADE-RECORD MUTATION RESULTS

Baseline: authorized synthetic record verifies (`VERIFIED`, `downstream_trusted=True`
with a custody provider). Each mutation keeps every approved provenance field.

| Attack | Mutation | Observed |
|---|---|---|
| T01 | canonical SELL→BUY | `CANONICAL_VALUE_MISMATCH` |
| T02 | native boolean True→False | `CANONICAL_VALUE_MISMATCH` |
| T03 | native field `isBuyerMaker`→`side` | `NATIVE_FIELD_MISMATCH` |
| T04 | provider `BINANCE_USDM`→`OKX` | `PROVIDER_MISMATCH` |
| T05 | venue `BINANCE`→`COINBASE` | **VERIFIED**, `down=True`, `instrument_authenticated=False` |
| T06 | instrument `BTCUSDT`→`ETHUSDT` | **VERIFIED**, `down=True` |
| T07 | contract instance swap | **VERIFIED**, `down=True` |
| T08 | source revision swap | **VERIFIED**, `down=True`, `source_revision_authenticated=False` |
| T09 | acquisition refs swap | **VERIFIED**, `down=True`, `source_lineage_verified=False` |
| T10 | cutoff before availability | `APPROVAL_NOT_YET_AVAILABLE` |
| T11 | approval id swap | `PROVENANCE_MISMATCH` |
| T12 | methodology version swap | `PROVENANCE_MISMATCH` |
| T13 | evidence reference swap | `PROVENANCE_MISMATCH` |
| T14 | registry digest swap | `PROVENANCE_MISMATCH` |

Economic meaning is genuinely re-derived for trade records: the canonical side,
the native boolean, the native field and the provider cannot be rewritten. Venue,
instrument, contract, revision and acquisition identity are **not** bound by the
approved mapping, and the result says so in its per-dimension flags — but it still
returns `downstream_trusted=True` (F-R1-02).

---

## 4. COORDINATED LIQUIDATION FORGERY

Baseline liquidation record: `position_side_liquidated=LONG`, `execution_side=SELL`,
admission `(side, provisional=LONG)`.

| Family | Mutation | Observed |
|---|---|---|
| L01 | canonical only (`LONG`→`SHORT`) | `CANONICAL_VALUE_MISMATCH` |
| L02 | admission only (`provisional`→`SHORT`) | `CANONICAL_VALUE_MISMATCH` |
| L03 | **coordinated**: position `LONG`→`SHORT`, execution `SELL`→`BUY`, both admissions rewritten, native values rewritten, approval/evidence/digest untouched | **VERIFIED — `semantic_mapping_approved=True`, `record_transformation_verified=False`, `downstream_trusted=False`, fields `(position_side_liquidated, execution_side)`** |
| L03b | canonical+admission rewritten but execution side left contradictory | `CANONICAL_VALUE_MISMATCH` (contradiction law) |
| L04 | cross-field admission (`side_exec` for the position claim) | `NATIVE_FIELD_MISMATCH` |

The coordinated forgery **is accepted as an approved semantic mapping**, exactly as
the frozen directive predicted, and the result refuses the economic claim
(`record_transformation_verified=False`) and full trust (`downstream_trusted=False`).
That classification is correct and consistent with the frozen authority: no
executable liquidation transformation exists, and none may be invented. P2C-07
therefore stays PARTIAL; the defect is not a false PASS but an unavoidable limit of
the evidence base.

---

## 5. EXECUTABLE TRANSFORMATION AUTHORITY

`apply_declared_side_transformation(row, native)`:

| Probe | Result |
|---|---|
| `isBuyerMaker=True` | `SELL` |
| `isBuyerMaker=False` | `BUY` |
| native `"true"` (string) | `None` |
| native `1` (int) | `None` |
| wrong provider, same field name | `None` |
| wrong methodology id | `None` |
| liquidation row (`side`, `LONG`) | `None` |

No rule is inferred from provider name, prose `transformation`, or another venue's
polarity. The liquidation path therefore reports `TRANSFORMATION_UNVERIFIABLE`
rather than borrowing a convention — correct.

---

## 6. CUSTODY-PROVIDER FORGERY — **F-R1-01 (CRITICAL)**

```python
class FakeCustody:                      # conforms to the Protocol
    def held_digest(self, reference): return approved_digest   # holds no bytes
```

| Probe | Observed |
|---|---|
| `isinstance(FakeCustody(...), TrustedCustodyProvider)` | `True` |
| trade verify with counterfeit | **`custody_verified=True`, `downstream_trusted=True`** |
| caller-authored dict | `TypeError` (repaired from P2B-11) |
| object returning a wrong digest | `CUSTODY_UNVERIFIED` |
| `BlobStoreCustody` over an intact blob | `custody_verified=True`, `downstream_trusted=True` |
| `BlobStoreCustody` over a mutated blob | `CUSTODY_UNVERIFIED` |
| `BlobStoreCustody` whose index names an absent blob | `CUSTODY_UNVERIFIED` |

`runtime_checkable` Protocols test for a method name, not for provenance. Because
the approved evidence digest is public in the manifest, any caller can mint an
object that satisfies the boundary without holding a byte, and receive the
strongest verdict the module issues. `INTERFACE_CONTRACT_SATISFIED` is being
treated as `INDEPENDENT_CUSTODY_AUTHENTICATED`. The implementation evidence already
discloses that the index is `INTEGRATION_REQUIRED`, but the verdict does not
reflect that disclosure: `downstream_trusted` is awarded.

**This is the reason this audit cannot ratify the checkpoint.**

---

## 7. INTRADAY PIT AND TIMEZONE MATRIX

| Probe | Observed |
|---|---|
| availability 15:00Z, cutoff 14:59Z | `APPROVAL_NOT_YET_AVAILABLE` |
| availability 15:00Z, cutoff 15:00Z (equality) | `VERIFIED` |
| availability 15:00Z, cutoff 15:01Z | `VERIFIED` |
| date-only, same day 09:00Z | `INTRADAY_PIT_AMBIGUOUS` |
| date-only, same day 23:59Z | `INTRADAY_PIT_AMBIGUOUS` |
| date-only, next day 00:00Z | `VERIFIED` |
| availability `15:00-05:00` (=20:00Z), cutoff 19:59Z | `APPROVAL_NOT_YET_AVAILABLE` |
| availability `15:00-05:00`, cutoff 20:00Z | `VERIFIED` |
| same instant expressed as `+00:00` | `VERIFIED` (instants compared, not strings) |
| date-crossing: availability `23:30-05:00` (=03-02T04:30Z), cutoff 03-02T04:00Z | `APPROVAL_NOT_YET_AVAILABLE` (date is later, instant is earlier — correctly refused) |
| date-crossing, cutoff 04:30Z | `VERIFIED` |
| DST repeated hour: availability `01:30-04:00`, cutoff `01:30-05:00` | `VERIFIED` |
| DST reverse: availability `01:30-05:00`, cutoff `01:30-04:00` | `APPROVAL_NOT_YET_AVAILABLE` |
| naive cutoff | `PIT_CUTOFF_REQUIRED` |
| missing cutoff | `PIT_CUTOFF_REQUIRED` |
| naive `available_at_instant` in the manifest | `MALFORMED_MANIFEST` |
| instant before `approved_at` | `MALFORMED_MANIFEST` |
| approval with **neither** availability field, cutoff before approval date | **`VERIFIED`** (no PIT constraint at all) |

Timezone handling is instant-correct, DST-safe and fail-closed on same-day
date-only approvals. The last row is a genuine fail-open hole: absence of both
fields imposes no availability claim, so a date-less/instant-less approval can
certify any earlier cutoff. It is a manifest-shape gap, not a timezone bug.

---

## 8. TRUSTED ROOT AND BOOTSTRAP

| Probe | Observed |
|---|---|
| production manifest sha | `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` |
| pin == bytes | `True` |
| empty production manifest, approved artifact id | `NO_APPROVAL` |
| empty production manifest, unapproved artifact id | `NO_APPROVAL` |
| forged manifest as context | `TRUSTED_CONTEXT_MISMATCH` |
| raw manifest bytes passed as context | `TypeError` |
| different registry bytes | `DIGEST_MISMATCH` |
| cutoff after `valid_until` | `AUTHORITY_EXPIRED` |
| revoked approval replay | `APPROVAL_REVOKED` |
| mutable module-level approval cache | none (only `__cached__`) |

`TrustedAuthorityContext` authenticates manifest bytes against the pinned constant
and nothing else. Its authority is therefore a **deployment assumption**: the
initializer that owns those bytes does not exist in this repository. No network or
wall-clock access occurs in the verifier.

---

## 9. RESULT-STATUS COHERENCE — **F-R1-02 / F-R1-03**

Measured verifier output for an authorized trade record with custody:
`mapping=True, transform=True, custody=True, lineage=False, instrument=False,
revision=False, downstream=True`. Deterministic: two calls produce byte-identical
`model_dump_json()`.

F-R1-02: `downstream_trusted=True` coexists with unauthenticated venue, instrument,
contract, revision and acquisition fields, and with a counterfeit custody object.

F-R1-03: the model itself enforces no invariant. All of these construct and
serialize:

- `downstream_trusted=True`, `custody_verified=False` — ACCEPTED by the model
- `downstream_trusted=True`, `semantic_mapping_approved=False` — ACCEPTED
- `custody_verified=True`, `downstream_trusted=False` — ACCEPTED

The verifier happens to emit a consistent conjunction today, but nothing prevents
a consumer, a future adapter or a stored artifact from carrying an impossible
combination. The aggregate boolean is broader than the evidence.

---

## 10. HISTORICAL CUSTODY AND PINS

| Check | Observed |
|---|---|
| P2c changed paths | exactly the 10 disclosed |
| `authority/__init__.py` endings | 894 → 967 CRLF, 0 bare LF |
| I05 producer `--check` | 86 rows / 86 pass / 0 fail; scope audit 7/7 |
| I06 producer `--check` | 14 rows / 14 pass / 0 fail; scope audit 8/8 |
| I09 producer `--check` | 35 rows / 35 pass / 0 fail / 3 unresolved; `567716a469675480b9bfa26e9eb06143d4d14b7fd297f52d833fe029f3cd0eb9` |
| I09 unresolved states | unchanged (I08 units, depth-bps, T2 CVD) |
| Governance binding audit | 4 passed |
| Seven frozen Bloc 5 docs | byte-identical since `dafcd86a02` |
| Unauthorized-module negative probes | I10/I11 scope audits pass unmodified |

No history was republished to conceal a discrepancy.

---

## 11. VERIFICATION EXECUTED

| Check | Result |
|---|---|
| `test_b5_i09p2c_record_verification.py` | 43 passed (within the 321 focused selection) |
| `-k "i09 or i10 or i11"` normalization selection | 321 passed, 846 deselected |
| I10 trade + I11 liquidation + P2a + P2b suites | 150 passed |
| Governance binding audit | 4 passed |
| I05 / I06 / I09 producers `--check` | exit 0 / 0 / 0, pins reproduced |
| Disposable probes | `p2cr1_probe.py`, `probe2.py`, `probe3.py` (`.bu_tmp/`, unstaged) |
| Canonical suite | **not re-executed**: no production/test byte changed since `3a732e1887` measured 4565 passed / 14 skipped / exit 0 (1266.84 s). Cited as prior evidence, not as a new run. |

---

## 12. P2C-01 … P2C-24 RE-ADJUDICATION

24 rows; 17 PASS, 6 PARTIAL, 1 FAIL. (The implementation evidence reported 19/5/0;
the difference is the custody and scope reclassification below.)

| Gate | Frozen clause | Expected | Observed | Independent probe | Verdict | Limitation |
|---|---|---|---|---|---|---|
| 01 | repository custody | clean, linear | clean, linear | `git rev-parse`/`ls-remote` | PASS | — |
| 02 | frozen plan integrity | unchanged | unchanged since freeze | `git diff --stat dafcd86a02 HEAD` empty | PASS | — |
| 03 | trusted-root integrity | pin == bytes | pin == sha `3d707c59…` | probe2 | PASS | pin strength = review of the commit |
| 04 | empty production approvals | `{}` | `{}`, `NO_APPROVAL` | probe2 | PASS | — |
| 05 | full trade-record verification | record in scope | economic fields re-derived; venue/instrument/revision/acquisition pass through while `downstream_trusted=True` | T05–T09 | PARTIAL | unauthenticated dimensions reach the trust flag |
| 06 | full liquidation-record verification | record in scope | per-field admission bound to record provider | L01–L04 | PASS | canonical value checked against admission, not a transform |
| 07 | economic transformation coherence | re-derived | coordinated L03 accepted as mapping, economic claim refused | L03 | PARTIAL | no executable liquidation transform exists |
| 08 | provider/venue binding | bound | provider bound; venue never checked | T04, T05 | PARTIAL | mapping framework carries no venue field |
| 09 | native field/value binding | bound | field and boolean enforced | T02, T03 | PASS | — |
| 10 | instrument/contract binding | bound | preserved only | T06, T07 | PARTIAL | no approval surface for instrument identity |
| 11 | methodology/evidence identity | bound | `PROVENANCE_MISMATCH` on any swap | T11–T14 | PASS | — |
| 12 | source revision authenticity | bound | preserved only | T08 | PARTIAL | no revision-authentication mechanism |
| 13 | intraday PIT fail-closed | refuse ambiguity | same-day refused, instants compared, DST correct | probe PIT matrix | PASS | see 14-row fail-open on absent availability |
| 14 | trusted custody boundary | byte-reading boundary | counterfeit Protocol object receives custody and full trust | FakeCustody probe | **FAIL** | `runtime_checkable` tests shape, not provenance |
| 15 | evidence-blob integrity | mutation refused | real adapter refuses tampering; counterfeit bypasses it | blob-store probe | PARTIAL | integrity only as strong as the supplied object |
| 16 | no caller self-approval | manifest not self-supplied | forged root / raw bytes refused | probe2 | PASS | in-process boundary only |
| 17 | no direct-record bypass | forged record refused | T01–T03 refused | probe | PASS | — |
| 18 | I10 nonregression | unchanged | 1167 normalization tests previously; 321 focused now | pytest | PASS | — |
| 19 | I11 nonregression | unchanged | four sides, all-or-nothing intact | pytest | PASS | — |
| 20 | deterministic verification | byte-identical | `model_dump_json` identical | probe3 | PASS | — |
| 21 | historical custody/pins | preserved | producers reproduce pins | `--check` x3 | PASS | — |
| 22 | canonical regression | 4522/14 baseline | 4565/14/0 measured at this exact commit | prior run | PASS | not re-executed (no byte changed) |
| 23 | no program-gate promotion | none | none | diff surface | PASS | — |
| 24 | fast-forward Git custody | linear | fast-forward, local == remote | push receipt | PASS | — |

---

## 13. FINDINGS

| ID | Severity | Finding |
|---|---|---|
| F-R1-01 | **CRITICAL** | A counterfeit custody provider satisfying the runtime Protocol receives `custody_verified=True` and, for trade, `downstream_trusted=True`, without holding any bytes. P2C-14 FAIL. |
| F-R1-02 | **HIGH** | `downstream_trusted=True` is awarded while venue, instrument, contract, source revision and acquisition references are unauthenticated (T05–T09). The claim exceeds the evidence. |
| F-R1-03 | **MEDIUM** | `RecordVerification` enforces no invariant; contradictory combinations (`downstream_trusted=True` with `custody_verified=False`) construct and serialize. |
| F-R1-04 | **MEDIUM** | An approval carrying neither `available_at` nor `available_at_instant` imposes no PIT constraint, so any earlier cutoff verifies. |
| F-R1-05 | OBSERVATION | The coordinated liquidation forgery is accepted as an approved mapping but correctly refused as economic verification; no repair may fabricate a transform. |
| F-R1-06 | OBSERVATION | `TrustedAuthorityContext` authority rests on a deployment assumption; the owning initializer does not exist in this repository. |

No other measured defect: economic trade mutation, provider/native binding,
provenance identity, revocation, expiry, artifact substitution, PIT instants, DST,
determinism and historical pins all held under attack.

---

## 14. RATIFICATION DISPOSITION

**`I09P2C_RATIFICATION_HOLD`.**

Bounded recognition, recorded explicitly: trade canonical-side verification,
provider/native/provenance binding, liquidation record-binding with honest refusal
of economic verification, intraday PIT fail-closure, deterministic output and
historical custody all survived independent attack and are accepted as working
within their stated limits.

Ratification is withheld because the strongest verdict the module issues can be
obtained without earning it: a caller-minted object satisfies the custody boundary
and receives full downstream trust, and the same flag is awarded while several
record dimensions are known to be unauthenticated. An unqualified acceptance would
carry unearned provenance claims, which the directive forbids.

---

## 15. MINIMAL REMEDIATION — `SENSOR-B5-I09P2d` (SPECIFIED, NOT EXECUTED)

1. **Custody identity, not custody shape.** Accept custody only from an
   application-owned handle (a `BlobStoreCustody` built from an operator-supplied
   store, or a capability minted by `TrustedAuthorityContext`), and refuse any
   duck-typed object. Keep the dict refusal.
2. **Scope the verdict.** Replace (or constrain) `downstream_trusted` so it is
   derived only from dimensions the authority can actually establish, and emit
   `unverified_dimensions` explicitly. Add a model validator forbidding
   `downstream_trusted=True` with `custody_verified=False` (F-R1-03).
3. **Close the availability gap.** Refuse an approval with neither availability
   field for point-in-time verification (F-R1-04).
4. **Regression tests** for: counterfeit custody object, coordinated liquidation
   record+admission rewrite, contradictory `RecordVerification` construction,
   availability-less manifest.

Explicitly out of scope for P2d: inventing a provider-side liquidation
transformation, fabricating provider evidence, building the ingestion application,
I11 ratification, I12/I17, any program-gate promotion.

---

## 16. NEXT CHECKPOINT PROPOSAL — NOT EXECUTED

`SENSOR-B5-I09P2d — Verified-Result Scope and Provenance Closure`, followed by an
independent `P2dR1` re-attack of the same four vectors. If P2d is not authorized,
the alternative is a bounded ratification that grants only the dimensions listed in
§14 and names `downstream_trusted` as an unearned claim.
