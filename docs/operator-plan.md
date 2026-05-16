# Operator Plan — Phased Implementation

> **Source:** `C:\Users\wifik\Downloads\operator idea.txt`
> **Lead:** PM (Polymorph) + CC coordination
> **Status:** Ready for PM execution
> **Timeline:** While others finish OCE Phase 1 tasks

---

## What This Is

Turning OpenClaw from a chat interface into a **system-level operator** — something that can control the desktop, operate VS Code, execute system commands, and modify its own environment.

## Architecture

```
OpenClaw Core (Node.js)
  │
  ├── Desktop Control Layer (NEW)
  │     ├── Screen Capture
  │     ├── Input Simulation (mouse/keyboard)
  │     └── UI-TARS integration (visual analysis)
  │
  ├── VS Code Controller (NEW)
  │     ├── File operations (open, edit, search)
  │     ├── Terminal control
  │     ├── Git operations
  │     └── Extension management
  │
  └── System Operator (NEW)
        ├── Shell command execution
        ├── Process management
        ├── Resource monitoring
        ├── Package installation
        └── Cron/scheduled tasks
```

---

## Phase 1: System Operator (PM — Start Immediately)

**Goal:** Give OpenClaw full system-level control via shell commands, process management, and resource monitoring.

### Files to Create

1. **`tools/operator/system-operator.js`** — Core system control
   - `system_run_command` — Execute shell commands (already partially exists, extend it)
   - `system_run_script` — Create and run temp scripts
   - `system_list_processes` — List/kill processes
   - `system_get_resources` — CPU, memory, disk, network
   - `system_install_package` — Auto-detect package manager (brew/apt/winget/npm/pip)
   - `system_cron_manage` — List/add/remove cron jobs
   - `system_env_manage` — Get/set environment variables
   - `system_file_permissions` — chmod/chown

2. **`tools/operator/system-operator.test.js`** — Tests for each tool

### Implementation Notes
- Windows is the target platform (PowerShell + winget)
- Use `child_process.exec` for simple commands, `spawn` for long-running
- Auto-detect package manager: winget (Windows), brew (macOS), apt (Linux)
- All tools return `{ success: true/false, ...data }` format

### Estimated Effort: 2-3 hours

---

## Phase 2: VS Code Controller (PM — After Phase 1)

**Goal:** Give OpenClaw direct control over VS Code through its CLI.

### Files to Create

3. **`tools/operator/vscode-controller.js`** — VS Code control
   - `vscode_open_file` — Open files with line/column navigation
   - `vscode_run_command` — Execute any VS Code command by ID
   - `vscode_run_in_terminal` — Run commands in integrated terminal
   - `vscode_search_workspace` — Search across workspace (use ripgrep)
   - `vscode_edit_file` — Insert/replace/delete text
   - `vscode_install_extension` — Install extensions
   - `vscode_git_commit` — Stage, commit, push
   - `vscode_get_problems` — Read error/warning panel

4. **`tools/operator/vscode-controller.test.js`** — Tests

### Implementation Notes
- VS Code CLI (`code` command) is the primary interface
- For file edits, use `code --goto` + terminal sendSequence
- For search, use ripgrep (`rg`) — faster than VS Code's built-in
- Find VS Code CLI path: check common locations (LOCALAPPDATA on Windows)

### Estimated Effort: 2-3 hours

---

## Phase 3: Desktop Control (PM — After Phase 2)

**Goal:** Give OpenClaw eyes and hands — screen capture + input simulation.

### Files to Create

5. **`tools/operator/desktop-control.js`** — Desktop control
   - `desktop_screenshot` — Capture screen (full or region)
   - `desktop_click` — Click by coordinates or element description
   - `desktop_type` — Type text into focused element
   - `desktop_key` — Keyboard shortcuts (Ctrl+S, Alt+Tab, etc.)
   - `desktop_find_element` — Find UI elements (coordinates or description)
   - `desktop_wait_for` — Wait for element to appear
   - `desktop_scroll` — Scroll in direction
   - `desktop_drag` — Drag and drop

