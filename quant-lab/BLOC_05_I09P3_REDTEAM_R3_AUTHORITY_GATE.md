# BLOC 05 — SENSOR-B5-I09P3-REDTEAM-R3 — AUTHORITY-ORIGIN SECURITY GATE

**Checkpoint:** `SENSOR-B5-I09P3-REDTEAM-R3`
**Role:** Agent 2 — independent security auditor
**Branch:** `agent/crypto-sensor-fabric-p3-redteam-r3`
**Tested tree:** `9824927666a53dc02a6153d7084bb3e1bf5eed49` (published R2 red-team baseline) **+ this checkpoint's untracked gate file**
**Audited P3 implementation baseline:** `c0e3440bf4b0ed09156be360be0bdeeeb00d3460`
**Latest known P3 implementation (read-only inspection):** `5ce62c26da8a63dd84160f21694e5eceef406018`
**Disposition:** `P3_REDTEAM_R3_GOVERNANCE_HOLD`

No production merge. No consuming application. No provider approval. No custody-authority
promotion. No I11/I12/I17 or Bloc 6 advancement. No program-gate promotion. No source repair.

---

## 0. Reference lock (measured before anything was run)

| Item | Observed |
|---|---|
| R2 published on origin | `refs/heads/agent/crypto-sensor-fabric-p3-redteam-r2` = `9824927666a53dc02a6153d7084bb3e1bf5eed49` |
| R2 local == remote | identical SHA |
| R2 parent | `c0e3440bf4b0ed09156be360be0bdeeeb00d3460` |
| R3 branch base | `9824927666a53dc02a6153d7084bb3e1bf5eed49` (created from the verified R2 commit) |
| `5ce62c26` descends from `c0e3440` | YES (`git merge-base --is-ancestor`) |
| `5ce62c26` vs `c0e3440` — `quant-lab/src` | **empty diff** — the authorization source is unchanged |
| `5ce62c26` vs `c0e3440` — whole commit | 2 files: the P3 evidence document and the P3 conformance test file |
| Environment | C: 55 GB free; worktree scoped `core.autocrlf=false`; no sparse/salvage checkout used |

The R2 worktree had been removed by an earlier disk cleanup; the committed branch was intact,
so R3 was created from the commit rather than from any surviving working tree. No recovery of
untracked state was attempted or needed.

**Preserved:** the 58 R2 adversarial tests and the R2 audit document are untouched on this
branch. `test_b5_i09p3_redteam_adversarial.py` still passes 58/58; the P3 conformance suite
still passes 70/70 (both re-run on this branch, §7).

---

## 1. Reclassification of the finding (Phase 1)

AT43 and AT53–AT58 were **observational**: they asserted that the vulnerable behaviour
occurred, then recorded it. An observation is not an acceptance test. This checkpoint restates
each as a gate that requires the safe behaviour, and reports the failure as RED.

The layer separation the earlier records blurred:

| Layer | Where it lives | State |
|---|---|---|
| Production verifier | `normalization/sensors/verification.py` | `verify_trade_record` / `verify_liquidation_record` **hardcode** `custody_source_authorized=False` |
| Experimental consumer policy | **test-resident**, `ConsumerPolicy` in `test_b5_i09p2e_trust_consumer.py` **and** `test_b5_i09p3_redteam_adversarial.py` | reads `custody_source_authorized` from whatever `rederive()` returns |
| Attacker-controlled caller inputs | `rederive` callable, `replay_evaluation` object, evidence-reference digest map, serialized verdict, `TrustedAuthorityContext` object | all accepted without an origin check |
| Policy-owned authority inputs | none | the policy owns no attestation, no key, no custody store it controls |
| Synthetic fixtures | `_base_verdict` / `_forged_verdict` in both test modules | set the flag directly |
| Authenticated external authority | **does not exist** | no operator custody attestation anywhere in the repository |

### 1.1 The consumer policy is duplicated, and both copies are affected

