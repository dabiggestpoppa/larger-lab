# CLEANROOM OPERATOR DELETION PACKET (Part G)

Date: 2026-08-30
Physical deletion requires separate authorization:
`AUTHORIZED_STAGE=CLEANROOM-PERMANENT-DELETE`
This packet does NOT grant that authorization.

## Items held (do NOT delete without explicit operator authorization)

### 1. Duplicate clone (trashed)
- Path: `C:/Users/wifik/Desktop/projects/.trash-larger-lab-duplicate`
- Size: ~20 GB
- Contents: full duplicate clone of dabiggestpoppa/larger-lab (second checkout
  that was superseded by the workspace-root clone)
- Git-tracked: n/a (it is a whole repo checkout)
- Pushed remotely: yes — all reachable refs already on origin; also served as
  the recovery source for deleted-branch former heads (archive/* refs, etc.)
- Unique refs: none found with unpushed commits (grant/OCE checked pre-move);
  remote-tracking refs to previously-deleted branches were read for recovery
- Untracked files: none of value (verified before move)
- Recovery method: `mv` back to original path from trash
- Expected reclaimed space: ~20 GB
- Risk: LOW — no unique unpushed refs identified; but keep until operator
  confirms nothing else is needed
- Recommended action: permanent deletion only after operator review of the
  pushed cleanroom branch and confirmation of no data need
- Authorization required: YES

### 2. Legacy worktree leftovers
- Path: `C:/Users/wifik/Desktop/projects/.trash-legacy-worktrees`
- Size: 32 KB
- Contents: leftover unregistered worktree directories (larger-lab-asia-jpy,
  larger-lab-ctbt-forward) whose branches were already deleted remotely;
  uncommitted research data was intentionally discarded per earlier operator
  decision
- Git-tracked: no
- Pushed remotely: no (uncommitted working files)
- Unique refs: no
- Untracked files: yes (previously discarded by operator decision)
- Recovery method: n/a (data intentionally discarded per earlier decision)
- Expected reclaimed space: negligible
- Risk: LOW
- Recommended action: permanent deletion when authorized
- Authorization required: YES

### 3. Git LFS cache
- Path: `C:/Users/wifik/Desktop/larger-lab/.git/lfs/objects`
- Size: 7.2 GB
- Contents: downloaded LFS blobs (parquet research data etc.) for branches;
  recoverable from GitHub LFS on demand
- Git-tracked: LFS-managed (not in normal tree)
- Pushed remotely: yes (objects are on GitHub LFS)
- Unique refs: none
- Untracked files: n/a
- Recovery method: `git lfs fetch` / `git lfs pull` re-downloads on demand
- Expected reclaimed space: ~7.2 GB
- Risk: LOW-MEDIUM (offline work needing parquet data would re-download)
- Recommended action: `git lfs prune` only when authorized; safe because
  objects are committed to GitHub via LFS
- Authorization required: YES

### 4. Reflogs / dangling objects / unreachable Git objects
- Path: repository `.git/logs`, `.git/objects`
- Contents: recovery metadata and unreachable commits
- Recovery method: reflog/dangling-object recovery (used earlier to restore
  oce-full-program-planning-books-2-10 and the four misclassified branches)
- Risk: HIGH to delete — dangling objects are the safety net that made
  branch restoration possible
- Recommended action: DO NOT expire reflogs or run gc --prune=now. Leave
  untouched.
- Authorization required: YES (and strongly discouraged)

## Summary

| Item | Size | Recoverable space | Authorization |
|---|---|---|---|
| .trash-larger-lab-duplicate | 20 GB | ~20 GB | CLEANROOM-PERMANENT-DELETE |
| .trash-legacy-worktrees | 32 KB | ~0 | CLEANROOM-PERMANENT-DELETE |
| LFS cache | 7.2 GB | ~7.2 GB (re-downloadable) | CLEANROOM-PERMANENT-DELETE |
| reflogs/dangling objects | n/a | n/a | DO NOT DELETE |

Total recoverable once authorized: ~27 GB.
Nothing was permanently deleted during this task (permanent-deletion count: 0).
