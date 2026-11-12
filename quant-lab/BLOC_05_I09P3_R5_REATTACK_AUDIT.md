# BLOC 05 — SENSOR-B5-I09P3-R5 — INDEPENDENT REATTACK AUDIT

**Checkpoint:** `SENSOR-B5-I09P3-R5-INDEPENDENT-REATTACK`
**Role:** Agent 2 — independent security auditor
**Branch:** `agent/crypto-sensor-fabric-p3-r5-reattack`
**Implementation target (exact, immutable):** `ea1fdeb7714b57f07085eb6dfadefafccd7658bb`
**Red-team R3 baseline:** `d829e0e69388a7bc4eb7453782803ef9c344fd1b`
**Audited P3 baseline:** `c0e3440bf4b0ed09156be360be0bdeeeb00d3460`
**Disposition:** `P3_R5_SECURITY_HOLD_CONFIRMED_BYPASS`

No implementation repair, no merge, no deployment, no production trust activation, no provider
approval, no custody authorization, no I11/I12/I17 or Bloc 6 advancement.

---

## 0. Reference lock

| Item | Observed |
|---|---|
| R3 published on origin | `d829e0e69388a7bc4eb7453782803ef9c344fd1b` |
| R5 target exists | `ea1fdeb7714b57f07085eb6dfadefafccd7658bb` (`commit`), published at `origin/agent/crypto-sensor-fabric-trust-consumer-r1` |
| R5 ancestry from `c0e3440` | YES |
| R5 ancestry from R3 | **NO** — R5 is on the implementation line, not the red-team line |
| R5 diff vs `c0e3440` | 3 files: P3 evidence doc, P3 conformance test file, I11R2 JSON |
| R5 diff vs `c0e3440` — `quant-lab/src` | **empty** |
| R5 diff vs `c0e3440` — config / frozen bloc_05 plan | **empty** |
| I11R2 publisher change | `python_files_scanned: 1096 → 1097` **only** (verified hunk, not assumed) |
| Isolated checkout | `.worktrees/p3-r5-reattack`, detached at `ea1fdeb77`, clean |
| Environment | 48 GB free; full checkout (6,773 files), no sparse or salvage mode |

The entire R5 "policy-owned capability" is therefore **test-resident**: production source is
byte-identical to the audited baseline. That is consistent with `INTEGRATION_REQUIRED`, and it
means every finding below is a prototype finding, not a deployed vulnerability.

---

## 1. R3 gate replay (Phase 1)

The R3 suite's 24 collected cases (13 gate identities × 2 prototype copies) were re-expressed
against the R5 API. R5 contains one policy copy, so the parameterisation collapses 24 → 13
identities; the invariants are unchanged. Two gates required a **disclosed** adaptation:

- **RG06.** R5 deliberately keeps a `SYNTHETIC_TEST_ONLY` capability for downstream field-scope
  tests, so the gate now requires status `SYNTHETIC_TEST_ONLY` with `custody_source_authorized
  is False` and forbids `AUTHORIZED`, instead of requiring outright refusal. The preserved
  hypothesis — *synthetic input never becomes operator authority* — is unchanged.
- **RG05.** R3 asserted the **absence** of cutoff binding. R5 adds it, so the gate now asserts
  the binding exists **and** that a capability minted at T1 is refused at T2.

No gate was converted from an expected refusal into an expected acceptance.

| Gate | R3 observed (both copies) | R5 observed | Attack reachable? | Unsafe state refused? | Verdict |
|---|---|---|---|---|---|
| RG01 caller rederive flag | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG02 forged context | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG03 agreeing forged copies | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG04 cross-record flag reuse | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG05 cutoff binding | no binding existed | minted-at-T1 refused at T2 | no | yes | **CLOSED** |
| RG06 synthetic authority | `ACCEPT` / `AUTHORIZED` | `SYNTHETIC_TEST_ONLY`, flag False | no | yes | **CLOSED** (adapted) |
| RG07 digest without authority | `INTEGRATION_REQUIRED` | `INTEGRATION_REQUIRED` | no | yes | **PASS** |
| RG08 forged replay eligibility | `ACCEPT` / `AUTHORIZED` | `ACCEPT` / `AUTHORIZED` | **yes** | **no** | **OPEN** |
| RG09 approval/artifact swap | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG10 deserialized replay | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG11 absent attestation | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | no | yes | **CLOSED** |
| RG12 empty manifest limits | pass | pass | no | yes | **PASS** |
| RG13 governance scope | outside allowance | outside allowance | n/a | n/a | **GOVERNANCE** |

