# BLOC_05 — SENSOR-B5-I09P2dR1 — INDEPENDENT CUSTODY, SCOPED VERDICT AND REGRESSION AUDIT

**Audited HEAD:** `cce32c549ea3f4b86b1ac1615856e5d7b8148bde` (local == remote at audit start)
**Production branch:** `agent/crypto-sensor-fabric-build` (linear on `0f0b3195b4`)
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Parallel research reference:** `agent/crypto-sensor-fabric-parallel-audit @ 9cec9679065cf4d745811b372446ef7441d7ffbd`
**Entering status:** `I09P2D_IMPLEMENTATION_PARTIAL`
**Audit disposition:** `I09P2D_RATIFICATION_HOLD`

Read-only audit. No production file, test file, frozen plan or historical artifact
was modified; no existing test was rewritten; no provider was certified. The three
preserved scratch paths (`.bu_tmp/`, `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`,
`scripts/b5_i03_redteam_results.json`) are untouched and unstaged. Probes are
disposable (`.bu_tmp/p2dr1_probe.py`, 54 cases) and are not part of the tree.

---

## A. Audited commit and custody

| Check | Observed |
|---|---|
| HEAD == remote | `cce32c549e` == `cce32c549e` |
| Branch / ancestry | `agent/crypto-sensor-fabric-build`, linear on `0f0b3195b4`, no rewrite |
| P2d surface | exactly 8 disclosed paths, +1596 / −47 |
| Frozen Bloc 5 planning docs | `git diff dafcd86a02 HEAD -- bloc_05/*.md` empty (7 documents) |
| Production manifest | `artifacts == {}`, `revoked == []`, sha `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` |
| P2cR1 audit record | unchanged by P2d (not in the 8-path surface) |
| I09a / I10 acceptance | unchanged; suites pass |
| I11 | `IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD` (unchanged) |
| Ledger | exactly one `## 196`; §195 P2cR1 heading intact |
| Scratch paths | preserved, unstaged |

**Governance correction recorded:** no separate worktree could be created for this
audit — the disk was 100 % full and `git worktree add` failed with
`No space left on device`. Testing therefore ran in the existing worktree against
the committed tree at `cce32c549e`; **no commit, stage or edit was made on the
production branch**. This is a departure from the directive's preferred isolation
and is disclosed rather than hidden.

---

## B. Source reconstruction of the four repairs

| Finding | Original failure | Changed function | New enforcement | Remaining caller control | Proving test | Alternative bypass |
|---|---|---|---|---|---|---|
| F-R1-01 | `held_digest()` trusted as self-report | `_custody_verified`, `TrustedCustodyProvider`, `BlobStoreCustody.read_evidence` | verifier hashes returned bytes via `authority.evidence_digest` | caller can still hold the approved bytes itself | SEC-D01..D10; probe C01–C10 | C04/C05b: caller-minted object returning real bytes earns `custody_verified=True` (**byte integrity only**) |
| F-R1-02 | `downstream_trusted` read as whole-record authenticity | `RecordVerification`, `_SCOPE_NOTE`, `_UNVERIFIED_DIMENSIONS` | `trust_scope` fixed to `ECONOMIC_FIELD_BINDING`; six dimensions always enumerated; empty list refused | the Boolean alone is still actionable by any consumer | SEC-D15..D18; probe C08 | none within the module; **no consumer enforces the scope** |
| F-R1-03 | contradictory verdicts constructible | `RecordVerification._trust_laws`, `assert_trustworthy` | conjunction + non-empty unverified list + proof-gated positive claims | `model_copy(update=...)` still bypasses validators | SEC-D11..D14; probe E01–E15 | E13: bypass constructible, only the explicit guard catches it |
| F-R1-04 | approval with no availability admits any cutoff | `_assert_intraday_pit` | `PIT_AVAILABILITY_MISSING` | none at the record entry | SEC-D21; probe F01 | **F02: `verify_mapping_provenance` still admits it** |

`apply_declared_side_transformation` is unchanged and still refuses liquidation
rows, non-Binance methodologies and non-boolean natives, so no polarity is
inferred from prose, another venue or tape direction.

---

