# SENSOR-B5-WAVE1 — Independent Acceptance and Wave 2 Rolling Audit (R2)

**Label:** `SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT`
**Target:** `B5_WAVE1_INDEPENDENT_ACCEPTANCE_AND_WAVE2_AUDIT_PROGRESS`
**Mission:** `SENSOR-B5-WAVE1-ACCEPTANCE-WAVE2-ROLLING-AUDIT-R2`

| Item | Value |
| --- | --- |
| Audited branch | `agent/crypto-sensor-fabric-b5-wave1-audit-r2` |
| Audited tree | `bc53ada805b8309e6aaf4d31684afb27a2b0e370` (the Wave 1 candidate) |
| Tree matches candidate | **yes** — `git diff` against the candidate is empty |
| Wave 1 implementation | `agent/crypto-sensor-fabric-b5-wave1-r1` @ `bc53ada80` |
| Preserved prior corpus | `agent/crypto-sensor-fabric-b5-wave1-audit-r1` @ `02d172223` |
| P3 ratification | `e8abe280f3b64f497756dcad8f5824899112afd4` (not reopened) |
| Frozen authority | `4bb677f9e0266f4dc48405181696019f359ae49f` |
| Evidence directory | `bloc_05/b5_wave1_acceptance_r2/` (additive; §5 collision) |

This audit **added no production code, changed no fixture, ratified no provider and
activated no manifest**. It executed the previously authored corpus against the
actually published entry points and reports what happened.

---

## 0. Hard stops

| Prohibition | Status |
| --- | --- |
| Reopen P3 | not done — `e8abe280f` untouched |
| Change production implementation | not done — tree byte-identical to the candidate |
| Self-ratify provider evidence | not done — every fixture `NOT_REVIEWED`, `ratified_golden=false` |
| Activate the approval manifest | not done — shipped root is still `B5_I09P2A_EMPTY_TRUST_ROOT_V1` |
| Authorize a custody source | not done |
| Approve a methodology | not done — `B5_I08_UNITS_V1` still absent |
| Merge to production | not done |
| Advance Bloc 6 | not done |
| Launch a duplicate full regression | not done — no canonical run started (§8) |

---

## 1. Executive result

Wave 1's four new normalizers **behave as the frozen contract requires on every
fixture this audit could execute**: **114 of 114 assertions passed**, with **0
executed fixture failures**. The failures this audit did find are *capability
boundaries and integration seams*, not wrong answers, and they are reported
separately below rather than folded into a pass.

| Surface | Executed | Result |
| --- | --- | --- |
| I12 open interest | 7 fixtures | pass — no USD minted, no unit promoted without authority |
| I13 funding | 3 fixtures | pass — no 8h default, realized/predicted distinct |
| I14 book snapshot | 11 fixtures | pass — certification requires full + contiguous |
| I15 positioning | 3 fixtures | pass — population carried, no generic ratio slot |
| I15 basis | 0 executed | **blocked** — no provider-native basis field exists |
| I14 sequence corpus | 10 controls | **7 supported, 3 capability gaps** |
| `admission.py` | 20 checks | pass — ladder and model laws hold |
| I16 lineage (preliminary) | 13 checks | pass — IDs deterministic, **resolution absent** |
| I21 properties | 15 controls | pass |
| I20 captured evidence | 13 payloads | **acquired, not ratified** |

### Corpus disposition (all 58 fixtures, unmodified)

| Status | Count |
| --- | --- |
| Executed and passed | 24 |
| Executed and failed | **0** |
| Fixture adaptation required | 23 |
| Unsupported sensor family (no entry point) | 11 |
| Executed with adaptation notes | 18 |

The 58-fixture corpus was consumed **unmodified**. Its corpus digest was
recomputed and matches the r1 declaration
(`b15278b0…a6295b`), with tier counts preserved exactly: 27 documented-shape,
28 synthetic-adversarial, 3 provider-reference.

---

## 2. I12–I15 rolling verification

Entry points exercised: `normalize_open_interest`, `normalize_funding`,
`normalize_book_snapshot`, `normalize_positioning`, `normalize_basis`.

