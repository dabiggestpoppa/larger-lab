---
name: agent-onboarding
description: Onboard a new agent into the larger-lab workspace. Creates identity, progress tracking, memory files, standby prompt, registers in agent tags, and distributes skills. Use when a new agent joins the team or when asked to "onboard X", "add agent X", "set up X agent", or "create a new agent". Also triggers on "new agent", "register agent", "agent setup".
---

# Agent Onboarding Skill

Creates a complete agent presence in the workspace with all required files, registrations, and skill distributions.

## When to Use
- A new agent is joining the team
- User says "onboard X", "add agent X", "set up X agent"
- User says "create a new agent for X"
- Any agent needs to be formally registered in the workspace

## Quick Start (CLI Tool)
```bash
python tools/agent-onboarding-tool.py --name "Sentinel" --tag "ST" --emoji "🛡️" --role "Security Monitor"
```

## Required Inputs
Collect these before starting (ask if not provided):
1. **Agent name** — e.g., "OWL", "Sentinel", "Architect"
2. **Tag** — 2-3 letter code, e.g., "RL", "ST", "AR"
3. **Emoji** — e.g., 🦉, 🛡️, 🏗️
4. **Role** — e.g., "Research Lead", "Security Monitor"
5. **Reports to** — which existing agent (usually CC)

## Onboarding Steps

### Step 1: Create Identity File
Create `progress/{TAG}_IDENTITY.md` with:
- Name, alias, tag, emoji, role, vibe
- Purpose (what the agent does)
- Signature format: `{emoji} [{tag}] — All progress entries tagged with this signature`
- Domain expertise
- Reports to

### Step 2: Create Progress File
Create `progress/{tag}-progress.md` with:
- Header: `# {emoji} [{tag}] {name} — Progress`
- Auto-sync note
- Initial entry: agent initialized, identity created, registered

### Step 3: Create Memory File
Create `progress/{tag}-memory.md` with:
- Header: `# {emoji} [{tag}] {name} — Working Memory`
- Auto-sync note
- Key findings section (empty initially)

### Step 4: Create Standby Prompt
Create `shared-conversations/{tag.lower()}-prompt.md` with:
- Agent name, tag, role, reports to
- Purpose (5 bullet points)
- How You Work (6 bullet points)
- Key Commands
- Onboarding instructions (if applicable)
- Error handling
- Current build status
- What to Do Right Now

### Step 5: Register in Agent Tags
Add to `.agent-tags.json` under `agents`:
```json
"{tag.lower()}": {
  "tag": "{TAG}",
  "name": "{name}",
  "role": "{role}",
  "color": "{emoji}",
  "progress_prefix": "{tag}"
}
```

### Step 6: Add to Progress Sync
Add to `tools/progress-sync.py` AGENTS dict:
```python
"{TAG}": {
    "tag": "{TAG}",
    "name": "{name}",
    "emoji": "{emoji}",
    "progress_file": "progress/{tag}-progress.md",
    "memory_file": "progress/{tag}-memory.md",
    "section_header": "{emoji} [{tag}] {name}",
},
```

### Step 7: Update Workspace Memory
Add entry to `MEMORY.md`:
```
## {emoji} [{tag}] {name}
- **Role:** {role}
- **Registered:** {date}
- **Identity:** `progress/{TAG}_IDENTITY.md`
```

### Step 8: Post Intro to Team Chat
Add to `shared-conversations/team-chat.md` under Messages:
```markdown
### {emoji} [{tag}] {name} — {timestamp}Z — Agent Onboarded
- Registered in `.agent-tags.json` as {tag}
- Identity: `progress/{tag}_IDENTITY.md`
- Progress: `progress/{tag}-progress.md`
- Memory: `progress/{tag}-memory.md`
- Standby prompt: `shared-conversations/{tag.lower()}-prompt.md`
- Added to `tools/progress-sync.py` AGENTS registry
- Standing by for task assignments
```

### Step 9: Distribute Skills
Copy relevant skills to agent skill directories:
- `.openclaw/skills/` (for OpenClaw)
- `.hermes/skills/` (for Hermes persistent)
- `agent-lab/agents/hermes/skills/` (for Hermes workspace)

## Verification Checklist
After onboarding, verify:
1. [ ] Identity file exists at `progress/{TAG}_IDENTITY.md`
2. [ ] Progress file exists at `progress/{tag}-progress.md`
3. [ ] Memory file exists at `progress/{tag}-memory.md`
4. [ ] Standby prompt exists at `shared-conversations/{tag.lower()}-prompt.md`
5. [ ] Agent appears in `.agent-tags.json`
6. [ ] Agent appears in `tools/progress-sync.py` AGENTS dict
7. [ ] MEMORY.md updated with agent entry
8. [ ] Team chat has intro message
9. [ ] Skills distributed to agent directories
