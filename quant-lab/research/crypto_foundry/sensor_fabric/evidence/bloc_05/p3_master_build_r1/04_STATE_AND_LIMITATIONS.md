# 04 — State, limitations, unresolved requirements

## 1. Integration state (unchanged, deliberately)

```
approval_manifest.json   artifacts = {}          revoked_approval_ids = []
INTEGRATION_STATE        INTEGRATION_REQUIRED
```

The manifest was not modified to make tests pass. A test asserts the shipped
manifest is byte-identical to `TRUSTED_MANIFEST_SHA256` and still empty. No real
provider can be authorized while it is empty — that is the integration state,
not a defect in the code.

## 2. The unresolved operator-authority contract

**The gap, stated exactly.** `ApprovalManifest` has exactly four fields —
`schema_version`, `authority_id`, `artifacts`, `revoked_approval_ids` — and
`ApprovedArtifact` names a registry artifact (`sha256`, `approval_id`,
`registry_schema_version`, `approved_at`, `valid_until`, `available_at`,
`evidence_blobs`, `allowed_methodologies`, `evidence`,
`declared_native_fields`, `approved_transformations`,
`resolved_blocking_assumptions`). None of them says *"this custody store, run by
this operator, may authorize these record kinds for these providers"*. A test
introspects both models and asserts the absence of `custody_source`,
`authorized_custody_provider`, `operator_authority`, `source_authorization`.

**What is required.** A record type — named in the code as
`OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` — that binds, under the reviewed
root, (a) the custody store identity, (b) the operator, (c) the record kinds it
may authorize, (d) the providers it may authorize them for, (e) an availability
window, and (f) a revocation channel. Until that record exists and is reviewed
by the operator, every derivation correctly stops at `INTEGRATION_REQUIRED`.

**What was not done.** Artifact approval was not reinterpreted as source
authorization. No token was invented, and no constant exists in `src/` that an
operator could write into a manifest to obtain authority — a test asserts the
derivation defines none.

**Consequence.** The `AUTHORIZED` branch of `derive_custody_authority` is
unreachable in production today. It is exercised in `policy.py`'s tests only
through a test-local wiring double, and `test_the_production_source_never_authorizes`
asserts the production source cannot reach it. **No positive authorization path
has been proven**, and this packet does not claim one.

## 3. Known limitations

| # | Limitation | Why it stands | What would change it |
|---|---|---|---|
| L1 | The accepting branch is only reachable through a test double | the operator-authority record does not exist (§2) | a reviewed record type |
| L2 | Divergence diagnostics are omitted; `CACHED_VERDICT_DIVERGENCE` is defined but unreachable | design §5 permits omitting the seam and forbids a cached verdict establishing acceptance | a deliberate diagnostic interface with its own threat model |
| L3 | No store-consistency guarantee across the two reads of a consumption | the custody backend is a keyed read; two references are not read atomically | a snapshot read API, or a store with read-your-writes isolation |
| L4 | A crashed verifier's own message prefix (≤200 chars) is relayed for diagnosis | design §3 specifies "exception class + first 200 chars" | redaction, at the cost of operability |
| L5 | `X01`–`X06` privileged-code conditions are out of scope | an in-process object cannot withstand code with the application's privileges | process/privilege separation |
| L6 | Full canonical **execution** not run in this pass | which rung owns it — see §4 | Rung 6 |
| L7 | `__init__.py` exports nothing | a re-export would make `consumer` unimportable without `sensors.verification` (design A1.5) | a lazy public API, if one is ever needed |

## 4. Verification actually performed

| Check | Command | Result |
|---|---|---|
| Consumer suites (5 files) | `pytest -q <five consumer files>` | **139 passed** |
| Governance set (10 files: I01/I05/I08/I09/I10/I11 scope audits, I09P2C, I09P2E, I11R2 binding + evidence) | `pytest -q <ten files>` | **344 passed** |
| I09 SEM evidence determinism | `b5_i09_semantics.py --check` | exit 0, artifact `e5c84451…dbd1b` |
| I11R2 inventory republish | `UPDATE_I11R2_EVIDENCE=1 pytest …test_i11r2_binding_audit.py` | 4 passed, pin 1,111 |
| Canonical collection | `canonical_runner.py collect --workers 4` | **4,930 nodes**, digest `716a05796a5060963edfbf3259afbd0636572390ecb954983f648f35d3456905`, 0 duplicates, 0 malformed, 0 errors, 13 groups |

**What was NOT run, stated plainly:** the full canonical *execution* (4,930
nodes). Collection is not execution, and this packet makes no `COMPLETE` claim.
The count was re-measured rather than inherited: 4,733 → 4,930 = +197 nodes, of
which 139 are the new consumer tests and 58 are the AUTH counterexample tests.

## 5. Proposed Rung 6 execution plan

1. Full canonical execution through `canonical_runner.py run --workers 4`, with
   the guarded-evidence snapshot/restore and the collected-vs-executed
   reconciliation it already implements. Report `COMPLETE` only if no node is
   missing.
2. If the operator-authority record is reviewed in the meantime, activate the
   `AUTHORIZED` branch behind it and re-run R3–R5 against a *real* positive path;
   until then, leave it unreachable and keep saying so.
3. Hand the independent probes to Agent 2 unchanged; do not fold audit evidence
   into this implementation packet.
4. Rung 7 (operator acceptance) remains a separate checkpoint. No merge, no gate
   advancement, no trust promotion happens here.

## 6. Dispositions

```
implementation   P3_PRODUCTION_CONSUMER_RUNGS_1_TO_5_IMPLEMENTED_AWAITING_FINAL_VERIFICATION
integration      INTEGRATION_REQUIRED   (unchanged)
source authority NOT GRANTED            (no record type exists)
trust promotion  NOT PERFORMED
gate advancement NOT PERFORMED
self-ratification NOT CLAIMED
```

## 7. Disclosed governance findings from this pass

* **G14** — canonical collection re-measured, not inherited (§4).
* **G15** — I09 SEM evidence republished: its `sha256_inventory` pins the I01 and
  I05 audit files, so amending them changes two digest rows. Discovered by
  running the check, then republished mechanically with `--check` exit 0.
* **G16** — `test_b5_i08_scope_audit.py` refuses any tree beside `common/`,
  `sensors/` and `authority/` under an I08-era base diff, so admitting
  `consumer/` required one disclosed word in that file. The amendment is
  prospective, keeps every previously admitted path admitted, and is constrained
  elsewhere by `P3_MASTER_EXACT_PATHS` in I05/I10 — the directory is not thereby
  opened. Both exact-path sets name the I08 audit file itself so the amendment is
  admitted rather than smuggled.
* The I08 refusal was found **by execution**, on the first full governance run
  after R5 — not by inspection. It is recorded here rather than quietly patched.
