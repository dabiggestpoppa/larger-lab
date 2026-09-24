# CSIA Book 2 — Source Authority Matrix — v0.2

Status: RATIFICATION CANDIDATE
Companion to: `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.2.md`
Supersedes for planning: `CSIA_BOOK_2_SOURCE_AUTHORITY_MATRIX_v0.1.md`
Preserved unchanged: v0.1
Operator decision: D2-5 (`CLAIM_FAMILY_SCOPED_TRUST_DOWNGRADE`)

## 1. Authority key

Source authority is evaluated only at the proposition-specific key:

```text
SOURCE × CLAIM_FAMILY × VALID_TIME
```

It is **not**:

```text
SOURCE → ONE GLOBAL TRUST SCORE
```

A source may be primary for one claim family and supporting or inadmissible
for another in the same valid-time window. Authority is a versioned decision,
not an intrinsic scalar attached permanently to a source.

## 2. Claim-family matrix

Preferred classes carry primary authority only for the proposition in the
named family and valid-time window. Supporting classes may corroborate but
do not replace the required primary evidence. “Never sufficient alone” is a
hard promotion exclusion.

| Claim family | Preferred evidence classes | Supporting | Never sufficient alone | Default freshness |
|---|---|---|---|---|
| CHAIN ARCHITECTURE | NATIVE_TECHNICAL specs; source REPOSITORY; official docs | ACADEMIC; SECURITY_AUDIT | NEWS; SOCIAL; AGGREGATOR | supersession-oriented |
| DEPLOYMENT / ACTIVATION | RPC; verified deployed-contract state; post-lag EXPLORER | first-party announcement as timing context | press releases; AGGREGATOR; SOCIAL | SHORT default policy |
| GOVERNANCE EXECUTION | on-chain governance state; executed on-chain change | GOVERNANCE forum; official docs for phase context | forum sentiment; NEWS | event-driven |
| GOVERNANCE PROPOSAL | GOVERNANCE proposal text and vote state | NEWS/SOCIAL only for narrative existence | nothing proves execution except execution | event-driven |
| INTEGRATION | deployed integration state (RPC/verified contract/explorer) plus first-party confirmation | official docs of both parties | announcements; AGGREGATOR; NEWS | MEDIUM default policy |
| NARRATIVE | NEWS; SOCIAL; interviews; official blog | AGGREGATOR for existence/context only | structural proposition embedded in narrative | fast-decay default policy |
| SECURITY EVENT | exploit transactions/chain state; incident report; SECURITY_AUDIT; postmortem | official comms; STATUS_SYSTEM | SOCIAL rumor; NEWS alone | event-driven |
| TOKEN ROLE / MECHANICS | protocol specification plus deployed mechanics | REPOSITORY; governance records | AGGREGATOR; SOCIAL | MEDIUM; spec supersession |
| BRIDGE / ROUTE STATE | deployed route state (RPC/verified explorer) | STATUS_SYSTEM; official docs | NEWS; SOCIAL | SHORT–MEDIUM default policy |
| VALIDATOR SET / EPOCH STATE | chain state (RPC/epoch queries) | explorer; chain-specific dashboards | NEWS | chain-specific policy |
| HISTORICAL GENESIS / SPEC | genesis data; original specs; archival captures | ACADEMIC | time alone | historical; supersession, never automatic stale |
| IDENTITY ATTRIBUTES | first-party docs; REPOSITORY; verified listings | AGGREGATOR subject to S-4 | unverified SOCIAL | MEDIUM default policy |
| MARKET DATA | no structural authority | AGGREGATOR; exchanges | every source for structural graph truth | fast-decay; out of structural scope |

Concrete numeric windows and usage/health thresholds are not frozen by this
matrix. Policy defaults may be tuned and versioned during later authorized
implementation planning; no universal stale window exists.

## 3. Binding cross-family rules

- **A-1 — dual-key docs/deployed-state doctrine.** For “what IS,” deployed
  state outranks documentation; for “what is SPECIFIED,” documentation
  outranks deployed state. Neither universally wins. Both evidence lines and
  their valid-time semantics are preserved.
- **A-2 — aggregator limitation.** AGGREGATOR evidence may corroborate
  identity attributes and contextual/narrative propositions. It may never be
  sole authority for structural graph truth.
