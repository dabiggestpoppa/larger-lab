# OCE Branch Policy

## Authorized integration branch: `oce`

The operator explicitly authorized consolidation onto a single permanent
branch named `oce` (direct instruction, session 2026-08-26): "stop making
new branches ... change the name of the new branch to simply oce, the other
oce branch commits should be merged to the oce branch ... all future work
will be pushed to the oce branch".

As a result:

- Per-increment OCE branches (`oce/block-1-i1r3g-*`, etc.) are **not** used
  going forward. Their commits were merged into `oce` (they were already
  linear ancestors) and the old `oce/*` refs were deleted locally and on
  origin so the plain `oce` ref could exist (Git forbids a file and a
  directory at the same ref path).
- All future OCE validation work is committed and pushed directly to `oce`.
- The checkpoint contract (`checkpoint-identity-data.json`) declares
  `"authorized_branch": "oce"` and the CI workflow
  (`b1-i1r3-validation.yml`) triggers on `[oce]`.

## Guardrails (unchanged)

- Never merge to `main` without explicit operator approval.
- `main` must remain untouched by OCE increments.
- Do not create new `oce/*` sub-branches unless the operator asks for one.
