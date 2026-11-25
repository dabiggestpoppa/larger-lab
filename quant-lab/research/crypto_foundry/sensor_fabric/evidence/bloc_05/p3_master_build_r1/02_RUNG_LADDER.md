# 02 — Rung ladder

Mission `SENSOR-B5-P3-PRODUCTION-CONSUMER-MASTER-BUILD-R1`, operator
authorization `AUTHORIZE_P3_RUNGS_1_THROUGH_5_BOUNDED`.

Branch `agent/crypto-sensor-fabric-p3-production-master-r1`, based on
`ea17eb5ae3df9319745c66780e85e0a9f1aa9b98`. No merges of audit branches, no
force-push, no history rewrite.

| Rung | Commit | Subject |
|---|---|---|
| AUTH | `f4972cba898d6e202a32ba2566bb30fce4566ab2` | `B5-P3-MASTER-AUTH: admit bounded production consumer implementation` |
| R1 | `198e2aaab4721e087a430e7c781a58bfa0edc482` | `B5-P3-R1: implement production consumer contracts` |
| R2 | `7cb7763b9` | `B5-P3-R2: implement policy-owned verification derivation` |
| R3 | `7155cbf60` | `B5-P3-R3: implement bounded custody authority derivation` |
| R4 | `6af9200fa` | `B5-P3-R4: complete temporal eligibility and evidence rebinding` |
| R5 | (this commit) | `B5-P3-R5: complete executable production consumer security suite` |

Full SHAs for R2–R5 are in the final package message; they are short here
because a document cannot contain its own commit hash.

## Changed paths

Production (4, all inside the authorized package):

```
quant-lab/src/crypto_sensor_fabric/normalization/consumer/__init__.py
quant-lab/src/crypto_sensor_fabric/normalization/consumer/models.py
quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py
quant-lab/src/crypto_sensor_fabric/normalization/consumer/custody_authority.py
```

Tests (5):

```
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_policy.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_custody.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_rebinding.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py
```

Governance amendments (3 audits, all disclosed in place):

```
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i01_scope_audit.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i08_scope_audit.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i10_scope_audit.py
```

Mechanically republished evidence (3):

```
.../evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json   (inventory pin)
.../evidence/bloc_05/bloc_05_semantic_validation.json              (I09 SEM inventory pin)
.../evidence/bloc_05/p3_master_build_r1/*.md                       (this packet)
```

No other production source was touched. `git diff --stat ea17eb5a..HEAD --
quant-lab/src` names exactly those four files.

## Rung by rung

### R1 — contracts (`models.py`)

`ConsumerDecision` is exactly `{ACCEPT_FIELD_BINDING, REFUSE,
INTEGRATION_REQUIRED}`. `CustodyAuthorityBasis` is exactly `{AUTHORIZED,
INTEGRATION_REQUIRED, UNAUTHORIZED}`. `SYNTHETIC_TEST_ONLY` does not exist in
`src/` and a test asserts no enum member carries the word.

`ConsumerRequest` carries a concrete T1 record, artifact bytes, required
fields, evidence references, an offset-aware cutoff and replay evidence — and
nothing else. Frozen, extra-forbidden, immutable nested containers, bare dates
refused, `series`/`digest`-only evidence references refused. No callback, no
authority object, no caller verdict: there is nowhere to put one.

`__init__.py` is a docstring only, deliberately. A re-export would import
`policy`, which imports `sensors.verification`, and the package would no longer
be importable without the verification stack — the design's A1.5 forbids that.
Verified in a clean subprocess.

36 tests.

### R2 — policy-owned derivation (`policy.py`)

`TrustConsumerPolicy.evaluate(request)` derives everything: pinned root, parsed
registry, custody provider, the verifier call, `assert_trustworthy`, replay
adjudication, custody rebinding, authority. The harness's `rederive` callback
has no parameter to arrive in; `evaluate` takes `self, request`.

The four booleans stay four: field verification, custody bytes, custody source
authority, downstream trust. No positive field-binding result promotes source
authority.

Refusal ordering is normative and tested: cutoff shape → replay → verification
→ required fields → trust scope → custody → rebinding → authority.

Unexpected exceptions become `REFUSE / VERIFIER_CRASH` with ≤200 characters of
detail; `KeyboardInterrupt` and `SystemExit` propagate.