## C. Custody and byte-forgery results (54-probe independent suite)

| Probe | Attack | Observed |
|---|---|---|
| C01 | object exposing only `held_digest()` | `TypeError` |
| C02 | plain `{reference: digest}` dict | `TypeError` |
| C03 | `read_evidence()` returns wrong bytes | `CUSTODY_UNVERIFIED` |
| C04 | caller-minted object returns the *approved* bytes | `custody_verified=True`, `custody_source_authorized=False` — **byte integrity only** |
| C05a | `BlobStoreCustody` over a colluding store holding other bytes | `CUSTODY_UNVERIFIED` |
| C05b | same adapter, colluding store holding the approved bytes | `True` / `False` (index is caller-supplied; no ownership) |
| C06a | real `LocalBlobStore`, object absent | `CUSTODY_UNVERIFIED` |
| C06b | real store, index names another digest | `CUSTODY_UNVERIFIED` |
| C07 | approved bytes vs a different approval's expected digest | `CUSTODY_UNVERIFIED` |
| C08 | approved bytes + forged venue/instrument/revision/acquisition | `downstream_trusted=True`, scope `ECONOMIC_FIELD_BINDING`, 6 unverified dimensions |
| C09 | custody returns approved bytes at verification, different bytes afterwards | verification `True`; the later read differs — **no TOCTOU binding after verification** |
| C10 | approved synthetic blob via the accepted Bloc 4 API | `True` / `False` |

The P2cR1 critical finding is genuinely closed: a digest with no bytes cannot pass,
and a store that merely claims integrity is overridden by the verifier's own hash.
What remains is exactly what the directive told this audit to classify separately:
**content equality is not operational custody**. `custody_source_authorized` is
`False` in every probe, including the honest one, because no application-owned
handle exists in this tree. C05b and C09 are the two residual facts an integrator
must inherit: the operator index decides which object is read, and the verified
bytes are not re-bound when consumed later.

---

## D. Trust scope and consumer analysis

Static survey of the whole tree: `downstream_trusted`, `RecordVerification`,
`trust_scope`, `unverified_dimensions`, `custody_source_authorized` and
`assert_trustworthy` appear **only** in `sensors/verification.py` and the two test
suites. `RecordVerification` is imported by no production module; there is no
ingestion, scoring, replay or storage consumer in this repository.

Consequences, stated plainly:

* the scope is enforced **at construction** by the result model, and every verdict
  names the six dimensions it does not cover — that part is real and measured;
* the scope is **not enforced at any consuming boundary**, because there is no
  consuming boundary. A future consumer can read `downstream_trusted` and ignore
  `trust_scope`, `unverified_dimensions` and `custody_source_authorized`, and
  nothing in this tree would stop it;
* therefore consumer safety is **unverified, not proven**. It is a contract term
  for the integration checkpoint, not an established property here.

A scoped economic verdict is not full market-record authenticity, and nothing in
the committed code lets a reader mistake one for the other *inside the module* —
but the module alone cannot protect a consumer that reads one Boolean.

---

## E. Model-copy and serialization attacks

| Probe | Construction | Observed |
|---|---|---|
| E01 | `downstream_trusted=True`, mapping approval false | `ValueError` |
| E02 | `downstream_trusted=True`, transformation false | `ValueError` |
| E03 | `downstream_trusted=True`, custody false | `ValueError` |
| E04 | `downstream_trusted=True`, PIT false | `ValueError` |
| E05 | positive trust, no verified fields | `ValueError` |
| E06 | positive trust, empty `unverified_dimensions` | `ValueError` |
| E07 | `source_lineage_verified=True`, no proof | `ValueError` |
| E08 | `instrument_authenticated=True`, no reference | `ValueError` |
| E09 | `source_revision_authenticated=True`, no reference | `ValueError` |
| E10 | dimension claimed authentic *and* listed unverified | `ValueError` |
| E11 | `trust_scope="FULL_RECORD"` | `ValueError` |
| E12 | positive claims **with** proof references | accepted (the laws are not blanket refusals) |
| E13 | `model_copy(update={downstream_trusted: True, custody_verified: False})` | constructs; `assert_trustworthy()` → `CONTRADICTORY_VERIFICATION`; a valid result passes unchanged |
| E14 | JSON/`model_dump` reconstruction of the copied payload | `ValueError` |
| E15 | verifier-produced verdict re-validated | no refusal |

