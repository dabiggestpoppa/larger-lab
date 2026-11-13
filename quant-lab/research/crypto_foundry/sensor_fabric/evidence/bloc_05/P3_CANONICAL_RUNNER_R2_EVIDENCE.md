# BLOC_05 — SENSOR-B5-P3-CANONICAL-R2 — VERIFIER HARDENING EVIDENCE

**Branch:** `agent/crypto-sensor-fabric-p3-canonical-r2`
**Runner under repair:** `b7dfa3b9ef126b533f6bf6d4b1772fb7c871b038` (P3-CANONICAL-R1)
**Independent audit that found the weaknesses:** `5406c553f1aeacff0b82d8c6d7d950e83afed823`
**R6 security implementation (reference only, not merged):** `9d289500fd7bdd4145d2b9d5e052b93e471cd1f1`

This checkpoint repairs the four verifier weaknesses the R1 audit preserved as
counterexamples, and changes nothing about how the runner executes tests.

---

## 1. The four weaknesses, reproduced RED

Against the unmodified R1 runner, on the committed `canonical-p3-r1` bundle:

```
V01 forged pass count:      COMPLETE
V02 forged digests:         COMPLETE
V03 shrunken universe:      COMPLETE
V04 emptied JUnit:          COMPLETE
```

Every forgery verified clean, exactly as the audit reported. The audit's own
suite (`scripts/test_canonical_runner_audit_attacks.py`) encodes these as
`test_forged_pass_count_is_still_complete`,
`test_forged_digest_is_not_reverified` and
`test_shrunken_universe_is_invisible_to_verify`.

## 2. Repairs

The verifier no longer reads a bundle's summary of itself. `evaluate_bundle`
now calls `_reconcile_evidence`, which recomputes every derived number from the
evidence that number claims to summarise.

| Finding | Mechanism | Refused because |
|---|---|---|
| **V01 forged aggregate counts** | Per-node `outcomes` maps are summed; each partition's recorded `counts`, and the execution totals, must equal the recomputation. | A total that no per-node outcome supports is `counts_reconciliation_failed`. |
| **V02 forged digests** | `collection.count`/`digest` and `execution.unique_count`/`digest` are recomputed from the listed node IDs. | A stale or invented digest is `digest_reconciliation_failed`; a count that disagrees with its own list is `counts_reconciliation_failed`. |
| **V03 consistently reduced universe** | Three structural anchors: the union of partition outcomes must equal the execution node set; a partition may only account for files it was given (or nodes it declared as intended); no node may be reported by two partitions. Plus an optional external universe anchor (`--expect-count`, `--expect-digest`). | A hidden node leaves a trace somewhere: in the partition that ran it, in the file list it came from, or in the anchor recorded outside the bundle. |
| **V04 JUnit / result-stream disagreement** | When the bundle declares `junit_sha256`, the artifact beside `evidence.json` must exist, hash to the recorded value, parse, and report exactly as many cases as the partition executed. Producers now also record `junit_case_count`. | Divergence is `junit_missing` / `junit_digest_mismatch` / `junit_unreadable` / `junit_case_count_mismatch`, all `INCOMPLETE_INFRA`. |

Disposition classes are unchanged: integrity and coverage failures are
`INCOMPLETE_COVERAGE`, artifact failures are `INCOMPLETE_INFRA`, and `COMPLETE`
still requires every existing gate to pass as well.

## 3. Post-repair results

| Suite | Result |
|---|---|
| R2 attack suite (`scripts/test_canonical_runner_r2_attacks.py`) | **16 passed** |
| R1 runner self-tests (`scripts/test_canonical_runner.py`) | **24 passed** |
| R1 audit suite re-run against the repaired runner | **27 passed, 3 failed** |
| Governance (I05/I09/I10 scope audits + I11R2 evidence and binding) | **75 passed** |

The three R1-audit failures are the three counterexamples, now failing because
they assert the *unsafe* outcome: `test_forged_pass_count_is_still_complete`,
`test_forged_digest_is_not_reverified`,
`test_shrunken_universe_is_invisible_to_verify`. That is the repair working.
The audit's JUnit case still passes only because that suite calls
`evaluate_bundle` without a bundle directory; the R2 suite exercises the same
mutation with one and it is refused.

## 4. Positive control and anchors

```
verify evidence.json                                  -> COMPLETE, reasons [], 4708/0/0/11
verify evidence.json --expect-count 4719 \
        --expect-digest 468a66ae…d2328c              -> COMPLETE, rc 0
verify evidence.json --expect-digest 0000…0000        -> rc 1, digest_reconciliation_failed
```

The committed 4,719-node bundle still verifies. Its aggregates were never
forged, and the repair proves that rather than assuming it.

## 5. Guarantees preserved

- The execution path, partitioning, ownership gate, containment guard,
  restoration proof, resource limits and interruption handling are unchanged.
- `run_partition` gains one field (`junit_case_count`); nothing it decided before
  it decides differently now.
- Historical bundles and run directories were not rewritten. The committed
  `canonical-p3-r1` bundle is byte-unchanged; every attack mutates a copy.
- No allowlist was widened and no frozen plan was touched.

## 6. Governance

| Check | Result |
|---|---|
| Tracked `.py` | 1,100 → **1,101** (this checkpoint adds one `.py`) |
| I11R2 republish | mechanical, single-line diff `python_files_scanned: 1100 → 1101` |
| Governance suites | **75 passed** |
| Provider approval manifest | `artifacts == {}` |
| `quant-lab/src` | unchanged |
| Canonical universe | **not executed** — Agent 2 owns that run |
| Production merge / authority promotion | none |

## 7. Residual limitations (stated, not hidden)

1. **A fully consistent forgery still needs the anchor.** An attacker who
   rewrites the node lists, every partition outcome, every digest *and* the
   file lists produces a bundle that is internally consistent. Only
   `--expect-count`/`--expect-digest`, taken from a source outside the bundle,
   can refuse it. The flag is available and enforced when supplied, but it is
   not mandatory, because making it mandatory would invalidate every previously
   published bundle.
2. **JUnit agreement is count-level, not identity-level.** JUnit cannot be
   mapped back to pytest node IDs without guessing at classname mangling — the
   R1 plugin docstring says so — so a JUnit file that reports the right *number*
   of cases with the wrong names would pass. Closing that requires a JUnit
   `classname`/`name` → node ID derivation that is not yet trustworthy.
3. **Two bounded R1 blind spots are untouched**, as they were outside this
   checkpoint's four findings: a truncated result stream is re-credited by the
   post-call append (R1 case 24), and duplicate records inside one partition
   collapse into a single outcome (R1 case 25).
4. **The canonical universe is not re-measured here.** This is a verifier
   checkpoint; the 4,719-node execution at a pinned commit remains Agent 2's.

## 8. Disposition

`VERIFIER_HARDENED_WITH_BOUNDED_ANCHOR`

The four independently reproduced verifier weaknesses are closed and proven
closed by an independent attack suite that fails without the repair. The
remaining gap is not a bug in the verifier but a property of self-describing
evidence: internal consistency is necessary and no longer sufficient, and the
external anchor that makes it sufficient is supported, tested, and still the
operator's to supply.
