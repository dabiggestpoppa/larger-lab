# SENSOR-B5-I09P2a - TRUSTED PROVIDER-SEMANTIC AUTHORITY LOADER

**Status:** IMPLEMENTATION COMPLETE - HARD STOP, NOT RATIFIED
**Checkpoint:** `SENSOR-B5-I09P2a` (bounded I09-a trust root; `B5-I09b` real-provider
semantic certification remains unauthorized and untouched)
**Custody base:** `e2df7109b4ae336c2ed71f1cb8b56e2b4360874e`
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Prior:** I09P1 = `PLANNING_COMPLETE` (ledger section 189). B5-I09a = OPERATOR_ACCEPTED;
B5-I09b = DEFERRED; B5-I10 = OPERATOR_ACCEPTED (bounded); B5-I11 =
IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD.

---

## 1. Custody (measured before any change)

```text
REPOSITORY   = dabiggestpoppa/larger-lab
BRANCH       = agent/crypto-sensor-fabric-build
HEAD         = e2df7109b4ae336c2ed71f1cb8b56e2b4360874e   (= origin after fetch)
FROZEN PLAN  = 4bb677f9e0266f4dc48405181696019f359ae49f, 7/7 bloc_05 blobs SAME
SCRATCH      = .bu_tmp/, evidence/bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md,
               scripts/b5_i03_redteam_results.json  (untracked, never staged)
```

No reset, no rebase, no amend, no force-push. The whole delta is linear on top of
`e2df7109b4`.

## 2. VERIFY - what the pre-state actually was

Read at source, not inferred. The I09P1 finding reproduced exactly:

* `providers/registry.py` is text-in only: `ProviderSemanticMapping` accepts any
  non-pending evidence STRING and any methodology_id STRING, and no code path
  resolves a methodology id.
* `normalize_trade` typed its registry as `object`; `_admit_field` in
  `sensors/liquidation.py` admitted a row whenever a bare registry accepted it.
* No trusted root existed anywhere: no approval artifact, no pinned digest, no
  evidence-to-provider binding, no revocation, no loader.

## 3. RED - the contract that had to fail first

`tests/crypto_sensor_fabric/normalization/test_b5_i09p2a_authority.py`
(sha256 `cfd2146e0a1f3ad802ff01bd0547016132df0e14b281ca18b28719cb6c182a07`,
32 tests) was written before the loader and run against the pre-state, where it
failed: 20 contract probes covering the seven I11R2 gaps plus the loader refusal
classes, and six of the seven G-rows. They pass only against the implementation below.

## 4. IMPLEMENT - the loader and its minimal adoption

```text
LOADER      src/crypto_sensor_fabric/normalization/authority/__init__.py
            sha256 4b766ee73500b08cc7edb6722e67b6e67c0ec9a0d8c51b1ae668d4cf5d7501a6
            496 lines, module-private seal
MANIFEST    config/crypto_sensor_fabric/provider_semantics/approval_manifest.json
            sha256 3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654
            "artifacts": {} - zero approved artifacts
LIQUIDATION src/crypto_sensor_fabric/normalization/sensors/liquidation.py
            sha256 21a51a00f7f135f150d2253c32aa11286b9303e0421c6501bf0301d3e8f17f2d
TRADE       src/crypto_sensor_fabric/normalization/sensors/trade.py
            sha256 f796787c4e9151bf1acf22ba6a8af92685e8001c23bbfe08d02c7b206ae04171
```

Why a new package and not `common/authority.py`: the ratified I08 purity audits forbid
`hashlib` and JSON parsing inside `common/`. Placing the loader there failed four I08
purity tests. That first attempt was reverted and the loader moved to
`normalization/authority/`; no purity law was weakened to accommodate it.

`SemanticAuthority` cannot be constructed by a caller. Its
`model_validator(mode="before")` requires a module-private `_LOADER_SEAL`, and
construction happens through `SemanticAuthority.model_validate({...})` inside
`load_semantic_authority`, so `mypy` stays clean and no unsealed path exists.

Refusals (distinct, fail-closed, each exercised):
`NO_APPROVAL`, `ARTIFACT_NOT_APPROVED`, `DIGEST_MISMATCH`, `APPROVAL_REVOKED`,
`AUTHORITY_EXPIRED`, `EVALUATION_TIME_REQUIRED`, `VERSION_MISMATCH`,
`UNREGISTERED_METHODOLOGY`, `EVIDENCE_NOT_BOUND_TO_PROVIDER`,
`NATIVE_FIELD_NOT_DECLARED`, `TRANSFORMATION_NOT_APPROVED`,
`BLOCKING_ASSUMPTION_UNRESOLVED`, `MALFORMED_MANIFEST`, `MALFORMED_ARTIFACT`,
`UNTRUSTED_AUTHORITY`, `AMBIGUOUS_MAPPING`.

The expected digest is read only from the manifest. No public entry point accepts an
expected digest, so bytes cannot arrive carrying their own authority, and rewriting
artifact bytes together with a matching embedded digest still fails with
`DIGEST_MISMATCH`.

