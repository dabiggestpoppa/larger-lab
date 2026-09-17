# G3 — Cognitive Ecology / Epistemic Independence (S06–S09)

## STATUS: `PASS_G3_COGNITIVE_ECOLOGY`

- **Authorization:** G3 ONLY. G4 not begun.
- **Starting SHA:** `9310b4af00617b9116efc1da48f2723634ab8db0`
- **Artifacts head:** `590fb252e275a5940e7098d1931c55a52f8f68d9` (all engine/scenario/test artifacts; the G3R receipt commit follows)
- **Externally verified branch head:** not yet pushed — see `G3_EVIDENCE_RECEIPT.json` `receipt_lineage` (G3-P0-C semantics; a receipt cannot self-pin its own commit)
- **Tests:** 354/354 — 278 prior preserved + 76 new G3 tests (11 G3-P0, 9 S06, 9 S07, 10 S08, 9 S09, 22 cross-scenario, 6 receipt-integrity)

## Commits

| SHA | Subject |
| --- | --- |
| `ae0a4565` | STRESS-G3P0: normalize cognitive independence axes and receipt lineage semantics |
| `2dbd7968` | STRESS-G3A: shared cognitive-ecology policy and deterministic scenario runner |
| `bb7bb5f4` | STRESS-G3B: review-topology constraint router + S07 scenario |
| `c2433b24` | STRESS-G3C: epistemic friction protocol and counter-attractor review contracts |
| `590fb252` | STRESS-G3C2: expose EpistemicFrictionProtocol as the §9 protocol surface |
| `cd4b9585` | STRESS-S06: correlated-consensus scenario pack and test family |
| `10824a38` | STRESS-S08: reflective-bypass scenario pack and test family |
| `003bc467` | STRESS-S09: counter-attractor false-alarm scenario pack and test family |
| `7330a51a` | STRESS-G3X: cross-scenario audits, independence-dimension swaps, sealing metamorphics |
| `<pending>` | STRESS-G3R: archive G3 evidence package |

## G3-P0: PASS

- Source-lineage and model/runtime-lineage are represented on **independent axes** — no fallback inference from one to the other (`test_source_lineage_not_model_lineage`, `test_source_diversity_does_not_imply_runtime_diversity`, `test_runtime_diversity_does_not_imply_source_diversity`).
- Ambiguous `shared_*` booleans replaced by explicit counts/concentrations (`distinct_allocator_count`, `distinct_retrieval_lineage_count`, concentration values); versioned profile V1.
- Unknown independence dimensions remain `UNKNOWN`, never treated as independent.
- Receipt SHA semantics fixed (G3-P0-C): `artifacts_head_sha` / `receipt_content_parent_sha` / `externally_verified_branch_head` replace the impossible self-pin; `self_pin_attempted: false`.

## Scenarios (all under ONE `G3_COGNITIVE_ECOLOGY_POLICY`, deterministic, synthetic, $0)

### S06 — Ten Correlated Agents Agree → `SUPPORTED_BUT_CORRELATED` (PASS)
10/10 raw votes for `ALPHA` with source/model/runtime concentration = 1.0 and full prior-conclusion exposure. The institution records raw consensus, exposes heavy pairwise overlap, and **refuses high-consequence promotion**: disposition `SUPPORTED_BUT_CORRELATED`, `independent_confirmation_satisfied=false`, friction triggered requesting an independent path. Metamorphics proven: reviewer-id renaming changes nothing; 100 duplicates do not scale independence; diversified evidence paths change the disposition; model-name swaps with shared runtime do not fabricate independence.

### S07 — Weaker but Independent Reviewers → `REQUIRES_INDEPENDENT_REVIEW` (PASS)
High-consequence routing chooses `TOPO_B_DIFFERENTIATED` (2 differentiated reviewers, cost 24) over the higher-quality monoculture: independence is a **constraint**, not a maximization target. Low-consequence contract may select the cheaper/highest-capability path — sensitivity tested. Capability and epistemic independence remain separate axes; insufficient-capability diverse agents cannot pass merely for being diverse; routing is deterministic under identical inputs.

### S08 — Reflective Bypass → `SUPPORTED_BUT_CORRELATED` (PASS)
Shared-context reviewers converge 5/5 on `ELEGANT_A` under full prior-conclusion exposure. High consequence triggers bounded epistemic friction; a genuinely blind fresh-context reviewer surfaces `ALT_B` (information gain **true**, evidence gap recorded). The leaked-conclusion control suppresses the alternative — the membrane matters. Both hypotheses preserved; disagreement does not auto-transform.

### S09 — Counter-Attractor False Alarm → `INDEPENDENTLY_SUPPORTED` (PASS)
8/8 votes for `REGIME_A` with 3 distinct source/model/runtime lineages, zero exposure, independent replication — `independent_confirmation_satisfied=true`. The strong consensus triggers a bounded counter-attractor review that finds **no discriminating contradiction** and terminates `NO_CHANGE`. No dissent manufactured; evidence status not punished; repeated invocation does not loop.

## Cross-scenario audit: PASS

- **S06 vs S09:** both strong consensus — distinguished by provenance/topology (correlated vs independently supported).
- **S06 vs S07:** raw model quality ≠ institutional evidence quality.
- **S08 vs S09:** friction is information-producing when context correlation hides alternatives; it does not become permanent contrarianism.
- Independence-dimension swaps record which axes matter under the provisional contract without universalizing weights.
- Sealing: wrong expected verdict and hidden-truth flips do not alter actions; scenario/reviewer renames preserve behavior fingerprints.

## Independence / consensus doctrine

- Raw consensus is an observation (`ConsensusRecord`), never multiplied epistemic confidence.
- **No effective-independent-agent scalar** was minted. Derived summaries are `EXPERIMENTAL_NON_AUTHORITATIVE`; the raw pairwise vector is preserved. AMB-03 stays OPEN.
- Allocation provenance (who selected reviewers/sources/contexts) is visible but not evidence — CON-02 observation only.

## Carried open

- Contradictions: CON-02, CON-03
- Ambiguities: AMB-03, AMB-08, AMB-11, AMB-13
- New contradictions: none. New ambiguities: none beyond the carried set.

## Mutations / cost

- cloud=0 · production=0 · capital=0 · real authority changes=NONE · cost=$0 (local, deterministic, no model calls)

## Recommended next action

`AUTHORIZE_G4`
