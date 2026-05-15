#!/usr/bin/env python3
"""
CLI for Parallel Thought Synthesis System
"""

import asyncio
import click
from .parallel_thought_synthesizer import ParallelThoughtSynthesizer, SynthesisStrategy
from .hermes_parallel_agent import ParallelThinkingAgent

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Parallel Thought Synthesis CLI - Query multiple AI models in parallel."""
    pass

@cli.command()
@click.argument('prompt', nargs=-1)
@click.option('--model', '-m', multiple=True, help='Specific models to query')
@click.option('--strategy', '-s', 
              type=click.Choice(['weighted_consensus', 'contrarian_scoring', 'best_score', 'vote', 'contrast']),
              default='weighted_consensus', help='Synthesis strategy')
@click.option('--max-tokens', default=512, help='Max tokens per response')
def query(prompt, model, strategy, max_tokens):
    """Query multiple models in parallel and synthesize results."""
    prompt_str = " ".join(prompt)
    if not prompt_str:
        raise click.UsageError("Please provide a prompt.")
    
    async def run_query():
        synthesizer = ParallelThoughtSynthesizer()
        if model:
            synthesizer.models = list(model)
        
        responses = await synthesizer.dispatch_thoughts(prompt_str, max_tokens=max_tokens)
        result = synthesizer.synthesize(responses, strategy=SynthesisStrategy(strategy))
        return result, responses
    
    result, responses = asyncio.run(run_query())
    
    click.echo(f"\n🤖 RESPONSES FOR: {prompt_str}")
    click.echo("=" * 60)
    
    for response in responses:
        if response.content:
            click.echo(f"\n{response.model}:")
            click.echo(f"  Tokens: {response.tokens} | Latency: {response.latency:.2f}s")
            click.echo(f"  {response.content[:300]}...")
        elif response.error:
            click.echo(f"\n{response.model}: ERROR - {response.error}")
    
    click.echo("\n" + "=" * 60)
    click.echo("✨ SYNTHESIZED RESULT:")
    click.echo(result["synthesized"])
    click.echo(f"\nConfidence: {result['confidence']:.2f}")

@cli.command()
@click.argument('goal', nargs=-1)
@click.option('--context', '-c', default="", help='Additional context')
@click.option('--strategy', '-s',
              type=click.Choice(['weighted_consensus', 'contrarian_scoring', 'best_score', 'vote', 'contrast']),
              default='weighted_consensus', help='Synthesis strategy')
def plan(goal, context, strategy):
    """Generate a plan using parallel thought synthesis."""
    goal_str = " ".join(goal)
    if not goal_str:
        raise click.UsageError("Please provide a goal.")
    
    async def run_plan():
        agent = ParallelThinkingAgent()
        result = await agent.plan(
            goal=goal_str,
            context=context,
            strategy=SynthesisStrategy(strategy)
        )
        return result
    
    result = asyncio.run(run_plan())
    
    click.echo(f"\n🎯 GOAL: {result.goal}")
    click.echo(f"\n✅ PLAN (confidence: {result.confidence:.2f}):")
    click.echo(result.plan)

@cli.command()
def models():
    """List available models."""
    # Default models without requiring API key
    default_models = [
        "poolside/laguna-m.1:free",  # Main agent - primary
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",  # Orchestrator
        "inclusionai/ring-2.6-1t:free",  # Large code tasks
    ]
    default_weights = {
        "poolside/laguna-m.1:free": 1.0,
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": 0.9,
        "inclusionai/ring-2.6-1t:free": 0.8,
    }
    click.echo("\n📋 Available Free Models (Hermes Configuration):")
    click.echo("  - poolside/laguna-m.1:free (weight: 1.0) - Main agent")
    click.echo("  - nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free (weight: 0.9) - Orchestrator")
    click.echo("  - inclusionai/ring-2.6-1t:free (weight: 0.8) - Large code tasks (rate limited)")
    click.echo("\nNote: Ring-2.6-1t may hit rate limits; system falls back to poolside main if needed")

if __name__ == "__main__":
    cli()