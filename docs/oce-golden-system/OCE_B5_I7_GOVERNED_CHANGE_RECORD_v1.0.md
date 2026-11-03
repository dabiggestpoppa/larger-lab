# OCE Golden System — B5-I7 Governed Change Record — v1.0

**Stage:** B5-I7 (charter increment I-8; plan §7 "C4 change cycle plus C5
measurements/learning").
**Branch:** `oce-book-5-i7-build`, created directly from merged P0 main
`9dc0b7d29ab869e256653a6b6ec68c987d0a4090`.
**Change under governance:** exactly one — *add a queue-depth observability
panel* (`B5I7-R02`).
**Status of this record:** implementation and proof record. It is written before
any ratification and it does not authorize a merge: `MERGE_AUTHORIZED=false`.

This record is a **same-agent** artifact. It is **not organizationally
independent** review (`B5I7-EL13`).

---

## 1. Intent (recorded before implementation)

The stage needs one governed, read-only change that makes queue depth visible to
an operator through the existing console client without creating a second state
owner, a second endpoint, or a sixth authoritative status section. The change is
responsive to `B5I7-R02` and is bounded by contract §5.

## 2. Plan and bounded affected surfaces

| Surface | Path | Nature |
|---|---|---|
| governed module | `infrastructure/console/src/oce_console/panel.py` | new, read-only projection |
| additive CLI token | `infrastructure/console/src/oce_console/cli.py` | one `panel` choice + its branch |
| packaging registration | `infrastructure/console/packaging/make_release_manifest.py` | one line in `DECLARED_INSTALL_SET` |
| proofs | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py`, `.../test_b5_i7_evidence_laws.py` | 12 + 15 frozen nodes |
| reproduction harness | `infrastructure/control-plane/scripts/b5_i7_mutation_battery.py` | plan §4.6 named deliverable; same location as the ratified `b5_i2_`/`b5_i6_` batteries |
| evidence | this record, `..._REUSE_INVENTORY_v1.0.md`, `..._REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json`, `..._MUTATION_RESULTS_v1.0.json` | evidence only |
| CI selection | `.github/workflows/b1-i1r-validation.yml` | one additive step |

Not touched at any rung: `infrastructure/control-plane/src/**`,
`infrastructure/control-plane/contracts/**`, every pre-existing file under
`infrastructure/control-plane/tests/**`, every `OCE_B5_I0*`–`OCE_B5_I6*`
document. `test_b5_i7_web_view.py` does not exist and is not created
(`B5I7-DF01`).

## 3. The thirteen governed change-cycle stages

| # | Stage | Record |
|---|---|---|
| 1 | Owner | console client surface, operator-invoked; engine retains all canonical authority |
| 2 | Input | `--base-url` (loopback literal), `--grant`, `--actor`, optional declared surface subset |
| 3 | Transition | one read per declared surface, fixed order, into a projection document |
| 4 | Output | canonical JSON: `state`, `queue`, `workers`, `schedules`, `reads`, `snapshot`, `provenance` |
| 5 | Allowed next state | the console's existing four presentation states only (`OK`, `DENIED`, `UNVERIFIABLE`, `STACK_UNREACHABLE`) |
| 6 | Refusal condition | undeclared surface, duplicate surface, malformed/oversized input, non-loopback base URL |
| 7 | Observable refusal | `ConsoleRefusal(reason, detail)` before any I/O; CLI exit `3` |
| 8 | Rollback path | revert the two additive files; `status` and its exit codes are untouched, so rollback needs no data migration |
| 9 | Retry path | none by design: the panel performs zero retries and no silent re-read |
| 10 | Recovery ownership | engine-owned (`recover_abandoned_leases` is never called by this change); the panel may only *report* engine recovery state |
| 11 | Evidence produced | this record, reuse inventory, addendum, mutation results, 27 nodes, CI artifact |
| 12 | Authority effect | none: `non_authoritative = true`, no write, no cache, no lease/requeue/invoke |
| 13 | Cost effect | none: local stdlib only, `$0` recurring, `capital.authority = none` |

Rollback (8) and retry (9) are deliberately distinct: rollback removes a
deployed surface, retry would re-issue a governed action. This change has no
governed action to re-issue.

## 4. Defects found and repaired during implementation

Every row is a demonstrated defect, not a stylistic note. None is removed from
the record after repair (`B5I7-EL12`).

| ID | Defect (demonstrated) | Evidence that it was real | Disposition |
|---|---|---|---|
| D1 | A health read that returned an intact envelope but no usable counters still summarized `OK`, presenting an unreported queue as a healthy empty queue | the queue law in `TestChangeCycle`/`TestPanelFailClosed` fails against the pre-repair behaviour | Repaired: `known_count < len(QUEUE_FIELDS)` marks the read `partial` and forces `UNVERIFIABLE` |
| D2 | Token material inside a carried denial survived top-level redaction | the R21 node rendered the token through the verbatim block | Repaired: recursive `_sanitize` at every depth |
| D3 | A cookie-shaped value (`session=…`) carried no marker and survived; and a secret-NAMED key was replaced while the value it labelled leaked under the placeholder name | the R21 proof failed on both assertions | Repaired: marker set extended (cookie/session/token/secret/password/credential) and a redacted key redacts its whole value |
| D4 | `contract_pack_sha256` hashed raw working-tree bytes, so the panel's own provenance was CRLF on Windows and LF on Linux and did not equal the frozen pack blob | local value `03fe8063…` versus the contracted `45bcb4f6…` | Repaired: provenance is hashed over the normalized blob; local value now equals `45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa` |
| D5 | The M03 mutation matched an indentation that the module does not use, so it was recorded `ANCHOR_MISSING` instead of discriminating | battery verdict `FAIL`, 13/14 discriminated | Repaired: anchor corrected against the real body; battery now 14/14 |

No defect was repaired by weakening an assertion, and no frozen test was
modified (`B5I7-R03`, `B5I7-R10`).

## 5. Compatibility and refusal behaviour

`status` keeps its five sections (`health`, `readiness`, `system`, `workers`,
`schedules`), its documented invocation and every documented exit code:
`0` OK, `2` unreachable, `3` refused, `4` degraded, `5` unverifiable. The panel
is strictly additive (`B5I7-R23`). One observation carried forward: the frozen
transport accepts loopback **literals** only, so the hostname spelling
`localhost` is refused (`non_loopback_refused`). That is stricter than the
prose of contract §10, never weaker, and is left unchanged because `B5I7-R23`
forbids altering frozen refusal behaviour.

## 6. Measurements (C5.S1; labels are load-bearing, `B5I7-R24`)

| Measurement | Method | Value | Label |
|---|---|---|---|
| focused node count | `pytest --collect-only` over the two files | 27 | OBSERVED |
| focused execution | `pytest --junitxml` over the two files | see addendum | OBSERVED |
| mutation discrimination | `b5_i7_mutation_battery.py` | 14/14 RED, restoration verified | OBSERVED |
| canonical drill reports | two live loopback stacks, closed three-field mask | byte-identical | OBSERVED |
| adjacent population at base | 9-file B5 selection at the base SHA | 186 nodes | OBSERVED |
| adjacent population at head | same selection at the implementation head | see addendum | OBSERVED |
| panel render duration | `time.perf_counter` around `render_panel`, 50 iterations, local host | see addendum | OBSERVED |
| panel document size | bytes of `render_panel` output for the frozen fixture | see addendum | OBSERVED |
| shared authoritative runner | `bash infrastructure/cloud-ground/scripts/run-validation.sh` | `RC=1`, 26 PASS / 5 BLOCKED, gate `BLOCKED` | OBSERVED |
| production performance, RTO/RPO, scalability | not measured and not claimed | — | NOT APPLICABLE |

The shared runner is **not green** and is not reported as green: its five
blockers are environmental (`registry tool`, `ansible-playbook`,
`ansible-lint`, `docker`, `gitleaks` absent locally). CI is authoritative for
those checks. Local timings are host measurements, not production claims.

## 7. Learning record (C5.S4, `B5I7-R14`)

| Field | Entry |
|---|---|
| Expected | an additive read-only projection would need no behavioural repair, only wiring |
| Observed | five defects (D1–D5), three of them in the redaction and summary laws that carry the security and fail-closed guarantees |
| Variance | the "partial is not success" law and the secret laws were the load-bearing parts, not the happy path |
| Surprise | provenance hashing was platform-dependent (D4): a determinism law can be violated by the *checkout*, not by the code path |
| Decision | keep the panel; treat provisioning/digest normalisation as part of the determinism law, not as cosmetics |
| Follow-up owner | operator review at this stage; no new stage is opened |
| Frozen rule changed | none. No requirement was amended, reinterpreted or dropped |

This learning record does not authorize B5-I8 or B5-I9. Both remain locked.

## 8. Reuse inventory (summary; detail in the reuse inventory document)

The panel reuses, without modification: the console kernel's refusal vocabulary
and pack loader, the loopback transport's `read`, the console's four-state
presentation vocabulary, the packaging manifest machinery, the B5-I6 drill
report builder and the B5 test/CI selection conventions. No platform
extraction, no new abstraction layer, no second authority (`B5I7-R26`).

## 9. Same-agent audit (visible arithmetic)

| Dimension | Score | Deduction basis |
|---|---|---|
| SPEC | 8.5 | all 27 frozen node strings executed verbatim; −0.5 because the contract §10 prose and the frozen literal-only loopback implementation disagree and I preserved behaviour rather than text |
| DESIGN | 8.5 | one additive projection, no new authority; −0.5 for adding a machine-readable mutation-results artifact beyond the three artifacts named in contract §5 |
| CORRECTNESS | 7.5 | 27/27 focused nodes green and 14/14 mutations discriminated locally; −2.5 because no exact-head CI artifact had been parsed at the time this section was written |
| QUALITY | 8.5 | recursive redaction, bounds, deterministic canonicalisation; −0.5 for the residual CRLF working-tree versus LF blob split that the provenance fix now normalises but does not eliminate at checkout |

Arithmetic: `(8.5 + 8.5 + 7.5 + 8.5) / 4 = 33.0 / 4 = 8.25`.

This audit is **same-agent**. It is **not organizationally independent**. It is
scored from evidence, starting from the defects in §4 rather than from a perfect
score.

## 10. Gate status at the time of this record

Not all exit gates are executed. Gates that depend on GitHub Actions are
recorded `NOT_EXECUTED` with no run id, check id or artifact id, because those
identifiers may not be written before they exist (`B5I7-EL02`). The addendum
carries the machine-readable gate table this section summarises.

`MERGE_AUTHORIZED=false`. B5-I8 and B5-I9 are `LOCKED`. Freebuff is untouched.
Recurring cost is `$0` and `capital.authority = none`.
