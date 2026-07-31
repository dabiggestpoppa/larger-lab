---
name: context-compaction
description: 5-layer context compaction pipeline for AI agents. Reduces context size before model calls using budget reduction, snip, microcompact, context collapse, and auto-compact strategies.
---

# Context Compaction Skill

Reduces agent context size using a 5-layer pipeline, cheapest first.

## Usage

```python
from tools.context_compaction import ContextCompactor, compact_messages

# Method 1: Use the compactor directly
compactor = ContextCompactor(max_tokens=200000)
result = compactor.compact(messages)

# Method 2: Convenience function for raw dicts
result = compact_messages(messages, max_tokens=200000)

# Check results
print(f"Reduction: {result.reduction_pct:.1f}%")
print(f"Layers applied: {result.layers_applied}")
```

## 5 Layers (Cheapest First)

1. **Budget Reduction** — Caps individual message sizes (always active)
2. **Snip** — Trims older history, keeps first 2 + last 4 turns
3. **Microcompact** — Deduplicates, compresses whitespace, truncates long outputs
4. **Context Collapse** — Groups related messages into summaries
5. **Auto-Compact** — Full model-generated summary (last resort)

## When to Use

- Before every model call when context exceeds 70% of max tokens
- When working with long conversation histories
- When delegating to subagents with limited context windows
