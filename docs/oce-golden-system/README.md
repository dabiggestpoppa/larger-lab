# OCE Golden System Program

This directory is the canonical planning and governance entrypoint for the OCE Golden System program.

## Required Reading Order

1. **OCE Golden System Architecture Constitution 1.1** — mission, philosophy, authority, invariants, truth rules, cloud doctrine, and amendment process.
2. **OCE Master Program Atlas 1.0** — complete Block → Chapter → Section map and deep-planning protocol.
3. **OCE Unified End State, Branch Roles, and Convergence Doctrine 1.0** — current one-OCE / two-hemisphere target, branch responsibilities, forward-port convergence method, domain-institution placement, and Model Foundry / Runtime Dynamics / Resource Intelligence destination.
4. **Block 0 Constitutional Control Plan 1.0** — ratified mission, authority, truth, program-control, and build-intelligence contracts.
5. **Block 1 Cloud Ground Plan 1.0** — ratified capacity, trust, data, runtime, worker, evidence, and cost contracts.
6. **Block 1 Agent Master Prompt 1.0** — stage-scoped execution instructions and hard hold points.
7. **Amendment A-002** — PO is the OCE/Quant/Larger Lab chief operator; Hermes is the separate personal/supplemental agent.
8. **Current Chapter and Section Dossiers** — ratified step-by-step design.
9. **Current Block Gate Report and Build Learning Ledger** — evidence, failures, lessons, unresolved matters, and operator decision.

No builder or agent should begin implementation from a section title alone.

## Canonical Program Order

| Block | Name | Baseline status recorded on `main` | Active implementation |
|---|---|---|---|
| B0 | Constitutional Control | GATED_COMPLETE | — |
| B1 | Cloud Ground | RATIFIED — historical main baseline | continuous local hardening on `oce-program-build` |
| B2 | OCE Reality Seal | MAPPED | tracked on `oce-program-build` |
| B3 | OCE Constitutional Spine | MAPPED | tracked on `oce-program-build` |
| B4 | PO Governed Builder | MAPPED on main | tracked on `oce-program-build` |
| B5 | Reference Application Factory | MAPPED | not started |
| B6 | Reusable Platform Surfaces | MAPPED | not started |
| B7 | Quant Foundation | MAPPED | not started |
| B8 | Quant Lab and Quant Watch | MAPPED | not started |
| B9 | Controlled Execution | MAPPED | not started |
| B10 | Operational Compounding | MAPPED | not started |

Planning completion is not build completion. Only an exact operator-provided `AUTHORIZED_STAGE=B<n>-I<m>` plus its ratified dependency authorizes an implementation increment. The operational evidence record and progress ledgers on `oce-program-build` are the only source for active authorization and observed build status; this table records program placement, not authorization.

### Book 4 configuration/security work is not Atlas Program Block 4

The Book 4 work on `oce-program-build` is **configuration/security-spine and local-recovery hardening** (governed local runtime, recovery transaction integrity, evidence integrity, receipt authority). It is not a claim that Block 4 as mapped in the Master Program Atlas — the PO Governed Builder — has been implemented, ratified, or closed. Book 4 is **not closed**. No Atlas Program Block 4 implementation is authorized by any document in this repository.

## Cross-Branch Strategic State — 2026-09-17

`main` is the reviewed integration/program surface. It does not imply that every active development line has already been merged.

- **Operational hemisphere:** `oce-program-build` — executable OCE/control-plane implementation and Block 4 hardening. It is the active operational implementation branch. Head recorded when the convergence doctrine was written: `8ce72fb86c88a2d7768dc1c9a2bd9568f60d6aa1`; head observed at the R39 convergence merge: `f3ef0dd875ff60f4babbe0068c6ac64753db314a`. Forward movement on this branch is expected; the branch's own commits are the truth.
- **Epistemic hemisphere:** `agent/oce-institutional-stress-suite-build` — A004+ institutional architecture and deterministic stress validation. Recorded G7 exit: `PASS_G7_SENSITIVITY_METAMORPHIC`; G8 not begun in the G7 result.
- **Runtime Dynamics side lab:** `agent/oce-rlt-runtime-dynamics-lab` — research-only recurrent-state / runtime-dynamics program; no OCE truth or authority ownership.

