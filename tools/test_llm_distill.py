"""
Quick test script for LLM distillation quality.
Tests the LLMDistiller with Nemotron model.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab")

from core.research.ingestion.models import Author, Concept, Paper
from core.research.distillation.llm_distill import LLMDistiller


async def test_llm_distill():
    """Test LLM distillation with a sample paper."""
    
    # Check for API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set - cannot run LLM test")
        print("Set it with: $env:OPENROUTER_API_KEY='your-key-here'")
        return
    
    print("✅ OPENROUTER_API_KEY found - running LLM distillation test\n")
    
    # Create sample paper
    paper = Paper(
        id="W_test_llm",
        doi="10.1234/test.llm.2024",
        title="Attention Mechanisms for Multi-Agent Orchestration",
        abstract=(
            "The problem of coordinating multiple AI agents in dynamic environments "
            "remains challenging due to communication bottlenecks and conflicting objectives. "
            "We propose a novel attention-based framework that improves coordination "
            "efficiency by 23.5% while reducing message overhead by 31%. "
            "Our method uses transformer attention to route messages between agents "
            "based on task relevance and agent capability. Results show accuracy of "
            "94.2% on standard benchmarks, outperforming prior work by 15%. "
            "Limitations include scalability beyond 100 agents and reliance on "
            "synthetic training data. This work enables more efficient multi-agent "
            "systems for real-world deployment."
        ),
        year=2024,
        source="openalex",
        source_id="W_test_llm",
        url="https://openalex.org/W_test_llm",
        citation_count=42,
        authors=[Author(name="Alice Smith", id="A_test")],
        concepts=[
            Concept(name="attention mechanisms", score=0.95, level=0),
            Concept(name="multi-agent systems", score=0.87, level=1),
        ],
        referenced_works=[],
    )
    
    # Create distiller
    distiller = LLMDistiller()
    
    print(f"Paper: {paper.title}")
    print(f"Model: {distiller.model}")
    print(f"Daily cap: ${distiller.daily_cap_usd}")
    print("-" * 60)
    
    # Distill
    result = await distiller.distill(paper)
    
    if result:
        print("✅ LLM Distillation Result:\n")
        print(result)
        print("\n" + "-" * 60)
        print(f"Status: {distiller.get_status()}")
    else:
        print("❌ Distillation returned None (check logs for error)")


if __name__ == "__main__":
    asyncio.run(test_llm_distill())