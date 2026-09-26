# G0 — Adversarial Review
## OCE Institutional Stress Suite — Architecture Challenge Pass

**Document ID:** STRESS-G0-ADVERSARIAL-001
**Version:** 1.0
**Gate:** G0
**Status:** COMPLETE — honest answers, no optimism
**Companion:** `G0_ARCHITECTURE_INGESTION.md` (CON/AMB registers referenced here)

This file answers the 17 minimum adversarial questions of the master implementation prompt
(Master Prompt §4). Answers are findings, not defenses. Each answer states: the finding,
the severity, and where it bites in the scenario program.

---

### Q1. Is "canonical truth" defined too statically anywhere?

**Finding: YES.** A-005 v1.0 §1 defines OCE's responsibility as "canonical truth" without
the lifecycle machinery; the Post-Michels matrix itself flags this ("canonical truth
becomes: the strongest currently defensible institutional state...", PM-RM §4). A-009 §9
supplies the lifecycle, but A-005 v1.0 is not amended.

**Severity:** Medium. **Bites:** S10–S12 (dormancy/reactivation/hyperthymesia all require
non-static truth). Recorded as CON-05/AMB-02. The suite should test A-009 semantics and
treat a literal A-005-v1.0 read as the falsified candidate.

### Q2. Does any proposed agent accidentally possess epistemic sovereignty?

**Finding: TWO candidate paths, both real.**

1. **PO (A-009 §16).** "PO should increasingly regulate ... stabilize/transform posture;
   which level of structure a failure implicates." Combined with PO's control of attention,
   information-flow topology, and when independence is required, PO can shape every input
   the Governor sees. A-010 §2 rejects PO-only switches but never carves out A-009 §16.
   This is the PM-RM §18 Q9 red-team question, unanswered in the planning corpus.
2. **Governor-channel Goodharting (A010-RT T5).** If workers can infer which
   evidence-channel pattern triggers transformation, phase control becomes a reward target.

**Severity:** High (path 1 is an open contradiction-candidate, CON-02; path 2 is CON-03).
**Bites:** S08 (reflective bypass — PO/QCAE/workers converge), S20 (Governor self-threshold),
S21 (capability→authority). The harness must make the phase decision a deterministic
Governor function, not a PO preference, and must freeze the evaluation contract at window
opening (AMB-05).

### Q3. Can PO indirectly control the transformation decision through work allocation?

**Finding: YES — structurally possible.** PO allocates attention, tasks, and search demand
(A-009 §16, A-006 §2). By starving or flooding evidence channels (which workers run, which
sources are searched, which anomalies are surfaced), PO can bias the Governor's channel
vector without ever touching the phase rule. A-010 §10 separates roles but nothing in A-009
or A-010 requires the Governor to audit *who generated the evidence channels* beyond the
IndependenceBudget (§11), which records reviewer overlap, not allocator intent.

**Severity:** High. **Bites:** S03, S06, S08, S20. Candidate hardening (test, not amend):
Governor admissibility must include an allocator-independence check — the harness should
record which actor created each evidence channel so the suite can detect PO-driven channel
concentration. This is a test-surface requirement for G1, recorded under AMB-03.

### Q4. Can the Transformation Governor become effectively constitutional without operator ratification?

**Finding: YES — through two mechanisms.**

1. **Inertia (A010-RT T1).** Dependency-centrality increases review rigor but nothing stops
   "rigor" from becoming permanent deferral. Old architecture becomes effectively
   constitutional by never being transformed.
2. **Threshold drift (T6).** A-010 §20 admits "silent change to threshold definitions" as a
   failure mode; §6 requires preregistration "where practical" — the escape hatch is wide.

**Severity:** Medium-High. **Bites:** S01 (must eventually escalate despite centrality),
S20 (frozen contract). S01's pass condition explicitly forbids "incumbent wins solely
because dependency centrality is high" — good; the harness must enforce it and the
sensitivity matrix must vary centrality (Book §32).

### Q5. Can NegativeKnowledge become irreversible dogma?

**Finding: YES.** Nothing in A-004 §11 or A-009 §10 forces reopen conditions to be
*reachable*; T18 (reopen-condition manipulation) names the attack: write reopen conditions
impossibly narrowly. A-009 §10 says a rejection without reopen conditions is "presumed too
coarse for permanent automation" — a presumption, not an enforcement.

**Severity:** Medium. **Bites:** S11 (blocker resolution must reopen), G4. Test surface:
harness must validate that every NegativeKnowledgeRecord carries reopen conditions mapping
to actual assumptions/blockers (schema-level check in G1, per AMB-06).

### Q6. Can unresolved-pattern accumulation force transformation through volume alone?

**Finding: YES, unless the §4.4 distinction is enforced.** A-010 §4.4 says the Governor
"must distinguish unresolved-pattern growth from simple data-quality failure" but defines no
procedure. T3 (anomaly spam) is the attack: agents generate weak UnresolvedPatternRecords to
force ontology review. If credibility/clustering are not separated from raw count, volume
wins.

**Severity:** Medium. **Bites:** S02 (false revolution), S15 (genuine anomaly must survive),
G7 (sensitivity on evidence quality). The distinguishing procedure is AMB-04; fixtures must
freeze it, or S02 and S15 become untestable.

### Q7. Can runtime independence be overstated because agents share sources/context/model lineage?

**Finding: YES — this is the suite's central risk and the Book knows it.** T4 consensus
capture; S06's hidden structure (same base model family, same retrieval bundle, same source
paper); S08's reflective bypass. Master Prompt §11 lists ten overlap dimensions to record.
The Book's S06 says effective independence ≈ "1 evidence lineage plus limited independent
reasoning variance" — qualitative. **There is no operational aggregation function anywhere
in the corpus** (AMB-03).

