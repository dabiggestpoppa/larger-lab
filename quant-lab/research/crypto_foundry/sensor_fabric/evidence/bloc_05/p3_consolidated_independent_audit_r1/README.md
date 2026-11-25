# SENSOR-B5-P3-R6 — CONSOLIDATED INDEPENDENT TECHNICAL AUDIT

**SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**

| | |
|---|---|
| Mission | `SENSOR-B5-P3-R6-INDEPENDENT-ACCEPTANCE-R1` |
| Audited candidate | `5ee268b1d872fe4040d2d1505d012f344e7b5d54` (R5) |
| Carrier | `agent/crypto-sensor-fabric-p3-production-master-audit-r1` |
| Authorization base | `13086755d22a539c6a4dcb20e782bce97fcde82d` |
| Disposition | **`P3_FINAL_REPAIR_REQUIRED`** (F1) |
| Canonical acceptance | **PENDING** — no R6 collection evidence published |

Supersedes the R0 package (`p3_production_master_audit_r0`, head `18857504a`,
disposition `P3_CONSUMER_IMPLEMENTATION_ABSENT`). That package's absence finding
was correct for the tree it measured and is now obsolete.

---

## 1. Lineage verified before measurement

All six commits exist locally and on `origin`, in this order, each an ancestor
of the next; the audited worktree's `HEAD` is exactly R5.

```
f4972cba8  B5-P3-MASTER-AUTH  admit bounded production consumer implementation
198e2aaab  R1 contracts
7cb7763b9  R2 policy-owned verification derivation
7155cbf60  R3 bounded custody authority derivation
6af9200fa  R4 temporal eligibility and evidence rebinding
5ee268b1d  R5 executable production consumer security suite
```

`git ls-remote --heads origin` shows only `…-design-r0`, `…-master-audit-r1`
and `…-master-r1`. No R6 canonical branch or collection exists.

## 2. What was actually executed

| # | Command (materialized from `.py.txt`) | Observed |
|---|---|---|
| 1 | `pytest test_master_governance_challenge_v2.py` | **27 passed**, 0 failed, 0 errors |
| 2 | `pytest test_second_agent_p01_p06.py` | **49 passed, 3 failed** (the three findings) |
| 3 | `run_source_mutations.py` (7 mutations, disposable `src/` copies) | 4 detected, 3 survived, 0 invalid |
| 4 | Agent 1's consumer suite, reproduced independently | **139 passed** |
| 5 | The six amended governance audits, reproduced | **180 passed** |

No probe is a specification: every case here ran. `test_*.py.txt` files are
non-collected research artifacts; they add no tracked `.py` and inflate no
canonical count.

## 3. Findings

### F1 — Replay evidence is not bound to the record, provider or cutoff — MEDIUM — OPEN

**Audited SHA** `5ee268b1d`.

**Counterexample (executed).** A record with `source_revision_id="rev-OWN"`
evaluated at cutoff `2026-06-01T12:00Z`, with otherwise-eligible replay evidence
whose selected revision is `rev-FOREIGN` and whose `market_available_at` is
`2027-01-01T00:00Z`:

```
replay_status = "ELIGIBLE"
decision      = ACCEPT_FIELD_BINDING   (with a non-empty reviewed root)
```

**Positive control.** The same code with matching evidence reports `ELIGIBLE`;
with `interval_complete=False` it refuses `REPLAY_BLOCKED`. The gate is
policy-owned and it does fire — it is the *binding* that is absent.

**Cause.** `TrustConsumerPolicy._adjudicate_replay(request.replay_evidence)`
receives only the evidence. `ReplayEvidence` derives from `TimeEvidenceBase`,
which is an empty base: it carries no record id, no provider and no cutoff.
`assess_replay_eligibility(evidence)` takes no cutoff argument. The policy owns
adjudication; nothing owns provenance.

**Impact.** `ConsumerVerdict.replay_status` asserts replay admissibility the
policy did not establish. Today that cannot become an acceptance, because the
shipped root approves no artifact and verification refuses first. The moment an
operator supplies a non-empty manifest, the same request accepts on another
record's evidence, and on evidence that says the data only became public after
the request's own knowledge cutoff.

**Required repair (bounded, no governance amendment).** Both record kinds expose
`source_revision_id`. Before concluding, require

* every `replay_evidence.revision.selected[*].source_revision_id == request.record.source_revision_id`, and
* `replay_evidence.market_available_at <= request.knowledge_cutoff`,

refusing `REPLAY_BLOCKED` otherwise. If the operator prefers the binding to live
in I05, that is an amendment and needs separate authorization — the bounded
repair above does not.

### F2 — The crash verdict relays a dependency's exception message — LOW — OPEN

A wired custody provider raising `RuntimeError("SECOND-AGENT-SENTINEL-…")`
produced

