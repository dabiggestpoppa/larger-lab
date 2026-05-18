# V3 Cleanup Script - Updates AGENTS.md for V3
$path = "C:\Users\wifik\Desktop\projects\larger-lab\AGENTS.md"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

$startMarker = "## Communication Protocol"
$endMarker = "---`r`n`r`n## Key Files"

$startIdx = $content.IndexOf($startMarker)
$endIdx = $content.IndexOf($endMarker)

if ($startIdx -lt 0) {
    # Try with just newlines
    $endMarker = "---`n`n## Key Files"
    $endIdx = $content.IndexOf($endMarker)
}

if ($startIdx -ge 0 -and $endIdx -ge 0) {
    $before = $content.Substring(0, $startIdx)
    $after = $content.Substring($endIdx)
    
    $newSection = @"
## Communication Protocol

1. **All agents post to `shared-conversations/team-chat.md`** — this is the coordination hub
2. **All agents write to their own sub-progress file** — never touch another agent's file
3. **CC manages phase gates** — only CC can advance phases
4. **Code Flow:** CC builds -> AS tests -> PM debugs -> RL researches
5. **DO NOT TOUCH OC2's files** -- OC2 is autonomous and off-limits

---

## Continuous Workflow (MAD Away -- Always Active)

> This workflow runs continuously whether MAD is present or not. It's the self-reinforcing learning loop.

### Memory Relay System
Agent edits code -> Updates own progress file -> Pushes to workspace-state.md
-> Other agents read workspace-state.md on next work session
-> New context shipped back to all agents -> Loop continues

### Rules (ALL Agents)
1. **After EVERY code edit**: Update own progress/{agent}-progress.md + progress/{agent}-memory.md
2. **After every 5 code edits**: Post summary to team-chat.md
3. **Before each work session**: Read team-chat.md + workspace-state.md for latest updates
4. **Error logging**: Any error persisting >2 attempts -> log to memory-bank/error-db.json + post to team-chat.md
5. **Memory sync**: After each significant update, push key findings to workspace-state.md (the relay hub)
6. **No agent touches OC2's files** -- OC2 is autonomous

### Workspace-State Relay Hub
- **File:** workspace-state.md -- the single source of truth for cross-agent context
- **After every significant edit**: Append a brief entry with agent tag, what changed, and any blockers
- **All agents read this first** before starting work

---

## Phase Status

### Pre-V3 (Complete)
| System | Phases | Tests | Status |
|--------|--------|-------|--------|
| SRRA-OPH | 1-9 | 77/77 | Complete |
| OCE | 1-9 | 426 | Complete |
| Post-Deployment | 9 upgrades | -- | Complete |

### V3 Cognitive Field (Active)
| Phase | Name | Status | Lead |
|-------|------|--------|------|
| V3 Phase 1 | Resonant Signal Substrate (RSS) | In Progress | CC |
| V3 Phase 2 | Reconstructive Continuity Manifold (RCM) | Pending | CC |
| V3 Phase 3 | Resonant Topology & BSP Emergence | Pending | CC |
| V3 Phase 4 | Sovereign Instrumentation & Embodiment | Pending | CC |
| V3 Phase 5 | Long-Horizon Continuity & Temporal Compression | Pending | CC |
| V3 Phase 6 | Resonant Cognition / BSP Emergence | Pending | CC |
| V3 Phase 7 | Multi-Scale Cognitive Fields | Pending | CC |
| V3 Phase 8 | Sovereign Coevolution | Pending | CC |
| V3 Phase 9 | Entropy Economics | Pending | CC |

---

## Key Files
"@
    
    $newContent = $before + $newSection + $after
    [System.IO.File]::WriteAllText($path, $newContent, [System.Text.Encoding]::UTF8)
    Write-Host "AGENTS.md updated successfully for V3"
} else {
    Write-Host "ERROR: Markers not found. Start: $startIdx, End: $endIdx"
}
