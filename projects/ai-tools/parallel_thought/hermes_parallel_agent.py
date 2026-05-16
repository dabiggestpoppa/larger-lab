"""
Hermes Agent Integration for Parallel Thought Synthesis
Integrates the parallel thought system with Hermes agent framework.
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import the parallel thought synthesizer
from .parallel_thought_synthesizer import ParallelThoughtSynthesizer, SynthesisStrategy

@dataclass
class PlanningResult:
    """Container for planning results."""
    goal: str
    plan: str
    confidence: float
    model_contributions: List[Dict[str, Any]]
    strategy: str

class ParallelThinkingAgent:
    """
    Hermes agent that uses parallel thought synthesis for planning and decision-making.
    """
    
    def __init__(self, 
                 name: str = "ParallelThinker",
                 api_key: Optional[str] = None,
                 models: List[str] = None,
                 strategy: SynthesisStrategy = SynthesisStrategy.WEIGHTED_CONSENSUS):
        """
        Initialize the parallel thinking agent.
        
        Args:
            name: Agent name
            api_key: OpenRouter API key
            models: List of models to query
            strategy: Default synthesis strategy
        """
        self.name = name
        self.synthesizer = ParallelThoughtSynthesizer(api_key=api_key, default_models=models)
        self.strategy = strategy
        self.last_result = None
    
    async def plan(self, 
                   goal: str, 
                   context: str = "",
                   sub_tasks: List[str] = None,
                   strategy: SynthesisStrategy = None) -> PlanningResult:
        """
        Generate a plan using parallel thought synthesis.
        
        Args:
            goal: The main goal to plan for
            context: Additional context
            sub_tasks: Optional list of sub-tasks to plan for
            strategy: Synthesis strategy (uses default if not specified)
            
        Returns:
            PlanningResult with the synthesized plan
        """
        strategy = strategy or self.strategy
        
        # Generate agent's own initial plan
        own_plan = await self._generate_own_plan(goal, context)
        
        # Break goal into sub-thoughts if not provided
        if not sub_tasks:
            sub_tasks = self._break_into_sub_tasks(goal)
        
        # Query models for each sub-task
        specialist_inputs = {}
        for sub_task in sub_tasks:
            prompt = f"""Think step-by-step about: {sub_task}
            
            Provide a concise plan with 3-5 specific actions.
            Context: {context}"""
            
            responses = await self.synthesizer.dispatch_thoughts(prompt)
            specialist_input = self.synthesizer.synthesize(
                responses=responses,
                agent_own_idea=own_plan,
                strategy=strategy
            )
            specialist_inputs[sub_task] = specialist_input
        
        # Integrate specialist inputs
        final_plan = self._integrate_inputs(own_plan, specialist_inputs)
        
        # Calculate confidence
        confidence = self._calculate_confidence(specialist_inputs)
        
        result = PlanningResult(
            goal=goal,
            plan=final_plan,
            confidence=confidence,
            model_contributions=[
                {"task": task, "input": inp.get("model_breakdown", [])}
                for task, inp in specialist_inputs.items()
            ],
            strategy=strategy.value
        )
        
        self.last_result = result
        return result
    
    async def _generate_own_plan(self, goal: str, context: str) -> str:
        """Generate the agent's own initial plan."""
        # Simple heuristic-based planning
        steps = [
            f"Analyze requirements for: {goal}",
            "Identify key components and dependencies",
            "Create implementation roadmap",
            "Set up testing and validation",
            "Deploy and monitor"
        ]
        return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
    
    def _break_into_sub_tasks(self, goal: str) -> List[str]:
        """Break goal into sub-tasks for parallel thinking."""
        # Simple heuristic: split by common conjunctions
        import re
        parts = re.split(r'\s*(?:,|;|\band\b|&)\s*', goal)
        return [p.strip() for p in parts if p.strip()]
    
    def _integrate_inputs(self, own_plan: str, specialist_inputs: Dict) -> str:
        """Integrate specialist inputs into final plan."""
        # Start with agent's own plan
        integrated = [own_plan]
        
        # Add specialist insights
        for task, inp in specialist_inputs.items():
            if inp.get("synthesized"):
                integrated.append(f"\n--- {task} ---\n{inp['synthesized']}")
        
        return "\n\n".join(integrated)
    
    def _calculate_confidence(self, specialist_inputs: Dict) -> float:
        """Calculate overall confidence from specialist inputs."""
        confidences = [inp.get("confidence", 0) for inp in specialist_inputs.values()]
        return sum(confidences) / len(confidences) if confidences else 0.0

# Example usage
async def main():
    agent = ParallelThinkingAgent()
    
    print("🤖 Parallel Thinking Agent Demo")
    print("=" * 50)
    
    # Plan a complex task
    result = await agent.plan(
        goal="Build a web app that analyzes financial data and provides trading signals",
        context="Using Python, FastAPI, and machine learning",
        strategy=SynthesisStrategy.WEIGHTED_CONSENSUS
    )
    
    print(f"\n🎯 GOAL: {result.goal}")
    print(f"\n✅ PLAN (confidence: {result.confidence:.2f}):")
    print(result.plan)

if __name__ == "__main__":
    asyncio.run(main())