E13 is the residual: the guard exists and works, but no boundary in this tree
calls it. That is the same deferred-consumer gap as section D, not a second defect.

---

## F. PIT and liquidation

| Probe | Case | Observed |
|---|---|---|
| F01 | approval with neither availability field | `PIT_AVAILABILITY_MISSING` |
| F02 | same approval through `verify_mapping_provenance` | **no refusal** (residual; see below) |
| F03 | forged manifest as trusted context | `TRUSTED_CONTEXT_MISMATCH` |
| F04 | raw manifest bytes passed as context | `TypeError` |
| F05/F06 | date-only approval, same day 09:00Z / 23:59Z | `INTRADAY_PIT_AMBIGUOUS` |
| F07 | date-only approval, next day 00:00Z | admitted |
| F08 | instant availability 15:00Z, cutoff 14:59Z | `APPROVAL_NOT_YET_AVAILABLE` |
| F09/F10 | cutoff 15:00Z (equality) / 15:01Z | admitted |
| F11/F12 | availability `15:00-05:00` (=20:00Z), 19:59Z / 20:00Z | refused / admitted |
| F13/F14 | DST fall-back repeated hour (`01:30-04:00` = 05:30Z), 05:15Z / 05:45Z | refused / admitted |
| F15/F16 | missing cutoff / naive cutoff | `PIT_CUTOFF_REQUIRED` |
| F17 | revoked approval | `APPROVAL_REVOKED` |
| F18 | cutoff before availability | `APPROVAL_NOT_YET_AVAILABLE` |
| F19 | cutoff after `valid_until` | `AUTHORITY_EXPIRED` |

**F02 is a genuine residual, not a probe artifact.** The record entry
(`verify_trade_record` / `verify_liquidation_record`) refuses an availability-less
approval, but the older mapping entry `verify_mapping_provenance` still admits it
because the check lives in `verification._assert_intraday_pit`, not in the
authority loader. A caller that decides "was this approval operative at cutoff C"
through the mapping path gets no constraint at all. P2D-16 is therefore PARTIAL,
not PASS.

| Probe | Liquidation case | Observed |
|---|---|---|
| G00 | baseline | `mapped=True`, `transform=False`, `down=False` |
| G01 | canonical-only rewrite | `CANONICAL_VALUE_MISMATCH` |
| G02 | admission-only rewrite | `CANONICAL_VALUE_MISMATCH` |
| G03 | **coordinated** record + admission + native rewrite | `mapped=True`, `transform=False`, `down=False` |
| G04 | cross-field admission | `NATIVE_FIELD_MISMATCH` |
| G05 | canonical+admission rewritten, execution side contradictory | `CANONICAL_VALUE_MISMATCH` |

Liquidation economic uncertainty is preserved exactly as the frozen authority
requires: the coordinated forgery is accepted as a *mapping*, refused as an
*economic transformation*, and never earns downstream trust. No transform was
invented anywhere in the audited surface.

---

## G. Regression reconciliation — **FAIL**

### Universe and coverage

| Quantity | Value |
|---|---|
| Canonical files | 223 (`quant-lab/tests/crypto_sensor_fabric/**/test_*.py`) |
| Canonical collection | **4616** tests |
| Partition entries | 220 files (3 `i11r1` files collect 0 tests: they are import-skipped integration files) |
| Union of partition node-ids | 4616 — **0 omitted, 0 duplicated, 0 foreign** |

Coverage is exact at node-id level, so the partition scheme is auditable.

### Independent execution (11 partitions, sequential, no overlap)

