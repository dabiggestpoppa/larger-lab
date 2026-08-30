# CLEANROOM-F09 — Legacy Branch Classification and Archive Evidence

Date: 2026-08-30
Stage: CLEANROOM-RECOVERY-AND-FINAL-REVIEW

## Purpose

Classify every previously deleted branch with ancestry/content evidence and
provide durable archive references for unique concluded research. Per review
rules: failed/falsified research is valuable evidence; ambiguity defaults to
BLOCKED_UNRESOLVED, never deletion. No additional refs were deleted.

Former head SHAs were recovered from the retained duplicate clone's
remote-tracking refs (`.trash-larger-lab-duplicate/.git/refs/remotes/origin/`).

## Classifications

### ABSORBED_VERIFIED (content proven inside a protected successor)

| Branch | Former head | Proof |
|---|---|---|
| agent/crypto-data-1.1 | 1d9607525d13a39f5229837c7513ecf8a7d42c07 | `git merge-base --is-ancestor 1d960752 agent/crypto-quant-foundry` → ANCESTOR. Fully absorbed into the canonical crypto research branch. Local branch ref retained. |
| tb-forward-engine-plan-anchor-temp | 223fd024418db2e1bb2c6ed9ac7334488f263f5b | `git merge-base --is-ancestor 223fd024 tb-forward-engine` → ANCESTOR. Fully absorbed into the protected TB engine branch. |

### KEEP_PROTECTED (restored — see F08 record)

| Branch | Former head | Reason |
|---|---|---|
| capital-routing | 43a6473c1b | Unique MT5 capital-risk work; not absorbed |
| cerebus-mve-implementation | 30359692cc | MVE lineage; 991 unique commits |
| hermes-set-up | b4ef87b7af | OCE Hermes Telegram Operator |
| execution-runtime-foundation | 03eb68f8d4 | Unique TradeLocker read-only integration |
| tv-review | 1a53cbb1d4 | OCE B1-I1R cloud-ground infra lineage; ancestor of oce |

### ARCHIVE_REF_REQUIRED → durable archive tags created and pushed

Unique concluded research with no active branch need, preserved as annotated
tags on origin so the commits remain reachable and the evidence is durable.

| Tag | Points at (former head) | Content |
|---|---|---|
| archive/agent/asia-triangle-foundry@8f84243f | 8f84243f | SW-AJCF R1/R2 + CTBT T1-T4.1 + PFT research seals (incl. negative evidence) |
| archive/agent/atomic-structure-foundry@efe025a1 | efe025a1 | ASE 1-2.3 atomic-terrain seals incl. RLock falsification seal |
| archive/agent/deepers-strategy-foundry@b4ab4620 | b4ab4620 | PFT B0-B5 seals (A0 not recoverable, LFS-blocked data — honest negative evidence) |
| archive/agent/shallow-well-foundry@39cb980e | 39cb980e | CTBT forward-collector runtime seals incl. T4.1.1 checkout recovery |
| archive/agent/obb-01-book-01-reality-audit@48a7c0ae | 48a7c0ae | OpenBB FORGE integration docs package |
| archive/agent/openbb-forge-obb-01-02-docs@d8ee6b47 | d8ee6b47 | OpenBB FORGE docs (Phase 0 evidence alignment) |

Each tag is annotated with the branch name, former head, and reason.

## Unique commit counts (vs main) — evidence basis

| Branch | Former head | Unique commits vs main | Classification |
|---|---|---|---|
| agent/asia-triangle-foundry | 8f84243f | 16 | ARCHIVE_REF_REQUIRED |
| agent/atomic-structure-foundry | efe025a1 | 7 | ARCHIVE_REF_REQUIRED |
| agent/crypto-data-1.1 | 1d960752 | 0* | ABSORBED_VERIFIED (*ancestor of crypto-quant-foundry) |
| agent/deepers-strategy-foundry | b4ab4620 | 8 | ARCHIVE_REF_REQUIRED |
| agent/shallow-well-foundry | 39cb980e | 14 | ARCHIVE_REF_REQUIRED |
| agent/obb-01-book-01-reality-audit | 48a7c0ae | 1 | ARCHIVE_REF_REQUIRED |
| agent/openbb-forge-obb-01-02-docs | d8ee6b47 | 15 | ARCHIVE_REF_REQUIRED |
| tb-forward-engine-plan-anchor-temp | 223fd024 | 0* | ABSORBED_VERIFIED (*ancestor of tb-forward-engine) |
| tv-review | 1a53cbb1 | 18 (vs main) / 0 (vs oce) | KEEP_PROTECTED — ancestor of oce |
| capital-routing | 43a6473c | 58 | KEEP_PROTECTED (restored) |
| cerebus-mve-implementation | 30359692 | 991 | KEEP_PROTECTED (restored) |
| execution-runtime-foundation | 03eb68f8 | 1018 | KEEP_PROTECTED (restored) |
| hermes-set-up | b4ef87b7 | 1 | KEEP_PROTECTED (restored) |

## Note on archive/review-branch

archive/review-branch (c7902326, 1054 unique commits vs main) was a deliberate
archive snapshot of pre-cleanup master with triangular-basis research. Restored
as an archive branch (F08) rather than deleted; content not proven absorbed.

## Rule compliance

- No refs deleted during this task.
- Negative research (RLock falsification, A0 non-recovery, LFS-blocked data)
  treated as valuable evidence, not junk.
- Ambiguity → BLOCKED_UNRESOLVED default avoided by restoring where unique work
  was found; nothing remains deleted without a verified successor or archive ref.