**Every closable R3 gate is genuinely closed except RG08.** The record-carried boolean is no
longer consulted: R5's `_custody_grant` reads only the policy's capability. RG01–RG06, RG09–RG11
all now return `INTEGRATION_REQUIRED` (or the documented `SYNTHETIC_TEST_ONLY` status); only RG08
remains open.

---

## 2. Capability forgery (Phase 2)

The question is whether `CustodyAuthorityCapability` is a trust boundary or an API convention.

It is a **public `@dataclass(frozen=True)`** with no private issuance seal, no `__post_init__`
validation, and an optional `manifest_sha256` that `_custody_grant` never reads. `basis` is a
plain enum field. `from_reviewed_context` is guarded, but it is not the only constructor.

| Case | Control | Required | Observed at `ea1fdeb77` | Verdict |
|---|---|---|---|---|
| CAP01 | direct dataclass construction, `basis=ATTESTED_OPERATOR`, identity + cutoff matching | no operator authority | `ACCEPT_FIELD_BINDING`, `authorized=True`, `AUTHORIZED` | **OPEN — CONFIRMED** |
| CAP02 | same, with `manifest_sha256="0"*64` (never validated) | refused | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | **OPEN — CONFIRMED** |
| CAP03 | `dataclasses.replace(synthetic, basis=ATTESTED_OPERATOR)` | refused | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | **OPEN — CONFIRMED** |
| CAP04 | duck-typed `SemanticAuthority` passed to `from_reviewed_context` | refused | `SemanticAuthorityRefusal` raised | PASS |
| CAP05 | `model_construct` verdict with flag True, no capability | no authority | `INTEGRATION_REQUIRED` | PASS |
| CAP06 | `model_construct`-forged context into `from_reviewed_context` | refused | `RecordVerificationError` raised | PASS |
| CAP07 | genuine reviewed root + unauthorized source object | refused | `SemanticAuthorityRefusal` raised | PASS |
| CAP08 | capability for artifact A, verdict artifact B | refused | `INTEGRATION_REQUIRED` | PASS |
| CAP08b | capability for provider A, verdict provider B | refused | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | **OPEN — CONFIRMED** |
| CAP09 | cross-approval reuse | refused | `INTEGRATION_REQUIRED` | PASS |
| CAP10 | cross-registry reuse | refused | `INTEGRATION_REQUIRED` | PASS |
| CAP11 | cross-cutoff reuse | refused | `INTEGRATION_REQUIRED` | PASS |
| CAP12 | `record_kind=None` capability, `LIQUIDATION` record | refused | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | **OPEN — CONFIRMED** |
| CAP12b | explicit `TRADE` capability, `LIQUIDATION` record | refused | `INTEGRATION_REQUIRED` | PASS |
| CAP13 | synthetic capability never `AUTHORIZED` | `SYNTHETIC_TEST_ONLY` | `SYNTHETIC_TEST_ONLY`, flag False | PASS |
| CAP14 | shipped manifest approves nothing | `artifacts == {}` | `artifacts == {}`, `INTEGRATION_REQUIRED` | PASS |

### 2.1 Classification of the CAP01 path

The required attacker capability is **ordinary Python in the same process constructing a
dataclass** — the same class of caller that previously supplied `rederive`. It needs:

- no key, no signature, no approval artifact, no manifest bytes;
- no elevated privilege, no loader seal, no `SemanticAuthority`;
- only the six public constructor arguments, five of which it already knows from the verdict.

R5's own docstring bounds the claim to "a data boundary inside one process" that "does not
resist code running with the application's privileges". That disclosure does **not** cover
CAP01: constructing a frozen dataclass is unprivileged data manipulation, not privileged code.
`SemanticAuthority` genuinely requires a loader-issued private seal; `CustodyAuthorityCapability`
requires nothing, so the comparison the docstring draws is not accurate for this type.

**Consequence:** AT53's attacker is not removed. AT53 asked "can a caller make the policy report
operator authority from data it supplied?" Under R5 the answer is still yes — the boolean was
replaced by a forgeable object, which is a relocation of the vector, not a closure.

