"""
Semantic State Field — Core cognition substrate.

Every message produces an internal SemanticState object BEFORE response generation.
This replaces the regex-template routing with actual semantic interpretation.

Architecture:
    User Input → Semantic Interpreter → SemanticState → Response Synthesizer → Response

NOT:
    User Input → regex match → template → Response
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SemanticState:
    """
    Internal interpretation of a user message.
    This is the central cognition substrate — every response is generated
    FROM this object, not from raw text matching.
    """
    raw_input: str

    # Core interpretation
    primary_intent: str = ""          # greeting, question, request, command, ambiguity, identity_probe, etc.
    task_type: str = ""               # coding, research, architecture, conversation, etc.

    # Cognitive dimensions
    abstraction_level: float = 0.5    # 0.0=concrete, 1.0=abstract
    reasoning_depth: float = 0.5      # 0.0=shallow, 1.0=deep

    # Uncertainty
    uncertainty: float = 0.5          # 0.0=certain, 1.0=completely ambiguous
    entropy: float = 0.5              # operational entropy of this message

    # Response shaping
    emotional_vector: str = "neutral" # neutral, curious, frustrated, playful, urgent
    response_mode: str = "answer"     # answer, clarify, execute, explain, deflect, recover

    # Continuity
    requires_clarification: bool = False
    continuity_reference: Optional[str] = None  # references previous topic

    # Inferred goal
    inferred_goal: Optional[str] = None

    # Confidence in our own interpretation
    confidence: float = 0.5

    # Metadata
    word_count: int = 0
    has_question_mark: bool = False
    has_action_verb: bool = False
    is_short: bool = False

    def to_dict(self) -> dict:
        return {
            "raw_input": self.raw_input[:100],
            "primary_intent": self.primary_intent,
            "task_type": self.task_type,
            "abstraction_level": self.abstraction_level,
            "reasoning_depth": self.reasoning_depth,
            "uncertainty": self.uncertainty,
            "entropy": self.entropy,
            "emotional_vector": self.emotional_vector,
            "response_mode": self.response_mode,
            "requires_clarification": self.requires_clarification,
            "continuity_reference": self.continuity_reference,
            "inferred_goal": self.inferred_goal,
            "confidence": self.confidence,
        }
