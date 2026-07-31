"""Quick test for LLM reasoning gateway."""
import asyncio
import json
import os
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, '.')

from core.research.cognition.llm_reasoning import LLMReasoning

SAMPLE_PAPER = """
We show that transfer entropy between financial institutions predicts systemic instability 
through asymmetric information propagation mechanisms. Our results demonstrate that higher 
transfer entropy between institutions predicts increased systemic instability (p < 0.001, 
R² = 0.87). We assume efficient information propagation between institutions and that 
market equilibrium conditions hold. The model uses the transfer entropy formula:
TE(X,Y) = Σ p(x_{t+1}, x_t, y_t) log[p(x_{t+1}|x_t, y_t) / p(x_{t+1}|x_t)].
However, this study is limited by its small sample size of only 50 institutions and 
restricted to the 2008-2012 period. Unlike previous work that used correlation-based 
approaches, we introduce CEEMDAN filtering prior to entropy estimation, which is the 
first application of this method to financial contagion analysis. We found that 
information asymmetry causes volatility expansion through reduced market depth. 
Our findings suggest that short-medium horizon diversification is strongest during 
periods of high transfer entropy. Future work should extend this analysis to 
cryptocurrency markets and decentralized finance protocols.
"""

async def test():
    llm = LLMReasoning()
    
    print("=== R1: Knowledge Extraction ===")
    result = await llm.extract_knowledge(SAMPLE_PAPER, "Transfer Entropy and Systemic Risk")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    
    print("\n=== R2: Relationship Building ===")
    r2 = await llm.build_relationships(
        "transfer entropy financial markets",
        [result]
    )
    print(json.dumps(r2, indent=2, ensure_ascii=False)[:2000])

asyncio.run(test())