28 tests (with contracts).

### R3 — custody authority (`custody_authority.py`)

Authorization is a function, not an object: `derive_custody_authority(
manifest_bytes, identity)` where the identity binds reviewed root digest,
artifact, approval, registry digest, record kind, provider and cutoff. No
`_issue()`, no issuance marker, no capability type, no `SYNTHETIC_TEST_ONLY`
basis. A test walks the module's AST and asserts those identifiers do not exist,
so a future hand cannot quietly reintroduce the R5/R6 architecture.

Under the shipped empty manifest every identity returns `INTEGRATION_REQUIRED`,
and a property test asserts no input in a matrix reaches `AUTHORIZED`. Under a
synthetic fixture root with a complete approvable artifact it *still* returns
`INTEGRATION_REQUIRED`: the reviewed manifest schema has no record type naming a
custody **source** as operator-authorized, and artifact approval is not source
authorization (design spec E). The missing contract is named —
`OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` — and not invented: the derivation
defines no token an operator could write to obtain authority, and a test asserts
`ApprovalManifest` and `ApprovedArtifact` have no custody-source field.

32 tests.

### R4 — temporal eligibility and rebinding

PIT and replay are settled before authority, and the suite proves the ordering
by asserting the authority source was **never consulted** (`source.seen == []`),
not by reading the decision. A PIT violation is distinguished from an absent
integration: an approval that was not yet operative at the cutoff is
`PIT_INADMISSIBLE`, not `INTEGRATION_REQUIRED`.

Rebinding re-reads and re-hashes every referenced blob at the consumption
boundary. The load-bearing fixture is `FlipCustody`: it returns the approved
bytes for the verifier's read and tampered bytes for the consumer's re-read. A
policy that trusted its own earlier read would accept; this one refuses with
`EVIDENCE_BYTES_MISMATCH`. Bytes that disappear between the two reads refuse
with `EVIDENCE_BYTES_MISSING`. Digest-only custody is not custody. A reference
bound to another artifact refuses with `EVIDENCE_NOT_BOUND_TO_ARTIFACT` even
when the bytes are intact.

Each reference is read exactly twice per consumption — once by derivation, once
by rebinding — and never cached across consumptions.

17 tests.

### R5 — executable adversarial security

See `03_SECURITY_EXECUTION.md`. 26 tests, including four mutation controls.

## Architecture-to-implementation matrix

| Design element | Where | Status |
|---|---|---|
| Immutable request/verdict contracts | `models.py` | implemented |
| Three-valued decision + 12 refusal codes + 2 boundary codes | `models.py` | implemented |
| Policy-owned derivation, no callback | `policy.py` | implemented |
| Four distinct trust dimensions | `models.py`, `policy.py` | implemented |
| Normative refusal ordering | `policy.py` | implemented |
| Revalidation at the consuming boundary | `policy.py` | implemented |
| Function-derived custody authority | `custody_authority.py` | implemented |
| Complete authority identity (7 elements) | `custody_authority.py` | implemented |
| No capability / marker / synthetic basis | `custody_authority.py` | asserted by AST test |
| PIT + replay adjudication before acceptance | `policy.py` | implemented, ordering asserted |
| Evidence rebinding on re-read bytes | `policy.py` (`_rebind`) | implemented |
| Full normative decision table | `policy.py` (`_conclude`) | implemented |
| Operator custody-source record | — | **unresolved**, returns `INTEGRATION_REQUIRED` |
| Divergence diagnostics (`CACHED_VERDICT_DIVERGENCE`) | — | **omitted** (design §5 permits) |

## Inventory reconciliation

| Checkpoint | Pinned nodes in I11R2 evidence | Note |
|---|---|---|
| AUTH `f4972cb` | 1,102 | +3 audit files, no Python yet |
| R1 `198e2aa` | 1,105 | `__init__.py`, `models.py`, contracts test |
| R2 `7cb7763` | 1,107 | `policy.py`, policy test |
| R3 `7155cbf` | 1,109 | `custody_authority.py`, custody test |
| R4 `6af9200` | 1,110 | rebinding test |
| R5 (this) | 1,111 | security test |

Republished mechanically each time with
`UPDATE_I11R2_EVIDENCE=1 pytest tests/crypto_sensor_fabric/storage/test_i11r2_binding_audit.py`,
never by hand-editing the JSON.
