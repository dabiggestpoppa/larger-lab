# OCE Book 4 — Configuration & Security Control Spine Evidence Record

**Status:** `COMPLETE / B4-CXR3-CLOSURE / GATED_COMPLETE`
**Branch:** `oce-program-build`
**Book 4 start SHA:** `acddeb696e6b5df1828fc7baf8c7bfbd2eb43e90`
**B4-R3R repair start SHA:** `a58671b45e812049b72669466020bb88b7019489`
**B4-CXR3 repair start SHA:** `27a21c9ae2a089dbc324b356407237751082c9d5`
**Book 2:** `RATIFIED / GATED_COMPLETE` · **Book 3:** `COMPLETE / GATED_COMPLETE`
**main:** `7e7ef7222c4ecdea568b34583fd81406165cc9b6` (untouched)

## Core invariant (this repair)

> **THE CONFIGURATION OCE VALIDATES IS THE CONFIGURATION EVERY RUNTIME
> PROCESS ACTUALLY USES**, and **NO UNTRUSTED RUNTIME INPUT CAN MODIFY,
> REPLACE, OR BYPASS THE AUTHORITY THAT VALIDATES IT.**

Independent review found the previous green suite still allowed a runtime
input to modify the authority that validates it. The B4-CXR3 sequence
repairs every enumerated escape path. Each is closed with a real proof.

## Ordered repair commits (all pushed, `oce-program-build`)

| Commit | Message | Defect |
|---|---|---|
| `0e44617c` | B4-CXR3R1: separate secret initialization from runtime authority | CXR3-01 |
| `c17b7142` | B4-CXR3R2: remove arbitrary runtime DSN injection paths | CXR3-02 |
| `1cb9a8d7` | B4-CXR3R3: canonicalize outbound worker target and DB host boundary | CXR3-03 / CXR3-04 |
| `c508212c` | B4-CXR3R4: enforce setting ownership in the real resolver | CXR3-05 |
| `8ff074cd` | B4-CXR3R5: lock capital authority to none | CXR3-06 |
| `888a6adc` | B4-CXR3R6: repair override-audit durability truth label | CXR3-07 |
| `07314b43` | B4-CXR3R7: unify startup-truth semantics and doctor readiness | CXR3-08 |
| `780f7ceb` | B4-CXR3R8: refresh config-input inventory and close adversarial gaps | CXR3-09 / CXR3-10 |

No repair commit was amended, squashed, or rewritten. Intermediate CI runs
that failed the exact-count gate before the registry was regenerated at
B4-CXR3R8 are preserved as truthful historical evidence (e.g. `33460848791`
.. `33504839138`), never deleted.

## Final authoritative Book 4 run

Authoritative closure proof is the dedicated `b4-config-spine-validation`
run below. Its conclusion was verified from the actual junit XML +
independent gate + final package verifier + cleaned artifact, not inferred
from the run conclusion alone.

- **Branch:** `oce-program-build`
- **Implementation commit:** `780f7ceb40d328b6bde7d9909d45a5f276e2883c`
- **Implementation tree:** `ef965e944b2132c2888ff957431c7c3dd99392da`
- **CI workflow:** `b4-config-spine-validation`
- **CI run:** `33505225957`
- **CI conclusion:** `success`
- **CI URL:** `https://github.com/dabiggestpoppa/larger-lab/actions/runs/33505225957`
- **OCE_RUN_ID:** `c4ca8bfc70cb`
- **Artifact ID:** `9799398331`
- **Artifact name:** `b4-config-spine-evidence-c4ca8bfc70cb`
- **Outer ZIP SHA-256:** `dcf290aab6485e34aad3a30b4f4b93f5d54fe5ab330b80602f3ab25e394a9daa`
- **Totals (from junit.xml, independent):** 510 collected / 510 executed /
  510 passed / 0 failed / 0 errors / 0 skipped; 0 duplicate full node-ids.
- **config-spine category:** 216 / 216 executed / 216 passed / 0 skipped / 0 missing.
- **Independent gate:** `PASS` (137 checks — identity, exact totals, no
  duplicates, every mandatory id, category totals, migrations, source clean
  before/after, cleanup verified, durable PG volume preserved, manifest
  hashes/sizes match, cloud mutations 0, cost `ZERO`).
