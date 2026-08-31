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