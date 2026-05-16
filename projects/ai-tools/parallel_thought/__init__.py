"""
Parallel Thought Synthesis System
Query multiple AI models in parallel and synthesize their responses.
"""

from .parallel_thought_synthesizer import (
    ParallelThoughtSynthesizer,
    ModelResponse,
    SynthesisStrategy
)
from .hermes_parallel_agent import ParallelThinkingAgent, PlanningResult

__version__ = "0.1.0"
__all__ = [
    "ParallelThoughtSynthesizer",
    "ModelResponse", 
    "SynthesisStrategy",
    "ParallelThinkingAgent",
    "PlanningResult"
]