# CLEANROOM-F08 — Branch Restoration Record

Date of operation: 2026-08-30
Authorizing stage: CLEANROOM-RECOVERY-AND-FINAL-REVIEW

## Summary

Later independent review determined that several branches deleted under an
earlier "legacy" classification contained valuable, non-absorbed work.
This record documents the restoration of those branch references at their
exact former head SHAs. No commits were modified; no cherry-picks were made.

## Restored branches (Part B — misclassified, restored at exact SHA)

| Branch | Former head SHA | Tree SHA | Reason |
|---|---|---|---|
| capital-routing | 43a6473c1bc01bb79efd3b415e482d65640e1226 | 807ca04d700629552061987a2bd5f941aacf55d0 | Unique MT5 physical-profile + capital-risk work; no common ancestor with tb-forward-engine; not absorbed |
| cerebus-mve-implementation | 30359692ccd4c1ce0c7a52096cd64ec4902520ee | 5e4a509f38d3de0845235825c7934010a9f8af07 | Active CEREBUS Morphic Volatility Engine lineage; 991 unique commits vs main |
| hermes-set-up | b4ef87b7af9b9fafdd9f050e0b90319f76c1e0ff | 6a3fe1c3946713033732ee33beee4df255a3a485 | OCE Hermes Telegram Operator, MCP facade, audit logging, runbooks; OCE architecture |
| execution-runtime-foundation | 03eb68f8d4c684c4ccaf7b4f93b3fc4e1127a1ee | c4fad463ba23f88ab82ced34eba2d2f4cf7933a7 | Unique TradeLocker demo read-only integration; diverges from tb-forward-engine |

Restoration method for each: `git branch <name> <sha>` (commit object verified
present locally), `git push origin <name>`, `git fetch origin --prune`,
then `git ls-remote --heads origin <name>` verified the remote SHA matches the
exact former head.

## Restored archive refs (previously deleted durable archive branches)

These branches already lived under the `archive/*` namespace — a deliberate
durable-archive mechanism. Deleting them removed the archive references
themselves. Restored at former heads recorded in the retained duplicate clone.

| Branch | Former head SHA | Content |
|---|---|---|
| archive/cerebus-local-extra | 133364c9cb | MVE-P4 causal acceptance engine |
| archive/content-oc2 | aeb3afdde9 | OC2 content snapshot |
| archive/hermes-02e51f11 | d4be1f2302 | OC2 architecture docs |
| archive/hermes-262c2f34 | 217f48c297 | OC2 journal/skill loader fixes |
| archive/hermes-cde01a2a | 63474e77b4 | CC2 Cognitive Filesystem Foundation |
| archive/pruned-master-2026-08-15 | 6922c08382 | Workspace snapshot |
| archive/pruned-snapshot-vtuber | d7cb598a86 | Workspace snapshot |
| archive/review-branch | c79023263b | Master triangular-basis research snapshot |

## Restored tv-review (OCE lineage)

tv-review (former head 1a53cbb1d400bec5b77b0b3b6816d707050df1c6) contains
exclusively OCE Block 1 I1R cloud-ground infrastructure commits (B1-I1R*
series) and is an ancestor of `oce`. Per the OCE protection override, it is
classified KEEP_PROTECTED and restored.

## Verification

- All restored remote SHAs confirmed via `git ls-remote --heads origin` after push.
- No protected branch was modified.
- main unchanged at 7e7ef7222c4ecdea568b34583fd81406165cc9b6.