**Nothing in this lane is reimplemented as an oracle.** The adapters only translate
fixture fields into the production input models; the assertions read the returned
records. Every family also carries a **positive intermediate control**: a
self-minted synthetic approval root (built by this probe, not the producer's test
helper) proving the admission *mechanism* can admit, so a blanket refusal cannot
masquerade as a pass.

What the executed fixtures confirmed:

* `oi_usd` is never a number, with or without an admitted unit row.
* An OI unit reading is never promoted from a caller claim; `NO_REGISTRY` and
  `UNTRUSTED_AUTHORITY` are the recorded causes.
* A funding interval is never defaulted to 28800 s, and the comparable
  equivalents refuse when the interval is absent.
* No funding notional or PnL slot exists on the record at all.
* `book_state_certified` is true **iff** full snapshot **and** contiguous sequence.
* A crossed book, an ascending bid list and a bid ≥ ask are all refused at input.
* A reconstructed book metric cannot name an uncertified source book.
* Positioning carries `population_scope` verbatim and offers **no**
  `long_short_ratio` slot, so cross-population equivalence is structurally
  unavailable.
* Basis refuses cross-venue synthesis, self-basis, and annualisation without a
  method.

### Why 23 fixtures could not execute

Not tolerance — representation. Each is a stated cause in
`results/03_i12_i15_execution.json`:

| Cause | Count |
| --- | --- |
| Payload has no provider-native basis field (every basis would be derived) | 6 |
| No native funding field in the payload | 8 |
| No native OI value field in the payload | 5 |
| No book levels in the payload | 3 |
| No sequence token in the payload | 2 |
| Range-update chain the entry point cannot consume | 8 (overlapping) |
| Expectation vocabulary not in the frozen enums (`UNVERIFIED`, `USD_NOTIONAL`) | 5 |

The last row is an **audit-side** vocabulary mismatch, recorded so it cannot be
mistaken for an implementation defect: the r1 corpus used expectation tokens
(`OI_UNIT_UNVERIFIED`, `oi_native_unit: UNVERIFIED`) that are not members of the
frozen enums. The fixtures remain valid as evidence; their expectation keys are
prose, not enum values.

---

## 3. I14 sequence controls — 7 of 10 supported

| Control | Outcome |
| --- | --- |
| Contiguous successor | supported and correct |
| Missing sequence (2006 → 2008) | supported and correct |
| Duplicate update | refused — **by exception**, not a typed status |
| Out-of-order update | refused — by exception |
| Snapshot/update mismatch | **not implemented** — no surface consumes `(snapshot, updates[])` |
| Sequence reset | **conflated** with an out-of-order update; no epoch member |
| Metric across a gap | supported — enforced by the record, not by a caller flag |
| Valid recovery snapshot | partially supported — no discard rule, no authorization ref |
| **Range update (U/u)** | **unsupported** — see F1 |

The implemented capability set is deliberately narrow and honest:

```
pairwise classification      PRESENT
crossed-book refusal         PRESENT (input law)
metric gap propagation       CALLER-SUPPLIED AND RECORD-ENFORCED
chain ingestion              ABSENT
snapshot + delta reconstruction ABSENT
epoch recovery               ABSENT
gap-recovery authorization   ABSENT
range-update sequences       ABSENT (single-token comparison only)
```

`bloc_05/04` §6.2 defines the update vocabulary and a sequence status; it does not
require a reconstruction engine in I14. The eight-case corpus therefore asks for
more than the checkpoint contracted, and that is recorded as a scope boundary
rather than a defect.

### F1 — a contiguous range update is classified as a gap

Measured against the published entry point:

```
classify_sequence("1005", "1000") -> GAP_DETECTED
classify_sequence("1001", "1000") -> CONTIGUOUS
```

Both calls describe the **same** contiguous update (`U=1001, u=1005` following a
snapshot at `lastUpdateId=1000`). The classifier has one successor token and no
range member, so the verdict depends on which token the adapter happens to pass —
and a correct adapter that passes the range tail reports a gap for a chain that
never gapped. Eight of the fifty-eight fixtures sit on this seam.

---

## 4. Shared semantic admission (`sensors/admission.py`)

20 checks, 20 passing. The requested distinctions resolve as follows.