```
refusal_detail = "RuntimeError: SECOND-AGENT-SENTINEL-7f3c1a-DO-NOT-ECHO"
```

The 200-character bound holds; the *content* is whatever the dependency said.
The module docstring claims no detail carries payload, and the post-verification
custody path keeps that promise (fixed message, verified). Only the generic
handler in `evaluate()` breaks it. Artifact bytes and evidence bytes are never
echoed (separately verified with a sentinel inside them).

Reachability: a trusted dependency must raise with sensitive text; a caller
cannot choose the message. Repair: emit the class name only, as the
custody-authority handler already does.

### F3 — An unexpected loader failure escapes `evaluate` — LOW — OPEN (composition)

With `load_trusted_authority` raising `KeyError` during rebinding,
`TrustConsumerPolicy.evaluate` propagates the exception and no verdict is
returned. `_rebind` catches only `RecordVerificationError` and
`SemanticAuthorityRefusal`.

Reachability: the loader is trusted composition (X02/X03). All nine request-level
bypasses in the P04 matrix returned a verdict — **0 unexpected exceptions from
data**. So this is a fail-closed gap for a composition fault, not a remote
attack. Repair: the same bounded handler as `_derive`, mapping to
`VERIFIER_CRASH`, letting `BaseException` propagate.

## 4. Governance reconciliation (the previous 26 cases)

| R0 case | R5 status |
|---|---|
| M1 I01 lacks `consumer` | **RESOLVED** — membership is now `{identity, terms, time, common, sensors, authority, consumer}` |
| M2/M3 I01 historical + exactness | unchanged green |
| M4/M5 I05/I10 admit the granted path | **RESOLVED** — 18 prefixes + 11 exact / 26 prefixes + 11 exact |
| M5b inventory | reconciled: the D-1 packet's "25" for I10 was off by one; the tuple alone has 26 entries, plus an 11-entry exact grant |
| M6 suffix variants admitted | **SPLIT** — see below |
| M7 required-oracle control | retained (re-scoped to the exact entries) |
| M8/M9/M10/M11 | retained; M11 now measures the shipped predicate in a disposable repo |
| M12 frozen artifact rewritten | **RECLASSIFIED** — the rewritten file is a *generated* inventory (see G15) |
| M13/M14 manifest and integration state | green — still empty, still pinned, unchanged since the base |
| M15 I09 sealed surface | green — 8 surfaces named, `consumer` absent |
| M16 I11R2 inventory | green — 1111 == measured repo-root count |
| M17 grant verdict | superseded by the path-set delta measurement |
| 12 R0 ERRORs | **fixed** — they assumed a function-local `allowed_prefixes`; v2 imports the shipped `_authorized` in a subprocess and calls it |

**The exact admitted path set (measured, not reconstructed).** Over a universe of
5,808 paths (every tracked `.py` at base and at HEAD, the disclosed grant, the
refused variants and the historical samples), base predicate vs live predicate:

```
i05: +9 added, 0 removed      i10: +9 added, 0 removed
added = exactly the nine P3 paths (4 sources, 5 tests)
```

**New exact-file behaviour.** The nine new paths are admitted by equality:
`models.py_evil.py` is refused 9/9 in both audits. This closes the R0 law defect
*for the new grant*.

**Historical prefix weakness — intentionally preserved.** File-kind entries that
predate the grant are still tested with `startswith`: 4/4 in I05 and 9/9 in I10
admit `<entry>_evil.py`, exactly as at the base. No new entry joined them, so
the blast radius did not grow. Two of the eleven granted audit paths
(`test_b5_i08_scope_audit.py`, `test_b5_i10_scope_audit.py`) sit inside the
historical `test_b5_i08` / `test_b5_i10` prefixes and therefore remain exposed;
that is the pre-existing defect, not an expansion. Because pytest collects
`test_*.py*`-shaped files, a suffix variant would still be collected if an actor
who can add repository files added one — a low-severity residual, unchanged.

**G15 — I09 semantic evidence republication.** `bloc_05_semantic_validation.json`
*was* rewritten since the authorization base. It is a generator output
(`generator: …/b5_i09_semantics.py`, no timestamps), all **13** digest rows now
verify against the bytes they pin, no row was added, and exactly three rows moved
— the I01, I05 and I08 scope audits this checkpoint amended. No hand-written
artifact (`BLOC_05_I01_*`, `BLOC_05_I10_*`, `bloc_05_unit_validation.json`) was
rewritten. This is lawful republication, disclosed in the R1 and R5 commit
messages; it is not retroactive editing.

**G16 — I08 sealed-tree amendment.** One branch was added, `"/consumer/"`, beside
`/common/`, `/sensors/` and `/authority/`; all three historical branches survive,
and the diff the assertion evaluates is pathspec-limited to
`src/crypto_sensor_fabric/normalization`, so the substring test cannot admit a
tree outside the package. I08 executes green at R5 (10 passed).