---

## 3. Operator authority cannot be minted (Phase 3)

Two paths, two different answers:

**`from_reviewed_context` — a real boundary.** It re-validates manifest bytes through
`TrustedAuthorityContext.from_reviewed_root` (CAP06 dies here), requires a genuine
`SemanticAuthority` carrying the loader's private issuance seal (CAP04, CAP07 die here), and
checks artifact identity. The shipped manifest has `artifacts == {}` (CAP14), so
`load_semantic_authority` refuses every artifact and **no supported application path can mint
`ATTESTED_OPERATOR`**. This part of R5's claim is correct and measured.

**`ConsumerPolicy._custody_grant` — not a boundary.** It trusts `capability.basis` at face value.
It compares cutoff, `record_kind` (only when not `None`), and the triple
`(artifact_id, approval_id, registry_digest)`. It never checks `manifest_sha256`, never checks
provider, and never asks whether the object was issued. Any directly constructed object with
`basis=ATTESTED_OPERATOR` therefore reaches the `AUTHORIZED` branch.

So the constructor is an **API convention**, not a trust boundary, and the policy cannot tell the
difference between an issued capability and a hand-built one.

---

## 4. PIT, replay and custody (Phase 4)

Measured by source inspection of `_apply` plus the gates above:

| Requirement | Result |
|---|---|
| PIT rejection precedes authority acceptance | **YES** — `_apply` refuses `PIT_INADMISSIBLE` before `_custody_grant` is called |
| Replay blocking independent of authority | **YES structurally** — but the eligibility *object* is caller-supplied, so RG08 stays OPEN |
| Evidence-byte integrity grants no authority | **YES** — RG07 `INTEGRATION_REQUIRED` |
| Synthetic authority never labelled `AUTHORIZED` | **YES** — RG06/CAP13 `SYNTHETIC_TEST_ONLY`, flag False |
| Cached verdict agreement creates no authority | **YES** — RG03 `INTEGRATION_REQUIRED` |
| Unverified dimensions remain explicit | **YES** — 79-test suite plus RG gates |
| Verified fields individually scoped | **YES** — `FIELD_NOT_IN_ALLOWLIST` path unchanged; 79-test suite passes |
| Liquidation transformation limits intact | **YES** — explicit kind mismatch refused (CAP12b); liquidation still reports `record_transformation_verified=False` |

The `knowledge_cutoff` parameter is a genuine improvement: `RG05` now passes and `CAP11` proves
cross-cutoff reuse is refused. Note that a capability with `knowledge_cutoff=None` matches a
call with the default `knowledge_cutoff=None`, which is why CAP01 needs no cutoff juggling.

---

## 5. Governance (Phase 5)

The R3 finding stands unchanged at R5: `test_b5_i09p3_redteam_*` and `test_b5_i09p3_r5_reattack_*`
are **not** admitted by the I10 scope audit's named-entry list (A10-24), while the I05 staged-view
list's broader `test_b5_i09` prefix would admit them. The two audits still disagree.

What this checkpoint did:

- executed the independent suite from an **isolated detached checkout at the exact R5 SHA**, not
  by merging the red-team branch into the implementation;
- added no test path to the implementation branch and widened no allowlist;
- kept the honest `..._r5_reattack_` name rather than renaming into an admitted prefix.

**Separating the two decisions, as required:**

1. *Running independent tests as external audit evidence* — already valid. The suite is
   self-contained, loads the policy by path, and mutates nothing. No governance amendment is
   needed for this checkpoint's evidence.
2. *Incorporating tests into the governed canonical suite* — requires one disclosed named entry
   per file (or one explicit ruling that red-team/reattack suites are evidence-only), plus a
   resolution of the I05/I10 prefix conflict. This checkpoint does **not** perform that and does
   not claim it.

Narrowest compliant proposal: leave the canonical suite untouched; state in the ledger that
`SENSOR-B5-I09P3-R2/R3/R5-REATTACK` suites are external audit evidence executed against a pinned
SHA, and admit them only if the operator later chooses to, by disclosed named entry.

---

## 6. Independent regression (Phase 6)

Executed on `ea1fdeb7714b57f07085eb6dfadefafccd7658bb` in the isolated checkout:

| Suite | Collected | Passed | Failed | Note |
|---|---|---|---|---|
| P3 conformance suite (`test_b5_i09p2e_trust_consumer.py`) | 79 | **79** | 0 | matches the mission's expected 79 |
| R5 reattack suite (this checkpoint) | 29 | 23 | **6** | all 6 are security findings, §2 |
| R3 gate against R2 baseline (historical) | 24 | 4 | 20 | unchanged, not re-run here |

The 6 failures are: RG08, CAP01, CAP02, CAP03, CAP08b, CAP12. No failure is environmental, and
none is a test artefact: each was reproduced independently by a direct probe before the suite was
written. The full canonical tree suite was **not** run — Agent 1 owns it and this checkpoint does
not compete for that resource; the P3-scoped suite is the relevant surface.

---

## 7. Security acceptance matrix (Phase 7)

| Finding | Old result | R5 result | Verdict | Proof |
|---|---|---|---|---|
| AT43 synthetic fixture promotes to AUTHORIZED | `ACCEPT` / `AUTHORIZED` | flag ignored; synthetic capability → `SYNTHETIC_TEST_ONLY` | **CLOSED** | RG06, CAP13 |
| AT53 caller-supplied rederive forges custody | `ACCEPT` / `AUTHORIZED` | flag ignored → `INTEGRATION_REQUIRED` | **CLOSED (relocated)** | RG01; but see CAP01 |
| AT54 forged `TrustedAuthorityContext` | accepted, never read | `INTEGRATION_REQUIRED` | **CLOSED** | RG02, CAP06 |
| AT55 cached verdict authority escalation | `ACCEPT` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | **CLOSED** | RG03 |
| AT56 cross-record flag reuse | `ACCEPT` / `AUTHORIZED` | flag path closed; capability path bound to identity | **PARTIAL** | RG04 pass, CAP08 pass; CAP08b/CAP12 open |
| AT57 no authority-category distinction | all categories identical | basis distinguishes; basis itself forgeable | **PARTIAL** | CAP01, CAP03 |
| RG01 caller rederive | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG02 forged context | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG03 agreeing forged copies | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG04 cross-record flag reuse | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG05 cutoff binding | gap | binding present and enforced | **CLOSED** | §1, CAP11 |
| RG06 synthetic authority | OPEN | `SYNTHETIC_TEST_ONLY` | **CLOSED** (adapted) | §1 |
| RG07 digest without authority | PASS | `INTEGRATION_REQUIRED` | **PASS** | §1 |
| RG08 forged replay eligibility | OPEN | `ACCEPT` / `AUTHORIZED` | **OPEN** | §1 |
| RG09 approval/artifact swap | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG10 deserialized replay | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG11 absent attestation | OPEN | `INTEGRATION_REQUIRED` | **CLOSED** | §1 |
| RG12 empty manifest limits | PASS | PASS | **PASS** | §1, CAP14 |
| RG13 governance admission | HOLD | HOLD | **GOVERNANCE** | §5 |
| CAP01 forged capability | n/a (new) | `ACCEPT` / `AUTHORIZED` | **OPEN** | §2 |
| CAP02 manifest digest unvalidated | n/a | `ACCEPT` / `AUTHORIZED` | **OPEN** | §2 |
| CAP03 basis replace | n/a | `ACCEPT` / `AUTHORIZED` | **OPEN** | §2 |
| CAP04 forged `SemanticAuthority` | n/a | refused | **PASS** | §2 |
| CAP05 `model_construct` flag | n/a | `INTEGRATION_REQUIRED` | **PASS** | §2 |
| CAP06 forged reviewed context | n/a | refused | **PASS** | §2 |
| CAP07 right digest, unauthorized source | n/a | refused | **PASS** | §2 |
| CAP08 cross-record reuse | n/a | `INTEGRATION_REQUIRED` | **PASS** | §2 |
| CAP08b provider substitution | n/a | `ACCEPT` / `AUTHORIZED` | **OPEN** | §2 |
| CAP09 cross-approval reuse | n/a | `INTEGRATION_REQUIRED` | **PASS** | §2 |
| CAP10 cross-registry reuse | n/a | `INTEGRATION_REQUIRED` | **PASS** | §2 |
| CAP11 cross-cutoff reuse | n/a | `INTEGRATION_REQUIRED` | **PASS** | §2 |
| CAP12 `record_kind=None` wildcard | n/a | `ACCEPT` / `AUTHORIZED` | **OPEN** | §2 |
| CAP12b explicit kind mismatch | n/a | `INTEGRATION_REQUIRED` | **PASS** | §2 |
| CAP13 synthetic never authorized | n/a | `SYNTHETIC_TEST_ONLY` | **PASS** | §2 |
| CAP14 shipped manifest empty | n/a | `artifacts == {}` | **PASS** | §2 |