- **Final package verifier:** `PASS` (read-only).
- **Evidence manifest:** `33` entries, all hashes and sizes independently
  re-verified.
- **Regression on the same head:** `b1-local-ground-validation` success,
  `b2-control-plane-validation` success, `b3-worker-fabric-validation`
  success.

## Repair proof summary (each has tests)

- **CXR3-01 secret self-legitimation closed:** ambient `POSTGRES_PASSWORD`
  cannot rewrite an existing store, cannot materialize a missing store, and
  a matching password + DSN cannot self-legitimate; denial has zero
  authority-side effects (store hash invariant). Runtime reads are read-only
  (`read_runtime_secret` / `derive_runtime_dsn`); init is explicit
  (`initialize_runtime_secret`).
- **CXR3-02 DSN escapes removed:** `worker_loop --dsn` rejected at CLI;
  `build_durable_app` has no DSN override; lifecycle `migrate()` takes no DSN;
  `migrate.py --db` is required and loopback-only.
- **CXR3-03 worker target canonicalized:** `outbound_cp_url()` runs the gate
  first and treats `OCE_CP_URL` as a verified compatibility assertion —
  external hosts, noncanonical ports, credentials, and forbidden configs
  block before any socket activity.
- **CXR3-04 DB host boundary:** `postgres.host` is a loopback-only enum
  (`127.0.0.1`); external / RFC1918 / IPv6 / credential values rejected via
  env, file, and cli.
- **CXR3-05 ownership enforced:** policy-owned and operator(po)-owned
  settings reject every non-default source in the real resolver; the full
  weakening matrix (redact toggles, sandbox, sessions, egress, redis, live,
  cloud, capital) fails closed.
- **CXR3-06 capital locked:** `capital.authority` is `none`; `approved` is
  blocked through env/file/cli/default/override for every actor including PO.
- **CXR3-07 audit truth label:** the in-process override audit is explicitly
  NON-AUTHORITATIVE; durability requires an attached append-only sink; no
  canonical path claims durability it does not have.
- **CXR3-08 startup truth:** `validate_startup` is the config gate,
  `validate_runtime_readiness` is the complete contract (ready implies
  secret_ok implies ok), `require_runtime_startable` fails closed on all;
  doctor fails when the reference is absent, custom-unresolved, or revoked.
- **CXR3-09 inventory:** `B4-CONFIG-INPUT-INVENTORY.md` v2 records every
  authority-bearing input with an explicit disposition.
- **CXR3-10 adversarial closure:** unresolved/revoked doctor proofs and the
  aggregate "denial has zero authority-side effects" store-hash proof.

## Durable archive

- **Location:** `~/Desktop/oce-b4-archive/run-33505225957/`
- Original ZIP preserved byte-exact at `original-evidence.zip`
  (SHA-256 `dcf290aa…`, 50046 bytes).
- Expanded machine-readable copy under `expanded/` (33 files).
- Full provenance in `provenance.json`.

## Previously superseded evidence (preserved, not closure proof)

- Run `33461183563` / `27a21c9a` (B4-CXR2 head) — prior green run,
  superseded by the CXR3 sequence; preserved byte-exact.
- Runs `33460848791` .. `33504839138` — intermediate CXR3 commits that
  failed the exact-count gate until the registry was regenerated at
  B4-CXR3R8; preserved as truthful failure evidence.

## Confirmation

- `main` untouched: `7e7ef7222c4ecdea568b34583fd81406165cc9b6`.
- Book 5 NOT started; Program Block 4 NOT started.
- No cloud resources purchased/provisioned/deployed; cloud dormant;
  recurring cost `$0`; cloud mutations `0`; no GPU spend.
- Broker / paper / live trading disabled; no capital authority
  (`capital.authority=none`, locked); no execution mutations.
- No trading-strategy or CEREBUS rule changes.
- No OpenClaw activation; a second Hermes agent was not created.
- Book 2 and Book 3 evidence records unchanged; both remain GATED_COMPLETE.
- The source tree was clean before and after the authoritative run; cleanup
  removed containers and networks while preserving the durable PostgreSQL
  volume.