| PART | rc | passed | skipped | failed | collected |
|---|---|---|---|---|---|
| 1 | 0 | 459 | 0 | 0 | 459 |
| 2 | **1** | 464 | 0 | **1** | 465 |
| 3 | 0 | 465 | 0 | 0 | 465 |
| 4 | 0 | 462 | 0 | 0 | 462 |
| 5 | 0 | 464 | 0 | 0 | 464 |
| 6 | 0 | 464 | 3 | 0 | 467 |
| 7 | **1** | 452 | 2 | **1** | 455 |
| 8 | 0 | 462 | 4 | 0 | 466 |
| 9 | 0 | 370 | 1 | 0 | 371 |
| 10 | 0 | 461 | 1 | 0 | 462 |
| 11 | 0 | 80 | 0 | 0 | 80 |
| **TOTAL** | **2 nonzero** | **4603** | **11** | **2** | **4616** |

### The two failures, reproduced in isolation

Both are the **P2d commit itself**, and both are one root cause: the checkpoint
added one tracked Python file (`test_b5_i09p2d_custody_scope_pit.py`) without
updating the two governance count pins that the repository measures against
`git ls-files '*.py'`.

| Test | Assertion |
|---|---|
| `test_b5_i05_scope_audit.py::test_the_governance_audit_republish_is_mechanical_only` | `assert 1094 == 1095` — `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` still records `python_files_scanned: 1094`; the index now tracks 1095 `.py` files |
| `test_i11r2_binding_audit.py::test_governance_binding_audit_is_measured_and_committed` | `audit artifact drifted` at byte 4428 (`'4' != '5'`) — the rebuilt audit carries 1095, the committed artifact carries 1094 |

They reproduce individually (`rc=1` for each, on a tree with no other test running),
so they are not overlap artifacts. They are a **committed regression**: the P2d
evidence reports "governance 4 passed" and "I05 86/86/0 (+7/7)", but those numbers
were measured *before* the new test file was staged. `git ls-files` sees staged and
committed files, so the same commands fail once the file is tracked. **The tree was
never regression-tested as committed.**

### The six-failure anomaly in the P2d record

| Claim in `BLOC_05_I09P2D_IMPLEMENTATION_EVIDENCE.md` | Audit observation |
|---|---|
| six failures in a first storage chunk pass, "did not reproduce" | the only surviving trace is one summary line (`chunk8_first_pass.txt`); **no test identity and no failure trace were retained**, so the claim cannot be checked either way |
| chunk totals 4604 passed / 11 skipped / 4615 collected | the 11 chunk summaries sum to 4604 + 11 = **4615**, while the canonical collection is **4616**; partition 3 recorded 464 passed against 465 collected. One test is unaccounted for in the P2d arithmetic |
| P2d suite "39 passed" (ledger §196) vs "40-test suite" (evidence §9) | the suite collects and passes **40**; the ledger entry is wrong |
| matrix row P2D-22 shows `—`, while the operator report claimed 23 PASS / 1 PARTIAL | the committed matrix itself contains a blank gate that was counted as PASS in the report |

### Environment finding

The audit's single-invocation run — the shape the P2d record could not complete —
failed en masse at ~68 % because the volume reached **4 MB free**; stale
`pytest-of-wifik` temp held ~1.2 GB and was reclaimed afterwards. The earlier
"host terminated the run at 74 %" episodes are consistent with this exhaustion, not
with nondeterministic code. Partitions then completed cleanly apart from the two
real failures. **Classification: `FAIL`** — the failures are reproducible at the
audited commit, so the environment does not excuse them. P2D-22 is not awarded.

---

## H. Historical artifact and pin audit

| Check | Observed |
|---|---|
| `authority/__init__.py` endings | 998 CRLF, 0 bare LF (preserved) |
| `verification.py` endings | 0 CRLF, 1026 bare LF |
| P2c / P2d / I10 test endings | 0/986, 0/1011, 477 CRLF (each preserved) |
| I05 producer `--check` | exit 0 — 86 rows / 86 pass / 0 fail; scope 7/7 |
| I06 producer `--check` | exit 0 — 14 rows / 14 pass / 0 fail; scope 8/8 |
| I09 producer `--check` | exit 0 — 35 rows / 35 pass / 0 fail / 3 unresolved; artifact `845f1c660cd659dafc0e00503ce10264647eb0b9b85dd63db1b3ee6db77edde2` == disk |
| I09 unresolved states | unchanged (I08 units, depth-bps, T2 CVD) |
| Production manifest | `artifacts == {}`, pin == bytes |
| Ledger | one `## 196`, §195 intact |
| Unauthorized-module negative probes | I10/I11 scope audits pass unmodified |

