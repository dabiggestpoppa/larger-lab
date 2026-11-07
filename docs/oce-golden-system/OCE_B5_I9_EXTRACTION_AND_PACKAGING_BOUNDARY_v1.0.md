# OCE Golden System — B5-I9 Extraction and Packaging Boundary — v1.0

**Document ID:** OCE-B5-I9-BOUNDARY-001
**Version:** 1.0
**Status:** `B5-I9 P0 = DRAFT FOR OPERATOR REVIEW`
**Base:** `833f7d1b9f2dfec2986fb9516d0abde06bf23dae`
**Cost:** `$0` · **`capital.authority = none`**

---

## 1. Classification method

Every candidate below is classified by **what it decides**, not by whether a test can
import it. The nine permitted classes are disjoint:

| Class | Meaning | B6 may consume as |
|---|---|---|
| `EXTRACTABLE_PATTERN` | A shape or contract that carries no authority and no private dependency | Design input, re-derived, not copied |
| `EXTRACTABLE_WITH_LIMITATION` | Reusable only with a stated limitation (path, environment, single-operator, repo-bound law) | Design input with the limitation carried verbatim |
| `REFERENCE_ONLY` | Useful to study; copying it would import product- or repo-specific assumptions | Nothing |
| `PLATFORM_INTERNAL` | Lives inside the canonical spine; extraction would move authority | Nothing |
| `PRIVATE_API` | Not a published contract; a test-only or internal helper | Nothing |
| `AUTHORITY_BEARING` | Decides identity, admission, refusal, recovery, spend or execution | Never extracted |
| `PROHIBITED` | Extraction is forbidden by constitution or charter | Never |
| `DEFERRED_TO_BOOK_6` | Extraction is legitimate but belongs to Book 6 | Book 6, after authorization |
| `NOT_APPLICABLE` | Does not exist in the reference application | Nothing |

Two rules make the classification falsifiable:

- **R1 — import is not promotion.** A module that a test can import is not therefore a
  stable contract. `PRIVATE_API` and `PLATFORM_INTERNAL` are decided by ownership.
- **R2 — authority is contagious.** A pattern that embeds one authority decision becomes
  `AUTHORITY_BEARING` even if its data structure is generic.

---

## 2. Candidate classification (27 items)

