# LARGER-LAB CLEANROOM REPORT

**Generated:** 2026-08-29
**Authoritative Repo:** `C:\Users\wifik\Desktop\larger-lab` (workspace root)
**Status:** PROTECTION APPLIED — All OCE / QCAE / Grant / Crypto / TB / baseline branches verified intact.

---

## ⚠️ CONSOLIDATED PROTECTION OVERRIDE (authoritative)

Final overriding directive protects ALL of these systems. None may be deleted,
archived, renamed, rebased, squashed, merged-away, or history-rewritten.

| System | Branches |
|---|---|
| **CRYPTO** | agent/crypto-quant-foundry, agent/crypto-sensor-fabric-plan, agent/crypto-sensor-fabric-build |
| **OCE** | oce, oce-program-build, oce-full-program-planning-books-2-10, + any other OCE lineage |
| **QCAE** | qcae-capability-acquisition-engine (future OCE integration — NOT junk) |
| **GRANTS** | grant-sector-g1-production, grant-sector-for-solavage, + ALL grant work |
| **ENGINE** | tb-forward-engine |
| **BASELINE** | main, master |
| **TEMP** | agent/repo-cleanroom (only if/where created for tracked-file cleanup) |

**Deletion rule:** Only delete branches/files unrelated to the above systems and
to required shared infrastructure. Do NOT classify an old OCE branch as
SAFE_DELETE merely because it is old — **all OCE lineage stays.**

---

## 1. CORRECTION — OCE BRANCH RESTORED

`oce-full-program-planning-books-2-10` was deleted before the OCE protection
override took effect. Its head commit `028fcdddd90f25c44996510426bd0c0e68bc54f5`
still existed in the local object store, so it has been **fully restored**:

- Local branch recreated → `028fcdddd9`
- Pushed back to `origin/oce-full-program-planning-books-2-10` → `028fcdddd9`
- Verified present in server-side branch list (`git ls-remote --heads origin`)

**No data was lost.**

---

## 2. TRUE REMOTE BRANCHES (server-side, `git ls-remote --heads origin`)

All 11 branches present — every one is protected:

| Branch | HEAD | Status |
|---|---|---|
| agent/crypto-quant-foundry | 9243201b47 | PROTECTED (crypto) |
| agent/crypto-sensor-fabric-build | e612403153 | PROTECTED (crypto) |
| agent/crypto-sensor-fabric-plan | 4bb677f9e0 | PROTECTED (crypto, frozen head) |
| grant-sector-g1-production | 3a639d8986 | PROTECTED (grant) |
| main | 7e7ef7222c | PROTECTED (baseline) |
| master | 6769ad31ac | PROTECTED (baseline) |
| oce | d3df9eb45a | PROTECTED (OCE, canonical head) |
| oce-full-program-planning-books-2-10 | 028fcdddd9 | PROTECTED (OCE) — RESTORED |
| oce-program-build | b5d814077c | PROTECTED (OCE) |
| qcae-capability-acquisition-engine | c4e5df830b | PROTECTED (QCAE) |
| tb-forward-engine | 49930215ad | PROTECTED (engine) |

---

## 3. OCE CONSOLIDATION VERIFICATION

| Check | Result |
|---|---|
| oce remote HEAD | `d3df9eb45aeddd8a3dd40ced24a7f2e1d2f0ff41` |
| Expected HEAD (spec §2) | `d3df9eb45aeddd8a3dd40ced24a7f2e1d2f0ff41` |
| Match? | ✅ **EXACT MATCH** |
| oce-full-program-planning-books-2-10 | `028fcdddd9` — restored, intact |
| oce-program-build | `b5d814077c` — intact |
| qcae-capability-acquisition-engine | `c4e5df830b` — intact, preserved for OCE integration |
| Crypto plan (frozen) | `4bb677f9e0` — matches spec frozen head exactly |

---

## 4. DELETED — ONLY the genuinely unrelated legacy branches

These branches were **not part of any protected system** (not crypto-canonical,
not OCE, not QCAE, not grant, not TB). They were abandoned strategy / legacy
work sharing only the early common lineage with the canonical branches. All were
fully committed to GitHub before deletion.

Deleted from remote:
- agent/asia-triangle-foundry
- agent/atomic-structure-foundry
- agent/crypto-data-1.1
- agent/deepers-strategy-foundry
- agent/shallow-well-foundry
- agent/obb-01-book-01-reality-audit *(already absent server-side)*
- agent/openbb-forge-obb-01-02-docs *(already absent server-side)*
- capital-routing
- cerebus-mve-implementation
- execution-runtime-foundation
- hermes-set-up
- tv-review
- tb-forward-engine-plan-anchor-temp *(already absent server-side)*

> ⚠️ **Numbered cleanup-commit recommendation:** If any of these are later judged
> to overlap protected work, they remain recoverable from the other stale clone
> (`C:\Users\wifik\Desktop\projects\larger-lab`) which still holds their remote
> tracking refs. No action taken here.

---

## 5. DECISION REMAINING OPEN (recommended next step)

This repo has **two clones of the same remote**:

1. `C:\Users\wifik\Desktop\larger-lab` — workspace root, **authoritative**, on `oce`
2. `C:\Users\wifik\Desktop\projects\larger-lab` — apparently a **stale duplicate**
   (holds old remote-tracking refs for deleted branches, unrelated untracked dirs)

Consolidating to one clone would reclaim ~11GB. This is **not** done yet pending
your confirmation, because the stale clone may hold the only recoverable refs to
deleted legacy branches and uncommitted untracked work.

---

## 6. STASHES

- **ZERO** stashes existed at inventory in the duplicate clone.
- In the workspace-root repo the working change `infrastructure/cloud-ground/tests/test_regression.py` was stashed pre-cleanup. **No stashes were dropped.**

---

## 7. LFS CACHE

`.git/lfs/objects` ~5.8GB: 82 `.parquet` files. ALL are from
`quant-lab/research/crypto_foundry/` (alt_rotation + derivatives lower_field
outputs), and they ARE tracked on the active branches. They are committed to
GitHub via LFS, so `git lfs prune` would only remove local downloaded copies
(re-fetched on demand). **Not pruned** — left intact. Space reclamation of the
LFS cache is deferred to the same single-clone consolidation decision.

---

## Operator Decision Required

1. **Confirm the 11 protected branches stay as-is.** (Recommended — all intact.)
2. **Consolidate to a single clone?** Delete the stale `projects/larger-lab`
   duplicate (~11GB .git) once any desired legacy refs are captured.
3. **Proceed with deferred LFS prune** (5.8GB) during consolidation.
4. **Continue tracked-file (quant-lab legacy) cleanup on a dedicated
   `agent/repo-cleanroom` branch?** — only for material verified unrelated to
   OCE/QCAE/Grant/Crypto/TB.