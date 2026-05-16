---
name: as-code-review
description: >
  Assistant Manager code review checklist for SRRA-OPH components.
  Use when reviewing patches, tests, or infrastructure code written by CC/OC/HR.
version: 1.0.0
---

# AS Code Review Skill

## Review Checklist for SRRA-OPH Components

### Architecture Compliance
- [ ] No global state (Rule 1) — every component is bounded
- [ ] Repair is local first (Rule 4) — no centralized repair
- [ ] Memory compresses (Rule 3) — sublinear growth
- [ ] Consensus emerges (Rule 5) — no hardcoded authority
- [ ] Components are replaceable — no hidden coupling

### Code Quality
- [ ] Type hints on all functions
- [ ] Docstrings with Args/Returns
- [ ] Error handling (no silent failures)
- [ ] No hardcoded paths or credentials
- [ ] Follows existing codebase style (snake_case, async/await)

### Test Coverage
- [ ] Unit tests for each component
- [ ] Integration tests for cross-component flows
- [ ] Failure injection tests (partial failure, corruption)
- [ ] Performance benchmarks where applicable

### SRRA-OPH Specific
- [ ] Collar protocol compliance (JSON schema)
- [ ] Patch bounded state (max limits enforced)
- [ ] Drift detection triggers correctly
- [ ] Anchor compression ratio tracked
- [ ] Entropy metrics logged

## Review Output Format

```markdown
## Code Review: <component_name>
**Reviewer:** AS
**Date:** YYYY-MM-DD
**Status:** ✅ Approve / ⚠️ Changes Required / ❌ Reject

### Issues
1. [CRITICAL] Description
2. [MINOR] Description

### Suggestions
- Improvement suggestion

### Verdict
Summary of review decision.
```
