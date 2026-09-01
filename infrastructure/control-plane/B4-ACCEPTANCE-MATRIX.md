# OCE Book 4 — Configuration & Security Control Spine
## Acceptance Matrix

Status: `IN_PROGRESS` · Branch `oce-program-build` · Start SHA `acddeb696e6b5df1828fc7baf8c7bfbd2eb43e90`

### Planning interpretation (recorded, no material conflict)
There is no literal "Book 4" file in the planning history. The governing/ratified
planning material is the **OCE Constitution (Block 00)** and the **Block 03
Constitutional Spine dossier**, with this mission's prompt as the concrete Book 4
spec. Book 4 is the next **implementation book** after the closed Book 3 Worker
Fabric on `oce-program-build` — it is **not** Program Block 4 (PO Governed
Builder). Field names and precedence below are derived from the mission inventory
(A–J) and the frozen Book 2/3 contracts; no competing standard is invented.

### Acceptance surfaces

| # | Requirement (mission) | Implementation surface | Test | Evidence |
|---|----------------------|------------------------|------|----------|
| A | Canonical settings ownership | `config_spine.py` registry/schema | `test_b4_config_spine` (registry/validation) | `b4-config-registry-results.json` |
| B | Deterministic resolution / precedence | `resolve()` layered precedence | `test_b4_config_spine` (precedence) | `b4-precedence-results.json` |
| C | Startup validation — fail closed | `validate_effective()` | `test_b4_config_spine` (startup rejection) | `b4-startup-failclosed-results.json` |
| D | Secret reference model | `secret ref + resolve/rotate/revoke` | `test_b4_config_spine` (secret lifecycle) | `b4-secret-reference-results.json` |
| E | Redaction / leakage defense | `redact()` over logs/exceptions/evidence | `test_b4_config_spine` + leak scan | `b4-redaction-results.json`, `b4-secret-leak-scan-results.json` |
| F | Authorization boundaries / overrides | operator override audit | `test_b4_config_spine` (override audit) | `b4-authorization-results.json` |
| G | Network / firewall posture | public-listen / egress deny | `test_b4_config_spine` (network denial) | `b4-network-posture-results.json` |
| H | Live-order / execution denial | mode/market gates, deny path | `test_b4_config_spine` (live-order denial) | `b4-live-order-denial-results.json` |
| I | Billable cloud gates | cloud/burst/provision deny | `test_b4_config_spine` (cloud denial) | `b4-cloud-gate-results.json` |
| J | Config drift / effective state | deterministic fingerprint | `test_b4_config_spine` (fingerprint) | `b4-drift-fingerprint-results.json` |
| M | Adversarial matrix | see test module cases | `test_b4_config_spine` (adversarial) | `b4-adversarial-results.json` |
| R | Book 2/3 regression | shared runner full suite | container CI + local | `unit/pg/...` category artifacts |

### Milestones (ordered commits)
- B4-R1: settings registry + ownership + fail-closed startup validation
- B4-R2: deterministic precedence/resolution + drift fingerprint
- B4-R3: secret reference model + redaction + leak scan + rotation/revocation
- B4-R4: authorization boundaries + operator-override audit
- B4-R5: network posture + live-order denial + billable cloud gates
- B4-R6: adversarial matrix + regression wiring + dedicated CI
- B4-R7: authoritative execution, evidence archive, evidence-only commit

---

## ACTUAL IMPLEMENTATION LEDGER / SUPERSEDING MILESTONE STATUS (B4-R3R7)

*The section above preserves the original planning sequence as historical
intent. It does NOT describe what shipped. The ledger below is the truth;
never infer completed scope from commit labels alone.*

### Superseding implementation history

| Planned milestone | Actual commit | Actual scope | Remaining scope | Reason for deviation | Evidence status |
|---|---|---|---|---|---|
| R1 registry/startup | `d793f36b` B4-R1 | canonical settings registry + ownership + fail-closed resolution | — | planning intent | superseded by R3R repairs |
| R2 precedence/fingerprint | `14da06f8` B4-R2 | surfaces A-J spine tests (95) | — | planning intent | superseded by R3R repairs |
| R3 secret lifecycle | `a58671b4` B4-R3 | startup gate hooked into ControlPlane/lifecycle/doctor | — | startup gate took priority | superseded (fabricated-ref defect) |
| (unplanned) B4-R4 | `4624ec38` B4-R4 | config-spine CI category + dedicated workflow | — | completed before B4-R3R mission arrived | active (provisional) |
| R3R1 provenance + namespace | `488f1699` B4-R3R1 | env!=file provenance; governed OCE_* namespace; input inventory | — | independent review of B4-R3 | active |
| R3R2 runtime convergence | `fdcbf34b` B4-R3R2 | host/port + scheduler interval from effective config; every entrypoint gated | — | split-brain repair | active |
| R3R3 secret storage | `f9b85f5d` B4-R3R3 | RuntimeSecretBackend; config-vs-runtime start split; unbacked refs fail closed | — | fabricated-ref removal | active |
| R3R4 DB binding | `518c4e01` B4-R3R4 | governed DSN derivation; POSTGRES_DSN bypass denied | — | secret-boundary convergence | active |
| R3R5 fingerprints | `dde36795` B4-R3R5 | config-identity + security-state fingerprints | — | blind-fingerprint defect | active |
| R3R6 redaction | `9eb926eb` B4-R3R6 | cand-error no-echo validation; canonical redaction primitive | — | error-path leakage defect | active |
| R3R7 ledger | (this commit) B4-R3R7 | acceptance matrix / implementation ledger | — | Defect R-10 | active |
| R4 authorization/override audit | covered in code + suite since B4-R2 | `ConfigAuthorization` boundary; operator_override audit tests exist in `test_b4_config_spine` (surface F) | not yet isolated as a dedicated closure milestone / evidence artifact | original milestone ordering folded into B4-R2 spine suite | partially (tests green; milestone-level evidence artifact pending) |
| R5 network/live/cloud gates | not started as isolated milestone | — | deny surfaces implemented inside spine `validate_effective` + R3R2 runtime gate; dedicated gate milestone outstanding | folded into earlier milestones | open |
| R6 adversarial/regression + CI | partially | — | dedicated B4 workflow pushed; full adversarial matrix + authoritative CI run pending | workflow landed in B4-R4 | open |
| R7 authoritative evidence | not started | — | authoritative run, artifact archive, evidence-only commit | — | open |

