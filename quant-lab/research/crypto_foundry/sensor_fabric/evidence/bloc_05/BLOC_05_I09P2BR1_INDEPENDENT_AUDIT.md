# BLOC_05 — SENSOR-B5-I09P2bR1 — INDEPENDENT PROVENANCE AUDIT

**Audited commit:** `7144b554729e30f0ff938a505ec5cc194644b5f0`
**Predecessor:** `fa758874ea766eebcb3a6d31ade09b7dece6f4ae` (I09P2aR1)
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Entry disposition audited:** `I09P2B_IMPLEMENTATION_PARTIAL`
**Disposition after audit:** `I09P2B_RATIFICATION_HOLD`

Read-only audit. No production file, test or frozen document was changed. All
fixtures were synthetic and disposable. No venue is certified and no production
approval exists.

---

## 1. REALITY LOCK

| Item | Observed |
|---|---|
| HEAD | `7144b55472…` |
| Remote HEAD | `7144b55472…` (equal) |
| Ancestry | `7144b55472` → `fa758874ea` → `6b112f196e` (linear, no rewrite) |
| Tracked tree | clean at audit start; unchanged by `--check` producer runs |
| Preserved scratch | `.bu_tmp/`, `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`, `scripts/b5_i03_redteam_results.json` untouched |
| P2b scope | 10 paths, +1253/−4 |
| Production manifest artifacts | `{}` |
| Frozen plan documents | not modified by P2b (no plan path in the P2b diff) |

The plan ref `agent/crypto-sensor-fabric-plan` is not a local branch in this
worktree; the frozen SHA is recorded from the checkpoint chain and the P2b diff
contains no plan path.

---

## 2. RECONSTRUCTED AUTHORITY CHAIN (source, not names)

| Step | Component | Verifies | Caller-controlled? |
|---|---|---|---|
| 1 | `resolve_authority_inputs` | type discrimination only | yes (both slots) |
| 2 | `load_semantic_authority` | manifest parse, validity/revocation, artifact digest, schema generation, per-row coverage | **yes — manifest bytes and artifact bytes both caller-supplied** |
| 3 | `load_trusted_authority` | SHA-256 of manifest bytes against the source constant `TRUSTED_MANIFEST_SHA256`, then generation, then delegates to (2) | manifest is refused unless it is the reviewed root |
| 4 | `SemanticAuthority.attests` | row coverage of the loaded approval | derived from (2)/(3) |
| 5 | `trade.normalize` | sets `authority_provenance` only when side admitted **and** `attests` passes | n/a |
| 6 | `verify_mapping_provenance(provenance, …)` | approval id, registry digest, row identity on (provider, provider_field, canonical_sensor), canonical field, methodology/version, evidence reference, confidence, attestation | **provenance object only — no record** |
| 7 | `verify_liquidation_admission_provenance(admission, …)` | `admitted`, approval id, digest, and a unique row on (provider_field, canonical_field, methodology_id, version) | admission object only — no record, no provider |
| 8 | `verify_evidence_custody(authority, custody)` | approved reference → digest equality **against a caller-supplied map** | custody map is caller-controlled |

Measured enumeration of the liquidation verifier's record-level reads:
`admission_approval_id`, `admission_registry_digest`, `canonical_field`,
`evidence_reference`, `mapping_version`, `methodology_id`, `provider_field`.
Provider and every record-level economic value are outside that set.

---

## 3. FINDINGS

### F1 — CRITICAL: the verifier does not bind the record (P2B-18, P2B-19)

`verify_mapping_provenance` parameters are exactly
`['provenance', 'manifest_bytes', 'artifact_bytes', 'methodology_registry', 'evaluation_at']`.
No record, no native value, no canonical value is in scope.

Disposable probe, synthetic root, one authorized provenance:

```text
A0 baseline authorized provenance                      PASSED
A1 record.aggressor_side='BUY', provenance unchanged  PASSED  <- contradiction accepted
B4 same provenance, record claims provider='OKX',
   venue='OKX_SWAP', instrument='BTC-USDT-SWAP'       PASSED
```

The approved row reads `isBuyerMaker=true -> SELL`. A record claiming `BUY`
carrying the unchanged provenance is verified as authorized, because the only
compared facts are the provenance's own fields and the approved row — never the
record. `T1TradeRecord`'s laws reference `aggressor_side` only in
`_provisional_admission_law` (provisional/canonical coherence), not in relation
to `authority_provenance`, so no model-level refusal closes the gap.