**`bloc_04` side effects, classified rather than silently restored:** at audit start
11 committed `bloc_04` artifacts were dirty from the P2d test runs (they were
excluded from the P2d commit, correctly). After the audit's own partitions they were
compared to `HEAD`: **7 semantically identical**, **4 semantically different**
(`I15R1_TOCTOU`, `I15_MANIFEST_SCAN`, `I15_RESOURCE_BOUNDS`, `I15_SECRET_SAFETY` —
matrices that carry environment-measured fields such as `platform` and
`files_scanned`). All 11 were then restored to their committed bytes with
`git checkout --`; none was staged. No historical evidence was rewritten, and no
regenerated variant was published.

---

## I. Corrected P2D-01 … P2D-24 matrix

| GATE | EXPECTED | OBSERVED | EVIDENCE | RESULT | LIMITATION |
|---|---|---|---|---|---|
| P2D-01 | start at `0f0b3195b4`, linear, no rewrite | 8-path fast-forward, local == remote | `git rev-parse` / `ls-remote` | PASS | audit could not use a separate worktree (disk full) |
| P2D-02 | frozen planning docs byte-identical | `git diff dafcd86a02 HEAD -- bloc_05/*.md` empty | `git diff` | PASS | none |
| P2D-03 | four findings measurable pre-repair | closure of all four measured at HEAD; pre-repair RED taken from the P2d record | probes C/E/F, SEC-D01/D11/D21 | PARTIAL | RED not re-executed at `0f0b3195b4` |
| P2D-04 | no trust from `held_digest()` alone | `TypeError` (C01), dict `TypeError` (C02) | probe C01/C02 | PASS | none |
| P2D-05 | application-owned custody source | absent; `custody_source_authorized=False` in every probe | C04/C05b/C10 | PARTIAL | no initializer exists in this tree |
| P2D-06 | verifier hashes bytes itself | digest computed in `authority.evidence_digest`; lying store overridden | C03/C05a/C06b | PASS | none |
| P2D-07 | scoped trust verdict | scope fixed and enforced at construction; **no consumer enforces it** | C08, section D | PARTIAL | consumer safety unverified (no consumer exists) |
| P2D-08 | out-of-scope dimensions enumerated | six dimensions on every verdict; empty list refused | C08, E06 | PASS | none |
| P2D-09 | contradictory states unrepresentable | 11/11 constructions refused | E01–E11 | PASS | direct payloads only |
| P2D-10 | JSON reconstruction re-runs the laws | `ValueError` | E14 | PASS | none |
| P2D-11 | copy bypass detectable | copy constructs; guard raises `CONTRADICTORY_VERIFICATION` | E13 | PARTIAL | no boundary calls `assert_trustworthy` |
| P2D-12 | lineage never falsely claimed | `False` + note; positive claim needs proof | E07/E12 | PASS | authorship unverifiable by construction |
| P2D-13 | instrument/venue not falsely claimed | `instrument_authenticated=False`, venue enumerated | C08, E08 | PASS | approval names no instrument |
| P2D-14 | revision data is not authentication | `source_revision_authenticated=False` | C08, E09 | PASS | none |
| P2D-15 | liquidation uncertainty preserved | coordinated rewrite `mapped=True`/`transform=False`/`down=False` | G00–G05 | PASS | no executable transform exists |
| P2D-16 | PIT missing availability fails closed | record entry refuses; **mapping entry does not** | F01, F02 | PARTIAL | `verify_mapping_provenance` still admits it |
| P2D-17 | instants ordered, DST honoured | offset, equality, same-day, repeated-hour matrix correct | F05–F14 | PASS | none |
| P2D-18 | I10 nonregression | 361 passed in the i09/i10/i11 selection | focused run | PASS | none |
| P2D-19 | I11 nonregression | four sides, all-or-nothing, maker/taker unchanged | focused run | PASS | none |
| P2D-20 | pinned root, empty approvals | sha `3d707c59…`, `artifacts == {}` | manifest read | PASS | pin strength = review of the commit |
| P2D-21 | producers reproduce; pins declared | I05 86/86/0 +7/7, I06 14/14/0 +8/8, I09 35/35/0/3, `845f1c66…` | producer `--check` ×3 | PASS | none |
| P2D-22 | no new failure | **2 reproducible failures** (1094 vs 1095 count pins) | partitions 2 + 7; isolated reruns | **FAIL** | committed tree was never tested as committed |
| P2D-23 | no program-gate promotion | none attempted | diff surface | PASS | none |
| P2D-24 | local/remote equality, fast-forward only | `cce32c549e` == remote; audit commit on a separate branch | `git ls-remote` | PASS | production branch not modified |

