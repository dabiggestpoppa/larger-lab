# OCE Golden System
## B5-I1 — Scorecard: PASS B (sequential adversarial/red-team pass)

**Document ID:** OCE-B5-I1-SCORECARD-PASS-B-001
**Version:** 1.0
**Status:** SEALED — sequential dual pass per AMEND-001
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)
**Governing amendment:** `OCE_B5_I0_AMEND-001_SEQUENTIAL_DUAL_PASS_REVIEW_v1.0.md` (OPERATOR_RATIFIED — ACTIVE)
**Review base commit:** `f381ce0eaaeb2139bf1e531b14e7fb03daf17008` (packet content identical to intake commit `52843ffc11ff97511ec7e7242f6adc7083290360`). Sealed Pass A artifact: commit `b05c61d0a547d3b9287eac55c7a0f1def7487fb7`, file SHA-256 `6a937706a42debda35b5d4e170c5c47b9745f80f26c307457f8a766878b6917c`.
**Scored on:** 2026-10-07
**Pass identity:** This is **Pass B, the adversarial/red-team pass**, performed by the same agent that performed Pass A, in the same conversation, **after** Pass A was sealed. Under AMEND-001 the two passes are **NOT independent and NOT blind**, and must never be described as independent, blind, or dual-reviewer verified. Pass B's integrity derives solely from its explicitly different falsification mandate; Pass A's scores were an available input, and optimism inherited from Pass A is itself a reviewed failure mode.

---

## 0. Conflict-of-interest declaration (honest form per AMEND-001 §4)

- The scoring agent is the author of the intake register and all five evidence packets, and performed Pass A. It therefore attacks its own produced evidence under a falsification mandate, by explicit operator direction (AMEND-001). This COI is declared here and must be carried into the decision packet; it is not mitigated by erasure.
- No recusal: the operator explicitly directed both passes in this context. Candidate identifiers only; working names unused in this file.

## 0a. Method and evidence posture

- D1–D14 **re-executed from scratch** per candidate against the frozen packet §14 text (not inherited from Pass A).
- C1–C10 re-scored under the frozen scale. Falsification posture: every qualifying claim attacked (`existence → is it operability?`), every optimistic Pass A judgment stress-tested, and scores lowered where the frozen packet text does not support the Pass A level under adversarial reading.
- Every score change is keyed to a recorded falsification attack with packet-section citations. No packet was modified; findings are recorded here as observations.
- **All packet evidence is static contract evidence or repository assets. No runtime measurements exist for any candidate.** Pass A credited the disclosed not-yet-measured evidence class at face value; Pass B discounts criteria where the packet's own text is an authored claim rather than a cited, verified asset. This is the intended disagreement between the two lenses, preserved for the operator.
- **No ranking, no comparison, no recommendation is expressed in this scorecard.** Per-candidate threshold results only.

---

## CAND-001

### Screen (re-run from packet §14)

| D | Item | Required? | Evidence ref | Verdict |
|---|---|---|---|---|
| D1 | Capital/execution authority | N | §14 D1 | CLEAR |
| D2 | Live trading/broker credentials | N | §14 D2 | CLEAR |
| D3 | Irreversible external effects | N | §14 D3 | CLEAR |
| D4 | Regulated submissions | N | §14 D4 | CLEAR |
| D5 | Public write access | N | §14 D5 | CLEAR |
| D6 | Sensitive mass data | N | §14 D6 | CLEAR |
| D7 | Paid external hosting | N | §14 D7 | CLEAR |
| D8 | Cloud-only operation | N | §14 D8 | CLEAR |
| D9 | Vercel/Railway/SonarCloud/Kilo | N | §14 D9 | CLEAR |
| D10 | External hosting authority | N | §14 D10 | CLEAR |
| D11 | Public SaaS | N | §14 D11 | CLEAR |
| D12 | LLM as canonical state | N | §14 D12 | CLEAR |
| D13 | Platform rewrite disguised as application | N | §14 D13 | CLEAR |
| D14 | Recurring cost > `$0` | N | §14 D14 | CLEAR |

Screen status: **PASS** (0 triggers, 0 UNKNOWN, 14/14 positively evidenced). Re-screen unrevealing: candidate is read/write-local; each §14 row is a bounded single-purpose statement consistent with §§5/7.

### Required-evidence checklist (§7.2)

All ten classes present (§1–§13). `EVIDENCE-MISSING` flags: none.

### Falsification attacks (recorded findings)