| Question | Answer |
| --- | --- |
| Registry-derived confidence? | **Yes** — read from the row; no `confidence` parameter exists on the ladder (verified by signature inspection) |
| Correct provider identity? | Yes — a foreign provider's row does not resolve |
| Correct sensor-family identity? | Yes |
| Correct canonical field? | Yes — a row for `oi_base` cannot admit `oi_native_unit` (`FIELD_MISMATCH`) |
| Approved methodology and evidence? | Yes — `UNCITABLE_METHODOLOGY`, then `PENDING_EVIDENCE` |
| Pending evidence rejected? | Yes — twice: the I09 registry refuses a pending token at verified confidence, and the **approval manifest refuses to cite it at all** |
| Ambiguous mappings rejected? | Yes — `AMBIGUOUS_MAPPING` |
| Corroboration-only rejected as equivalence? | Yes — `CORROBORATION_ONLY_MAPPING` |
| Fabricated authority rejected? | Yes — a hand-built admitted decision fails the model law; an admitted field must name approval id **and** registry digest |
| No promotion under the empty manifest? | Yes — `artifacts: {}` admits nothing |

**Model validity vs authenticated provenance** (the distinction the mission asked
for) is the one real seam here:

* **Model validity: proven.** The record refuses an admitted decision that lacks
  provider field, equivalence class, confidence, evidence reference, methodology,
  mapping version, approval id or registry digest.
* **Authenticated semantic provenance: absent.** `admission_approval_id` and
  `admission_registry_digest` are carried as unverified strings. Nothing binds the
  decision to a reviewed root cryptographically. A caller that can construct a
  `SemanticAuthority` reaches `admitted=True` exactly as a reviewed producer does,
  so the trust boundary is caller honesty plus procedure, not a signature.

This is a contract observation about the *trust model as published*, not a defect
introduced by Wave 1: I09 P2a defined the authority surface and Wave 1 reuses it.

---

## 5. I16 independent verification

13 checks, 13 passing. Deterministic identity is **accepted**; lineage resolution
is **absent**.

Verified:

* repeated derivation is stable (5 repeats, one id);
* the identity key contains **no** normalised value member, so a corrected number
  cannot collide with the original row;
* every identity member separates the id — provider, venue, contract instance,
  native identity, revision, generation, family;
* derivation is order independent (recomputed in reverse order);
* `created_at` is excluded from the generation fingerprint, while a code-commit
  drift is refused;
* the gate still reports `NOT_CLOSED` with 7 of 8 families missing.

### F6 — completeness proves presence, not resolvability

`assert_lineage_complete` reads the record's **self-declared** `lineage`
descriptor. Three fabricated references —
`arbitrary://nothing-1`, `arbitrary://nothing-2`, and 64 `f` characters — satisfy
the assertion:

```
assert_lineage_complete(record with fabricated refs) -> accepted
```

So "reference presence", "reference identity", "evidence resolution", "correct
evidence digest" and "coherent lineage chain" are **five different claims**, and
only the first two are established. A record can name a whole chain that does not
exist. This is the substantive I16 finding and it does not close the gate.

---

## 6. I20 captured-evidence development

Thirteen first-party payloads were captured from **documented, free, unauthenticated
public** endpoints. No trading endpoint, no authenticated endpoint, no paid tier, no
access-control circumvention, and no UI scraping was used. Raw bytes are retained
**outside the repository** in external approved evidence storage; Git carries the
compact manifest, the checksums and the reproduction record
(`CAPTURED_EVIDENCE_MANIFEST.json`). Every captured payload's digest was
**re-verified on disk** before the manifest was trusted.

| Requirement | Result |
| --- | --- |
| Three or more providers | **4** — OKX, Deribit, Gate, Kraken |
| BTC and ETH | **both** |
| Linear and inverse contracts | **both** |
| Required families where genuinely available | OI, funding, book snapshot (**3 of 8**) |

### F7 — positioning and basis are genuinely unavailable

| Family | Why absent |
| --- | --- |
| Positioning | The venue publishing a documented top-trader ratio family answered **HTTP 451** (jurisdictional block); a second answered **HTTP 403**. No lawful free access existed, so no capture was fabricated. |
| Basis | No captured endpoint publishes a provider-native basis field. Every basis is derived, and deriving one is not authorized. |
| Trade / liquidation | Not in this slice; trade semantics were already exercised offline in r1. No documented free event-level liquidation endpoint is published by the captured venues. |