No unresolved contract or governance item is marked PASS.

---

## 8. Required repair for R6/R7 (testable)

1. **Seal the capability.** Construct `CustodyAuthorityCapability` only through a
   loader-issued sentinel (`__post_init__` requires a module-private token), so a public
   constructor cannot produce `ATTESTED_OPERATOR`. CAP01, CAP03 then fail closed.
2. **Validate `manifest_sha256`.** Re-check it against `TRUSTED_MANIFEST_SHA256`, or drop the
   field so it cannot imply a binding it does not enforce. CAP02 then fails closed.
3. **Bind provider and canonical field.** Add provider (and the authorized field set) to the
   identity tuple, matching R3 RG04. CAP08b then fails closed.
4. **Remove the `record_kind=None` wildcard.** Require an explicit kind. CAP12 then fails closed.
5. **Make replay policy-owned.** Accept a replay verdict the policy computes, not an object the
   caller supplies. RG08 then fails closed.
6. **Keep the closed R3 gains.** RG01–RG07 and RG09–RG13 must stay green; the 79-test suite must
   stay green; production source, `INTEGRATION_STATE`, the hardcoded `False` verifiers and the
   empty manifest must stay unchanged.
7. **State the boundary honestly.** The docstring's "data boundary inside one process" is accurate
   only for `SemanticAuthority`; for the capability it currently understates the exposure.

---

## 9. Publication

Independent artifacts on `agent/crypto-sensor-fabric-p3-r5-reattack`, branched from
`ea1fdeb7714b57f07085eb6dfadefafccd7658bb`:

- `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p3_r5_reattack_authority.py`
- `quant-lab/BLOC_05_I09P3_R5_REATTACK_AUDIT.md`

Preserved: R2 (`982492766`) and R3 (`d829e0e69`) branches and their 58 adversarial tests plus 13
gates are untouched. No source change, no allowlist change, no Agent 1 artifact change.

---

## 10. Disposition

```
P3_R5_SECURITY_HOLD_CONFIRMED_BYPASS
```

**Why HOLD, not ACCEPTED_WITH_BOUNDED_AUTHORITY.** R5 closed every R3 gate except RG08 and all
of the record-flag attacks, and its `from_reviewed_context` path is a real boundary: with the
shipped empty manifest no supported path mints `ATTESTED_OPERATOR`. But six authority grants
remain reachable at the exact published SHA — CAP01, CAP02, CAP03, CAP08b, CAP12, RG08 — and
CAP01 requires only an unprivileged caller constructing a public dataclass. AT53's attacker is
therefore relocated, not removed, so the repair cannot be accepted as closing the bypass.

**Why not PARTIAL.** It is not incompleteness: the work is executed and measured. The blocker is
a reachable unsafe state at the published SHA.

**Why not a production finding.** Production source is byte-identical to `c0e3440`, the manifest
approves nothing, and `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`. This is a prototype
authorization bypass with no deployed consumer — it is not called secure on that basis, but it is
also not a production exploit.

**Exit criteria for reattack.** Seal the capability and validate the manifest digest (kills CAP01,
CAP02, CAP03), bind provider and an explicit record kind (kills CAP08b, CAP12), and make replay
policy-owned (kills RG08). At that point this suite should read 29 passed and the disposition can
move to `P3_R5_SECURITY_ACCEPTED_WITH_BOUNDED_AUTHORITY`.

---

## 11. Reproduction

```bash
cd .worktrees/p3-r5-reattack           # detached at ea1fdeb7714b57f07085eb6dfadefafccd7658bb
export PYTHONPATH=quant-lab/src PYTHONDONTWRITEBYTECODE=1

python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/\
test_b5_i09p3_r5_reattack_authority.py -q     # 29 collected: 6 failed, 23 passed
python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/\
test_b5_i09p2e_trust_consumer.py -q           # 79 passed
git diff --name-only ea1fdeb77 HEAD -- quant-lab/src   # must be empty
```