| # | Attack | Finding (cited) | Effect on score |
|---|---|---|---|
| F1 | "Does corpus truth-checking add durable value, or duplicate checks the reviewing agent already runs ad hoc at every governance cycle?" | §1 specifies a single-command static validator; §2 shows success judged from per-document PASS/FAIL tables. But nothing in the packet establishes a persistent watcher: §7 places the tool in governance cycles only (operator-loopback, no daemon), and §6 confines runtime state to the local `runs/` directory. Value accrues only when an operator invokes it at governance time | C1 3→2 (confidence LOW) |
| F2 | "Are the C2 lifecycle lines mechanized or pattern-shaped?" | §3 grants/workers lines describe pattern-shaped static equivalents (capability-grant concepts applied as check-battery plans) rather than execution against any OCE runtime; the intake register labels all packet items `AUTHORED_SPEC`/unmeasured and the packet discloses static-only evidence. Eleven surfaces are enumerated and designed-for, not exercised | C2 3→2 (LOW) |
| F3 | "Is the §13 identity surface real or asserted?" | §3 identity line records the producing process identity in report headers; it does not exercise existing identity contracts or a runtime identity path — an asserted surface | C10 3→2 (LOW) |
| F4 | "Is §12 reuse supportable or unexamined?" | §12 names specific repo contracts (`infrastructure/control-plane/contracts/evidence-manifest.schema.json`, `artifact-ref.schema.json`, `schema_validator` patterns) — sufficient cited grounding; extraction risk LOW analysis is credible for a single-corpus parser; no platform-shaped surface exists | attack FAILS — C9 holds at 2 |
| F5 | "Does §8 explainability overstate?" | §8's per-check counts and exact offender-text rendering are a well-specified output contract; explanation is counted evidence, not narrative | attack FAILS — C6 holds at 3 |
| F6 | "Does the recovery scenario hold up?" | §10 resume-from-record with atomic rewrite and no-false-success is a concrete, testable mechanism; §11 registers a as-governed additive check-set change with regression | attack FAILS — C8 holds at 3 |

### Scoring (Pass B — adversarial lens)

| Criterion | Weight | Score | Evidence ref | Confidence |
|---|---:|---:|---|---|
| C1 Meaningful operator outcome | 15 | 2 | §1, §2 — outcome real (mechanized truth-checking of a corpus with a demonstrated defect class, §1 basis); discounted per F1: value accrues only at governance-time invocations, no persistent watcher in packet | LOW |
| C2 Broad OCE lifecycle coverage | 15 | 2 | §3 — surface set enumerated; pattern-shaped per F2 | LOW |
| C3 Deterministic non-LLM kernel | 12 | 3 | §4 — unbroken; strongest characteristic of this candidate | MEDIUM |
| C4 Bounded inputs and canonical state | 10 | 3 | §5, §6 — unbroken | MEDIUM |
| C5 Local operation | 10 | 3 | §7 — unbroken (HIGH) | HIGH |
| C6 Explainable outputs | 8 | 3 | §8 — unbroken (F5) | MEDIUM |
| C7 Bounded completion window | 8 | 3 | §9 (4–6 increments) | LOW |
| C8 Recovery and change-cycle coverage | 8 | 3 | §10, §11 — unbroken (F6) | MEDIUM |
| C9 Reuse without premature platform extraction | 6 | 2 | §12 — cited contracts (F4); integer unchanged from Pass A | MEDIUM |
| C10 Governed-path exercise breadth | 8 | 2 | §13 — enumerated, not mechanized (F3) | LOW |
| **Total** | **100** | | **W = 64.00** | |

Weighted arithmetic: 15·2/4=7.50, 15·2/4=7.50, 12·3/4=9.00, 10·3/4=7.50, 10·3/4=7.50, 8·3/4=6.00, 8·3/4=6.00, 8·3/4=6.00, 6·2/4=3.00, 8·2/4=4.00 → sum 64.00. **W = 64.00**.

### Threshold evaluation (§5.4)

| Condition | Result |
|---|---|
| W ≥ 70.00 (64.00) | **FAIL** |
| C1,C2,C3,C5 ≥ 2 (2/2/3/3) | PASS |
| Zero disqualifiers triggered | PASS |
| Every disqualifier question answered with cited evidence | PASS (14/14) |
| Both passes completed | YES — Pass A sealed (`b05c61d0…`), Pass B sealed (this record) |
| Operator decision boundary respected | PASS (recommendation only) |

Threshold status: **NOT-PASSED — W = 64.00 < 70.00** under the adversarial lens. Recorded with evidence; never re-scored upward (§5.4).