The intended architecture is **one OCE**, not two. The institutional line is not to be raw-merged into the operational build line. After institutional G8→G9→G10 and operator ratification, surviving deltas are to be forward-ported onto the then-current `oce-program-build` tree through a dedicated convergence branch and independently integration-tested.

See `OCE_CONVERGENCE_END_STATE_AND_BRANCH_ROLES_v1.0.md` for the complete target state.

## Agent Architecture

- **PO:** high-level OCE, Quant Lab, Quant Watch and Larger Lab operator/builder.
- **Hermes:** separate personal and supplemental Telegram agent (A-002 boundary).
- **OCE:** canonical identity, authority, state, evidence and recovery.
- **Workers:** task-scoped subagents with minimum context and expiring authority.

PO and Hermes have direct Telegram access, separate identities and separate memories. Hermes is not a mandatory gateway to PO. Neither agent can approve its own consequential action.

## Local-First Doctrine

Planning, development, debugging, ordinary execution and validation run locally. Cloud is a later surface for deployment, durability, remote availability, observability, backups and heavy compute. Telegram is an interface, not canonical state. Core OCE/PO operation must not depend on Telegram or cloud availability (A-003).

## Block Checkpoint Workflow

Each block follows:

> articulate → interrogate → simulate → refine → ratify → build when authorized → verify → review → commit

At the end of every block:

1. review delivered artifacts against the Block Charter;
2. review evidence, failures, contradictions, security, authority, and cost;
3. review the Build Learning Ledger;
4. decide advance, revise, quarantine, or stop;
5. update this status index;
6. commit the completed block checkpoint to Git.

Planning commits do not authorize implementation. Build authorization must be explicit in the ratified section dossier or operator decision.

## Build Workflow

> plan → ratify → authorize one increment → bounded branch → implementation commit → local validation → authoritative CI → evidence-only commit → operator review → next authorization

Every failed attempt remains truthful evidence. Agents do not merge, deploy, purchase, expose, rotate credentials, delete history, connect brokers or act on capital without separate authority.

## Git Doctrine

- The main branch holds ratified/reviewed program baselines, major strategic-state records, and reviewed block checkpoints.
- Active implementation and research branches may be ahead of `main`; their state must be named explicitly rather than silently implied to be integrated.
- Work that has not passed its block review must not be labeled complete.
- Each completed block receives a distinct checkpoint commit.
- Earlier reasoning is preserved through Git history and superseding documents rather than silently rewritten.
- Commit messages identify the block and gate state.
- Legacy documentation remains evidence for the reality audit but does not override the Constitution, Atlas, or later operator-ratified superseding documents.

## Holistic Learning Doctrine

Every build produces both a product artifact and process knowledge. Meaningful attempts, errors, partial successes, corrections, rejected paths, and recurring practices are recorded and dispositioned.

“No observation is trash” does not mean unlimited raw retention. Every meaningful observation receives an explicit decision: retain, normalize, summarize, redact, quarantine, expire, or delete with a tombstone and reason.

## Main-Branch Baseline Note

The older Block 1 checkpoint text on `main` is a historical baseline, not a claim that the active OCE program is still at B1-I1. Active implementation truth lives on the named operational branch until reviewed convergence/integration occurs.

## Superseded Claims (historical, do not act on)

The following statements appeared in an earlier revision of this file and are **retained only as historical record**. They are superseded by the convergence doctrine above:

- ~~“Canonical integration branch: `oce`.”~~ There is no branch `oce` in the canonical role set. The reviewed integration surface is `main`; the operational implementation line is `oce-program-build`.
- ~~“Block 1 remains the active implementation block.”~~ Block 1 is a ratified historical baseline on `main`. Active operational implementation is tracked on `oce-program-build` and is not described by this index.
- ~~“Blocks 2–10 are planned but build-locked.”~~ Planning completion is not build completion, and build authorization is not implied by this index in either direction.

**Strategic target:** One OCE with an operational hemisphere and an epistemic hemisphere, converged through canonical contracts and operator-ratified forward-porting.  
**Detailed new planning location:** `agent/oce-institutional-stress-suite-build`.  
**Next institutional stress gate:** G8 after operator authorization.  
**New planning programs:** Model Foundry Domain Institution, Runtime Dynamics/RLT, OCE Resource Intelligence / Compute Market Router, with PC-ALM initially contained as a Model Foundry research track.
