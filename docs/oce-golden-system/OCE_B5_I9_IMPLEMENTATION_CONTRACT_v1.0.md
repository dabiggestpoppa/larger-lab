# OCE Golden System — B5-I9 Implementation Contract — v1.0

**Document ID:** OCE-B5-I9-CONTRACT-001
**Version:** 1.0
**Status:** `B5-I9 P0 = DRAFT FOR OPERATOR REVIEW`
**Stage:** `AUTHORIZED_STAGE=B5-I9-P0`
**Base:** `833f7d1b9f2dfec2986fb9516d0abde06bf23dae` (merged `origin/main`, PR #23)
**Predecessor:** B5-I8 `RATIFIED_INDEPENDENT_AUDIT`, ratified and merged 2026-11-07
**Cost:** `$0` · **Cloud/provider mutations:** 0 · **`capital.authority = none`**

---

## 0. Status block

```
B5-I9 P0                      = DRAFT FOR OPERATOR REVIEW
B5-I9 IMPLEMENTATION          = NOT STARTED
MERGE_AUTHORIZED              = false
BOOK_6_AUTHORIZED             = false
BOOK_6_STARTED                = false
POST_BOOK_6_EVALUATION        = UNSTARTED
G16                           = OPEN (B5I8-DF05)
```

This document is planning and evidence-shaping only. It creates no code, no test, no
workflow, no extraction, no package, no Book 6 artifact, and no authority.

---

## 1. Governing identity of B5-I9 (derived, not assumed)

Every earlier report in this program described B5-I9 loosely. The identity below is read
from the governing text, and only from it.

| Source | Clause | Text that binds B5-I9 |
|---|---|---|
| Block 5 plan | §7 increment table, row `B5-I9` | *Factory gate and B6 reusable-extraction contract* — gate: *Operator-only completion* |
| Block 5 plan | §6 `B5.C5.S5` Factory corrections | Deliverables *correction ADRs and B6 contract*; gate *Operator ratifies reusable extraction scope* |
| Block 5 plan | §5 `B5.C5.S4` Learning captured | Deliverable *learning ledger*; gate *No meaningful observation silently discarded* |
| Full Program Build Roadmap | §4 increment pattern, row `I9` | *Produce gate packet, learning ledger, downstream contract, and operator hold* |
| Book 5 ledger | §1, row `B5-I9` | *Factory gate and B6 reusable-extraction contract* — **LOCKED** — *Operator-only completion; requires B5-I8 complete* |
| Product Charter | §8.4 Prohibited expansion | *package/plugin/reusable-platform extraction (B6 owns extraction decisions)* |
| B5-I7 reuse inventory | `B5I7-DF03` | *B6 extraction scope remains with B5-I9* |
| Block 6 plan | Dependency line | *B5 reference-application evidence and correction decisions* |
| Block 6 plan | §7 row `B6-I0` | *Freeze extraction decisions, API principles, compatibility and conformance baseline* — gate *Only B5-proven reuse included* |
| Constitution 1.1 | §5.2 non-goals | *No general SDK/platform extraction before evidence* |

**Derived identity (frozen for this stage):** B5-I9 is a **governed combination** of four
clauses, in this order of precedence:

1. **Factory gate** — the Book 5 closure packet: what was built, what it proves, what it
   does not, with arithmetic and identities that reconcile.
2. **Learning closure** — the learning ledger and factory-correction decisions
   (`B5.C5.S4`/`S5`), including what must *not* propagate.
3. **B6 reusable-extraction contract** — the classification, provenance, packaging and
   prohibition contract that B6 must honour. **A contract, not an extraction.**
4. **Operator hold** — the stage ends at operator review; "operator-only completion" means
   the operator, not the agent, performs completion.

B5-I9 is therefore **not** extraction, **not** packaging of code, **not** portability
engineering, **not** Book 5 closure performed by an agent, and **not** Book 6.

### 1.1 Sources checked for conflict

The Block 5 plan's "Non-goals" forbids *general SDK/platform extraction before evidence*;
its §7 assigns B5-I9 the *contract*; the Block 6 plan states extraction *is* B6's work and
that B6 consumes B5 evidence. The three agree: B5-I9 contracts, B6 extracts. No conflict
required a stop. Where the ledger's §1 row still reads `LOCKED`, that row lives inside the
protected EL09 prefix, is historically accurate at the moment it was written, and is **not
edited**; §4 below states the live status.

---

## 2. Source-to-claim table

| # | Claim in this packet | Source | Clause |
|---|---|---|---|
| 1 | B5-I9 is the factory gate plus the B6 extraction contract | Block 5 plan | §7 row `B5-I9` |
| 2 | The extraction scope is operator-ratified, not agent-decided | Block 5 plan | §6 `B5.C5.S5` |
| 3 | No meaningful observation may be silently discarded | Block 5 plan | §5 `B5.C5.S4` |
| 4 | The stage produces a gate packet, learning ledger, downstream contract and a hold | Roadmap | §4 row `I9` |
| 5 | Extraction decisions belong to B6 | Charter / reuse inventory | §8.4 / `B5I7-DF03` |
| 6 | Only B5-proven reuse may enter B6 | Block 6 plan | §7 row `B6-I0` |
| 7 | Applications may not duplicate identity, lifecycle, evidence or recovery | Constitution | §7.8 |
| 8 | One spine, many domains | Constitution | Principle 5 |
| 9 | Shared concepts are defined once and versioned | Constitution | Article VI |
| 10 | Every important result names inputs, version, environment, actor | Constitution | Article VII |
| 11 | Control plane stays private; internal admin is never exposed | Constitution | Article XIII |
| 12 | Every governed build yields the artifact *and* knowledge about the build | Constitution | Article XVII |
| 13 | Packaging lineage must link source, dependencies, build, config, tests, digests | Block 5 plan | §4 `B5.C3.S4` |
| 14 | Downstream blocks consume the ratified dependency contract, not informal claims | Roadmap | §10 |
| 15 | G16 is open and unusability is disclosed, not closed | B5-I8 record | §16, `B5I8-DF05` |
| 16 | The ledger is append-only and its prefix is immutable | EL09 X1 | §3–§4 |

---

## 3. Eight categories this stage must not collapse

The single most likely failure of B5-I9 is a category error: calling a thing "reusable"
because it can be imported, or calling a contract "extraction" because it names files.
Each row below is a distinct object with a distinct owner.

| # | Category | What it is | Owner | May B5-I9 produce it? |
|---|---|---|---|---|
| 1 | Reusable **product** pattern | A shape of product behaviour (charter fields, lifecycle stages) any bounded app can adopt | B6 (after B5 evidence) | Describe and classify only |
| 2 | Reusable **test/evidence** pattern | A shape of proof (node naming, mutation battery, manifest laws) | B6 | Describe and classify only |
| 3 | **Local packaging** artifact | A runnable, hash-manifested local install set | B5-I6 owns release packaging; B6 owns templates | No — classify only |
| 4 | **Deployment** artifact | Anything that binds a target environment, provider or ingress | Operator, separately authorized | No |
| 5 | **Platform/kernel extraction** | Moving OCE internals into a shared library or new framework | B6 | No |
| 6 | **Private/internal interface** | A module, helper or endpoint that is not a published contract | OCE | No — must stay private |
| 7 | **Authority-bearing capability** | Anything that decides identity, admission, refusal, recovery or spend | OCE | No — never "reusable" |
| 8 | **Book 6 implementation** | B6 code, tests, templates, branches, evidence | Book 6 | No — `BOOK_6_STARTED = false` |

A component that carries hidden authority or a private dependency is **not** promoted by
proximity: §5 of the boundary document rejects it explicitly.

---

## 4. Inputs, deliverables, exclusions, exit gate

### 4.1 Inputs inherited (read-only)

Ratified Product Charter (`CAND-004`); B5-I2 interface contract plus reproducibility
result; B5-I3 registry and construction record; B5-I4 gap/scope and vertical slice; B5-I5
scope contract, acceptance matrix, end-to-end/CI evidence record; B5-I6 deployment,
observability and recovery runbook plus chaose/recovery evidence; B5-I7 P0 contract,
governed change record, reuse inventory, mutation results, EL09 X1 correction and
superseding manifest; B5-I8 P0 contract, Amendment 001, implementation, audit evidence
record, node non-vacuity audit, usability protocol and results, ratification; the Book 5
ledger through the B5-I8 merge.

### 4.2 Deliverables of the P0 packet

| # | Artifact | Role |
|---|---|---|
| 1 | `OCE_B5_I9_IMPLEMENTATION_CONTRACT_v1.0.md` (this file) | Identity, categories, deliverables, exclusions |
| 2 | `OCE_B5_I9_EXTRACTION_AND_PACKAGING_BOUNDARY_v1.0.md` | Classification of every candidate, no-platform law, packaging contract, Book 6 boundary |
| 3 | `OCE_B5_I9_REQUIREMENT_TEST_REGISTRY_v1.0.json` | Canonical requirement set with bindings and states |
| 4 | `OCE_B5_I9_ACCEPTANCE_MATRIX_v1.0.md` | Requirement → observable → binding → planned node |
| 5 | `OCE_B5_I9_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md` | Failure classes and mutation plan |
| 6 | `OCE_B5_I9_CONSTRUCTION_PLAN_v1.0.md` | Phases, planned node inventory, gates |
| 7 | `OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` §21 (append-only) | Stage record |
| 8 | `infrastructure/control-plane/scripts/b5_i9_p0_validate.py` | Read-only P0 validator (committed so the packet is reproducible) |

### 4.3 Exclusions (binding)

No extraction; no packaging of code; no publishing; no deployment; no Book 6 start; no
Book 5 closure performed by the agent; no G16 closure; no web-view authorization; no
capital or execution authority; no modification of production, runtime, frontend, test,
workflow or B5-I0–I8 evidence files; no history rewrite.

### 4.4 Exit gate

The stage is complete only when the operator has (a) reviewed this packet, (b) ratified
the extraction scope and the correction decisions, and (c) recorded the Book 6 handoff as
authorized or withheld. Until then the stage is `DRAFT FOR OPERATOR REVIEW` and
`MERGE_AUTHORIZED = false`.

### 4.5 Deferred owners

| Item | Owner | Gate |
|---|---|---|
| Extraction execution (code moves, templates, SDK, API surface) | Book 6 | `B6-I0`; requires fresh operator authorization |
| G16 independent usability audit | Operator (independent auditor distinct from the implementer) | `B5I8-DF05` closure condition |
| Optional loopback web view | Operator (directable) | Charter §12 `I-7`; not authorized here |
| Book 5 closure ratification | Operator | This stage's gate |
| Post-Book-6 evaluation system | Future operator | `POST_BOOK_6_EVALUATION = UNSTARTED` |

---

## 5. What this P0 does not do

It does not extract, package, publish, deploy, close Book 5, close G16, authorize the web
view, start Book 6, create a Book 6 artifact, grant capital or execution authority, or
change any B5-I0–I8 evidence byte. `MERGE_AUTHORIZED` is `false`, and B5-I9 starts from
`false` regardless of the B5-I8 registry, whose `merge_authorized: true` was scoped to PR
#23 only (ratification §R4: *for the P0 ratification PR only*; §R9: *PR #23 only*).

## 6. Locks and accounting

```
B5-I9 IMPLEMENTATION = NOT STARTED      B5_I9_LOCKED = true (until operator authorizes)
BOOK_6_AUTHORIZED   = false             BOOK_6_STARTED = false
WEB_VIEW            = ABSENT            POST_BOOK_6_EVALUATION = UNSTARTED
G16                 = OPEN (B5I8-DF05)  MERGE_AUTHORIZED = false
RECURRING_COST      = $0                CAPITAL_AUTHORITY = none
```