Pass B dissent/uncertainty (verbatim-preserved): The NOT-PASSED rests on three interpretive discounts (C1, C2, C10), each exactly one point, all of the same kind: the C2/C10/C6 lines the packet claims are authored designs, not runtime-tested mechanisms. If the operator credits designs as adequate basis while explicitly noting the missing runtime mechanism, a higher score is arguable — but under the adversarial standard, unexercised pattern-shaped surfaces do not earn Pass A's stronger integer.

---

## CAND-002

### Screen (re-run from packet §14)

| D | Item | Required? | Evidence ref | Verdict |
|---|---|---|---|---|
| D1 | Capital/execution authority | N | §14 D1 | CLEAR |
| D2 | Live trading/broker credentials | N | §14 D2 | CLEAR |
| D3 | Irreversible external effects | N | §14 D3 | CLEAR |
| D4 | Regulated submissions | N | §14 D4 | CLEAR |
| D5 | Public write access | N | §14 D5 | CLEAR |
| D6 | Sensitive mass data | N | §14 D6 | CLEAR |
| D7 | Paid external hosting | N | §14 D7 | CLEAR |
| D8 | Cloud-only operation | N | §14 D8 | CLEAR |
| D9 | Vercel/Railway/SonarCloud/Kilo | N | §14 D9 | CLEAR |
| D10 | External hosting authority | N | §14 D10 | CLEAR |
| D11 | Public SaaS | N | §14 D11 | CLEAR |
| D12 | LLM as canonical state | N | §14 D12 | CLEAR |
| D13 | Platform rewrite disguised as application | N | §14 D13 | CLEAR |
| D14 | Recurring cost > `$0` | N | §14 D14 | CLEAR |

Screen status: **PASS** (0 triggers, 0 UNKNOWN, 14/14 positively evidenced).

### Required-evidence checklist (§7.2)

All ten classes present (§1–§13). `EVIDENCE-MISSING` flags: none.

### Falsification attacks (recorded findings)

| # | Attack | Finding (cited) | Effect on score |
|---|---|---|---|
| F1 | "The §8 example's counts (39/214/197) — fact, illustration, or unmeasured?" | §8 is a format demonstration, explicitly labeled "not a measurement"; the packet's §1 cites real suites and count-carrying documents, but the specific example numbers are unmeasured illustrations quoted as though outcome-like. The claimed operator outcome has never been observed | C1 3→2 (MEDIUM) |
| F2 | "Is pattern-based claim extraction robust, or prose-boundary fragile?" | §4 states the trade-off honestly: extraction is deliberately pattern-based to keep the kernel deterministic, with corpus-rewording risk acknowledged (A recorded this too). The packet's chosen contract couples the reconciliation surface to evolving prose, where a wording change can silently change the claim set. In the adversarial worst case, the reconciliation surface can silently exchange one false reading for another under wording drift | C3 3→2 (LOW) |
| F3 | "Does the default scope survive the compose test?" | §7 flags the compose-dependent suites out of default scope, recorded explicitly either way — a real, testable boundary honoring the freeze/base commitments | C5 retained 3 — attack FAILS |
| F4 | "Does §11's regression guard the extraction live-wiring or only the report format?" | §11's suite-manifest `v2` regression covers prior manifests/formats, not extraction against prose drift (F2). The change-cycle mechanism is real but does not close the extraction fragility | C8 3→2 (LOW) |
| F5 | "Does the dual-clock timeliness check really verify freshness?" | §3's observability line is about reporting durations; the packet nowhere specifies a freshness-check mechanism verification. The FORM of a timeliness check is present; verification content is not | C6 3→2 (MEDIUM) |
| F6 | "Pattern-shaped C2/C10?" | §3/§13 assert surfaces with documented line-level roles, but same class of concern as F2 — surface-touching, not mechanism-touching | C2 3→2, C10 3→2 (LOW) |
| F7 | "Is §12 reuse supportable?" | §12 cites `job-envelope`/`lease` patterns and evidence-manifest shapes from oce_control contracts, and pytest as an existing repo-standard dependency — concrete reuse classifications | attack FAILS — C9 holds at 2 |

### Scoring (Pass B — adversarial lens)

