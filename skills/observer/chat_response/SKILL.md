# Skill: Chat Response Generation

> **Category:** observer
> **Version:** 1.0.0
> **Purpose:** Generate dynamic, context-aware chat responses for the Observer chat interface.

## Problem This Solves

The Observer chat was producing static, repetitive responses regardless of input. The root cause was:
1. Default response template was too generic — same template for ALL non-matching inputs
2. Pattern matching was too narrow — only caught exact phrases
3. No actual content analysis — just echoed user input with template wrapper

## Detection

Symptoms of the static response problem:
- User reports "same response every time"
- Response doesn't vary based on message content
- Generic template visible in responses ("I'm processing this through the observer field...")
- Factual questions get generic answers instead of specific information

## Fix Flow

1. **Classify intent** — Use `intent_classifier.py` to determine message type
2. **Extract entities** — Pull out key topics, references, question targets
3. **Generate dynamic response** — Build response from extracted content, not templates
4. **Add context awareness** — Reference conversation history, current system state
5. **Vary phrasing** — Never use the same template twice

## Response Generation Rules

### DO:
- Analyze the actual content of the user's message
- Reference specific topics mentioned by the user
- Vary sentence structure and phrasing
- Include relevant system state when appropriate
- Ask clarifying questions when intent is unclear

### DON'T:
- Use generic templates like "I'm processing this through the observer field"
- Echo user input back with minor variations
- Default to "Want me to take action or keep discussing?"
- Use the same opening phrase more than once per session
- Include "As an AI" or similar self-references

## Examples

### Bad (Static):
```
User: "What's the status of the vault writer?"
Response: "Got it — What's the status of the vault writer? I'm processing this through the observer field... Current routing: planner | Model: claude-haiku-4 | Agreement: 100%... Want me to take action or keep discussing?"
```

### Good (Dynamic):
```
User: "What's the status of the vault writer?"
Response: "Vault Writer (Phase 0A) is complete — 18/18 tests passing. It handles structured markdown writes to the O2C vault with CAUSE/FIX/RESULT/LINKS formatting. Ready for Phase 0B (Compressor)."
```

## Heuristics

- If message contains a question word (what, how, why, when, where), provide a direct answer
- If message contains an action verb (build, create, fix, update), acknowledge the action
- If message is short (< 10 words), ask for clarification or provide a concise answer
- If message references a specific component, include that component's status