One capture attempt was **rejected by this audit's own validation**: Kraken's
orderbook answered HTTP 200 with `{"result":"error","error":"marketUnavailable"}`
for the retired `PI_XBTUSD`. An HTTP 200 is not a capture. The live symbol is
`PF_XBTUSD`, and the corrected attempt is what is recorded.

### What the captures actually establish

These are the facts the thirteen payloads support. Each is **measured** (arithmetic
separable inside the payload) or **declared** (field name / documentation), and the
distinction is recorded per record.

1. **OKX publishes three separable OI quantities.** `oi`, `oiCcy` and `oiUsd` appear
   together, and:

   | Instrument | `oi` | `oiCcy` | `oi / oiCcy` | `oiUsd / oiCcy` |
   | --- | --- | --- | --- | --- |
   | BTC-USDT-SWAP (linear) | 3 203 435.41 | 32 034.35 | **100** | ≈ 59 941 (the price) |
   | ETH-USDT-SWAP (linear) | 6 730 233.15 | 673 023.32 | **10** | ≈ 1 663 (the price) |
   | BTC-USD-SWAP (inverse) | 6 790 506.20 | 11 334.83 | **599.08** | ≈ 59 908 (the price) |

   Three different native quantities for one observation. The ratio is not
   asset-constant, so a contract count cannot be read as a coin quantity. This is
   **first-party confirmation of the r1 Tier-A claim** that a single canonical
   `oi_native` would merge three measurements.

2. **OKX `fundingTime` is in the future relative to `ts`.** Measured on both
   captures: `fundingTime` 1 795 852 800 000 vs `ts` 1 795 825 623 668. A reader
   that treats it as the time the rate became known misdates the observation.
   `nextFundingRate` was the **empty string**, which is not zero and must not be
   coerced.

3. **Kraken publishes two funding fields that disagree by ~the index price.**
   `fundingRate` 0.04439133684998005 and `relativeFundingRate` 7.41533333333e-07
   differ by a factor of **59 864**, which is the contemporaneous BTC price. So one
   field is not a per-interval fraction — but the payload does not say which
   convention either uses, and this audit does not invent it.

4. **Kraken returns orderbook bids worst-first.** 1 147 levels, first element `1`,
   best bid `59 900`: bids arrive in **ascending** price order, so `bids[0]` is the
   deepest bid, not the best one.

5. **Gate carries `funding_interval` (28 800) and `quanto_multiplier` (0.0001)** as
   contract metadata, and its open interest is `total_size` on a different endpoint
   (`/tickers`, 634 712 786 contracts) from the one carrying the multiplier.

6. **Deribit reports open interest as a USD notional** (817 904 980), which divided
   by its mark price yields ≈ 13 653 BTC — a different native unit from a contract
   count.

### I20 readiness

**Not ratified, and not ratifiable by this audit.** A capture proves what a
provider returned at one instant; it does not prove what the field means. The 27
documented-shape fixtures remain `NOT_REVIEWED`, and promoting any of them toward
golden status requires operator-visible review. What the captures do provide is
the first-party payload evidence the r1 corpus expressly lacked, for three of the
eight families.

---

## 7. I21 property controls

15 controls, 15 passing: byte-determinism of normalisation; canonical flag ordering;
`oi_usd` never numeric; `B5_I08_UNITS_V1` still absent from the methodology
registry; JSON round-trip stability; crossed-book and disordered-book refusal; a
USD value cannot be stored as a positioning ratio; cross-venue and unmethodised
annualised basis refusal; an amount cannot be normalised as a funding rate; an
interval that contradicts its period bounds is refused; no sensor module imports
`hashlib`, `uuid`, a network client or reads a wall clock (AST scan, not substring
matching).

---

## 8. Canonical reconciliation

**Not started, and deliberately so.** Agent 1 owns canonical execution and no
Wave 1 raw execution bundle exists. No full regression was launched by this audit,
and **P3 canonical acceptance is not inherited as covering Wave 1**.