| Criterion | Weight | Score | Evidence ref | Confidence |
|---|---:|---:|---|---|
| C1 Meaningful operator outcome | 15 | 2 | §1, §2 — outcome design credible; discounted per F1 (§8 example counts are format illustration, no measured outcome claim to pass on) | MEDIUM |
| C2 Broad OCE lifecycle coverage | 15 | 2 | §3 — surfaced, not mechanized (F6) | LOW |
| C3 Deterministic non-LLM kernel | 12 | 2 | §4 — kernel is deterministic by construction, but the claim-extraction surface is a fragile fixed pattern contract over evolving prose (F2), the packet's own principal fragility | LOW |
| C4 Bounded inputs and canonical state | 10 | 2 | §5, §6 — closed suite set plus fixed claim corpus; but the factual a priori claim corpus is prose that drifts, so extraction mapping must follow every wording evolution (F2) | MEDIUM |
| C5 Local operation | 10 | 3 | §7 — unbroken (HIGH) (F3) | HIGH |
| C6 Explainable outputs | 8 | 2 | §8 — rows quote claim text and measured counts for rendered rows, but the timeliness/false-negative handling is a proposed mechanism whose verification content the packet does not specify (F5) | MEDIUM |
| C7 Bounded completion window | 8 | 3 | §9 (4–6 increments; highest test-execution burden in the set, honestly stated) | LOW |
| C8 Recovery and change-cycle coverage | 8 | 2 | §10, §11 — per-suite resume and additive suite-manifest change are real, but the regression guards report format, not extraction robustness under corpus drift (F4) | LOW |
| C9 Reuse without premature platform extraction | 6 | 2 | §12 — cited contracts and existing dependencies (F7); integer unchanged from Pass A | MEDIUM |
| C10 Governed-path exercise breadth | 8 | 2 | §13 — surfaced, not mechanized (F6) | LOW |
| **Total** | **100** | | **W = 54.50** | |

Weighted arithmetic: 7.50, 7.50, 6.00, 5.00, 7.50, 4.00, 6.00, 4.00, 3.00, 4.00 → sum 54.50. **W = 54.50**.

### Threshold evaluation (§5.4)

| Condition | Result |
|---|---|
| W ≥ 70.00 (54.50) | **FAIL** |
| C1,C2,C3,C5 ≥ 2 (2/2/2/3) | PASS |
| Zero disqualifiers triggered | PASS |
| Every disqualifier question answered with cited evidence | PASS (14/14) |
| Both passes completed | YES |
| Operator decision boundary respected | PASS |

Threshold status: **NOT-PASSED — W = 54.50 < 70.00** under the adversarial lens. Recorded with evidence; never re-scored upward (§5.4).

Pass B dissent/uncertainty (verbatim-preserved): The NOT-PASSED rests substantially on the unmeasured example counts (F1), the prose-coupled extraction surface (F2/F4), and the induction-on-unread-observed-verification trade (F5). If the operator judges the extraction contract as governable and the §8 counts as acceptable illustrations, a materially higher profile is arguable; per §5.4 the scoring was not changed upward to reach the threshold.

---

## CAND-003

### Screen (re-run from packet §14)

| D | Item | Required? | Evidence ref | Verdict |
|---|---|---|---|---|
| D1 | Capital/execution authority | N | §14 D1 | CLEAR |
| D2 | Live trading/broker credentials | N | §14 D2 | CLEAR |
| D3 | Irreversible external effects | N | §14 D3 | CLEAR |
| D4 | Regulated submissions | N | §14 D4 | CLEAR |
| D5 | Public write access | N | §14 D5 | CLEAR |
| D6 | Sensitive mass data | N | §14 D6 | CLEAR |
| D7 | Paid external hosting | N | §14 D7 | CLEAR |
| D8 | Cloud-only operation | N | §14 D8 | CLEAR |
| D9 | Vercel/Railway/SonarCloud/Kilo | N | §14 D9 | CLEAR |
| D10 | External hosting authority | N | §14 D10 | CLEAR |
| D11 | Public SaaS | N | §14 D11 | CLEAR |
| D12 | LLM as canonical state | N | §14 D12 | CLEAR |
| D13 | Platform rewrite disguised as application | N | §14 D13 | CLEAR |
| D14 | Recurring cost > `$0` | N | §14 D14 | CLEAR |

Screen status: **PASS** (0 triggers, 0 UNKNOWN, 14/14 positively evidenced).

### Required-evidence checklist (§7.2)

All ten classes present (§1–§13). `EVIDENCE-MISSING` flags: none.

### Falsification attacks (recorded findings)