Consequence: P2b's claim that G7 record verification is closed is not supported.
What exists is **mapping-metadata verification**, which is a real and useful
narrowing (a fabricated approval identity is refused) but is not verification of
the exported record's economic claim.

### F2 — Liquidation provenance is not record-bound and not provider-bound

The admission carries no provider; the verifier selects a row by
(provider_field, canonical_field, methodology_id, version) uniqueness. With one
venue approved this is unambiguous; with two venues publishing the same native
field name and methodology it refuses (safe) but can never *identify* which venue
authorized the record. Mutating the record's `position_side_liquidated` or
`execution_side` after admission is undetectable by this API, which never
receives the record.

### F3 — Evidence custody is conditional, not proof of custody

`verify_evidence_custody(authority, custody)` takes the inventory from the same
caller that supplies the evidence claim and reads no bytes:

```text
D3 custody map echoing the manifest's own digest      PASSED
D1 no blob for the reference exists on disk          (nothing consults disk)
```

A digest matching is only meaningful when `custody` comes from a separately
trusted storage inventory. The P2b doc discloses this; the gate must therefore
remain PARTIAL rather than PASS.

### F4 — PIT admissibility is date-granular only

```
E1 evaluation 2026-03-01 (date)        ADMITTED
E3 evaluation 2026-03-01T09:00         ADMITTED
E4 evaluation 2026-03-01T15:00         ADMITTED
E5 evaluation 2026-02-28T23:59         REFUSED APPROVAL_NOT_YET_AVAILABLE
```

Any `datetime` is truncated with `.date()` before comparison, so an approval
that became operative at 15:00 that day is admitted for a 09:00 cutoff.
Date-granular refusal works; intraday admissibility is **not enforced** and must
not be certified. The correct behaviour for intraday use is refusal, not
date-level inference.

### F5 — Trusted root: integrity proven, process and deployment not

The production pin matches the committed manifest bytes (`3d707c59…`), the
manifest still ships `artifacts == {}`, a changed manifest, an actor-supplied
manifest, an artifact+manifest pair rewritten together, and a wrong generation
are all refused. But the pin is a source constant in a library that nothing in
the repository initializes at runtime: `load_semantic_authority` still has no
caller outside the authority package, and `load_trusted_authority` has no
production caller either.

```text
PINNED_ROOT_INTEGRITY          = PROVEN
OPERATOR_APPROVAL_PROCESS      = NOT_PROVEN (no nonempty approval exists)
APPLICATION_INITIALIZATION     = CONTRACT_ONLY
PROVIDER_EVIDENCE_AUTHENTICITY = NOT_PROVEN
```

### F6 — Historical custody verified

`P2B_DISCLOSED_SHA256` is appended and merged last; every P2A/I08/I09/I10 pin is
byte-preserved; the I10 scope-audit allowlist gained exactly one named entry; the
I05 artifact is byte-identical; I06 and I09 artifacts regenerate deterministically
(`8b3dbd3f…`, 35 rows, 0 fail, 3 unresolved preserved); governance counts were
republished only after staging. No LF/CRLF churn and no sealed assertion weakened.

---

## 4. RE-ADJUDICATED MATRIX

| Gate | Frozen clause | Result |
|---|---|---|
| P2B-01 | repository custody | PASS |
| P2B-02 | frozen plan | PASS |
| P2B-03 | independent trusted root | PASS — source constant verified against committed bytes; deployment root not proven (F5) |
| P2B-04 | empty shipping approvals | PASS |
| P2B-05 | manifest/artifact separation | PASS |
| P2B-06 | caller self-approval refusal | PASS at the trusted entry; lower-level loader remains a disclosed residual |
| P2B-07 | approval integrity | PASS |
| P2B-08 | registry-version compatibility | PASS |
| P2B-09 | methodology binding | PASS |
| P2B-10 | provider/evidence binding | PASS |
| P2B-11 | actual evidence-blob custody | **PARTIAL** — caller-supplied inventory, no bytes read (F3) |
| P2B-12 | PIT revision admissibility | **PARTIAL** — date granularity only; same-day admitted (F4) |
| P2B-13 | trusted initialization | **PARTIAL** — contract only, no application caller (F5) |
| P2B-14 | I10 consumer safety | PASS |
| P2B-15 | I11 consumer safety | PASS |
| P2B-16 | trade-record provenance | PASS — slot present and populated only on admission; envelope README/quality laws unchanged |
| P2B-17 | liquidation-record provenance | **PARTIAL** — admission identity only, no provider, no record binding (F2) |
| P2B-18 | downstream independent verification | **FAIL** — verifies mapping metadata, not the record (F1) |
| P2B-19 | mutation refusal over the full record | **FAIL** — canonical side, provider, venue and instrument mutations verify clean (F1) |
| P2B-20 | historical evidence custody | PASS (F6) |
| P2B-21 | determinism | PASS — all three producers `--check` exit 0, tree unchanged |
| P2B-22 | canonical regression | PASS by provenance — `4522 passed, 14 skipped, exit 0` measured at this exact commit; not rerun because source and test bytes are unchanged |
| P2B-23 | no program-gate promotion | PASS |
| P2B-24 | Git custody | PASS — fast-forward, local == remote |

