"""Debug REV-1 decomposition."""
import sys
import os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from core.research.cognition.rev1_mechanisms import decompose_papers

papers = [
    {
        "text": "We show that transfer entropy between financial institutions predicts systemic instability through asymmetric information propagation mechanisms. Our results demonstrate that higher transfer entropy between institutions predicts increased systemic instability (p < 0.001, R² = 0.87). We assume efficient information propagation between institutions and that market equilibrium conditions hold. However, this study is limited by its small sample size of only 50 institutions and restricted to the 2008-2012 period.",
        "title": "Transfer Entropy and Systemic Risk",
        "id": "paper1",
    },
    {
        "text": "We demonstrate that network topology controls systemic risk in interbank markets. Our analysis reveals that information imbalance drives market instability through cascading default mechanisms. We present a novel graph-theoretic framework. Results indicate that centrality measures explain 62% of variance in default probability. The model assumes rational actor behavior and stationary network structure.",
        "title": "Network Topology and Systemic Risk",
        "id": "paper2",
    },
]

print("Starting REV-1 decomposition...")
results = decompose_papers(papers)
print(f"Decomposed {len(results)} papers")
for r in results:
    print(f"\n--- {r.paper_title} ---")
    print(f"  Claims: {len(r.claims)}")
    print(f"  Explicit assumptions: {len(r.explicit_assumptions)}")
    print(f"  Implicit assumptions: {len(r.implicit_assumptions)}")
    print(f"  Mechanisms: {len(r.mechanisms)}")
    print(f"  Limitations: {len(r.limitations)}")
    print(f"  Quality: {r.decomposition_quality:.2f}")
    print(f"  Complete: {r.is_complete}")