Awaiting: exact candidate SHA of the executed tree, external collection anchor,
raw executed node set, JUnit accounting with explained skips, artifact hashes, per
group exit codes, and a restoration record. The retained controls are unchanged:
node sets are compared as sets, every skip carries a stated cause, and
missing/extra/duplicate nodes remain three distinct defects.

---

## 9. Wave 2 rolling audit

No Wave 2 checkpoint is published. `agent/crypto-sensor-fabric-b5-wave2-r1` does not
exist yet, so I17 (duplicate/revision), I18 (generation publication) and I19
(pit/query enforcement) have nothing to verify. The only Wave 2-adjacent artefact in
the audited tree is the **preliminary** I16 module audited in §5, which states its
own incompleteness. The I21 end-to-end properties developed here are ready to be
re-pointed at I17–I19 as they land.

---

## 10. Findings index

| # | Finding | Class |
| --- | --- | --- |
| F1 | A contiguous `U/u` range update is classified as a gap; the verdict depends on which token the adapter passes | **candidate interface gap** |
| F2 | Duplicate, out-of-order and reset sequences are refused by exception, and a reset is indistinguishable from an out-of-order update | **candidate interface gap** |
| F3 | No chain ingestion, snapshot/delta reconstruction or epoch-recovery authorization exists | scope boundary |
| F4 | The canonical book input requires best-first ordering while a documented provider returns bids worst-first; no adapter exists | integration gap |
| F5 | The frozen OI scope vocabulary cannot express "bucket aggregation unresolved" | contract gap |
| F6 | Lineage completeness proves presence, not resolvability; fabricated references pass | **I16 preliminary defect** |
| F7 | Positioning is jurisdictionally blocked and basis has no provider-native field, so 5 of 8 families have no captured evidence | unavailable data |
| F8 | The shipped approval root is empty, so no semantic admission is possible today | missing authority |
| F9 | Admitted decisions carry an unverified approval id and digest; model validity ≠ authenticated provenance | trust-model observation |
| F10 | Canonical reconciliation has no bundle to verify | deferred integration |
| F11 | Wave 2 has no published checkpoint to audit | deferred integration |
| F12 | The `evidence/bloc_05/b5_wave1_r1/` namespace is shared; this audit published to an additive directory | resolved |
| F13 | Five r1 expectation tokens are not members of the frozen enums | audit-side vocabulary mismatch |
| F14 | Kraken's retired `PI_XBTUSD` answers HTTP 200 with an error envelope; an HTTP 200 is not a capture | measurement discipline |

`60_FINDINGS.json` carries the machine-readable form with evidence pointers.

---

## 11. Reproduction

```bash
# acceptance probe (offline, deterministic, no network)
B5_QUANT_LAB="$PWD/quant-lab" \
B5_EVIDENCE="$PWD/quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/b5_wave1_acceptance_r2" \
B5_R1_CORPUS="../p3-rung1-audit-prep/quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/b5_wave1_r1" \
python probes/probe_acceptance.py.txt

# I20 acquisition (network; documented public endpoints only)
python probes/acquire_i20.py.txt
python probes/compact_capture.py.txt <evidence-dir>/CAPTURED_EVIDENCE_MANIFEST.json
```

Determinism was proven by running the probe under three environments —
`PYTHONHASHSEED=0/TZ=UTC`, `PYTHONHASHSEED=12345/TZ=Asia-Tokyo`,
`PYTHONHASHSEED=777/TZ=Europe/Berlin` — and requiring **byte-identical** result
artifacts. All three runs produced identical digests.

Package integrity: `sha256sum -c EVIDENCE_DIR.sha256`.

---

## 12. What this audit does not claim

* It does not claim Wave 1 is accepted. It claims the executable fixture subset
  passes and names what could not be executed.
* It does not claim any provider semantic is correct. It claims what four
  providers published, measured, at one instant.
* It does not claim I16 is sound. It claims IDs are deterministic and that lineage
  resolution is not implemented.
* It does not claim the sequence contract is satisfied. It claims 7 of 10
  capabilities are present and three are not.
* It does not claim canonical acceptance. No Wave 1 run was verified.
