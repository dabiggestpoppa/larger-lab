# OCE Golden System
## B5-I1 — Evidence Packet: CAND-003

**Document ID:** OCE-B5-I1-PACKET-CAND-003
**Version:** 1.0
**Status:** INTAKE_EVIDENCE — UNSCORED
**Candidate identifier:** CAND-003
**Working name (register-only):** Repo Integrity & Governance-State Auditor
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)

---

## 1. Observable operator outcome

`AUTHORED_SPEC` — The operator asks "is this tree in a governed state?" and runs one local command that executes the standard reality-lock battery — working-tree cleanliness, `git diff --check` (staged and unstaged), secret-pattern scan, line-ending census (pure-CRLF corpus conformance), frozen-branch verification (declared branches sit at declared SHAs), and merge-parent verification (a declared merge commit has the declared two parents) — and prints a per-check PASS/FAIL table with the exact observed values. It is the reality-lock procedure, mechanized. Success is judgeable from the table (protocol C1).

Basis: `REPO_ASSET` — the reality-lock procedure itself is governance practice in this program (B5-I0/B5-I1 authorizations §1; Book 4 evidence §23–§24 detachment censuses), and every check has a concrete repo subject: frozen branches (`oce-program-build`, `oce-book-5-build`), merge commit `f89883471…` with declared parents, CRLF-normalized document corpus, `git diff --check` discipline.

## 2. Operator-testable acceptance scenarios

`AUTHORED_SPEC` —

1. S-1 (governed tree): run on the clean intake worktree; all checks PASS; table quotes observed SHAs and counts; exit 0.
2. S-2 (dirty tree): add an untracked scratch file; `tree-clean` check FAILs naming the path; other checks unaffected; exit 1.
3. S-3 (frozen-branch drift): audit against a declaration pinning `oce-book-5-build` to a wrong SHA; check FAILs showing declared vs observed.
4. S-4 (merge-parent check): verify merge `f89883471…` declares parents `3bde6cb2c…` + `18c279497…`; PASS; then a declaration with a wrong parent FAILs with both values shown.
5. S-5 (secret scan): a scratch file containing a fake `ghp_…` token pattern FAILs the scan with path+line; the canonical tree passes.

## 3. OCE lifecycle coverage matrix

`AUTHORED_SPEC` —

| OCE surface | Exercised by CAND-003 |
|---|---|
| Intent | Operator declares the audit target (worktree/branch declarations file). |
| Planning | Check battery compiled into ordered plan with per-check budgets. |
| Grants | Read-only filesystem/git grants; denial envelope for any write attempt. |
| Workers | Checks execute as independent jobs; failures isolate per check. |
| Artifacts | Audit packs stored digest-referenced under `audits/`. |
| Evidence | Each row = declared expectation, observed value, disposition (manifest-shaped). |
| Review | Operator reads the PASS/FAIL pack; no narrative trust. |
| Identity | Audit bound to producer identity; declaration file versioned. |
| Packaging | Local CLI + versioned declaration files. |
| Observability | Header: checks run, durations, git version, tree head. |
| Recovery | Atomic audit-pack writes; interrupted audits marked partial. |

## 4. Deterministic-kernel boundary

`AUTHORED_SPEC` — Deterministic core: git plumbing calls (`status --porcelain`, `diff --check`, `rev-parse`, `cat-file -p`), secret-pattern scanning (fixed regex set over tracked text files), newline census (byte counting), declaration matching, table rendering. Fixed tree + fixed declaration → identical results (timestamps excepted). LLM-permitted surfaces: none required.

## 5. Bounded input inventory

`AUTHORED_SPEC` grounded on `REPO_ASSET`:

| Input | Path/bounds |
|---|---|
| Declaration file | Versioned YAML/JSON: expected branch SHAs, expected merge parents, expected-CRLF path globs, scan excludes |
| Git repository | The local checkout (read-only git plumbing) |
| Secret patterns | Fixed pattern set (AWS/GitHub/PK/private-key/generic assignment forms, as used in B5-I0 validation) |

No network. Clone-level checks (`ls-remote`) optional and operator-flagged; default scope is local-only.

## 6. Canonical-state proposal

`AUTHORED_SPEC` — State = audit pack: `{audit_id, head_sha, declaration_version, per_check_results[{check, expected, observed, disposition}], complete}` — one append-only JSON per audit, schema-validated. Declarations are content-addressed inputs; audits are replayable from the same tree + declaration.