### Superseding milestone status

- **Book 4 status:** `IN_PROGRESS / CLOSURE_REPAIR` (post-B4-R3R sequence)
- **B4-R1..R4 commits:** preserved exactly as historical evidence; scope claims
  above reflect what they actually contain, not what the old milestone names
  suggested.
- **Known open items before book close:**
  1. R6-op: full adversarial matrix execution under the dedicated B4 workflow
     (currently only provisional workflow + registry wiring exist; the R3R
     adversarial proofs live in the local B4 suite classes TestR3R*).
  2. R7-op: authoritative CI evidence, artifact download + hashing, provenance
     record, evidence-only commit.
  3. Secret-leak scan over src/tests/scripts for the B4 canary + any committed
     fixture material.
  4. Registry regeneration from actual collection (new B4 test classes added
     across the R3R sequence) before the authoritative CI run.
  5. Final acceptance re-check: source cleanliness, cleanup evidence, cloud
     mutations=0, cost=$0, main=7e7ef722 untouched.

---

## SUPERSEDING LEDGER — B4-CXR3 / B4-R3R8 (authority-escape repair closure)

*Independent review of the B4-R3R closure found the suite green but still
untrue to the core invariants: a runtime input could modify the authority
that validates it (secret self-legitimation), and passing the gate did not
prove the process used that same authorized configuration. The CXR3 repair
sequence below closes those escape paths. Book 4 is closed after this
sequence; see `B4-EVIDENCE-RECORD.md`.*

| Repair | Commit | Scope | CXR3 defect | Evidence |
|---|---|---|---|---|
| B4-CXR3R1 | `0e44617c` | secret init vs runtime read authority (`initialize_runtime_secret` / `read_runtime_secret` / `derive_runtime_dsn`; no ambient self-legitimation; compose env read-only) | CXR3-01 | lifecycle + spine tests, store-snapshot invariance |
| B4-CXR3R2 | `c17b7142` | remove runtime DSN injection (worker `--dsn` removed; `build_durable_app` no DSN override; `migrate()` no DSN param; `migrate.py --db` required + loopback-guarded) | CXR3-02 | startup-gate subprocess proofs |
| B4-CXR3R3 | `1cb9a8d7` | outbound worker CP target canonicalized (`outbound_cp_url` gate-first + verified assertion); `postgres.host` loopback-only enum | CXR3-03 / CXR3-04 | worker-target + DB-host adversarial proofs |
| B4-CXR3R4 | `c508212c` | ownership enforced in the real resolver: policy/operator(po) settings reject non-default sources | CXR3-05 | full weakening matrix (env/file/cli) |
| B4-CXR3R5 | `8ff074cd` | capital authority locked to `none` (validate_effective + override guard) | CXR3-06 | capital lock proofs incl. PO |
| B4-CXR3R6 | `888a6adc` | override-audit truth label (in-process audit NON-AUTHORITATIVE; append-only durable sink seam) | CXR3-07 | audit-truth proofs |
| B4-CXR3R7 | `07314b43` | unified startup truth (`validate_configuration` vs `validate_runtime_readiness` vs `require_runtime_startable`; doctor readiness) | CXR3-08 | no start=True+secret_ok=False; doctor proofs |
| B4-CXR3R8 | `780f7ceb` | config-input inventory refresh (VERIFIED_COMPATIBILITY_ASSERTION / INIT_ONLY / DEPRECATED_AND_REJECTED dispositions); doctor custom/revoked ref; aggregate denial side-effect invariance; registry regenerated to 510 | CXR3-09 / CXR3-10 | inventory doc + adversarial closure |

### Authoritative closure (B4-CXR3, verified from junit + gate + artifact)

- **Run:** `33505225957` on `780f7ceb` — `b4-config-spine-validation` **success**
- **OCE_RUN_ID:** `c4ca8bfc70cb`; **artifact:** `b4-config-spine-evidence-c4ca8bfc70cb` (id `9799398331`)
- **JUnit:** 510 collected / 510 executed / 510 passed / 0 failed / 0 errors / 0 skipped
- **Independent gate:** PASS (137 checks); **final package verifier:** PASS
- **Manifest:** 33/33 entries hash+size verified; **outer ZIP SHA-256:** `dcf290aab6485e34aad3a30b4f4b93f5d54fe5ab330b80602f3ab25e394a9daa`
- **Source clean before + after; cleanup removed=True (PG volume preserved); cloud mutations 0; cost $0**
- **Archive:** `~/Desktop/oce-b4-archive/run-33505225957/`

### Previously superseded (preserved, not closure proof)

- Run `33461183563` / `27a21c9a` (B4-CXR2 head) — prior green run, superseded
  by the CXR3 sequence.
- Runs `33460848791`..`33504839138` — intermediate CXR3 commits failed the
  exact-count gate until the registry was regenerated at B4-CXR3R8; each
  preserved as truthful historical evidence.