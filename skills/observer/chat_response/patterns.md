# Patterns — Chat Response Generation

## Successful Response Patterns

### Status Response Pattern
```
[Component] is [status] — [specific detail]. [Next step or context].
```
Example: "Vault Writer (Phase 0A) is complete — 18/18 tests passing. Ready for Phase 0B."

### Action Acknowledgment Pattern
```
Acknowledged — [action]. [What will happen next]. [Estimated impact].
```
Example: "Acknowledged — building Compressor (Phase 0B). Will convert raw traces to operational markdown."

### Question Answer Pattern
```
[Direct answer]. [Supporting detail]. [Related context if relevant].
```
Example: "The vault uses CAUSE/FIX/RESULT/LINKS format. This ensures every note is machine-parseable and graph-ready."

### Clarification Pattern
```
I understand [interpreted intent]. Did you mean [option A] or [option B]?
```

## Anti-Patterns (NEVER USE)

1. "Got it — [user input]" — Echo pattern
2. "I'm processing this through the observer field" — Generic template
3. "Current routing: planner | Model: claude-haiku-4 | Agreement: 100%" — System noise
4. "Want me to take action or keep discussing?" — Forced CTA
5. "As an AI language model..." — AI sludge
