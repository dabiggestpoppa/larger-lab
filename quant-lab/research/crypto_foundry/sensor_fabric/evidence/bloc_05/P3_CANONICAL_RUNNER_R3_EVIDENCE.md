# BLOC_05 — SENSOR-B5-P3-CANONICAL-R3 — EVIDENCE VERIFIER INTEGRITY

**Branch:** `agent/crypto-sensor-fabric-p3-canonical-r3`
**Base:** `dc0898eb21e8e646c2e774573faf1cb767a0911c` (Canonical R2)
**Reference lock:** R1 runner `b7dfa3b9`, R1 independent audit `5406c553`, R6 implementation `9d289500`

R3 closes the five evidence-accounting gaps R2 disclosed. It does not change
the verified execution architecture: partitioning, ownership, containment,
restoration, resource limits and interruption handling are untouched.

---

## 1. RED reproductions (before any repair, R2 runner)

| ID | Condition | Observed at R2 |
|---|---|---|
| **R3-01** | A test truncates its own result stream mid-call; pytest appends the pass afterwards | the node is credited `passed`; no accounting error field exists |
| **R3-02** | A second `call` record is appended for the same node | the duplicate collapses into one outcome; nothing is flagged |
| **R3-03** | Collection and execution universe falsified consistently, partitions and JUnit rewritten to match | `COMPLETE`, with no way to distinguish it from an independently verified result |
| **R3-04** | JUnit carries the right number of cases with the wrong identities | `COMPLETE` (count matched; identity was never compared) |
| **R3-05** | A new untracked file appears under a guarded evidence prefix | the guard snapshots tracked files only; additions are invisible |

The R3 suite recording these is `scripts/test_canonical_runner_r3_attacks.py`.
Against the R2 runner it reported **8 failed, 1 passed**; the one pass was the
phase-semantics control, which must be true before and after.

## 2. Repairs and root causes

### R3-01 / R3-02 — result-stream accounting

Root cause: the stream was a bag of reports. Nothing distinguished "the session
finished" from "the file stops here", and per-node records were folded into a
set before anyone asked whether the fold was legitimate.

- The pytest plugin now writes a **session sentinel** (`record_type:
  session_end`) carrying the number of reports it wrote and the number of
  distinct node identities it saw. A truncated file cannot produce it, and a
  surviving prefix is caught by count disagreement.
- `_account_node` derives each node's outcome from its **phases**: a `pass`
  requires a `call` phase whose outcome is `passed`. A missing `call` phase is
  `missing_call_phase`, not an assumption; unknown phases, duplicate phase
  reports and unexpected call outcomes are all accounting errors.
- Legitimate skips remain skips: pytest reports them by failing `setup`, never
  by omitting a pass, so the 11 skipped nodes in the real bundle still classify
  as `skipped` with zero errors.
- Duplicates are detected **before** collapse, per phase and per node.
- Partition totals and the global universe reconcile from per-node outcomes;
  the global set must equal the union of partition accounting.

### R3-03 — assurance level

Two states are now named in the verdict:

| State | Meaning |
|---|---|
| `ANCHORED_COMPLETE` | the expected universe was established outside the bundle: `--expect-count`/`--expect-digest`, or a `universe_anchor` recorded at run time that matches |
| `SELF_CONSISTENT_COMPLETE` | every internal check agrees, but nothing outside the bundle vouches for the universe |
| `NOT_COMPLETE` | any refusal |

`--require-anchor` turns self-consistency into a refusal (`anchor_required`).
The default stays lenient so historical evidence remains verifiable, and the
assurance field keeps the distinction visible instead of collapsed.

### R3-04 — JUnit identity binding

`_junit_identity` rebuilds the `(classname, name)` pair pytest's JUnit writer
derives from a node ID: path separators become dots, `.py` is dropped, class
segments are joined, and the final segment — including parametrisation, spaces
and punctuation — is preserved verbatim.

Verified empirically against the committed bundle before being relied on: the
derived set equals the observed set for **all 4,719 cases** in both partitions.
The verifier now compares the case multiset, so right-count/wrong-identity is
refused, and duplicate case occurrences are visible. Case count and artifact
digest are still checked first.

