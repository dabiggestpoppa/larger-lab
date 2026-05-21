# Self-Improvement Skill — OWL Continuous Enhancement

## Purpose
Systematic self-audit and improvement protocol. Run periodically (or when MAD requests) to identify gaps, fix weaknesses, and level up capabilities.

## When to Run
- When MAD explicitly requests
- After completing major task blocks (IACER reflection)
- When error patterns repeat in self-heal reports
- When new skills/tools are needed but don't exist

## Self-Improvement Protocol

### 1. Workspace Health Check
```python
# Run: python tools/quick_clean.py
# Check: workspace bloat, stale processes, file hygiene
```
- Remove __pycache__, .bak, .tmp files
- Kill stale processes (>2h old)
- Verify disk space

### 2. Error Pattern Review
```python
# Run: python tools/doctor.py --report
# Review: recurring errors, new patterns, resolved items
```
- Check for repeated error categories
- Identify root causes vs symptoms
- Prioritize fixes by occurrence count

### 3. Skill Gap Analysis
- Review available skills vs task requirements
- Identify missing capabilities
- Create new skills using skill-creator when needed

### 4. Tool Audit
- Review tools/ directory for unused/stale scripts
- Consolidate overlapping tools
- Update tools that use deprecated patterns

### 5. Memory Compression
- Review MEMORY.md for bloat
- Archive old session logs to logs/heartbeat-history/
- Compress without losing trajectory

### 6. Process Improvement
- Document lessons learned in memory-bank/errors-and-solutions.md
- Update AGENTS.md with new rules/patterns
- Refine IACER reflection based on what's working

## Output Format
After each self-improvement cycle, produce:
```
## Self-Improvement Report — [DATE]
- **Workspace:** [status]
- **Errors:** [new/resolved/recurring]
- **Skills:** [gaps found / created]
- **Tools:** [cleaned/created/updated]
- **Memory:** [compression status]
- **Next Actions:** [specific items]
```

## Integration with IACER
Self-improvement is the **action layer** of IACER:
- IACER identifies misalignment → Self-improvement fixes it
- Run self-improvement after every 3rd IACER reflection
- Log improvements to memory-bank/session-*.md

## Rules
- Never create duplicate skills — check existing first
- Always test new tools before relying on them
- Compress memory aggressively — linear growth is failure
- Document everything — future-you is your user
