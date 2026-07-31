# Interpreter

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #semantic

```python
"""
Semantic Interpreter — converts raw user input into SemanticState.

This replaces the brittle regex-template routing with actual content analysis.
Every message is interpreted along multiple cognitive dimensions before
any response generation occurs.

Key principle: The interpreter doesn't match patterns — it UNDERSTANDS intent.
"""

from __future__ import annotations

import re
from typing import Optional

from core.semantic.semantic_state import SemanticState


# ── Intent pattern definitions ──
# These are NOT templates — they feed into semantic interpretation scoring.
# Each pattern has a weight and contributes to the final intent classification.

GREETING_PATTERNS = [
    (r"\b(hello|hi|hey|howdy|greetings|good\s+(morning|afternoon|evening))\b", 0.9),
]

IDENTITY_PATTERNS = [
    (r"\b(who\s+are\s+you|what\s+are\s+you|tell\s+me\s+about\s+(yourself|you)|what\s+type\s+of\s+system|what\s+kind\s+of\s+system|who\s+(built|made|created)\s+you)\b", 0.95),
]

CAPABILITY_PATTERNS = [
    (r"\b(what\s+can\s+you\s+do|what\s+do\s+you\s+do|capabilities|help\s+me\s+understand)\b", 0.9),
]

STATUS_PATTERNS = [
    (r"\b(how\s+are\s+you|how'?s\s+it\s+going|what'?s\s+up|status|how\s+do\s+you\s+do|how\s+are\s+you\s+doing|how'?s\s+everything)\b", 0.9),
]

SYSTEM_KNOWLEDGE_PATTERNS = [
    (r"\b(what\s+is\s+srra|what\s+is\s+oce|what\s+is\s+oph|how\s+does\s+the\s+field\s+work|how\s+does\s+the\s+observer\s+work|tell\s+me\s+about\s+the\s+(field|system|architecture))\b", 0.9),
]

FIELD_PATTERNS = [
    (r"\b(observer|field|topology|entropy|continuum|continuity)\b", 0.7),
]

ACTION_PATTERNS = [
    (r"\b(let'?s|can\s+you|could\s+you|would\s+you|please|i\s+want|i\s+need|should\s+we|show\s+me|tell\s+me|give\s+me|i'?d\s+like|help\s+me)\b", 0.8),
]

QUESTION_PATTERNS = [
    (r"^(what|who|where|when|why|how|which|can|could|would|is|are|do|does)\b", 0.7),
    (r"\?$", 0.6),
]

GRATITUDE_PATTERNS = [
    (r"\b(thanks|thank\s+you|thx|ty|appreciate)\b", 0.9),
]

FAREWELL_PATTERNS = [
    (r"\b(bye|goodbye|see\s+you|later|take\s+care)\b", 0.9),
]

AMBIGUITY_PATTERNS = [
    (r"^[^a-zA-Z]*$", 0.95),  # non-alphabetic only
    (r"^.{1,3}$", 0.8),       # very short
]


def _score_patterns(text: str, patterns: list[tuple[str, float]]) -> float:
    """Score text against a set of weighted patterns. Returns max score."""
    max_score = 0.0
    for pattern, weight in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            max_score = max(max_score, weight)
    return max_score


def _detect_action_verbs(text: str) -> bool:
    """Detect if text contains action-oriented verbs."""
    action_verbs = [
        "build", "create", "make", "fix", "debug", "write", "implement",
        "design", "analyze", "research", "explain", "show", "tell", "give",
        "help", "run", "test", "deploy", "configure", "setup", "install",
        "update", "modify", "change", "remove", "add", "check", "verify",
    ]
    lower = text.lower()
    return any(v in lower for v in action_verbs)


def _detect_emotional_vector(text: str) -> str:
    """Detect emotional tone of message."""
    lower = text.lower()
    # Frustration indicators
    if any(w in lower for w in ["damn", "fuck", "shit", "wtf", "hell", "dammit", "goddamn"]):
        return "frustrated"
    # Urgency
    if any(w in lower for w in ["urgent", "asap", "immediately", "quickly", "hurry", "now"]):
        return "urgent"
    # Playful/casual
    if any(w in lower for w in ["lol", "haha", "hehe", "lmao", "rofl"]):
        return "playful"
    # Curiosity
    if "?" in text or any(w in lower for w in ["wondering", "curious", "interested"]):
        return "curious"
    return "neutral"


def _estimate_abstraction(text: str) -> float:
    """Estimate how abstract vs concrete the message is."""
    abstract_words = ["concept", "idea", "theory", "philosophy", "abstract", "general", "overview", "explain", "understand"]
    concrete_words = ["code", "file", "function", "class", "variable", "line", "error", "bug", "fix", "run", "build"]
    lower = text.lower()
    abstract_score = sum(1 for w in abstract_words if w in lower)
    concrete_score = sum(1 for w in concrete_words if w in lower)
    total = abstract_score + concrete_score
    if total == 0:
        return 0.5
    return abstract_score / total


def interpret(message: str, conversation_history: list | None = None) -> SemanticState:
    """
    Convert raw user input into a SemanticState interpretation.

    This is the core cognition function — it doesn't match templates,
    it interprets intent along multiple dimensions.

    Args:
        message: Raw user input
        conversation_history: Previous messages for continuity

    Returns:
        SemanticState with full interpretation
    """
    text = message.strip()
    lower = text.lower()
    words = text.split()
    word_count = len(words)

    # ── Build semantic state ──
    state = SemanticState(raw_input=text)
    state.word_count = word_count
    state.has_question_mark = "?" in text
    state.is_short = word_count <= 3
    state.has_action_verb = _detect_action_verbs(text)
    state.emotional_vector = _detect_emotional_vector(text)
    state.abstraction_level = _estimate_abstraction(text)

    # ── Score all intent dimensions ──
    scores = {
        "greeting": _score_patterns(text, GREETING_PATTERNS),
        "identity_probe": _score_patterns(text, IDENTITY_PATTERNS),
        "capability_query": _score_patterns(text, CAPABILITY_PATTERNS),
        "status_query": _score_patterns(text, STATUS_PATTERNS),
        "system_knowledge": _score_patterns(text, SYSTEM_KNOWLEDGE_PATTERNS),
        "field_reference": _score_patterns(text, FIELD_PATTERNS),
        "action_request": _score_patterns(text, ACTION_PATTERNS),
        "question": _score_patterns(text, QUESTION_PATTERNS),
        "gratitude": _score_patterns(text, GRATITUDE_PATTERNS),
        "farewell": _score_patterns(text, FAREWELL_PATTERNS),
        "ambiguity": _score_patterns(text, AMBIGUITY_PATTERNS),
    }

    # ── Determine primary intent ──
    # Sort by score, pick highest above threshold
    sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary_intent, top_score = sorted_intents[0]

    if top_score < 0.3:
        # No strong pattern match — this is an open-ended input
        primary_intent = "open_ended"
        state.uncertainty = 0.6
    else:
        state.uncertainty = 1.0 - top_score

    state.primary_intent = primary_intent
    state.confidence = top_score

    # ── Determine task type from intent ──
    intent_to_task = {
        "greeting": "conversation",
        "identity_probe": "conversation",
        "capability_query": "conversation",
        "status_query": "system_analysis",
        "system_knowledge": "explanation",
        "field_reference": "explanation",
        "action_request": "task_execution",
        "question": "research",
        "gratitude": "conversation",
        "farewell": "conversation",
        "ambiguity": "clarification_needed",
        "open_ended": "conversation",
    }
    state.task_type = intent_to_task.get(primary_intent, "conversation")

    # ── Determine response mode ──
    if primary_intent == "ambiguity" or state.uncertainty > 0.7:
        state.response_mode = "clarify"
        state.requires_clarification = True
    elif primary_intent == "action_request":
        state.response_mode = "execute"
    elif primary_intent in ("question", "system_knowledge", "field_reference"):
        state.response_mode = "explain"
    elif primary_intent == "identity_probe":
        state.response_mode = "self_explain"
    elif primary_intent == "status_query":
        state.response_mode = "status_report"
    elif primary_intent == "capability_query":
        state.response_mode = "capability_list"
    else:
        state.response_mode = "converse"

    # ── Estimate reasoning depth ──
    # Longer, more complex messages need deeper reasoning
    if word_count > 30:
        state.reasoning_depth = 0.8
    elif word_count > 15:
        state.reasoning_depth = 0.6
    elif word_count > 5:
        state.reasoning_depth = 0.4
    else:
        state.reasoning_depth = 0.2

    # ── Continuity reference ──
    if conversation_history and len(conversation_history) > 1:
        # Check if this continues a previous topic
        last_msg = conversation_history[-2] if len(conversation_history) >= 2 else None
        if last_msg:
            last_domain = last_msg.get("task_domain", "")
            if last_domain and last_domain not in ["general", "conversation", ""]:
                # Check for continuity words
                continuity_words = ["continue", "more", "also", "additionally", "further", "next", "then", "and"]
                if any(w in lower for w in continuity_words):
                    state.continuity_reference = last_domain

    # ── Infer goal ──
    if state.has_action_verb and state.task_type == "task_execution":
        # Extract the action as the inferred goal
        state.inferred_goal = text[:100]

    # ── Calculate entropy ──
    # High entropy = ambiguous, contradictory, or degenerate input
    if state.uncertainty > 0.7:
        state.entropy = 0.7
    elif state.is_short and not state.has_question_mark:
        state.entropy = 0.5
    else:
        state.entropy = 0.2

    return state

```

LINKS:
[[Architecture]]
[[Identity]]
[[User]]
[[Ontology Core Summary]]
[[Action]]
[[Cal]]
[[Citation Workflow]]
[[Neutral]]
[[Patterns]]
[[Playful]]
[[Server]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Semantic State]]
[[Telegram Gateway]]
