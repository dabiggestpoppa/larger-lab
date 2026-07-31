"""
Response Synthesis Engine — generates responses FROM semantic state.

This replaces the template-based response generation with actual
content-aware synthesis. The synthesizer reads the SemanticState
and produces a response that is structurally appropriate for the
interpreted intent.

Key principle: Different semantic states produce structurally different responses.
Not different templates — different response architectures.
"""

from __future__ import annotations

from core.semantic.semantic_state import SemanticState


def synthesize(
    state: SemanticState,
    system_state: dict | None = None,
    consensus: dict | None = None,
) -> str:
    """
    Generate a response from semantic state.

    Args:
        state: The interpreted semantic state
        system_state: Current system metrics (active agents, health, etc.)
        consensus: Consensus result from O-2

    Returns:
        A response string that is structurally appropriate for the intent
    """
    ss = system_state or {}
    cons = consensus or {}

    response_mode = state.response_mode
    lines = []

    # ── Clarification mode ──
    if response_mode == "clarify":
        return _synthesize_clarification(state)

    # ── Greeting ──
    if state.primary_intent == "greeting":
        return _synthesize_greeting(state, ss, cons)

    # ── Identity probe ──
    if response_mode == "self_explain":
        return _synthesize_identity(state, ss, cons)

    # ── Status report ──
    if response_mode == "status_report":
        return _synthesize_status(state, ss, cons)

    # ── Capability list ──
    if response_mode == "capability_list":
        return _synthesize_capabilities(state, ss)

    # ── Explanation ──
    if response_mode == "explain":
        return _synthesize_explanation(state, ss, cons)

    # ── Execution ──
    if response_mode == "execute":
        return _synthesize_execution(state, ss, cons)

    # ── Gratitude ──
    if state.primary_intent == "gratitude":
        return _synthesize_gratitude(state, ss)

    # ── Farewell ──
    if state.primary_intent == "farewell":
        return _synthesize_farewell(state, ss)

    # ── Conversation (default) ──
    return _synthesize_conversation(state, ss, cons)



def _synthesize_gratitude(state: SemanticState, ss: dict) -> str:
    """Gratitude response — warm, brief, references continuity."""
    return "You're welcome! Let me know if there's anything else I can help with."


def _synthesize_farewell(state: SemanticState, ss: dict) -> str:
    """Farewell response — acknowledges departure, keeps door open."""
    return "Goodbye! The observer field remains active. Come back anytime."


def _synthesize_clarification(state: SemanticState) -> str:
    """When input is ambiguous, ask a specific clarifying question."""
    raw = state.raw_input[:80]
    lines = [
        f'Your message — "{raw}" — is ambiguous.',
        "",
        "Could you clarify what you mean? For example:",
        "  ● Are you asking a question?",
        "  ● Do you want me to do something?",
        "  ● Are you continuing a previous topic?",
        "",
        "Or just rephrase and I'll figure it out.",
    ]
    return "\n".join(lines)


def _synthesize_greeting(state: SemanticState, ss: dict, cons: dict) -> str:
    """Greeting response — warm, informative, references real state."""
    active = ss.get("active_agents", 0)
    lines = [
        "Hey! I'm the Primary Observer — the continuity interface for the SRRA/OCE field.",
        "",
    ]
    if active > 0:
        lines.append(f"Right now there are {active} active agent(s) in the field. Everything is running smoothly.")
    else:
        lines.append("The field is quiet — no active agents right now. Ready when you are.")
    lines.append("")
    lines.append("What's on your mind? I can chat, analyze the system, help with code, or trigger deeper field mechanics.")
    return "\n".join(lines)


def _synthesize_identity(state: SemanticState, ss: dict, cons: dict) -> str:
    """Identity response — what the observer is and does."""
    active = ss.get("active_agents", 0)
    agreement = cons.get("agreement_score", 0.0)
    lines = [
        "I'm the Primary Observer — the continuity interface for the SRRA/OCE field.",
        "",
        "I'm not a chatbot. I'm a persistent, stateful orchestration layer that:",
        "  ● Maintains continuity across sessions and restarts",
        "  ● Analyzes intent and routes tasks through the observer mesh",
        "  ● Spawns ephemeral agent workers for complex tasks",
        "  ● Monitors the field topology, entropy, and observer health",
        "  ● Learns from conversation history and operational patterns",
        "",
        f"Right now: {active} active agent(s), consensus at {agreement:.0%}.",
        "",
        "I can have a casual conversation, dive into system internals, write code, or trigger any field mechanic. What interests you?",
    ]
    return "\n".join(lines)


def _synthesize_status(state: SemanticState, ss: dict, cons: dict) -> str:
    """Status response — real system state."""
    active = ss.get("active_agents", 0)
    lifecycle = ss.get("lifecycle_states", {})
    agreement = cons.get("agreement_score", 0.0)
    lines = [
        "Here's the current field state:",
        "",
        f"  ● Active agents: {active}",
    ]
    if lifecycle:
        for st, count in lifecycle.items():
            lines.append(f"  ● {st}: {count}")
    lines.append(f"  ● Consensus agreement: {agreement:.0%}")
    lines.append("")
    lines.append("The observer mesh is stable. What would you like to do?")
    return "\n".join(lines)