`ConsumerPolicy` is defined **twice** in the tracked tree:

- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py:123` — the P3
  conformance engine (Agent 1's own artefact),
- `tests/crypto_sensor_fabric/normalization/test_b5_i09p3_redteam_adversarial.py:119` — the
  R1/R2 red-team harness.

Their authorization dataflow is identical. This is not an artefact of red-team modelling; the
prototype's own conformance engine contains the path. Every gate below is therefore
parameterised over **both** copies, so a repair that fixes one and not the other is visible.

### 1.2 The direction of travel is away from the safe contract

`5ce62c26` changed no policy code but changed two conformance assertions. One of them
(`TestMultiPathConformance.test_cached_path`) now **requires**
`decision == ACCEPT_FIELD_BINDING` **and** `custody_source_authorized is True` from a synthetic
fixture. The prototype's governed suite now asserts the unsafe outcome by name. A repair that
only edits the policy will fail that assertion, so the repair must amend it deliberately and
disclose the amendment — it must not be quietly relaxed back to a union of outcomes.

### 1.3 What is NOT claimed

There is **no production exploit** here, and this record does not claim one:

- no deployed consumer exists — `INTEGRATION_STATE == "INTEGRATION_REQUIRED"`;
- no production code path builds a `ConsumerPolicy` or passes a caller-supplied `rederive`;
- the production verifiers cannot emit `custody_source_authorized=True` at all;
- the production approval manifest admits zero artifacts.

Conversely, the prototype path is **not called secure** merely because its inputs are synthetic
or because no consumer is deployed. A function that accepts an attacker-controlled callback and
returns `AUTHORIZED` has demonstrated an unsafe authorization path inside the prototype, and the
consumer contract it is supposed to implement (`BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md`) is
what R5 will be built against.

---

## 2. Threat model

**Assets:** the meaning of `ACCEPT_FIELD_BINDING`; the meaning of
`custody_source_authorization_status == "AUTHORIZED"`; any downstream economic decision that
trusts either.

**Adversary capabilities assumed (all demonstrated below):**

1. supplies the `rederive` callable;
2. supplies the `replay_evaluation` object;
3. supplies the evidence-reference → digest map and the byte store adapter;
4. supplies serialized verdicts that are deserialized and replayed;
5. supplies a `TrustedAuthorityContext` object constructed directly;
6. sets `custody_source_authorized` on any verdict it can construct;
7. reuses one authorized verdict for another record, approval, artifact or cutoff.

**Not in scope (stated, not assumed away):** arbitrary Python executing in the same interpreter
with the policy's privileges, and the process boundary. Those are the authority module's
recorded limitations, not this gate's subject.

**Trust assumption the gate tests:** authorization must originate in something the *policy*
owns. A boolean that travels with data the policy does not own is an unverified caller claim,
whatever its value.

---

## 3. Gate results (Phase 2 + 3, measured)

File: `tests/crypto_sensor_fabric/normalization/test_b5_i09p3_redteam_r3_authority_gate.py`
SHA-256 `b17a4ee2d23c55572470791c8860a40f0c817101730ca5638aa10d1dcbb9ccef`.

**24 collected: 20 failed (RED), 4 passed.** Both prototype copies produce identical outcomes.

| Gate | Attacker control | Required outcome | Observed (both copies) | Classification |
|---|---|---|---|---|
| RG01 | supplies `rederive` returning authorized=True | REFUSE / INTEGRATION_REQUIRED | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONFIRMED PROTOTYPE BYPASS** |
| RG02 | constructs `TrustedAuthorityContext` directly (`model_construct`) | refuse or validate against pinned root | `ACCEPT_FIELD_BINDING`, `AUTHORIZED`; context never inspected | **CONTRACT GAP** |
| RG03 | forged cached **and** re-derived verdicts that agree | REFUSE (agreement is not corroboration) | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONFIRMED PROTOTYPE BYPASS** |
| RG04 | reuses the authorized flag for a different record (provider B) | REFUSE (record binding) | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONTRACT GAP** |
| RG05 | reuses an authorized decision after the cutoff moves | decision carries and checks its cutoff | `RecordVerification` has no `knowledge_cutoff`; `evaluate()` takes none | **CONTRACT GAP** |
| RG06 | model-VALID synthetic fixture with the flag True | never `AUTHORIZED` | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONFIRMED PROTOTYPE BYPASS** |
| RG07 | correct evidence digest, unauthorized source | `INTEGRATION_REQUIRED` | `INTEGRATION_REQUIRED`, flag False | **PASS** (pre-existing invariant) |
| RG08 | supplies `replay_evaluation` claiming ELIGIBLE while consumed | REFUSE | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONTRACT GAP** |
| RG09 | swaps approval_id / artifact_id / registry digest | REFUSE (identity binding) | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONTRACT GAP** |
| RG10 | deserializes an authorized verdict and replays it as both candidate and derived | REFUSE | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONFIRMED PROTOTYPE BYPASS** |
| RG11 | sets the flag True with **no** authority context at all | INTEGRATION_REQUIRED / REFUSE | `ACCEPT_FIELD_BINDING`, `AUTHORIZED` | **CONFIRMED PROTOTYPE BYPASS** |
| RG12 | empty production approval manifest | production mints no authority | `INTEGRATION_STATE=INTEGRATION_REQUIRED`; both verifiers hardcode `False`; model default `False` | **PASS** (production limit) |
| RG13 | governance scope of this file | record, do not assume, admission | outside the I10 named-prefix allowance | **GOVERNANCE FACT** |

`FALSE POSITIVE`: none. `ENVIRONMENT BLOCKER`: none — no test failed for an environmental
reason, and the same run is reproducible (§9).

### 3.1 Exact controls an attacker needs

For RG01/RG03/RG06/RG10/RG11 the attacker needs **only** the ability to pass a verdict or a
callable into `ConsumerPolicy.evaluate`. No key, no manifest, no custody store, no network.
For RG02 it additionally constructs a context object; the policy stores it and never reads it.
For RG04/RG05/RG08/RG09 the attacker needs the ability to reuse one authorized verdict — the
policy holds no record, cutoff, replay or identity binding to notice.

---

## 4. Record / cutoff identity analysis

`RecordVerification` carries: `record_kind`, `artifact_id`, `approval_id`, `registry_digest`,
`provider`, five boolean claims, `trust_scope`, `unverified_dimensions`, `fields_verified`,
proof references and `custody_source_authorized`.

**What the policy binds.** On the cached path it compares six fields between candidate and
re-derived verdict: approval, registry digest, artifact, trust scope, fields, and the
authorization flag itself. That is a *copy-equality* check, not an identity check: it detects a
divergent copy, not an unauthorized original.

**What is unbound.**

| Dimension | Bound? | Consequence |
|---|---|---|
| record payload (values, timestamps, side) | no — not represented in the verdict | authorization for one row covers any row under the same approval |
| knowledge cutoff | no — not a field, not a parameter | an authorization established at T is consumed at any later T |
| evidence byte provenance | partially — reference→digest map is caller-supplied | bytes are re-hashed, but *which* bytes are approved is the caller's claim |
| replay fingerprint | no | a caller-supplied eligibility object is accepted |
| custody attestation (who authorized the store) | **no** | the flag is a bare boolean with no issuer, no record, no expiry, no signature |

The flag therefore cannot be repaired by "binding it later": there is no issuer identity in the
verdict to bind to. The repair must add an authority-origin representation *and* the identity it
is about, or refuse to consume the flag at all.

---

## 5. Independent security specification (Phase 5)

### 5.1 Mandatory invariants

**M1 — Origin.** `ACCEPT_FIELD_BINDING` with `AUTHORIZED` custody status may be produced only
when custody authority was established from a policy-owned source: a pinned, reviewed
attestation the caller cannot write.

**M2 — No caller-provenance promotion.** A value that arrives through `rederive`, a serialized
verdict, a candidate copy, a replay object or an evidence map is `UNVERIFIED_CALLER_CLAIM` and
must never be promoted to `ATTESTED_EXTERNAL_AUTHORITY`.

**M3 — Context validation.** A `TrustedAuthorityContext` supplied to the policy must be
validated against the pinned root (the `from_reviewed_root` law) before it is used, or rejected.
A context that is stored and never read is not a control.

**M4 — Record binding.** Authorization is bound to `(record identity, provider, approval_id,
artifact_id, registry_digest, canonical field)`. Reuse across any of them is refused.

**M5 — Cutoff binding.** The decision records the knowledge cutoff at which authority was
established and refuses consumption at an earlier cutoff; reuse at a later cutoff requires
re-establishment, not re-presentation.

**M6 — Replay separation.** Replay eligibility is a policy-owned verdict over a fingerprint.
A caller-supplied eligibility object is never sufficient for `ACCEPT`.

**M7 — Evidence provenance.** The approved reference→digest map is policy-owned; re-hashing
caller-chosen bytes proves integrity of *those* bytes, not that they are the approved ones.

**M8 — Deserialization is not verification.** A rehydrated verdict is a claim. It must be
re-derived from policy-owned inputs before any `ACCEPT`, and agreement between two copies of
one claim must not be treated as corroboration.

**M9 — Fail-closed absence.** With no operator attestation present, the outcome is
`INTEGRATION_REQUIRED` (or `REFUSE`), never `AUTHORIZED`. This is the repository's current
production truth and must remain the prototype's default.

**M10 — Production boundary unchanged.** `INTEGRATION_STATE` stays `INTEGRATION_REQUIRED`;
the production verifiers keep `custody_source_authorized=False`; the empty approval manifest
mints nothing.

### 5.2 Possible designs (not prescriptions)

**D1 — Additive origin enum.** Add `custody_authority_origin` with values
`NO_AUTHORITY | SYNTHETIC_TEST_AUTHORITY | UNVERIFIED_CALLER_CLAIM | ATTESTED_EXTERNAL_AUTHORITY`,
defaulting to `NO_AUTHORITY`, and gate `AUTHORIZED` on `ATTESTED_EXTERNAL_AUTHORITY`. Additive
and model-law enforceable; does not alter existing field meanings.

**D2 — Attestation object instead of a boolean.** A frozen `CustodyAuthorityAttestation`
carrying issuer, record identity, cutoff, approved references and a signature/reference,
constructible only from a policy-owned verifier. The boolean becomes derived, not input.

**D3 — Policy-owned rederive.** Replace the caller-supplied callable with a policy method that
takes records, not verdicts, and calls the production verifier itself.

**D4 — Split decisions.** Keep `ACCEPT_FIELD_BINDING` for field binding and emit a separate
`custody_authority` verdict; a consumer that needs authority must require both.

**D5 — Remove the flag from the consumable model.** Emit authority only from a verifier-owned
result type, and make the consumer refuse any verdict whose authority it cannot independently
establish.

These are alternatives, not a required shape. The invariants in §5.1 are the contract; the
design is Agent 1's to choose. No frozen production model is prescribed for modification here.

---

## 6. Governance and dependencies (Phase 4)

### 6.1 The gate is outside the frozen I10 named-prefix allowance

`tests/crypto_sensor_fabric/normalization/test_b5_i10_scope_audit.py` (`test_only_the_i10_
authorized_prefixes_carry_tracked_changes`, item A10-24) enumerates the governed commit surface.
Its test entries are **named per checkpoint file**, in the audit's own words "admitted by its own
named entry rather than by widening a prefix":

```
tests/crypto_sensor_fabric/normalization/test_b5_i09p2a_
tests/crypto_sensor_fabric/normalization/test_b5_i09p2b_
tests/crypto_sensor_fabric/normalization/test_b5_i09p2c_
tests/crypto_sensor_fabric/normalization/test_b5_i09p2d_
tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_
tests/crypto_sensor_fabric/normalization/test_b5_i10_
tests/crypto_sensor_fabric/normalization/test_b5_i11_
tests/crypto_sensor_fabric/normalization/test_b5_i11r1_
tests/crypto_sensor_fabric/normalization/test_b5_i11f1_
```

There is **no** entry admitting `test_b5_i09p3_redteam_adversarial.py` (R2) or
`test_b5_i09p3_redteam_r3_authority_gate.py` (R3). This file is **not admitted**.

A conflicting, broader allowance exists: `test_b5_i05_scope_audit.py`'s staged-view list carries
the prefix `tests/crypto_sensor_fabric/normalization/test_b5_i09`, which *would* admit both
files. The two audits therefore disagree about this path. That ambiguity is itself the finding:
it must be resolved by an explicit operator ruling, not by picking whichever audit is convenient.

Actions taken, and deliberately not taken:

- **not** widened the I10 allowlist;
- **not** renamed the gate to `test_b5_i10…` or to any admitted prefix — that would disguise an
  unauthorized test, and RG13 asserts the honest name;
- **not** edited Agent 1's scope audits, ledgers or evidence;
- **not** created a competing ledger section.

### 6.2 Does R3 require a mechanical I11R2-style update?

**Yes, one, before the gate may count as a governed suite.** Minimum disclosed change:

1. one named entry `tests/crypto_sensor_fabric/normalization/test_b5_i09p3_redteam_r3_` in the
   I10 scope audit's `allowed` tuple, with its disclosure comment; and
2. one named entry for the R2 file, or an explicit ruling that red-team suites are outside the
   governed surface and are evidence-only.

Item 2 must be a ruling, not an inference: R2 is already published and equally unadmitted.

Until then the gate is published **as red-team evidence** on this branch. It is not claimed as a
governed acceptance suite and does not gate any checkpoint.

### 6.3 Independence

The gate imports the prototype by path and mutates nothing. It does not import or depend on the
R2 audit's conclusions. Its assertions are refusal assertions; it fails when the prototype
succeeds and passes when the prototype refuses.

---

## 7. Existing production limitations (what is already safe)

Re-verified on this branch, not inherited from R2:

- P3 conformance suite: **70 passed**.
- R2 adversarial suite: **58 passed**.
- R3 gate: **20 failed, 4 passed** (expected RED; see §3).
- `quant-lab/src` unchanged by this checkpoint (`git diff` empty; no source file staged).
- `INTEGRATION_STATE == "INTEGRATION_REQUIRED"`.
- Both production verifiers hardcode `custody_source_authorized=False` (asserted by RG12, not
  inspected by eye).
- `RecordVerification.custody_source_authorized` defaults to `False`.
- The production approval manifest admits zero artifacts, so no approved provider row exists.
- No production consumer, no deployment, no provider certification, no custody approval.

---

## 8. Requirements for Agent 1's repair (testable)

1. **R1** Any `ACCEPT` with `AUTHORIZED` custody status requires a policy-owned attestation.
   RG01, RG03, RG06, RG10, RG11 must pass.
2. **R2** `TrustedAuthorityContext` supplied to the consumer is validated against the pinned root
   or rejected. RG02 must pass.
3. **R3** Authorization is bound to record identity, approval, artifact, registry digest and
   canonical field. RG04, RG09 must pass.
4. **R4** The decision carries the knowledge cutoff at which authority was established and the
   consumer checks it. RG05 must pass.
5. **R5** Replay eligibility is policy-owned; a caller-supplied eligibility object is never
   sufficient. RG08 must pass.
6. **R6** Deserialized verdicts are re-derived from policy-owned inputs; copy agreement is not
   corroboration. RG10 must pass.
7. **R7** With no attestation present the outcome is `INTEGRATION_REQUIRED`. RG11 must pass, and
   RG07/RG12 must keep passing.
8. **R8** Repair **both** prototype copies, or delete one and make the other the single source.
   A divergent pair is a failed repair.
9. **R9** Amend — do not relax — the conformance assertion at
   `test_b5_i09p2e_trust_consumer.py::TestMultiPathConformance::test_cached_path` that now
   requires `ACCEPT_FIELD_BINDING` + `True` from a synthetic fixture. Disclose the amendment.
10. **R10** Do not widen an assertion to a union of outcomes to absorb a gate. RG13 and the R3
    file hash let the next auditor detect a gate that was edited instead of satisfied.
11. **R11** No production trust activation: `INTEGRATION_STATE`, the verifiers' hardcoded
    `False`, and the empty manifest stay as they are unless a separate checkpoint authorizes
    otherwise.

---

## 9. Independent reattack plan for R5

1. Read the **exact published R5 SHA**; do not test a working tree.
2. Re-run this gate unmodified on that SHA:
   `PYTHONPATH=quant-lab/src python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p3_redteam_r3_authority_gate.py -q`
   Expected after repair: 24 passed. Any remaining failure is a failed repair, not a stale test.
3. Verify the gate file hash is still `b17a4ee2d23c55572470791c8860a40f0c817101730ca5638aa10d1dcbb9ccef`.
   A changed hash means the gate was edited; diff it against this commit before trusting a pass.
4. Re-run the R2 suite (58) and the P3 conformance suite (70). A repair that breaks either is
   refused, and a repair that **loosens** either is refused.
5. Re-run RG12 and confirm production is still `INTEGRATION_REQUIRED` with both verifiers
   hardcoding `False`.
6. Add adversarial cases the repair invites: attestation replay across records, attestation for
   the wrong cutoff, attestation issued by the record producer, attestation with a correct
   signature over the wrong artifact, and a policy-owned rederive that is monkeypatched.
7. Publish the reattack on its own branch with the exact SHA, and do not award a PASS to any gate
   that was not executed against that SHA.

---

## 10. Disposition

```
P3_REDTEAM_R3_GOVERNANCE_HOLD
```

**Why not READY_TO_REATTACK_R5.** The technical package is complete — 13 gates, 20 measured RED
outcomes on two independent prototype copies, a threat model, an identity analysis, a mandatory
invariant set, repair requirements and a reattack plan. But the gate lives at a path that the
operative frozen governance surface does not admit, and two scope audits disagree about it. A
gate that cannot be admitted cannot serve as R5's governed acceptance criterion, so R5 cannot be
declared ready to reattack under it.

**Why not PARTIAL.** Nothing in Phases 0–6 is missing or unexecuted. The blocker is authorization
of the path, not the work.

**What would clear the hold (operator decision, not Agent 2's):**

- add the disclosed named entry (or entries) to the I10 scope audit and resolve the I05 prefix
  conflict; or
- rule that red-team suites under `test_b5_i09p3_redteam_*` are evidence-only and outside the
  governed surface, in which case the gate stays evidence and R5 reattack uses it as a
  non-governed probe.

After either ruling, the disposition moves to `P3_REDTEAM_R3_READY_TO_REATTACK_R5` with no change
to the gate's content.

---

## 11. Reproduction

```bash
cd .worktrees/p3-redteam-r3
export PYTHONPATH=quant-lab/src PYTHONDONTWRITEBYTECODE=1

# the gate (expected RED at this baseline)
python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/\
test_b5_i09p3_redteam_r3_authority_gate.py -q

# preserved suites
python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/\
test_b5_i09p3_redteam_adversarial.py -q      # 58 passed
python -m pytest quant-lab/tests/crypto_sensor_fabric/normalization/\
test_b5_i09p2e_trust_consumer.py -q          # 70 passed

# source scope of this checkpoint (must be empty)
git diff --name-only HEAD -- quant-lab/src
```

Measured on `9824927666a53dc02a6153d7084bb3e1bf5eed49` + the untracked gate file.