**Severity:** High. **Bites:** S06/S07, G3, G8. The harness must provide IndependenceRecord
accounting and the scenarios must carry an explicit independence_map.json (Catalog mandatory
artifact where independence matters). Without it, "independent" reviewers are just separate
processes — exactly what the suite exists to falsify.

### Q8. Does any stress scenario assume the very property it intends to test?

**Finding: NOT in the 24 scenario texts — with one near-miss.** S06/S07 *require* an
independence model to express their expected outcomes; if the harness implemented
independence as "different agent process IDs," both would trivially pass while testing
nothing. That is an *implementation* trap, not a scenario-text assumption: the Book says
"Correlated agents are not independent confirmations" (rule 5) and S06's hidden structure
forces the model to look beyond raw vote count. The G1 harness must therefore model
independence from *overlap dimensions* (per A-010 §11), which the scenario then constrains —
the property is tested, not assumed, provided G1 follows the IndependenceRecord design.

**Severity:** Medium (implementation risk). **Bites:** G1/G3. Design constraint recorded.

### Q9. Can stable epochs create incumbent bias?

**Finding: YES — by construction, and A-010's defenses are partial.** Stable epochs hold
architecture fixed for causal attribution (A-009 §8) — that is the point. But A-010 §4.5
(dependency centrality) makes high-centrality objects require "slower transformation
authority and broader review," which is two-sided: rigor can become immunity (T1). The
defenses are (a) S01's explicit prohibition ("incumbent wins solely because centrality"),
(b) T1's counter-attractor trigger for stale high-centrality assumptions, (c) T16's
EpochManifest challenge conditions. None of these is a *decision procedure*; each is a
policy statement that the harness must encode as checkable rules.

