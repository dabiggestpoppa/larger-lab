# LONG HORIZON TASK PROTOCOL — Quant Lab

> **Purpose:** Enable agents to work on complex, multi-step tasks that exceed normal timeout limits
> **Created:** 2026-05-17 per MAD directive

## The Problem
Complex strategy reconstruction takes time. Agents hit 15-min timeouts before completing. Context windows fill up. Work is lost.

## The Solution: Checkpoint-Based Work

### How It Works
1. **Break work into small, checkpointed steps**
2. **After each step, save progress to a file**
3. **If timeout occurs, next agent reads the checkpoint and continues**
4. **No work is ever lost**

### Checkpoint File Format
Every long-horizon task MUST use this format:

```markdown
# CHECKPOINT — [Task Name]
> **Agent:** [agent-name] | **Started:** [timestamp] | **Last Update:** [timestamp]
> **Status:** IN PROGRESS | COMPLETE | BLOCKED

## Progress
- [x] Step 1: Read CEREBUS manual
- [x] Step 2: Audit P90 strategy code vs manual
- [ ] Step 3: Fix P90 candle detection thresholds
- [ ] Step 4: Test P90 fix
- [ ] Step 5: Audit Cascade activation
- [ ] ...

## Current Step
**Working on:** Step 3 — Fix P90 candle detection thresholds

## Findings So Far
- P90 body thresholds in code don't match manual (code uses fixed 5p, manual varies by time window)
- Cascade max count not enforced in code
- 12:00 PM hard exit missing

## Files Modified
- projects/trading/nautilus/strategies/p90_core.py (partial edit)

## Next Actions
1. Fix P90 thresholds per manual section 3.1
2. Add cascade count enforcement
3. Add 12:00 PM hard exit
4. Test each fix individually
```

### Rules for Long-Horizon Tasks

1. **ALWAYS checkpoint** — Save progress after every meaningful step
2. **Write findings immediately** — Don't hold findings in memory, write to files
3. **One change at a time** — Make one fix, test it, then move to next
4. **Save results incrementally** — Don't wait until the end to save
5. **Use the file system as memory** — Files persist, context doesn't

### Agent Room Configuration

For tasks that need more than 15 minutes:
- Spawn with `runTimeoutSeconds: 900` (15 min) — this is the hard limit
- Agent MUST checkpoint every 5-7 minutes
- If agent times out, OWL reads checkpoint and respawns with continuation instructions
- Max 3 respawns per task before escalating to MAD

### Context Efficiency Rules

1. **Read only what you need** — Don't read entire manual at once, read section by section
2. **Write summaries, not copies** — When reading a file, write a summary to your checkpoint
3. **Use targeted file reads** — Use offset/limit to read specific sections
4. **Close the loop** — After each fix, verify it works before moving on