| # | Candidate | Source path | Class | Public/private | Authority | Reason |
|---|---|---|---|---|---|---|
| 1 | Product Charter as a freeze instrument | `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` | `EXTRACTABLE_PATTERN` | Public doc | None | Fields (identity, users, outcomes, authority law, non-goals, gates, ceiling) transfer; content does not |
| 2 | Product lifecycle stages | charter §9 | `EXTRACTABLE_PATTERN` | Public doc | None | Stage expectations are domain-neutral |
| 3 | Deterministic kernel contract | charter §7 (eleven functions) | `EXTRACTABLE_PATTERN` | Public doc | None | It is a *prohibition on LLM authority*, not an implementation |
| 4 | Read-only client seam | `infrastructure/console/src/oce_console/kernel.py` | `EXTRACTABLE_WITH_LIMITATION` | Internal package | None | Limitation: stdlib-only closure and loopback transport are frozen; copying the import set would freeze a consumer's dependency policy |
| 5 | Denial enveloping as a rendering law | `infrastructure/control-plane/contracts/denial-envelope.schema.json` | `EXTRACTABLE_PATTERN` | Public schema | None (rendering only) | Verbatim refusal rendering is a portable law; the *admission* decision is not |
| 6 | Admission / refusal decision | `infrastructure/control-plane/src/oce_control/authority.py` | `AUTHORITY_BEARING` | Internal | Decides | Cannot be extracted; would duplicate policy |
| 7 | Recovery drill protocol | `OCE_B5_I6_DEPLOYMENT_OBSERVABILITY_RUNBOOK_v1.0.md` | `EXTRACTABLE_PATTERN` | Public doc | None | Inject → observe → reconcile → report is portable |
| 8 | Recovery enactment | `infrastructure/control-plane/src/oce_control/recovery.py`, `infrastructure/control-plane/src/oce_control/worker_leases.py` lease expiry | `PLATFORM_INTERNAL` | Internal | Decides | Extraction would create a second recovery authority |
| 9 | Evidence laws EL01–EL10 | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` | `EXTRACTABLE_WITH_LIMITATION` | Public test | None | Limitation: laws are bound to this repository's paths and frozen manifest rows |
| 10 | Manifest computation | `infrastructure/console/packaging/make_release_manifest.py` | `EXTRACTABLE_WITH_LIMITATION` | Internal script | None | Limitation: install-set membership is console-specific |
| 11 | CI evidence-selection workflow | `.github/workflows/b5-i8-audit-validation.yml` | `REFERENCE_ONLY` | Public | None | Encodes this repo's supersession (Amendment 001) and gate names; copying would import a decision that is not a law |
| 12 | Mutation battery harness | `infrastructure/control-plane/scripts/b5_i*_mutation_battery*.py` | `EXTRACTABLE_WITH_LIMITATION` | Internal script | None | Limitation: targets are this repo's nodes |
| 13 | Requirement-test registry shape | `OCE_B5_I*_REQUIREMENT_TEST_REGISTRY_v1.0.json` | `EXTRACTABLE_PATTERN` | Public JSON | None | Fields and state vocabulary transfer; counts do not |
| 14 | Failure matrix shape | `OCE_B5_I*_FAILURE_MATRIX_*.md` | `EXTRACTABLE_PATTERN` | Public doc | None | Trigger/containment/proof/evidence/recovery is domain-neutral |
| 15 | Usability protocol | `OCE_B5_I8_USABILITY_PROTOCOL_AND_RESULTS_v1.0.md` | `EXTRACTABLE_WITH_LIMITATION` | Public doc | None | Limitation: single-operator, same-agent, non-blind sample |
| 16 | Web view | — | `NOT_APPLICABLE` | — | — | Never implemented; no disposition to extract |
| 17 | Canonical job/event stores | `infrastructure/control-plane/src/oce_control/job_store.py`, `infrastructure/control-plane/src/oce_control/worker_leases.py` | `PLATFORM_INTERNAL` | Internal | Decides | Extracting a copy creates a second canonical state |
| 18 | Canonical-state ownership rule | charter §5 | `PROHIBITED` | Public doc | — | Extracting "the rule" as a shared state container is exactly the prohibited duplication |
| 19 | Capability/authority machinery | control-plane grants | `AUTHORITY_BEARING` | Internal | Decides | Never reusable |
| 20 | Credential/provider boundaries | charter §10, runbook | `AUTHORITY_BEARING` | Internal | Decides | A reusable credential seam is an authority seam |
| 21 | Persistence boundaries (SQLite paths) | `infrastructure/control-plane/src/oce_control/pg_store.py` | `PLATFORM_INTERNAL` | Internal | None | Environment-specific |
| 22 | Local deployment assumptions (compose stack) | `infrastructure/control-plane/compose/compose.yml` | `REFERENCE_ONLY` | Internal | None | Local topology is an environment, not a contract |
| 23 | Console session records | charter §8.1 | `REFERENCE_ONLY` | Internal | None | Product-specific artifact |
| 24 | Queue-depth panel | `infrastructure/console/src/oce_console/panel.py` | `REFERENCE_ONLY` | Internal | None | A governed change instance, not a reusable surface |
| 25 | Control-plane health/status API | `infrastructure/control-plane/src/oce_control/health.py` | `PRIVATE_API` | Internal | None | Not published; consumers must not bind to it |
| 26 | Shared test support helpers | `infrastructure/control-plane/tests/b5_i8_audit_support.py` | `PRIVATE_API` | Test-only | None | Test scaffolding, not a contract |
| 27 | The extraction act itself (moving B5-proven surfaces into platform form) | B6 plan §7 `B6-I0` | `DEFERRED_TO_BOOK_6` | Not started | Would create | Legitimate work, but it belongs to Book 6 after a fresh operator authorization; B5-I9 contracts it and does not perform it |

Because no candidate reached `EXTRACTABLE_PATTERN` while carrying authority, no item is
promoted by importability. Exactly one candidate is `DEFERRED_TO_BOOK_6`: the extraction
act itself, which B5-I9 contracts and B6 performs (§5).

### 2.1 Fields recorded for every extractable candidate

For each of items 1–3, 5, 7, 9, 10, 12–15 the registry's `EX` requirements bind: source
path, public/private status, authority status, dependencies, required provenance,
portability assumption, configuration inputs, runtime dependencies, test obligation,
evidence obligation, failure mode and prohibited reinterpretation. Item 4 and item 15
carry their limitation in the `EX` row rather than here.

### 2.2 Negative control (worked)

`oce_console/kernel.py` *looks* like a reusable read-surface library: pure functions, no
network, no state. Classification is `EXTRACTABLE_WITH_LIMITATION`, not
`EXTRACTABLE_PATTERN`, because it (a) freezes a stdlib-only import closure that a consumer
package would inherit, and (b) depends on `ConsoleRefusal` reasons that encode this
product's refusal vocabulary. It is rejected as a stable API, and it must not be relabelled
`EXTRACTABLE_PATTERN` merely because `test_b5_i7_governed_change.py` can import it.
`job_store.py` is rejected more strongly: importing it would place canonical state in a
consumer, which is `PROHIBITED` by charter §5 law 5 and Constitution §7.8.

---

## 3. No-platform-extraction law (frozen)

**Law NP.** B5-I9 may not turn the reference application into a second platform, directly
or by contract that B6 could execute without review.

| Clause | Prohibition | Future executable proof |
|---|---|---|
| `NP-1` | Copying OCE internals into a new framework, package or SDK | Extraction manifest must show zero files under `infrastructure/control-plane/**` re-exported; a negative control plants a re-export and the proof rejects it |
| `NP-2` | Exposing private modules as stable APIs | Public surface list must contain only paths classified `EXTRACTABLE_*`; a planted `PRIVATE_API` path is rejected by name |
| `NP-3` | Duplicating canonical state | Any consumer-side store named as canonical fails a path+symbol scan; negative control plants a store copy |
| `NP-4` | Duplicating policy/authority decisions | Any extracted module containing admission, refusal-reason assignment, recovery choice or spend logic fails the authority scan |
| `NP-5` | Creating a second scheduler, worker, recovery or evidence authority | Ownership table must name exactly one owner per function; a second claimant fails |
| `NP-6` | Creating a second configuration truth | Configuration schema must declare one source; a duplicated key with a different default fails |
| `NP-7` | Embedding environment-specific paths, hostnames or provider assumptions | Extracted artifact must contain no absolute path, no host, no provider name; a planted path fails |
| `NP-8` | Weakening local-only constraints or introducing cloud/live-execution surfaces | Network-call and broker symbol scans must be empty; a planted `https://` call fails |

**Rejection of demo convenience.** A pattern is not reusable because it made one demo
convenient. `EXTRACTABLE_*` requires all four: no authority, no private dependency, a
declared limitation or none, and an executable proof that a wrong consumer fails closed.

---

## 4. Packaging and reproducibility contract

### 4.1 What B5-I9 packages

B5-I9 packages **evidence**, not software. The artifact is the gate packet: the seven
documents and one validator in contract §4.2, plus the ledger section. Runtime packaging
was B5-I6's release packaging; templates and install sets are B6's (`B6.C1.S3`).

### 4.2 Measurable definitions (no undefined adjectives)

| Term | Measurable meaning used here |
|---|---|
| **Deterministic** | Same input bytes + same generator version ⇒ **byte-identical** output bytes. No timestamps, no absolute paths, no hostnames, no iteration-order dependence (sorted keys, sorted rows, LF-normalized) |
| **Reproducible** | *Future B5-I9 obligation, not an accomplished P0 fact.* A second run of a committed generator in a clean worktree from the same commit yields byte-identical artifacts, verified by SHA-256 equality of every file |
| **Portable (packet)** | Every path referenced is repository-relative; every citation resolves in the repository; no Windows-only or POSIX-only path appears in the packet's own content |
| **Self-contained (packet)** | The packet's validator imports only the standard library and reads only committed files; it performs no network access |
| **Deployable** | **Not claimed.** No deployment artifact is produced by this stage |

### 4.3 Packet artifact rules

| Rule | Value |
|---|---|
| Artifact type | Markdown + JSON documentation set, plus one stdlib-only validator |
| Version identity | `v1.0`; `Document ID` present on every document; registry carries `version`, `stage`, `base_sha` |
| Source binding | Every artifact records `base_sha = 833f7d1b…` and the stage |
| Tree binding | Recorded by the validator as the tree of the commit under validation |
| Hash and size rules | SHA-256 over LF-normalized bytes; sizes in bytes; no row may be typed in by hand — the validator recomputes from bytes |
| Provenance record | Ledger §21 plus the registry's `provenance` block |
| Exclusions | No binary, no LFS, no large data, no secret, no absolute path, no credential, no generated cache |
| Offline behaviour | Validator runs with no network; absence of network is not a failure |
| Failure behaviour | Any failed check ⇒ non-zero exit and a named failure; no silent pass |
| Reproducibility proof | At P0: re-run the validator twice on the same commit and compare the emitted packet digest and mandatory-check total (verification stability). Byte-identical *regeneration* of the registry-derived documents is not claimed, because no generator is committed; it is a B5-I9 implementation obligation (`PK` rows) |

### 4.4 Explicit non-claims

No `portable` claim is made about code, because no code moves. No `deployable` claim is
made about anything. No packaging artifact is produced for B6 to consume; B6 consumes the
*contract*, not a bundle.

---

### 4.5 Current P0 status: verification is not regeneration

| Object | Committed | What it does | What it does not do |
|---|---|---|---|
| Validator `b5_i9_p0_validate.py` | yes | Recomputes arithmetic, closure, boundary, style and ledger prefix from committed bytes | Does not generate, repair or regenerate any artifact; writes nothing |
| Generator (transient builder) | **no** | Produced the matrix and construction plan once, outside the repository | Not reproducible at P0; carries no lineage and is not cited as evidence |
| Registry JSON | yes | Canonical requirement set and its arithmetic | Is not a runtime artifact and proves no behaviour |
| Generated documents (matrix, plan) | yes | Authoritative once committed; reproducible byte-for-byte verifiable by reading | Cannot be regenerated from committed inputs at P0 |
| Future evidence package / install set | **no** | — | Not produced; packaging of software remains B5-I6's and B6's |

The P0 packet therefore claims **verifiability**, not **regeneration**. Determinism and
reproducibility are requirements on the future B5-I9 implementation, not accomplishments
of this packet.

## 5. Book 6 handoff boundary

Seven states, deliberately not synonyms. Each row carries its meaning, the clause that
authorizes the meaning, the evidence required, the audited value, and who may transition
it. No state transitions on CI success alone.

| State | Meaning | Source clause | Required evidence | Value at P0 | Transition owner |
|---|---|---|---|---|---|
| Book 5 evidence complete | B5-I8 audit evidence exists and is ratified | B5-I8 §16; ledger §20 | ratified B5-I8 record, merged `833f7d1b…` | **true** | Occurred; immutable |
| Book 5 implementation complete | Every B5 increment's implementation scope is done | Block 5 plan §7 rows B5-I1–I8 | B5-I1–I8 implementation records | **true** | Occurred; immutable |
| Book 5 governance complete | Operator has ratified the factory gate (B5-I9 exit) | Block 5 plan §7 gate *Operator-only completion* | this stage's ratification record | **false** | Operator only |
| B5-I9 complete | This stage's operator-only completion has occurred | Block 5 plan §6 `B5.C5.S5`; ledger §1 | operator ratification + accepted packet | **false** | Operator only |
| Book 6 input-ready | **Narrow:** upstream B5-I0–I8 evidence exists and this packet's classification table is internally consistent | Block 6 plan dependency line; B6-I0 *only B5-proven reuse included* | B5-I0–I8 records; §2 table; §5.1 list | **true** | Occurred at P0 |
| Book 6 authorized | A fresh operator authorization names `AUTHORIZED_STAGE=B6-I0` | Block 6 plan dependency; roadmap §10 | a new operator authorization, not this record | **false** | Operator only |
| Book 6 started | A Book 6 artifact, branch, test or evidence file exists | Block 6 plan §1 scope | a Book 6 artifact; none exists | **false** | Operator only |

### 5.0 Non-implications (binding)

- **input-ready never implies authorized.** The narrow definition above deliberately
  excludes the ratified extraction contract; contract ratification is tracked separately as
  `BOOK_6 CONTRACT_RATIFIED` (false at P0), and authorization requires a fresh operator act.
- **authorized never implies started.** Authorization names a stage; it creates no artifact.
- **Evidence completeness never implies governance completeness.** The operator-only B5-I9
  exit gate is unperformed until this stage's ratification record exists.
- **No state transitions on CI success alone.** CI proves frozen surfaces still pass; it
  cannot ratify scope, authorize Book 6 or complete B5-I9.
- **B5-I9 is not complete because a packet exists.** `B5-I9 COMPLETE = false` until the
  operator accepts it.

### 5.1 Evidence Book 6 is permitted to consume (once authorized)

Ratified Product Charter; frozen lifecycle model; deterministic kernel contract; the
reference application's evidence (B5-I4–I8 records); refusal and recovery laws; usability
limitations including the open G16 disposition; the extraction classification and its
limitations; remaining limitations and open decisions; cost and authority boundaries; the
manifests and hashes named in this packet; and the exact merged-main identity
`833f7d1b9f2dfec2986fb9516d0abde06bf23dae`.

### 5.2 Book 6 start conditions

All must hold: operator issues a fresh `AUTHORIZED_STAGE=B6-I0`; this packet's gate is
ratified; `B6-I0`'s "only B5-proven reuse included" is honoured by consuming §2's
classifications rather than re-deciding them; no extraction begins before that
authorization; and the extraction remains local-first and provider-neutral per Block 6 §1.

`BOOK_6_AUTHORIZED = false` and `BOOK_6_STARTED = false` are asserted, not assumed: no
Book 6 folder, branch, test, source, workflow or evidence artifact exists in this program.

### 5.3 Contract-ratified gate

`BOOK_6 CONTRACT_RATIFIED` is a gate, not a handoff state: it is false while this packet is
a draft, and becomes true only when the operator ratification record exists. Input-readiness
does not wait on it; Book 6 *start* does. The two `agent/crypto-systems-intelligence-atlas-book6-*`
branches predate this program (2026-10-01, a different atlas effort) and are not OCE Book 6
artifacts.