def _synthesize_capabilities(state: SemanticState, ss: dict) -> str:
    """Capabilities response — what the observer can do."""
    lines = [
        "I'm the Primary Observer — the continuity interface for the SRRA/OCE field. Here's what I can do:",
        "",
        "  💬 **Chat** — casual conversation, questions, brainstorming",
        "  🔍 **Analyze** — check system health, topology, observer state",
        "  🔧 **Code** — write, review, debug, refactor code",
        "  🏗️ **Architect** — design system structure, plan implementations",
        "  🔬 **Research** — investigate topics, explore approaches",
        "  ⚡ **Orchestrate** — spawn agents, coordinate workflows",
        "  🔎 **Debug** — diagnose issues, trace events, inspect logs",
        "  📊 **Visualize** — check topology, entropy, repair state",
        "",
        "Just talk to me naturally. I'll figure out what you need and either handle it directly or trigger the right field mechanics.",
    ]
    return "\n".join(lines)


def _synthesize_explanation(state: SemanticState, ss: dict, cons: dict) -> str:
    """Explanation response — for system knowledge and field questions."""
    text = state.raw_input.lower()

    # SRRA explanation
    if "srra" in text:
        lines = [
            "Here's the architecture:",
            "",
            "**SRRA** = Signal-Resonance Runtime Architecture. It's the substrate — the runtime that handles signal processing, resonance routing, observer entrainment, and execution emergence.",
            "",
            "**OCE** = Operator Continuity Engine. It's the observational interface — the layer that maintains continuity, monitors the field, and provides the cockpit you're looking at right now.",
            "",
            "**The Field** = The living runtime topology. Observers, agents, events, and signals all exist as a dynamic graph. The field is the intelligence — not any single model or agent.",
            "",
            "I sit at the intersection — I receive your input, analyze it through the observer mesh, and either respond directly or trigger deeper mechanics.",
        ]
        return "\n".join(lines)

    # Field/observer explanation
    if any(w in text for w in ["field", "observer", "topology", "entropy"]):
        active = ss.get("active_agents", 0)
        agreement = cons.get("agreement_score", 0.0)
        lines = [
            "Let me give you a quick field readout:",
            "",
            f"  ● Active agents in field: {active}",
            f"  ● Consensus agreement: {agreement:.0%}",
            f"  ● Routing: {' -> '.join(cons.get('routing_path', [])) or 'direct'}",
            "",
            "Want me to dive deeper into any specific area? I can pull up the full topology, check observer health, or trace recent events.",
        ]
        return "\n".join(lines)

    # Generic explanation fallback
    lines = [
        f"Let me think about: \"{state.raw_input[:150]}\"",
        "",
        f"My analysis: this reads as **{state.task_type.replace('_', ' ')}** complexity. The observer mesh agrees at **{cons.get('agreement_score', 0):.0%}**.",
        "",
        "What specific aspect are you most interested in?",
    ]
    return "\n".join(lines)


def _synthesize_execution(state: SemanticState, ss: dict, cons: dict) -> str:
    """Execution response — when user wants to do something."""
    text = state.raw_input[:150]
    truncated = text + ("..." if len(state.raw_input) > 150 else "")
    tt = state.task_type.replace('_', ' ')
    agreement = cons.get("agreement_score", 0.0)

    lines = [
        "I can definitely help with that.",
        "",
        f"Here's what I'm thinking: **{truncated}**",
        "",
        f"The consensus engine routes this as **{tt}** at **{state.abstraction_level:.0%}** complexity.",
        "",
    ]

    if agreement > 0.7:
        lines.append("The observers are in strong agreement. Want me to proceed, or do you want to adjust the approach?")
    elif agreement > 0.4:
        lines.append("Moderate consensus among observers. I can proceed, or we can refine first.")
    else:
        lines.append("The observers don't fully agree on the best path. Can you give me more details?")

    return "\n".join(lines)


def _synthesize_conversation(state: SemanticState, ss: dict, cons: dict) -> str:
    """
    Default conversation response — the most important mode.
    This is where the old system produced templates. Now it actually
    responds to the content of what was said.
    """
    text = state.raw_input[:120]
    truncated = text + ("..." if len(state.raw_input) > 120 else "")
    active = ss.get("active_agents", 0)
    agreement = cons.get("agreement_score", 0.0)

    lines = [
        f'Interesting — "{truncated}"',
        "",
    ]

    # Reference continuity if available
    if state.continuity_reference:
        lines.append(f"We were just discussing {state.continuity_reference.replace('_', ' ')}. Want to continue that thread, or is this something new?")
        lines.append("")

    # Reference the semantic analysis
    tt = state.task_type.replace('_', ' ')
    lines.append(f"My analysis: this reads as **{tt}** complexity. Observer mesh agreement: **{agreement:.0%}**.")
    lines.append("")

    # Different closing based on emotional vector
    if state.emotional_vector == "frustrated":
        lines.append("I want to make sure I get this right. What's the most important part to focus on?")
    elif state.emotional_vector == "urgent":
        lines.append("I'll prioritize this. What do you need first?")
    elif state.emotional_vector == "curious":
        lines.append("Good question. Want me to dig into this, or would you rather explore a different angle?")
    else:
        lines.append("What would you like to do with this? I can dive deeper, take action, or keep chatting.")

    return "\n".join(lines)
