# B6-I2 Acceptance Matrix — templates and local harness

Status: FROZEN with the ratification record at `1be58fd9`.
Every row names executed evidence; no row is satisfied by declaration.

| ID | Criterion | Evidence | State |
|---|---|---|---|
| A01 | Stage identity and exit gate bound to merged authorities | scope/contract + validator `stage/*` | PROVEN |
| A02 | Fresh generated app starts locally, executably | `test_generated_app_starts_locally`; run `42809713938` | PROVEN |
| A03 | Readiness, shutdown, exit 0, bounded timeout | same node; `READY app` / `STOPPED` / rc 0 / 15 s | PROVEN |
| A04 | Second run and byte-identical rebuild | same node plus `test_deterministic_build_byte_identical` | PROVEN |
| A05 | Dirty destination and tampered artifact refused | `test_dirty_build_input_refused`; start artifact comparison | PROVEN |
| A06 | Archive traversal, symlink, absolute, malformed, oversize, digest refusals | archive suite, 6/6 nodes | PROVEN |
| A07 | Harness profiles, services, undeclared network refusal | harness suite | PROVEN |
| A08 | No cloud dependency or publication claim | `test_cloud_dependency_declared_absent`; deploy declaration | PROVEN |
| A09 | C1.S3 compatibility window | no published consumer; owner B6-I7 | UNPROVEN_BUT_EXIT_GATE_ALLOWS |
| A10 | C1.S4 compatibility window | local profiles only; owner B6-I7 | UNPROVEN_BUT_EXIT_GATE_ALLOWS |
| A11 | B6-I0 governed mutation arithmetic | 12/12 governed, floor 12, 13 restored; run `42809714005` | PROVEN |
| A12 | M13 classification | POSIX environmental probe, outside population | PROVEN |
| A13 | B6-I2 mutation discrimination | 6/6 discriminated and restored | PROVEN |
| A14 | Prior-stage tests byte-identical | validator `boundary/prior_test_bytes/*` | PROVEN |
| A15 | B6-I0 replay at its own head | 72/72, validator 136/136, run `42809714005` | PROVEN |
| A16 | B6-I1 replay at its own head | 42/42, run `42809713956` | PROVEN |
| A17 | Resolver authority sets exact, no future leak | controls 15/15, run `42809713938` | PROVEN |
| A18 | Paired comparison | 270 common, 0 base-only, 30 head-only, 20 checks, run `42809713955` | PROVEN |
| A19 | Manifest and cleanup | 9 artifacts + 7 code files; no residue | PROVEN |
| A20 | Locks, cost and authority | I3–I9 LOCKED; `$0`; capital none | PROVEN |
| A21 | Independent audit | none; same-agent review only | NOT PROVEN |