**I11R2 inventory.** 1102 → 1111 is exactly +9, and the nine added `.py` files are
exactly the authorized P3 set. The artifact equals the measured repository-root
count (the subtree count, 696, is the measurement error that file's own history
records).

## 5. Rung and acceptance matrices

| Rung | Verdict | Basis |
|---|---|---|
| R1 contracts | **ACCEPTED** | no callback, verdict, capability or basis field is representable |
| R2 derivation | **ACCEPTED WITH F1** | scope, dimensions, record kind and allowlist all refuse correctly; replay provenance unbound |
| R3 authority | **ACCEPTED** | empty-manifest invariant holds for every identity; four identity axes refuse; foreign roots refuse at construction |
| R4 rebinding/PIT | **ACCEPTED** | two reads per approved reference; omitted references still read the whole approved set; flipped bytes refuse |
| R5 suite | **ACCEPTED WITH F2/F3** | 139 tests reproduced; the findings are diagnostic and stage-exception surfaces |

A01–A20: **20/20 executed and green** in an independently written probe. A15 is
green for a *forged evaluation object*; it does not cover F1's foreign-but-valid
evidence, which is why F1 is reported separately rather than hidden inside A15.

## 6. Mutation accounting

| Mutation | Disposition | Why |
|---|---|---|
| M1 evidence rebinding (both digest comparisons) | **DETECTED** | flipped bytes then accept |
| M2 replay adjudication (`blocked = False`) | **DETECTED** | blocked evidence then accepts |
| M3 policy manifest identity check | **SURVIVED** | `ManifestCustodyAuthority` independently refuses the foreign root (N2) |
| M4 required-field inspection | **DETECTED** | an unknown required field then accepts |
| M5 consumer custody prerequisite | **SURVIVED** | the verifier raises `CUSTODY_UNVERIFIED` first (N1) |
| M6 authority identity binding | **DETECTED** | a cross-approval identity then derives `INTEGRATION_REQUIRED` |
| M7 empty-manifest guard | **SURVIVED** | the artifact-absent branch still returns `INTEGRATION_REQUIRED`; the guard is reporting-only (N3) |

7 executed, 4 detected, 3 survived, 0 invalid. No mutated source was committed;
each mutation ran against a fresh disposable copy.

## 7. Rung 6 reconciliation — PENDING

Agent 1 owns the canonical execution and has published none. This auditor will
not accept totals it cannot see, so implementation acceptance and canonical
acceptance are reported separately. The reconciliation checklist is: candidate
SHA, collection digest, partition membership, executed nodes, raw output, JUnit
totals, artifact hashes, exit codes, evidence restoration, missing and duplicate
nodes, skip dispositions.

## 8. Limitations

* The accept path exists only under a wiring-double root (X01/X03) because the
  shipped manifest approves nothing. Every case needing it says so; findings that
  need it are labelled COMPOSITION.
* The I08/I09 evidence producers spawn a numpy/OpenBLAS process that aborted with
  `Memory allocation still failed after 10 retries` on this host during compound
  runs. The clean governance run was 27/27 and the direct six-audit run was
  180/180; later re-runs were partially inconclusive for that environmental
  reason, which is recorded, not counted.
* The full canonical collection was not run here.
* The historical prefix weakness in the two audit paths is reported, not
  repaired: repairing it is a governance change this checkpoint may not make.

## 9. Hard stops

No production implementation change, no governance amendment, no provider
approval, no custody-source activation, no manifest change, no merge, no trust
promotion, no program-gate advancement, no capital authority, no self-ratification.

## 10. Repair handoff and re-entry

1. Agent 1 repairs **F1** (bounded, from existing record/evidence fields) and,
   at their discretion, **F2** and **F3**.
2. Republish the candidate; publish the repair SHA.
3. Re-entry is localized: re-run only `p02*` (F1), `p01a` (F2), `p04b` (F3) and
   mutation M1/M2, against the repair SHA:

```
RUN=$(mktemp -d)
cp test_second_agent_p01_p06.py.txt "$RUN/t.py"
AUDIT_QUANT_LAB=<quant-lab> PYTHONPATH=<quant-lab>/src \
  python -m pytest "$RUN/t.py" -q -p no:cacheprovider -k "p01 or p02 or p04"
```

4. A green F1 re-entry must show a **refusal** for foreign, post-cutoff and
   cross-provider evidence, and the matching-evidence control must still reach
   `ELIGIBLE` — otherwise the repair has replaced a false claim with a blanket
   refusal.

**Disposition: `P3_FINAL_REPAIR_REQUIRED`.** Rungs 1–5 are otherwise accepted and
their evidence is reconciled; canonical acceptance remains pending until the
canonical collection is published and reconciled.
