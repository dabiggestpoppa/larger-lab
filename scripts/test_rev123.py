"""Test REV-1, REV-2, REV-3 without LLM calls."""
import sys
import os
import json
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from core.research.cognition.rev1_mechanisms import decompose_papers
from core.research.cognition.rev2_adversarial import run_adversarial_reasoning
from core.research.cognition.rev3_theory import run_theory_competition

papers = [
    {
        "text": "We show that transfer entropy between financial institutions predicts systemic instability through asymmetric information propagation mechanisms. Our results demonstrate that higher transfer entropy between institutions predicts increased systemic instability (p < 0.001, R² = 0.87). We assume efficient information propagation between institutions and that market equilibrium conditions hold. However, this study is limited by its small sample size of only 50 institutions and restricted to the 2008-2012 period. Unlike previous work that used correlation-based approaches, we introduce CEEMDAN filtering prior to entropy estimation.",
        "title": "Transfer Entropy and Systemic Risk",
        "id": "paper1",
    },
    {
        "text": "We demonstrate that network topology controls systemic risk in interbank markets. Our analysis reveals that information imbalance drives market instability through cascading default mechanisms. We present a novel graph-theoretic framework for measuring systemic vulnerability. The model assumes rational actor behavior and stationary network structure. Results indicate that centrality measures explain 62% of variance in default probability.",
        "title": "Network Topology and Systemic Risk",
        "id": "paper2",
    },
    {
        "text": "This meta-analysis confirms that both transfer entropy and network topology are significant predictors of systemic risk. Our results are consistent with previous findings that information asymmetry drives market instability. We found that entropy accumulation precedes systemic crisis events, supporting the information propagation hypothesis. The analysis covers 500 institutions across 20 countries.",
        "title": "Meta-Analysis of Systemic Risk Predictors",
        "id": "paper3",
    },
]

print("=" * 60)
print("REV-1: Structural Decomposition")
print("=" * 60)

rev1_results = decompose_papers(papers)
for obj in rev1_results:
    print(f"\n--- {obj.paper_title} ---")
    print(f"  Domain: {obj.domain}")
    print(f"  Claims ({len(obj.claims)}):")
    for c in obj.claims[:3]:
        print(f"    [{c['claim_type']}] {c['claim'][:80]}...")
    print(f"  Explicit assumptions ({len(obj.explicit_assumptions)}):")
    for a in obj.explicit_assumptions[:2]:
        print(f"    {a['assumption'][:80]}...")
    print(f"  Implicit assumptions ({len(obj.implicit_assumptions)}):")
    for a in obj.implicit_assumptions[:2]:
        print(f"    [{a.get('assumption_type', '?')}] {a['assumption'][:80]}...")
    print(f"  Mechanisms ({len(obj.mechanisms)}):")
    for m in obj.mechanisms[:2]:
        print(f"    {m['mechanism'][:80]}...")
    print(f"  Limitations ({len(obj.limitations)}):")
    for l in obj.limitations[:2]:
        print(f"    [{l['severity']}] {l['limitation'][:80]}...")
    print(f"  Quality: {obj.decomposition_quality:.2f} | Complete: {obj.is_complete}")

print("\n" + "=" * 60)
print("REV-2: Adversarial Scientific Reasoning")
print("=" * 60)

rev1_dicts = [obj.to_dict() for obj in rev1_results]
rev2_results = run_adversarial_reasoning(rev1_dicts)

print(f"\nContradictions found: {rev2_results['summary']['num_contradictions']}")
for c in rev2_results.get("contradictions", []):
    print(f"  [{c.get('type', '?')}] severity={c.get('severity', 0):.2f}")
    print(f"    Paper A: {c.get('claim_a', c.get('assumption_a', ''))[:60]}...")
    print(f"    Paper B: {c.get('claim_b', c.get('assumption_b', ''))[:60]}...")
    if "possible_explanations" in c:
        for i, exp in enumerate(c["possible_explanations"][:3]):
            print(f"    Explanation {i+1}: {exp[:60]}...")

print(f"\nAttacks generated: {rev2_results['summary']['total_attacks_generated']}")
for pid, analysis in rev2_results.get("paper_analyses", {}).items():
    for ca in analysis.get("claim_analyses", [])[:2]:
        print(f"\n  Claim: {ca['claim'][:60]}...")
        for alt in ca.get("alternatives", [])[:2]:
            print(f"    Alternative: {alt[:60]}...")
        for attack in ca.get("attacks", [])[:2]:
            print(f"    Attack [{attack.get('attack_type', '?')}]: {attack.get('weakness', '')[:60]}...")
        for b in ca.get("boundaries", [])[:2]:
            print(f"    Boundary: {b[:60]}...")

print("\n" + "=" * 60)
print("REV-3: Theory Competition + Scientific Judgment")
print("=" * 60)

rev3_results = run_theory_competition(rev1_dicts, rev2_results)

print(f"\nTheories extracted: {rev3_results['theories_extracted']}")
ranking = rev3_results.get("ranking", {})
for t in ranking.get("ranked_theories", []):
    print(f"\n  Theory: {t.get('theory_name', '?')[:60]}")
    print(f"    Score: {t.get('composite_score', 0):.3f}")
    print(f"    Explanatory: {t.get('explanatory_score', 0):.3f} | Assumption cost: {t.get('assumption_cost_score', 0):.3f}")
    print(f"    Generalization: {t.get('generalization_score', 0):.3f}")
    print(f"    Variables: {', '.join(t.get('core_variables', [])[:5])}")

winner = ranking.get("winner")
if winner:
    print(f"\n  WINNER: {winner.get('theory_name', '?')[:60]} (score={winner.get('composite_score', 0):.3f})")

synthesis = rev3_results.get("synthesis", {})
if synthesis:
    print(f"\nSynthesis: {synthesis.get('statement', '')[:120]}...")
    print(f"Structural themes: {synthesis.get('structural_themes', [])}")
    print(f"Interdisciplinary: {synthesis.get('interdisciplinary_connections', [])}")

print("\nDONE")