- **A-3 — narrative limitation.** NEWS/SOCIAL may establish that a narrative
  exists. It cannot directly promote the structural proposition embedded in
  that narrative.
- **A-4 — RPC/explorer distinction.** RPC and EXPLORER both observe chain
  state, but RPC is primary. Explorer lag or disagreement is preserved and
  routed through contradiction handling with lag awareness.
- **A-5 — source registration requirement.** An unregistered source cannot
  contribute authority at any tier. No “obviously true” exception exists.

## 4. D2-5 documentation-versus-deployed-state procedure

When documentation and deployed state disagree:

1. Preserve both raw evidence lines and their source/claim versions.
2. Classify the immediate proposition into a claim family.
3. Resolve that factual proposition using the authority tier for
   `SOURCE × CLAIM_FAMILY × VALID_TIME`; do not use recency or source count
   as a substitute.
4. Create an evidence-backed discrepancy meta-claim that names both claims,
   both evidence lines, the selected proposition, and the resolution rule.
5. Append the event to discrepancy history for that source and claim family.
6. Do not globally demote the source because of one discrepancy.
7. Repeated demonstrated unreliability may justify a downgrade only for the
   specific claim family and valid-time scope supported by that evidence.
8. A downgrade must be evidence-backed, temporally versioned, and reversible.
9. A persistent authority-tier change requires operator review.
10. A later correction or successful revalidation may restore the prior tier
    through a new version; history is never erased.
11. No opaque global source trust score exists.

Example: repeated activation-timing errors may lower a source's authority
for DEPLOYMENT / ACTIVATION while preserving its authority for SPECIFICATION,
GOVERNANCE INTENT, and HISTORICAL DOCUMENTATION. The downgrade is not a
judgment that the source is globally unreliable.

## 5. Versioned authority decisions

Each authority resolution must be reconstructable as:

```text
authority_decision_id
source_id
claim_family
proposition_scope
valid_time_interval
effective_transaction_time
tier_before
tier_after
supporting_evidence_refs
discrepancy_meta_claim_refs
policy_version
operator_review_ref (required for persistent tier change)
supersedes_authority_decision_id
reason_code
```

An authority change is effective only for its recorded valid-time and
transaction-time scope. Historical graph facts retain the authority decision
and policy version pinned when they were promoted; later changes do not
rewrite that history. A reversible downgrade creates a successor authority
decision rather than mutating or deleting the prior one.

## 6. D2-1 source-class ratification

The 14 classes are ratified without change:

```text
NATIVE_TECHNICAL NATIVE_OPERATIONAL REPOSITORY RPC EXPLORER
GOVERNANCE STATUS_SYSTEM DATASET SECURITY_AUDIT ACADEMIC ANALYTICS
AGGREGATOR NEWS SOCIAL
```

Authority still depends on claim family and valid time. Class membership is
not a global rank.

## 7. D2-6 announced / deployed / used

The matrix preserves three distinct propositions:

```text
ANNOUNCED  → narrative/announcement existence
DEPLOYED   → deployed-state structural existence
USED       → empirically observed usage/activity
```

Evidence for one does not automatically promote another. Concrete USED and
health thresholds are deferred to a later explicitly authorized empirical
implementation-planning phase; this matrix intentionally does not invent
them.

## 8. Promotion and research-system firewall

- Structural promotion still requires evidence at the family-specific tier
  defined here.
- Source count cannot substitute for authority or independence.
- Research Mesh, QCAE, and OCE outputs enter only as registered sources,
  raw evidence, DECLARED claims, or corroborating material under Book 2.
- None of those systems can directly edit authority tiers, promote claims,
  or create graph facts.
- A family-scoped downgrade never authorizes a research system to promote.

## 9. v0.1 → v0.2 changelog

- Preserved all 13 claim families and the A-1..A-5 cross-family rules.
- Made `SOURCE × CLAIM_FAMILY × VALID_TIME` the mandatory authority key.
- Prohibited a global opaque trust score and single-discrepancy global
  demotion.
- Added the eleven-step D2-5 discrepancy and downgrade procedure.
- Added a reconstructable, temporally versioned, reversible authority-decision
  record and persistent-change operator-review requirement.
- Recorded D2-1's 14-class ratification and D2-6's three-way distinction
  while leaving usage/health parameters explicitly deferred.
