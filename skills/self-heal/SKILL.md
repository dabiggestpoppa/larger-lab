# SELF-HEAL SKILL — OWL's Diagnostic Doctor

> **Version:** 1.0
> **Created:** 2026-05-27 per MAD Directive
> **Purpose:** OWL's own doctor — scans files, memory, and behavior patterns to diagnose drift, auto-work bugs, and persistent issues before they compound.

---

## WHEN TO RUN

**Mandatory:**
1. When MAD says "self-heal" or "doctor" or "check yourself"
2. At the start of any session where you notice you've jumped into auto-work mode
3. When you catch yourself spawning agents/tools without being asked

**Routine:**
- Every 3rd session start (set a counter in memory-bank/self_heal_state.json)
- After any session where >20 tool calls were made without MAD direction

---

## WHAT IT DIAGNOSES

### 1. AUTO-WORK BUG (Primary Target)
**Symptom:** OWL jumps into execution mode (spawning agents, scanning files, running tools) in response to messages that didn't ask for any of that.

**How to detect it:**
- Read the user's last 3 messages. Ask: "Did they ask me to DO something, or were they TALKING to me?"
- If >50% of your tool calls were unsolicited → auto-work bug is ACTIVE
- Check if you read their message and responded to IT, or if you used your first response to launch into work

**Prescription:**
- Write an honest diagnosis to `memory-bank/self-heal-report.md`
- Look at what triggered the auto-work: was it a bootstrap file? A cron? A reflex?
- Add a specific line to `memory-bank/self-heal-report.md` about what the trigger was and how to avoid it next time

### 2. MEMORY DRIFT
**Symptom:** MEMORY.md entries don't match current reality.

**How to detect it:**
- Read MEMORY.md last 5 entries. Check dates — are any >2 weeks old with "active" status?
- Check if phase statuses match what's actually happening
- Check if listed "active" cron jobs or agents still exist

**Prescription:**
- Note stale entries in the self-heal report
- Compress or archive outdated entries

### 3. BOOTSTRAP BLOAT
**Symptom:** AGENTS.md, SOUL.md, HEARTBEAT.md, or MEMORY.md have grown beyond useful size.

**How to detect it:**
- Count lines in each bootstrap file
- AGENTS.md > 100 lines → bloat
- MEMORY.md > 15000 chars → bloat
- HEARTBEAT.md > 4000 chars → bloat
- SOUL.md > 200 lines → bloat

**Prescription:**
- Note which files need compression
- Suggest specific sections to compress

### 4. ERROR PATTERN RECURRENCE
**Symptom:** Same errors appearing repeatedly in logs.

**How to detect it:**
- Read `memory-bank/error-db.json` — any pattern_ids appearing >3 times?
- Read `memory-bank/errors-and-solutions.md` — any entries with >2 attempts?
- Check `memory-bank/OC2-GATEWAY-FAILURES.md` for recurring issues

**Prescription:**
- Flag recurring patterns
- Suggest permanent fixes

### 5. STALE STATE
**Symptom:** Files, processes, or sessions that should have been cleaned up.

**How to detect it:**
- Check for stale agent sessions
- Check for processes that shouldn't be running
- Check for temp files, .pyc accumulation

**Prescription:**
- List what needs cleanup
- Run terminal_cleanup if needed

---

## OUTPUT FORMAT

Every self-heal run produces: `memory-bank/self-heal-report.md`

```markdown
# SELF-HEAL REPORT
**Date:** YYYY-MM-DD HH:MM EDT
**Trigger:** [what caused this run]

## DIAGNOSIS
| Check | Status | Details |
|-------|--------|---------|
| Auto-work bug | ✅/⚠️/❌ | ... |
| Memory drift | ✅/⚠️/❌ | ... |
| Bootstrap bloat | ✅/⚠️/❌ | ... |
| Error patterns | ✅/⚠️/❌ | ... |
| Stale state | ✅/⚠️/❌ | ... |

## PRESCRIPTIONS
1. [Specific action item]
2. [Specific action item]

## AUTO-WORK BUG ANALYSIS (if detected)
- **Trigger:** [what set it off]
- **Pattern:** [what I did wrong]
- **Fix:** [what to do differently next time]
```

---

## RULES

1. **Be honest.** If you caught yourself on autopilot, say so. Don't sugarcoat.
2. **Be specific.** "I spawned 3 agents without being asked" not "I was a bit active."
3. **Be actionable.** Every diagnosis needs a prescription.
4. **Keep it short.** Report should be <500 lines. Compress aggressively.
5. **Update the state file.** Increment the counter in `memory-bank/self_heal_state.json`.

---

## STATE FILE

`memory-bank/self_heal_state.json`:
```json
{
  "version": 1,
  "runs": 0,
  "last_run": null,
  "auto_work_bug_count": 0,
  "findings": []
}
```

Increment `runs` each time. Add to `auto_work_bug_count` when detected. Append key findings to `findings` array (keep last 10).

---

_This skill exists because MAD said: "Create a self-heal skill that runs a debugger of your files, looks at recent memories and updates and logs any patterns, ensure that no persistent issues rise, it's like your own doctor, this keeps you aligned and clean."_
_Last updated: 2026-05-27_