6. **`tools/operator/screenshot.js`** — Screen capture helper
   - Use `screenshot-desktop` npm package (cross-platform)
   - Save to `.openclaw/screenshots/` directory
   - Return base64 + file path

7. **`tools/operator/input-sim.js`** — Input simulation helper
   - Windows: PowerShell mouse_event + SendKeys
   - Use `robotjs` npm package as alternative (native bindings)

### Implementation Notes
- **Windows-first:** Use PowerShell for mouse/keyboard (already available)
- `screenshot-desktop` package works cross-platform
- `robotjs` is more reliable for input but requires native compilation
- Start with PowerShell approach, add `robotjs` later if needed
- UI-TARS integration is **Phase 4** (requires separate server)

### Estimated Effort: 3-4 hours

---

## Phase 4: UI-TARS Integration (PM — After Phase 3, with CC coordination)

**Goal:** Visual desktop control — OpenClaw can see and understand the screen.

### Prerequisites
- UI-TARS-desktop cloned and running (`localhost:3000`)
- Or: Use a simpler vision model (GPT-4V, Claude Vision) for screen analysis

### Approach Option A: UI-TARS Server
```bash
git clone https://github.com/bytedance/UI-TARS-desktop.git
cd UI-TARS-desktop
npm install
npm run start
```

### Approach Option B: Direct Vision API (Simpler)
- Take screenshot → send to Claude/GPT vision API → get element coordinates
- No separate server needed
- Slower but works immediately

### Files to Create

8. **`tools/operator/ui-tars-client.js`** — UI-TARS API client
   - `analyze_screen(screenshot)` → UI element list
   - `find_element(screenshot, description)` → coordinates
   - `execute_action(action_plan)` → step-by-step execution

### Estimated Effort: 2-3 hours (Option B), 4-5 hours (Option A)

---

## Phase 5: Self-Modification (PM — After Phase 4, CC approval required)

**Goal:** OpenClaw can modify its own code, configs, and environment.

### Safety Rules (MUST implement first)
1. **No self-modification without CC approval** — log all changes
2. **Git backup before any self-change** — auto-commit current state
3. **Rollback capability** — keep last 5 states
4. **No modification of core OpenClaw runtime** — only workspace/tools

### Files to Create

9. **`tools/operator/self-mod.js`** — Self-modification with guardrails
   - `self_modify_file(path, changes)` — Edit own tool files
   - `self_create_tool(name, code)` — Create new tools
   - `self_update_config(key, value)` — Update own config
   - `self_backup()` — Create git backup
   - `self_rollback(steps)` — Rollback N steps

### Estimated Effort: 2-3 hours

---

## Execution Order

| Phase | Component | Lead | Depends On | Status |
|-------|-----------|------|------------|--------|
| 1 | System Operator | PM | None | Ready |
| 2 | VS Code Controller | PM | Phase 1 | Pending |
| 3 | Desktop Control | PM | Phase 2 | Pending |
| 4 | UI-TARS Integration | PM+CC | Phase 3 | Pending |
| 5 | Self-Modification | PM+CC | Phase 4 | Pending |

---

## Immediate Next Steps for PM

1. **Create `tools/operator/` directory**
2. **Implement Phase 1 (System Operator)** — start with `system_run_command` and `system_get_resources` since the patterns already exist in the codebase
3. **Test on Windows** — all code targets Windows first (PowerShell + winget)
4. **Post progress to team-chat.md** — tag CC when Phase 1 is done

## Integration with OCE

Once OCE Phase 1 completes, the Operator tools integrate naturally:
- OCE Continuity Core can call Operator tools via SRRA-OPH substrate
- Operator becomes the "hands" of the continuity shell
- Desktop control enables OCE to operate any application, not just APIs