| # | Attack | Finding (cited) | Effect on score |
|---|---|---|---|
| F1 | "Do these checks add value over what the reviewing agent already executes manually in every governance cycle?" | §1 mechanizes an existing, already-specified reality-lock battery (the packet's own §9 basis); §8 shows exact declared-vs-observed quoting, a real operator economy in table form. Value is real, though incremental over existing manual practice | C1 retained 3 — attack FAILS |
| F2 | "Are the C2 lifecycle claims mechanized or pattern-shaped?" | §3 checks-as-jobs is a pattern-shaped analogy; the oce_control module inventory exists but the packet cites no accepted commit, no module, no probe, no test run for this candidate's own execution surface. Enumeration without mechanization | C2 3→2 (LOW) |
| F3 | "Decisive S-1 fresh-clone exercise over a declared arbitrary remote — mechanized or surface-invocation?" | §13 identity path is a surface invocation; no supplied `--fullHistory`-style probe, no per-revision mechanism, no determinism/freshness test against existing evidence. The packet asserts the lineage check exists; it does not demonstrate one | C10 3→2 (LOW) |
| F4 | "Is §12 reuse supportable?" | §12 cites reality-lock procedures from authorizations as check specifications and the secret-pattern set from B5-I0 validation as reusable assets — a concrete, non-exhaustive but checkable reuse map | attack FAILS — C9 retained 2 |
| F5 | "Does the strongest §9 basis in the set hold?" | §9's 3–5 intermediate increments in the suite rest on today-already-executed manual checks — the most grounded §9 in the candidate set | C7 retained 3 — attack FAILS |

### Scoring (Pass B — adversarial lens)

| Criterion | Weight | Score | Evidence ref | Confidence |
|---|---:|---:|---|---|
| C1 Meaningful operator outcome | 15 | 3 | §1, §2 — strongest outcome-grounding of the console candidates; reality-lock practice already operator-recognized | MEDIUM |
| C2 Broad OCE lifecycle coverage | 15 | 2 | §3 — surfaced, not mechanized (F2) | LOW |
| C3 Deterministic non-LLM kernel | 12 | 3 | §4 — strongest determinism posture in the set (git plumbing outputs; fixed regex census) | HIGH |
| C4 Bounded inputs and canonical state | 10 | 3 | §5, §6 — unbroken; content-addressed, replayable audit packs | HIGH |
| C5 Local operation | 10 | 3 | §7 — unbroken (HIGH; default scope excludes network-level checks) | HIGH |
| C6 Explainable outputs | 8 | 3 | §8 — declared-vs-observed quoting on every row | MEDIUM |
| C7 Bounded completion window | 8 | 3 | §9 — strongest basis in the set (F5) | MEDIUM |
| C8 Recovery and change-cycle coverage | 8 | 3 | §10, §11 — unbroken mechanisms | MEDIUM |
| C9 Reuse without premature platform extraction | 6 | 2 | §12 — concrete reuse citations (F4) | MEDIUM |
| C10 Governed-path exercise breadth | 8 | 2 | §13 — surfaced, not mechanized (F3) | LOW |
| **Total** | **100** | | **W = 67.75** | |

Weighted arithmetic: 11.25, 7.50, 9.00, 7.50, 7.50, 6.00, 6.00, 6.00, 3.00, 4.00 → sum 67.75. **W = 67.75**.

### Threshold evaluation (§5.4)

| Condition | Result |
|---|---|
| W ≥ 70.00 (67.75) | **FAIL** (2.25 below) |
| C1,C2,C3,C5 ≥ 2 (3/2/3/3) | PASS |
| Zero disqualifiers triggered | PASS |
| Every disqualifier question answered with cited evidence | PASS (14/14) |
| Both passes completed | YES |
| Operator decision boundary respected | PASS |

Threshold status: **NOT-PASSED — W = 67.75 < 70.00** under the adversarial lens. Recorded with evidence; never re-scored upward (§5.4).

Pass B dissent/uncertainty (verbatim-preserved): The 2.25 shortfall is entirely attributable to the C2/C10 discounts (each exactly 1 integer, and the −5.75 W effect), both resting on surfaced-not-mechanized enumeration rather than feasibility. A single cited probe/test example per §3/§13 would plausibly restore both to Pass A's reading; that evidence does not exist in the frozen packet, so the score stands as recorded.

---

## CAND-004

### Screen (re-run from packet §14)

| D | Item | Required? | Evidence ref | Verdict |
|---|---|---|---|---|
| D1 | Capital/execution authority | N | §14 D1 (catalog = representative test workloads only, `REPO_ASSET`) | CLEAR |
| D2 | Live trading/broker credentials | N | §14 D2 (governance jobs only; no broker integrations in contracts/catalog, `REPO_ASSET`) | CLEAR |
| D3 | Irreversible external effects | N | §14 D3 (local job-state transitions; drills restore state) | CLEAR |
| D4 | Regulated submissions | N | §14 D4 | CLEAR |
| D5 | Public write access | N | §14 D5 (loopback-only client) | CLEAR |
| D6 | Sensitive mass data | N | §14 D6 (catalog payloads, `REPO_ASSET`) | CLEAR |
| D7 | Paid external hosting | N | §14 D7 (local compose) | CLEAR |
| D8 | Cloud-only operation | N | §14 D8 (explicitly local; fails closed without stack) | CLEAR |
| D9 | Vercel/Railway/SonarCloud/Kilo | N | §14 D9 | CLEAR |
| D10 | External hosting authority | N | §14 D10 (local operator machine is the authority) | CLEAR |
| D11 | Public SaaS | N | §14 D11 | CLEAR |
| D12 | LLM as canonical state | N | §14 D12 (canonical state remains the control plane's schema-validated stores) | CLEAR |
| D13 | Platform rewrite disguised as application | N | §14 D13 ("client, not second authority" rule) | CLEAR |
| D14 | Recurring cost > `$0` | N | §14 D14 | CLEAR |

Screen status: **PASS** (0 triggers, 0 UNKNOWN, 14/14 positively evidenced).

### Required-evidence checklist (§7.2)

All ten classes present (§1–§13). `EVIDENCE-MISSING` flags: none.

### Falsification attacks (recorded findings)

| # | Attack | Finding (cited) | Effect on score |
|---|---|---|---|
| F1 | "Is the D-row evidence grade uniform?" | D1/D2/D6 cite specific repo facts (representative_jobs.py catalog, contracts); other rows are packet-authored local-only statements of two grades — both grades evidenced differently but no grade is unevidenced | no change |
| F2 | "Is the optional local web view a time-bomb public surface?" | §7 keeps the optional view loopback-only for a read-only local UI, and §5/§6 keep it read-only and loopback-only. The risk is recorded for build-time verification (B5-I4+); no score-carrying defect is found in the packet text | C5 retained 3 |
| F3 | "Is the 'client, not second authority' anti-extraction rule actually enforced or just claimed?" | §12 names the mitigation, §6 designs console-local state as append-only session JSON while the control plane remains canonical, and §11's change-cycle regression (control-plane tests unchanged, contract-validated rendering) makes the claim build-time-verifiable. Accepted as designed-for; must be verified at build time (B5-I4+) | C9 retained 3 |
| F4 | "Does the S-4 fail-closed claim extend beyond simple request rejection?" | §5 'No direct database access — all reads go through the control plane's own API/contracts' plus §10's fail-closed STACK_UNREACHABLE posture keep the console a strict contract-validating client with no out-of-band path — the strongest such posture in the candidate set | C4 retained 3 |
| F5 | "Does §8 truly quote, or narrate?" | §8's timeline quotes the control plane's own event records; §10's recovery drill is corroborated by the existing control-plane recovery/adversarial test suites as executable ground, the packet's strongest corroboration | C6 retained 3, C8 retained 4 |

### Scoring (Pass B — adversarial lens)

| Criterion | Weight | Score | Evidence ref | Confidence |
|---|---:|---:|---|---|
| C1 Meaningful operator outcome | 15 | 3 | §1, §2 — retained; live visibility + drill + denial-envelope rendering over a real control plane | MEDIUM |
| C2 Broad OCE lifecycle coverage | 15 | 4 | §3 — direct exercise of the real worker fabric (leases/heartbeats/supervision), corroborated by the existing 36-module control plane and ~24 test files | MEDIUM |
| C3 Deterministic non-LLM kernel | 12 | 3 | §4 — unbroken (F4); job semantics correctly remain with the control plane | MEDIUM |
| C4 Bounded inputs and canonical state | 10 | 3 | §5, §6 — unbroken (F4); control plane remains canonical | MEDIUM |
| C5 Local operation | 10 | 3 | §7 — unbroken; fail-closed when stack absent (F2) | MEDIUM |
| C6 Explainable outputs | 8 | 3 | §8 — unbroken (F5) | MEDIUM |
| C7 Bounded completion window | 8 | 3 | §9 — 6–8 increments, honestly stated with integration-risk basis; longest window in the set | LOW |
| C8 Recovery and change-cycle coverage | 8 | 4 | §10 — recovery is the product's core scenario, corroborated by existing recovery suites as executable ground (F5) | MEDIUM |
| C9 Reuse without premature platform extraction | 6 | 3 | §12 — highest grounded reuse in the set; bounded with named build-time-verifiable mitigation (F3) | MEDIUM |
| C10 Governed-path exercise breadth | 8 | 4 | §13 — direct exercise of the real governed path, not pattern-shaped equivalents | MEDIUM |
| **Total** | **100** | | **W = 82.75** | |

Weighted arithmetic: 11.25, 15.00, 9.00, 7.50, 7.50, 6.00, 6.00, 8.00, 4.50, 8.00 → sum 82.75. **W = 82.75**.

### Threshold evaluation (§5.4)

| Condition | Result |
|---|---|
| W ≥ 70.00 (82.75) | PASS |
| C1,C2,C3,C5 ≥ 2 (3/4/3/3) | PASS |
| Zero disqualifiers triggered | PASS |
| Every disqualifier question answered with cited evidence | PASS (14/14) |
| Both passes completed | YES |
| Operator decision boundary respected | PASS |

Threshold status: **PASSES §5.4 CONDITIONS 1–5 — W = 82.75** under the adversarial lens. (Recommendation only; the operator decides.)

Pass B dissent/uncertainty (verbatim-preserved): No adversarial attack found a score-carrying defect; residual risks are recorded for build time — the loopback-only guarantee on the optional web view (F2), the build-time enforcement of "client, not second authority" (F3), and the honest longest completion window (§9, LOW confidence). The agreement between Pass A and Pass B here is a non-blind same-lens observation, not corroboration.

---

## CAND-005

### Screen (re-run from packet §14)

| D | Item | Required? | Evidence ref | Verdict |
|---|---|---|---|---|
| D1 | Capital/execution authority | N | §14 D1 | CLEAR |
| D2 | Live trading/broker credentials | N | §14 D2 (processes audit CSVs about credential-access events as inert data; holds/uses no credentials) | CLEAR |
| D3 | Irreversible external effects | N | §14 D3 (read-only over artifacts; writes only `out/`) | CLEAR |
| D4 | Regulated submissions | N | §14 D4 | CLEAR |
| D5 | Public write access | N | §14 D5 | CLEAR |
| D6 | Sensitive mass data | N | §14 D6 (fixed in-repo artifact set) | CLEAR |
| D7 | Paid external hosting | N | §14 D7 | CLEAR |
| D8 | Cloud-only operation | N | §14 D8 | CLEAR |
| D9 | Vercel/Railway/SonarCloud/Kilo | N | §14 D9 | CLEAR |
| D10 | External hosting authority | N | §14 D10 | CLEAR |
| D11 | Public SaaS | N | §14 D11 | CLEAR |
| D12 | LLM as canonical state | N | §14 D12 | CLEAR |
| D13 | Platform rewrite disguised as application | N | §14 D13 (single artifact family, single-purpose checks) | CLEAR |
| D14 | Recurring cost > `$0` | N | §14 D14 | CLEAR |

Screen status: **PASS** (0 triggers, 0 UNKNOWN, 14/14 positively evidenced).

### Required-evidence checklist (§7.2)

All ten classes present (§1–§13). `EVIDENCE-MISSING` flags: none.

### Falsification attacks (recorded findings)

| # | Attack | Finding (cited) | Effect on score |
|---|---|---|---|
| F1 | "Does the 'workbench' title hide scope creep?" | §12 pre-empts the threat: "single artifact family, single-purpose checks"; D13 is captured by the packet's own §0 distinction and bounded scope; §5 is a fixed 15-file artifact family with fixed column contracts | attack FAILS — C9 retained 2 |
| F2 | "Are §3/§13 surfaces mechanized or surfaced?" | Same class as CAND-001/002/003: §3 grants/workers/identity lines are pattern-shaped designs with no runtime test citations for this candidate; enumeration without mechanization | C2 3→2, C10 3→2 (LOW) |
| F3 | "Does S-1 on the real artifact set prove operability?" | §2 S-1 runs over the real `tv_vm_audit/` set (REPO_ASSET, the strongest §1 grounding among the non-console candidates), but the outcome is designed-for, not measured: §8's example is explicitly 'not a measurement' and no run has ever executed. Honest labeling limits the S-1 claim accordingly | C1 retained 3 |
| F4 | "Does the BLOCK-state subsection in §8 degrade C-explainability?" | §8's flag-of-provenance field-locating manner (real citizen-visible counts+offending-row quoting) is the design target; the BLOCK is a conservative posture per the packet's own zero-UNKNOWN discipline. No defect is found | C6 retained 3 |
| F5 | "Is S-5 cross-document reconciliation still worth C8's integer?" | §11 profile-v2 additive change + regression holds against the S-5 improvement, and §10's partial-record discipline directly supports it | C8 retained 3 |

### Scoring (Pass B — adversarial lens)

| Criterion | Weight | Score | Evidence ref | Confidence |
|---|---:|---:|---|---|
| C1 Meaningful operator outcome | 15 | 3 | §1, §2 — QA over a complete real artifact set (REPO_ASSET); real gap closed | MEDIUM |
| C2 Broad OCE lifecycle coverage | 15 | 2 | §3 — surfaced, not mechanized (F2) | LOW |
| C3 Deterministic non-LLM kernel | 12 | 3 | §4 — held (F3 postures the assumptions honestly) | MEDIUM |
| C4 Bounded inputs and canonical state | 10 | 3 | §5, §6 — held | MEDIUM |
| C5 Local operation | 10 | 3 | §7 — unbroken (HIGH) | HIGH |
| C6 Explainable outputs | 8 | 3 | §8 — held (F4) | MEDIUM |
| C7 Bounded completion window | 8 | 3 | §9 (4–6 increments; narrow fixed-schema domain) | LOW |
| C8 Recovery and change-cycle coverage | 8 | 3 | §10, §11 — held (F5) | MEDIUM |
| C9 Reuse without premature platform extraction | 6 | 2 | §12 — bounded, single-family; nothing platform-shaped (F1) | MEDIUM |
| C10 Governed-path exercise breadth | 8 | 2 | §13 — surfaced, not mechanized (F2) | LOW |
| **Total** | **100** | | **W = 67.75** | |

Weighted arithmetic: 11.25, 7.50, 9.00, 7.50, 7.50, 6.00, 6.00, 6.00, 3.00, 4.00 → sum 67.75. **W = 67.75**.

### Threshold evaluation (§5.4)

| Condition | Result |
|---|---|
| W ≥ 70.00 (67.75) | **FAIL** |
| C1,C2,C3,C5 ≥ 2 (3/2/3/3) | PASS |
| Zero disqualifiers triggered | PASS |
| Every disqualifier question answered with cited evidence | PASS (14/14) |
| Both passes completed | YES |
| Operator decision boundary respected | PASS |

Threshold status: **NOT-PASSED — W = 67.75 < 70.00** under the adversarial lens. Recorded with evidence; never re-scored upward (§5.4).

Pass B dissent/uncertainty (verbatim-preserved): The two discounts (C2, C10; each exactly 1) rest entirely on surfaced-not-mechanized coverage — the same class of finding as for the other console candidates. The candidate's factual grounding (real artifact set, D2 inert-data posture with the strongest evidence grade) survived the adversarial pass; a single cited probe/test example per §3/§13 would plausibly lift both integers back to Pass A's reading, but that evidence does not exist in the frozen packet.

---

## Per-candidate threshold summary (Pass B only — no ranking expressed)

| Candidate | Screen | W | Floors C1/C2/C3/C5 | EVIDENCE-MISSING | Pass B threshold result |
|---|---|---:|---|---:|---|
| CAND-001 | PASS (0/14, 0 UNKNOWN) | 64.00 | 2/2/3/3 | 0 | NOT-PASSED (W < 70.00) |
| CAND-002 | PASS (0/14, 0 UNKNOWN) | 54.50 | 2/2/2/3 | 0 | NOT-PASSED (W < 70.00) |
| CAND-003 | PASS (0/14, 0 UNKNOWN) | 67.75 | 3/2/3/3 | 0 | NOT-PASSED (W < 70.00) |
| CAND-004 | PASS (0/14, 0 UNKNOWN) | 82.75 | 3/4/3/3 | 0 | PASSES conditions 1–5 (W + floors + screen + evidence + both passes) |
| CAND-005 | PASS (0/14, 0 UNKNOWN) | 67.75 | 3/2/3/3 | 0 | NOT-PASSED (W < 70.00) |

Tie-break record (§7.5): NOT APPLICABLE at pass level. No tie-break was applied in this scorecard.

Recommendation-packet fields (§8) and operator decision (§9): intentionally absent — produced at reconciliation (recommendation only) and by the operator only.

## Amendment log (§10)

| Amendment ID | Clause changed | Trigger | Candidate results visible at change? | Operator ratified? | Re-scored under new version? |
|---|---|---|---|---|---|
| B5-I0-AMEND-001 | Protocol §7.9 execution mechanism → sequential dual pass | Operator declined additional chats/agents/external reviewers | NO | YES (2026-10-07) | N/A — first scoring under the amendment |

## Score-change immutability attestation (§11)

| Field | Entry |
|---|---|
| Scores edited after submission? | NO — this file is sealed at first submission; corrections require a new sealed artifact with the superseded seal recorded |
| Attested by | Pass B scorer (same agent as intake author and Pass A scorer, per AMEND-001) |

---

*End of Pass B scorecard. Contains no ranking, no recommendation, no selection, no working names, no product scope, no code.*