**Tally: 18 PASS, 5 PARTIAL, 1 FAIL.** No blank gate is counted as PASS.

---

## J. Ratification disposition

**`I09P2D_RATIFICATION_HOLD`.**

Bounded recognition, recorded explicitly: byte-level custody closure, the scoped
verdict with mandatory enumeration, the result laws, the record-level PIT closure
including offsets and the DST repeated hour, liquidation economic uncertainty, and
all historical pins survived independent attack. The four P2cR1 vectors are closed
**as measured**, and the critical custody forgery no longer yields a verdict.

Ratification is withheld for two reasons, both measured at the audited commit:

1. **A committed regression.** The checkpoint added a tracked `.py` file and left
   two governance count pins at 1094; two canonical tests fail deterministically at
   `cce32c549e`. The implementation's "governance 4 passed" and clean partition
   totals predate the file being staged, so its regression evidence does not apply
   to the committed tree.
2. **A closure that is narrower than claimed.** PIT fail-closure is enforced at the
   record entry only; `verify_mapping_provenance` still admits an availability-less
   approval. And the scoped Boolean has no enforcing consumer, so "safe downstream
   interpretation" is a contract for the integration checkpoint, not an established
   property.

Neither reason requires inventing a provider transform, a custody owner or an
ingestion application; both are recorded as deferred boundaries with a bounded
remediation.

### Bounded remediation (specified, NOT executed — production edits are not authorized here)

1. Update `python_files_scanned` from 1094 to 1095 in
   `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` through the established
   mechanical-republish mechanism (exactly one removed + one added line), then
   re-run the canonical set **with the new test file already tracked**.
2. Move the missing-availability refusal into the authority layer (or have
   `verify_mapping_provenance` delegate to it) so both entries fail closed.
3. State, in the integration contract that will consume `RecordVerification`, that
   `trust_scope`, `unverified_dimensions` and `custody_source_authorized` are
   mandatory reads and that copied results must pass `assert_trustworthy()`.

---

## K. Exact remaining external dependencies

1. An application-owned initializer that reads the reviewed manifest and holds the
   custody store, so `custody_source_authorized` can become a real claim (and so
   `INTEGRATION_STATE` can leave `INTEGRATION_REQUIRED`).
2. A consuming boundary that enforces the scope — otherwise the scoped Boolean is
   advisory outside the module.
3. Evidence-acquisition instants in the record model before any acquisition PIT
   assertion; today `ACQUISITION_LINEAGE` is correctly listed unverified.
4. An executable liquidation transformation backed by provider documentation
   before liquidation economics can be verified.
5. Disk headroom: this audit could not run one complete canonical invocation at
   100 % volume; a clean single run requires free space plus temp cleanup.

---

## L. Audit commit

Governance-only: this document plus append-only ledger §197, committed as a child of
`cce32c549e` on **`agent/crypto-sensor-fabric-audit-p2dr1`**. The production branch
`agent/crypto-sensor-fabric-build` is **not** modified or merged into. The exact SHA
and remote equality are reported in ledger §197's operator report; the commit
contains no source, test, frozen-plan or evidence artifact from the audited surface.

---

## M. Recommended next checkpoint — NOT EXECUTED

`SENSOR-B5-I09P2dR2 — Committed-Tree Regression Repair and PIT Entry Parity`:
re-publish the two governance count pins, move the availability refusal to a layer
both PIT entries share, and re-run the canonical set with the repository already in
its committed shape. Then an independent `P2dR2` audit of the repaired commit before
any ratification question is reopened.
