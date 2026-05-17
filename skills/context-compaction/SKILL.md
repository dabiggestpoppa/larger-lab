# Context Compaction Skill

## Purpose
Systematically reduce context size while preserving critical information. Based on the 5-layer compaction pipeline from Dive-into-Claude-Code research.

## When to Context is Full
- Context window > 80% used
- Model starts losing track of earlier instructions
- Repeated information across turns
- Long-running sessions with accumulated history

## 5-Stage Compaction Pipeline

### Stage 1: Budget Reduction (Cheapest)
- Remove redundant tool outputs
- Truncate long file reads to relevant sections
- Summarize repeated patterns
- Target: 10-20% reduction

### Stage 2: Snip
- Remove old tool calls that are no longer relevant
- Keep only the most recent N turns of conversation
- Preserve: current task, recent errors, active files
- Target: 20-30% reduction

### Stage 3: Microcompact
- Summarize completed subtasks into single entries
- Merge related memory entries
- Compress code snippets to signatures only
- Target: 30-40% reduction

### Stage 4: Context Collapse
- Replace full conversation with structured summary
- Keep: decisions made, files modified, errors encountered, next steps
- Lose: intermediate reasoning, exploration dead ends
- Target: 40-60% reduction

### Stage 5: Auto-Compact (Most Aggressive)
- Full conversation → structured memory entries
- Store in Structural Memory (WORK layer)
- Keep only: current task context + recent 3 turns
- Target: 60-80% reduction

## Implementation

### Compaction Trigger
```python
def should_compact(context_usage_percent):
    if context_usage_percent > 90:
        return "AUTO_COMPACT"  # Stage 5
    elif context_usage_percent > 75:
        return "CONTEXT_COLLAPSE"  # Stage 4
    elif context_usage_percent > 60:
        return "MICROCOMPACT"  # Stage 3
    elif context_usage_percent > 40:
        return "SNIP"  # Stage 2
    return None  # No compaction needed
```

### Compaction Rules
1. **Never compact**: Current task description, active file contents, recent errors
2. **Always preserve**: Decisions made, files modified, next steps
3. **Summarize**: Completed subtasks, resolved issues
4. **Remove**: Redundant tool outputs, old exploration, dead ends

### Integration with OCE
- Compaction events emit to Event Fabric
- Compressed memories stored in Structural Memory WORK layer
- Compaction statistics tracked in observer health metrics