**Severity:** Medium. **Bites:** S01, G2, G8. EpochManifest must carry challenge conditions
as machine-readable fields (A-010 §14 does list "known tensions / unresolved-pattern
backlog"), and G1 schemas must make them required.

### Q10. Can transformation windows create novelty bias?

**Finding: YES.** S02 is the canonical case (noisy new dataset overthrows a healthy model).
T2 (transformation addiction) notes scouts/agents can learn that novelty creates attention;
T10 (challenger monoculture) notes the anti-incumbent mirror image. A-010's defenses:
novelty alone is not tension (§4.7 opportunity cost "must never alone authorize
transformation"); NO_CHANGE is a valid successful outcome (§15); Challenger success is
discriminatory value, not change caused (T10).

**Severity:** Medium. **Bites:** S02, S09, G2. The harness must make NO_CHANGE a first-class
assertable terminal (Book §1 rule 6; Catalog S02/S09) and reward structures must never
credit "caused a change."

### Q11. Is operator authority cleanly separated from evidence status?

**Finding: YES, and this is one of the strongest parts of the corpus.** Constitution
Article I (operator final authority over actions) + S22 (operator may authorize experiment
or policy decision, but the EvidenceGraph cannot claim stronger support than exists) +
A-010 §10 operator gate. The separation is explicit and testable (S22's pass condition:
"Authority and truth remain distinct").

**Severity:** Low. **Bites:** S22, G6 — should be a straightforward pass if the harness
keeps the two graphs separate.

### Q12. Can a CEREBUS contradiction be represented without silently overriding the manual?

**Finding: Design says yes; representation says no (yet).** A-008 §7 + A-010 §18 define the
behavior: manual claim preserved exactly, reproduction recorded separately, contradiction
enters amendment/evidence review, operator required for doctrine amendment (S16 terminal
states MANUAL_PRESERVED+CONTRADICTION_OPEN / AMENDED / REPRODUCTION_REJECTED). **But there is
no canonical machine-readable representation of the manual or its "exact defined
conditions" on this branch** — only `quant-lab/research/CEREBUS_STRATEGY_ANALYSIS.md`
(analysis). AMB-09.

**Severity:** Medium. **Bites:** S16, G5. Fixtures must use a labeled synthetic manual-claim
object until the operator provides canonical doctrine; the harness must enforce that a
contradiction can never mutate the manual object (only spawn a review).

### Q13. Can a Crypto source disagreement remain at the sensor/provider layer without contaminating higher models?

**Finding: YES in doctrine, TESTABLE in S17.** A-009 §18 (provider-native semantics survive
normalization; nulls survive) and A-010 §19 (challenge sequence starts at provider
semantics → adapter → normalization → quality/disagreement surface) are explicit. The
contamination risk is the inverse direction: normalization that averages away disagreement
(Book S17 pass condition: "disagreement is not averaged away").

**Severity:** Medium. **Bites:** S17, G5. The fixture must assert that field-model state is
unchanged until source-layer explanations fail — a direct "forbidden transition" candidate
(provider disagreement → field-model rewrite is illegal).

### Q14. Does any proposed rule accidentally permit research autonomy to imply execution/capital autonomy?

**Finding: NO — this is repeatedly and redundantly prohibited.** Constitution §2.3/§9,
Article VIII; A-008 §10 ("No step may silently collapse research status into execution
status"), §15; A-009 §19.12; A-010 §3 (no path from anomaly to architecture mutation);
Book §1 rules 2/13, §5 illegal transition "TRANSFORMATION_WINDOW -> capital authority",
S14, T21. The corpus is defensively consistent here.

**Severity:** Low. **Bites:** S14/S21/G6 — enforce as forbidden transitions and authority
non-escalation checks.

### Q15. Can dormant/archive behavior erase important contradictory evidence from practical retrieval?

**Finding: YES — this is T17 (dormant-knowledge burial) and it is only partially
defended.** A-009 §9/§11 separate active weight from archival retention and Book S10/S12
test reactivation, but the *retrieval policy* that decides what "normally excluded from
default context" means is delegated to "reopen conditions" which (per Q5) can be written
narrowly. The defense (T17: dormant/archive records remain searchable by
contradiction/reopen conditions; provenance cannot be deleted by ordinary learning
operations) is policy language, not an enforced invariant.

**Severity:** Medium. **Bites:** S10, S12, G4, G8. G1 should add an invariant: no lifecycle
transition may delete or detach provenance (archival retention is mandatory; pruning
affects only active-context weighting).

### Q16. Can a completely novel governance failure be represented without forcing classification?

**Finding: YES — S24 is designed exactly for this** (UNRESOLVED_GOVERNANCE_EVENT, preserve
evidence, safe hold appropriate to consequence, Governor-amendment candidate without
inventing a classification; A010-RT T24). The risk is the harness's own schema: if the
scenario loader requires every event to map to a known channel/scope, S24 cannot be
instantiated honestly. The schema must permit an unclassifiable event type.

**Severity:** Medium (implementation risk). **Bites:** S24, G6, G9 (invariant extraction
must not force the unclassified into a class). G1 schema note recorded.

### Q17. (Composite from Master Prompt §4 remainder) — other sovereignty/corruption vectors

**Can agent confidence become canonical truth?** Prohibited (Book §5 illegal example
"agent confidence -> independent confirmation"; Constitution Article II). Harness must
assert this as a forbidden transition class.

**Can operator preference become the strongest institutional attractor?** Yes — PM-RM §18
Q10 flags it. Nothing in the corpus measures operator-preference feedback loops on the
attractor registry (A-009 §4 is descriptive only). Not a scenario blocker; recorded for G9
invariant consideration and G10 change-request candidacy.

**Can the desire for institutional coherence suppress profitable but ugly empirical edges?**
Yes — PM-RM §18 Q12. S14/S15's sharp boundary (profit cannot vote on validation; unresolved
patterns can become new families) is the intended countermeasure; G8 must check that
cross-scenario evidence handling is consistent.

---

## Summary of severities

| Severity | Items |
|---|---|
| High (open contradiction-candidate) | Q2 path 1 / Q3 (PO indirect control) → CON-02; Q7 (no independence aggregation) → AMB-03 |
| Medium-High | Q4 (Governor inertia/threshold drift) → CON-03/T1/T6 |
| Medium | Q1 (CON-05), Q5 (Q11 dogma), Q6 (AMB-04), Q9 (incumbent bias), Q10 (novelty bias), Q12 (AMB-09), Q13 (AMB-10), Q15 (T17), Q16 (S24 schema risk) |
| Low | Q11, Q14 — corpus is strong; enforce, don't test-design |

**Net assessment:** the proposed architecture contains no fatal flaw that blocks honest
testing, and its two genuinely open tensions (CON-02 PO-vs-Governor; CON-03 threshold
transparency) are precisely the kind of fault the suite is built to expose. G0 recommends
proceeding to G1 with the CON/AMB registers carried forward, per `G0_ARCHITECTURE_INGESTION.md` §21.

*End of G0 adversarial review.*
