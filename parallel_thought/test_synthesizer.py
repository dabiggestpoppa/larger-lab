"""
Test script for ParallelThoughtSynthesizer
Demonstrates basic functionality of the parallel thought synthesis system.
"""

import asyncio
import os
from parallel_thought import ParallelThoughtSynthesizer

async def main():
    # Initialize synthesizer (uses environment variable for API key)
    synthesizer = ParallelThoughtSynthesizer()
    
    # Define test prompt
    prompt = "Design a scalable microservices architecture for a social media app"
    
    print("🚀 Testing Parallel Thought Synthesis...")
    print(f"Prompt: {prompt}\n")
    
    # Dispatch thoughts to all configured models
    responses = await synthesizer.dispatch_thoughts(prompt)
    
    print("📊 Results:")
    for i, response in enumerate(responses, 1):
        print(f"\n{i}. {response.model}")
        print(f"   Tokens: {response.tokens}")
        print(f"   Latency: {response.latency:.2f}s")
        if response.error:
            print(f"   Error: {response.error}")
        else:
            print(f"   Content preview: {response.content[:100]}...")
    
    # Synthesize results with weighted consensus
    result = synthesizer.synthesize(
        responses=responses,
        agent_own_idea="Start with architecture diagram, then implement services incrementally",
        strategy="weighted_consensus",
        top_k=3
    )
    
    print("\n✨ Final Synthesis:")
    print(result["synthesized"])
    print(f"\nConfidence: {result['confidence']:.2f}")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY environment variable not set")
        print("   Set it before running: export OPENROUTER_API_KEY='your-key-here'")
    
    asyncio.run(main())