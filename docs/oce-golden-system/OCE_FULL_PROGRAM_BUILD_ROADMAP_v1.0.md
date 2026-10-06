# OCE Golden System
## Full Program Build Roadmap — Blocks 0 through 10

**Document ID:** OCE-ROADMAP-002  
**Version:** 1.0  
**Status:** PROPOSED COMPLETE PLANNING BASELINE  
**Parent authorities:** Constitution 1.1, Amendment A-002, Master Program Atlas 1.0  
**Build authorization:** Existing Block 1 authorizations only

## 1. Purpose

This roadmap converts the mapped program into a staged construction system. Detailed dossiers for Blocks 2–10 define what to build. A later single master build prompt will tell agents how to consume those dossiers, create one bounded increment at a time, stage commits, attach evidence, and stop at hold points. The roadmap itself authorizes no implementation.

## 2. Permanent architecture

- **Operator:** final authority.
- **OCE:** canonical governance, state, evidence, and recovery.
- **PO:** high-level OCE/Quant/Larger Lab operator and governed builder.
- **Hermes:** separate supplemental/personal Telegram agent.
- **Workers:** task-scoped executors with minimum context.
- **Cloud:** deployment, durability, observability, remote availability, backups, and heavy compute.
- **Local:** primary planning, development, debugging, ordinary execution, tests, and reproducible validation.

## 3. Program sequence

| Block | Name | Planning state | Build state | Dependency promoted by |
|---|---|---|---|---|
| B0 | Constitutional Control | Ratified; A-002 proposed | GATED_COMPLETE | Operator ratification of amendment |
| B1 | Cloud Ground | Ratified | IN PROGRESS | B1-I9 gate |
| B2 | OCE Reality Seal | Fully planned by this package | LOCKED | B1 stable audit environment |
| B3 | OCE Constitutional Spine | Fully planned by this package | LOCKED | B2 canonical-source decision |
| B4 | PO Governed Builder | Fully planned by this package | LOCKED | B3 verified governance spine |
| B5 | Reference Application Factory | Fully planned by this package | LOCKED | B4 complete governed build proof |
| B6 | Reusable Platform Surfaces | Fully planned by this package | LOCKED | B5 reference-app evidence |
| B7 | Quant Foundation | Fully planned by this package | LOCKED | B6 reuse proof |
| B8 | Quant Lab and Quant Watch | Fully planned by this package | LOCKED | B7 deterministic quant gate |
| B9 | Controlled Execution | Fully planned by this package | LOCKED | B8 research governance plus operator |
| B10 | Operational Compounding | Fully planned by this package | LOCKED | Evidence from prior blocks |

Planning a downstream block does not promote its dependency or authorize its build.

## 4. Standard block increment pattern

Every block B2–B10 uses ten bounded implementation increments:

| Increment | Function |
|---|---|
| I0 | Freeze block contracts, allowed scope, schemas, evidence model, and regression baseline |
| I1 | Build Chapter 1 |
| I2 | Verify Chapter 1 and build Chapter 2 foundation |
| I3 | Complete Chapter 2 and its adversarial tests |
| I4 | Build Chapter 3 |
| I5 | Verify Chapter 3 and build Chapter 4 foundation |
| I6 | Complete Chapter 4 and recovery behavior |
| I7 | Build Chapter 5 integration and end-to-end path |
| I8 | Run independent, adversarial, restart, security, cost, and evidence reconciliation |
| I9 | Produce gate packet, learning ledger, downstream contract, and operator hold |

The dossier for each block specializes these increments. An agent may execute only the exact `AUTHORIZED_STAGE=B{n}-I{m}` supplied by the operator.

## 5. Standard section contract

Each section is implemented only from its dossier row plus referenced decisions. Every row defines:

- present truth and target behavior;
- boundary and prohibited shortcuts;
- canonical deliverables and interfaces;
- deterministic, integration, adversarial, failure, restart, and abuse tests;
- evidence and exit condition;
- dependencies and downstream consumers.

If implementation discovers a contradiction, the section becomes `BLOCKED` or receives a versioned amendment. Code may not silently resolve architectural ambiguity.

## 6. Branch and commit assembly line

For every authorized increment:

1. Start from the exact ratified parent SHA.
2. Create `oce/b{n}-i{m}-<short-name>`.
3. Confirm source identity, clean state, and allowed-file list.
4. Create one implementation commit containing only the authorized scope.
5. Run local syntax, unit, integration, negative, restart, and repeated-run checks supported by the environment.
6. Push only the bounded branch.
7. Run authoritative CI from the exact implementation SHA.
8. Preserve failed evidence as evidence; do not overwrite it.
9. If authoritative execution passes, create a separate evidence-only commit.
10. Stop for review. Do not merge or begin the next increment.

Commit messages use `B{n}-I{m}: <observed result>`. Evidence commits use `B{n}-I{m}: record authoritative evidence`.

## 7. Universal gates

No increment can report ready while any mandatory requirement is FAIL, BLOCKED, silently skipped, simulated without disclosure, based only on static inspection, or inconsistent with manifest hashes. Every gate verifies source identity, versions, totals, required artifacts, cleanup, repository cleanliness, costs, cloud mutations, and unresolved blockers.

## 8. Universal hold points

Separate operator authorization is always required before purchase, provisioning, deployment, public exposure, new credentials, credential rotation, destructive deletion, history rewriting, external communication, broker connection, paper/shadow transition, live capital, authority expansion, or merge to a protected integration branch.

## 9. Local-first deployment rule

Every block must provide a local harness and local validation path. Cloud deployment packages are outputs consumed after local verification; they are not prerequisites for development. Remote services must fail closed or degrade explicitly without preventing local inspection and testing. Expensive compute is task-scoped, disposable, and never authoritative.

## 10. Cross-block evidence lineage

Each gate packet records constitution, amendment, atlas, dossier and implementation versions; exact commit and tree; environment fingerprint; test registry and totals; manifest hashes; costs; cloud mutations; operator decisions; unresolved risks; and the downstream dependency contract. A later block consumes only the ratified dependency contract, not informal claims from prior sessions.

## 11. Planning completion definition

The planning program is complete when Amendment A-002, this roadmap, and Blocks 2–10 dossiers exist; all 225 sections have unique IDs and build contracts; all 90 increments have specialized scope and gates; dependency references resolve; status language is consistent; and validation reports no unauthorized implementation claim.

Planning completion does not mean OCE completion.