Summary: 18 PASS, 4 PARTIAL (11, 12, 13, 17), 2 FAIL (18, 19). The P2b author's
matrix claimed 21 PASS / 3 PARTIAL; P2B-18 and P2B-19 do not survive independent
attack, and P2B-17 is narrower than claimed.

---

## 5. DISPOSITION

**`I09P2B_RATIFICATION_HOLD`.**

The trusted-root mechanics are sound and independently confirmed: an untrusted
actor cannot approve itself, the reviewed pin matches the shipped manifest, an
empty root admits nothing, and provenance-field mutation is refused. What fails
is the claim that matters most for G7: a forged record — one whose canonical
economic claim was replaced while its approval identity stayed valid — passes the
purported trusted verification boundary. Ratifying that boundary would certify a
guarantee the code does not provide.

I09P2a, I09b, I10, I11 status is unchanged: nothing is promoted, nothing is
ratified, no venue is certified.

---

## 6. SENSOR-B5-I09P2c — PROPOSED SCOPE (NOT IMPLEMENTED)

**Full-record verification and trusted integration contract.** Only what the
audit measured as missing:

1. `verify_trade_record(record, *, trusted_context)` — accepts the complete
   `T1TradeRecord`, re-derives the admitted row, and compares provider, venue,
   instrument identity, native field and native value, canonical field, canonical
   side against the approved transformation, source revision and PIT cutoff.
2. `verify_liquidation_record(record, *, trusted_context)` — same for the
   liquidation envelope, including the provider the admission currently omits.
3. Custody source: an inventory loader the record consumer does not supply
   (e.g. a storage-backed digest index signature), so `verify_evidence_custody`
   stops accepting a caller-authored map.
4. Intraday PIT: either an instant-precision `available_at` (additive, with
   historical dates preserved as day-start and labelled) or an explicit refusal
   for intraday evaluation — no silent date-level inference.
5. Integration contract: the initialization entry, the manifest source and the
   deployment assumptions, stated where an application can actually call them.
6. Tests: full-record mutation matrix (side, provider, venue, instrument, native
   field, native value, revision, cutoff, evidence ref, methodology) plus
   trust-source substitution and custody-forgery negatives.

Not in scope: any provider onboarding, any nonempty approval, I11 ratification,
I12, I17.

---

## 7. VERIFICATION EXECUTED IN THIS AUDIT

| Check | Result |
|---|---|
| Disposable provenance/custody/PIT probe | 18 observations recorded in §3 and §4 |
| `tests/crypto_sensor_fabric/normalization` | 1124 passed, exit 0 |
| `tests/crypto_sensor_fabric/storage/test_i11r2_binding_audit.py` | 4 passed, exit 0 |
| `b5_i05_time.py --check` | 86 rows, 0 fail; scope audit 7/7 |
| `b5_i06_replay_safety.py --check` | 14 rows, 0 fail; scope audit 8/8 |
| `b5_i09_semantics.py --check` | 35 rows, 0 fail, 3 unresolved; `8b3dbd3f…` |
| Tree after checks | unchanged (only the three preserved scratch paths untracked) |
| Full canonical suite | not rerun — accepted prior evidence `4522 passed, 14 skipped, exit 0` at the identical commit |

No test was skipped, xfailed or altered to reach these results.

---

## 8. GOVERNANCE

NO GOVERNANCE CHANGE. B5-I09a = OPERATOR_ACCEPTED; B5-I09b = DEFERRED; B5-I10 =
OPERATOR_ACCEPTED (bounded); B5-I11 = IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD;
B5-I09P2A = IMPLEMENTATION_COMPLETE, NOT RATIFIED (HOLD); B5-I09P2B =
IMPLEMENTATION_PARTIAL, NOT RATIFIED; B5-I09P2B audit = RATIFICATION_HOLD;
BLOC_05 = INCOMPLETE; all eight program gates NOT_YET_EARNED; B5-I12+ and BLOC_06
UNAUTHORIZED; RESEARCH = FROZEN; next_checkpoint_authorized = FALSE.