## 7. Local-run topology

`AUTHORED_SPEC` — Local Python CLI using git plumbing only; writes only `audits/`. No services, no daemons, no network by default.

## 8. Explainable-output example

`AUTHORED_SPEC` — Format demonstration (not a measurement):

```
CAND-003 audit a-0001  head=f8988347…  decl=gov-v1
  tree-clean            PASS (0 entries)
  diff-check            PASS (staged 0, unstaged 0)
  secret-scan           PASS (0 findings / 6,755 tracked files)
  crlf-census           PASS (28/28 corpus files pure CRLF)
  frozen-branch         PASS oce-book-5-build @ 18c279497… (declared match)
  merge-parents         PASS f8988347… → [3bde6cb2c…, 18c279497…]
  DISPOSITION: GOVERNED
```

Failures quote declared vs observed exactly.

## 9. Completion-window estimate and basis

`AUTHORED_SPEC` — The narrowest kernel in the set; fits B5-I2→B5-I5 in approximately 3–5 governed increments. Basis: each check is an independent, already-specified procedure (the reality locks run manually today); work is mechanization + tests, per plan B5.C3.S3 negative/adversarial coverage.

## 10. Recovery scenario

`AUTHORED_SPEC` — Injected failure: process killed mid-secret-scan. Audit pack records completed checks + `complete=false`; restart resumes at the first incomplete check; final disposition never printed for a partial audit.

## 11. Governed change-cycle scenario

`AUTHORED_SPEC` — Change: "add a tracked-file-census check (count of tracked files per top-level dir)." Applied as governed change: intent → plan → declaration `gov-v2` (additive) → new check module + tests → regression: all `gov-v1` checks unchanged and passing → prior audit packs remain valid and unedited.

## 12. Reuse inventory vs platform-extraction risk

`AUTHORED_SPEC` — Reuse: reality-lock procedures from B5-I0/B5-I1 authorization texts as check specifications; secret-pattern set from B5-I0 validation; git-plumbing conventions from existing tools. Bespoke: declaration schema and check wiring. Platform-extraction risk: LOW — it audits git state; it does not wrap or replace the control plane.

## 13. Governed-path mapping (C10 — all eleven paths)

`AUTHORED_SPEC` — identity: producer identity per audit · intent: declared audit target · planning: ordered check battery · grants: read-only git/fs grants · workers: checks as isolated jobs · artifacts: digest-referenced audit packs · evidence: expected-vs-observed rows · review: GOVERNED/VIOLATION pack · packaging: local CLI + versioned declarations · observability: audit header · recovery: atomic partial-audit discipline.

## 14. D1–D14 evidence (positive evidence for every "does not require")

| D | Disqualifier | Evidence | Class |
|---|---|---|---|
| D1 | Capital/execution authority | Read-only git/filesystem checks; no capital surface | AUTHORED_SPEC |
| D2 | Live trading/broker credentials | Scans for credential patterns; holds none; no broker API | AUTHORED_SPEC |
| D3 | Irreversible external effects | Writes only `audits/`; tree untouched (S-1/S-2) | AUTHORED_SPEC |
| D4 | Regulated submissions | Local report only | AUTHORED_SPEC |
| D5 | Public write access | No publish path | AUTHORED_SPEC |
| D6 | Sensitive mass data | Scans text patterns; does not exfiltrate or retain content beyond finding paths | AUTHORED_SPEC |
| D7 | Paid external hosting | Local only; `$0` | AUTHORED_SPEC |
| D8 | Cloud-only operation | Fully local (§7) | AUTHORED_SPEC |
| D9 | Vercel/Railway/SonarCloud/Kilo | Not referenced; git+stdlib | AUTHORED_SPEC |
| D10 | External hosting authority | None | AUTHORED_SPEC |
| D11 | Public SaaS | Not a service | AUTHORED_SPEC |
| D12 | LLM as canonical state | Deterministic kernel; JSON audit packs | AUTHORED_SPEC |
| D13 | Platform rewrite in disguise | Fixed check battery over git plumbing; no platform re-built (§12) | AUTHORED_SPEC |
| D14 | Recurring cost > `$0` | No paid services | AUTHORED_SPEC |

No UNKNOWN answers. Static contract evidence only; no runtime measurements claimed.