Consumer adoption is one parameter deep. Both consumers keep a single `registry`
argument typed `ProviderSemanticRegistry | SemanticAuthority | None`;
`resolve_authority_inputs()` splits it. A bare registry still resolves rows for
diagnostics and provisional paths, but admission refuses `UNTRUSTED_AUTHORITY`. That
keeps the evidence chain's own refusals (`PENDING_EVIDENCE`, `FIELD_MISMATCH`, ...) at
their historical meaning instead of collapsing them into an authority error.

`sensors/trade.py` gates on three conjuncts - ladder AND authority AND `attests` - so a
locally ladder-consistent theory cannot reach acceptance without a loader-issued
approval. `LiquidationSideAdmission` gained `admission_approval_id` and
`admission_registry_digest`, with a law requiring both whenever a side is admitted.

## 5. ATTACK - what the loader refuses

Every refusal above has a test that constructs the attack rather than describing it:
an approval for a different artifact; an approved file with one byte changed; artifact
bytes plus a self-declared digest; a revoked approval id; an expired `valid_until`; a
missing evaluation time; a registry `schema_version` mismatch; an unregistered
methodology; evidence citing a provider the artifact does not bind; a fabricated native
field; a transformation not named in `approved_transformations`; an unresolved blocking
assumption; a manifest with a duplicate key; an authority object minted outside the
loader; a mapping whose two rows claim one field.

Negative-path assertions were added, never softened, and no sealed historical evidence
was rewritten by hand.

## 6. REGRESSION

```text
NEW CONTRACT              32 passed
I11 SEALED SUITES         91 passed (three files, each wrapped by a labelled
                          synthetic trust root `_p2a_trust_root(registry)`)
NORMALIZATION PACKAGE     1100 passed, exit 0
FULL CANONICAL SUITE      4498 passed, 14 skipped, exit 0
```

Disclosed audit amendments, each carrying its reason in place:

* `test_b5_i01_scope_audit.py` - the authorized subpackage set gains `authority`.
* `test_b5_i05_scope_audit.py` - the added-path prefixes gain
  `src/.../normalization/authority/` and `config/.../provider_semantics/`.
* `test_b5_i08/i09/i10/i11_scope_audit.py` - sealed-diff excludes plus the I10 allowed
  tuple (the authority package, the manifest directory, the `test_b5_i09p2a_` prefix)
  and a rule refusing any `*.yaml` or non-manifest file in the manifest directory.
* `test_b5_i05_i06_replay_safety.py` - the disclosed source prefix tuple gains the
  authority package, and the regenerated I05 artifact is pinned at its disclosed
  post-extension bytes.
* `test_b5_i01`/`i05`/`i08`/`i09`/`i10`/`i11` exact bytes are pinned in the I06
  producer's `P2A_DISCLOSED_SHA256` block; predecessor pins were kept, not rewritten.
* The I09 producer's SEM-A01 inventory row now expects `authority.py`.

No allowlist was broadened to a pattern; every entry names one tree.

## 7. EVIDENCE AND PINS (mechanical republish only)

```text
I05 ARTIFACT  bloc_05_time_validation.json           9ba207fd74339c1bcd8422b39d104ea242a4094a4733eb7f9e3c974328168040
I06 ARTIFACT  bloc_05_replay_safety_validation.json  04770f5f31dfe275c91db044614f19c31983cb758b61839fe1c00dd14ff79f2a
I09 ARTIFACT  bloc_05_semantic_validation.json       7eeca3ec3b96eeb8d1f21437e6bbad655d6726be88ad424d7b30d73e68c3ff3a
```

Regenerated by their own producers in dependency order - the I05 artifact carries an
inventory that includes the amended audits, the I06 row pins the I05 artifact, and I09
pins the amended semantic surface. Each producer reports zero failing rows: I05 86/86,
I06 14/14 with its scope audit 8/8, I09 35 rows / 0 fail / 3 unresolved (unchanged from
the I09 checkpoint). The I06 producer gained a disclosed `P2A_DISCLOSED_SHA256` and
`P2A_DISCLOSED_EVIDENCE_SHA256` block; no earlier pin was edited.

## 8. NOT CLAIMED - explicit residuals

* **No real provider approval exists.** The manifest ships `"artifacts": {}`; the
  production trust root approves zero artifacts and every admission under it refuses.
  An approved schema is not an approved provider interpretation.
* **G7 record-level provenance is PARTIAL.** Admission records the approval id and the
  registry digest, but per-evidence-row provenance through the exported record is not
  earned.
* **No protection against same-privilege code.** A caller that can rewrite the manifest
  can mint authority. This loader defends artifact bytes against the manifest, not the
  manifest against the operator.
* **No gate promotion.** B5-I09b stays DEFERRED; I11 stays
  IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD; BLOC_05 stays INCOMPLETE; I12/I17 remain
  unauthorized; RESEARCH stays frozen.

STATUS: `B5-I09P2A_IMPLEMENTATION_COMPLETE` - NOT RATIFIED, NOT PROMOTED.