### R3-05 — untracked evidence guard

`snapshot_untracked` records untracked files under the guarded prefixes before
the run (respecting `.gitignore`); `detect_new_untracked` reports additions
afterwards, excluding the runner's own output tree. Additions are recorded in
`tree.untracked_added` and refused at verify time as
`untracked_evidence_added` → `INCOMPLETE_INFRA`.

The guard **reports and never deletes**: tracked-file restoration is unchanged,
ownership protections are unchanged, and no user file is removed.

## 3. Changed paths

```
quant-lab/research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py
quant-lab/research/crypto_foundry/sensor_fabric/scripts/canonical_pytest_plugin.py
quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_r3_attacks.py   (new)
quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json   (one count line)
quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/P3_CANONICAL_RUNNER_R3_EVIDENCE.md          (this file)
```

## 4. Test counts

| Suite | Result |
|---|---|
| R3 negative suite (new) | **9 passed** |
| R2 hardening suite | **16 passed** |
| R1 runner self-tests | **24 passed** |
| R1 independent attack suite | **27 passed, 3 failed** |
| Governance (I05/I09/I10 scope + I11R2 evidence and binding) | **75 passed** |

The three R1-audit failures are `test_forged_pass_count_is_still_complete`,
`test_forged_digest_is_not_reverified` and
`test_shrunken_universe_is_invisible_to_verify`. They are **obsolete positive
expectations**: they assert the unsafe outcome that R2 and R3 exist to refuse.
They were not edited, rewritten or deleted — they are reported here as
superseded. The audit's JUnit case still passes only because that suite calls
the verdict without a bundle directory; the R2 and R3 suites exercise it with
one.

## 5. Historical compatibility

The committed `canonical-p3-r1` bundle still verifies `COMPLETE` with
`4708 / 0 / 0 / 11`, now labelled `SELF_CONSISTENT_COMPLETE` because it predates
anchoring. Its JUnit artifacts pass the new identity binding, which is why the
binding could be applied without rewriting any historical evidence. No previous
bundle, ledger entry or evidence artifact was modified.

## 6. Governance

| Check | Result |
|---|---|
| Tracked `.py` | 1,101 → **1,102** (one new test file) |
| I11R2 republish | mechanical, single-line diff `python_files_scanned: 1101 → 1102` |
| Governance suites | **75 passed** |
| Frozen allowlists | not widened |
| Provider approval manifest | `artifacts == {}` |
| Frozen plan hashes | unchanged |
| `quant-lab/src` | **unchanged** (zero production source changes) |
| Canonical universe | **not executed** — Agent 2 owns that run |
| Production merge / provider approval / trust-consumer promotion | none |

## 7. Residual limitations

1. **Anchoring is optional by default.** A sufficiently determined forger can
   still produce a self-consistent bundle; R3 labels it rather than pretending
   to detect it. `--require-anchor` is the strict mode, and it is what an
   independent verification should use.
2. **Legacy bundles cannot gain an anchor retroactively.** The R1 bundle's
   assurance is honestly `SELF_CONSISTENT_COMPLETE`; only a fresh anchored run
   changes that.
3. **JUnit identity rests on pytest's mangle being stable.** It is verified
   exactly on 4,719 cases at this pinned pytest version. A future pytest that
   changes classname construction would make the binding refuse a genuine run —
   fail-closed, but it would need a deliberate re-derivation.
4. **The untracked guard is prefix-scoped.** Files added outside the guarded
   prefixes are still governed only by the worktree cleanliness check.
5. **A session sentinel cannot detect tampering by the producer itself.** A test
   process that forges both the records and the sentinel is indistinguishable
   from a real run without the external anchor; the sentinel closes truncation,
   not authorship.

## 8. Disposition

`EVIDENCE_ACCOUNTING_HARDENED_WITH_NAMED_ASSURANCE`

All five disclosed weaknesses are reproduced, repaired and proven repaired by
an independent suite that fails without the repair. The residual gaps are
labelled in the verdict rather than left implicit: the verifier now says
whether completeness was independently anchored or merely self-consistent, and
never claims the former on the strength of the latter.
