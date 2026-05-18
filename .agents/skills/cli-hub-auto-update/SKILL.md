# CLI-Hub Auto-Update Skill

> Automatically check CLI-Hub for new/updated skills and recommend updates.

## Purpose

CLI-Hub (`cli-anything-hub`) provides a registry of 76+ CLI tools organized by category.
This skill checks for new/updated CLIs, compares against installed ones, and recommends updates.

## Prerequisites

```bash
pip install cli-anything-hub
```

**Note:** Requires Python 3.12+ for full compatibility. On Python 3.11, a patch is needed
in `cli_hub/preview.py` (f-string backslash issue). See episodic memory for fix details.

## Usage

### List All Available CLIs
```bash
cli-hub list
```

### Search for Specific CLIs
```bash
cli-hub search <keyword>
cli-hub search memory
cli-hub search trading
cli-hub search agent
```

### Install a CLI
```bash
cli-hub install <cli-name>
cli-hub install hacker-feeds-cli
cli-hub install chromadb
```

### Check for Updates
```bash
cli-hub list --installed  # (if supported)
```

## Auto-Update Check Procedure

1. Run `cli-hub list` to get all available CLIs
2. Compare against installed CLIs (check `cli-hub list --installed` or track manually)
3. Check for new categories or CLIs not previously available
4. Recommend updates based on project needs

## Relevant CLIs for Our Project

| CLI | Category | Use Case | Installed |
|-----|----------|----------|-----------|
| hacker-feeds-cli | search | GitHub Trending, HN, Reddit | ❌ |
| chromadb | database | Vector DB for memory | ❌ |
| ollama | ai | Local LLM inference | ❌ |
| obsidian | knowledge | Note management | ❌ |
| obsidian-cli | knowledge | Vault automation | ❌ |
| n8n | automation | Workflow automation | ❌ |
| pm2 | devops | Node.js process management | ❌ |
| zotero | office | Research paper management | ❌ |

## Periodic Check Schedule

Run this check:
- **Weekly:** `cli-hub list` → compare against last known state
- **Before new project phases:** Search for relevant CLIs
- **When MAD requests new capability:** Search CLI-Hub first

## Integration with Agent Hooks

The pre-tool-use hook (`tools/agent-hooks/pre-tool-use-enhanced.py`) blocks edits to
config files without approval. When installing new CLIs that modify config, ensure
the hook is aware of the new config paths.

## Troubleshooting

### Python 3.11 Syntax Error
If `cli-hub list` fails with `SyntaxError: f-string expression part cannot include a backslash`:
1. Open `site-packages/cli_hub/preview.py`
2. Find the f-string with escaped quotes inside `{}`
3. Extract the string to a variable before the f-string

### Encoding Errors on Windows
If install fails with `UnicodeEncodeError: 'charmap' codec`:
```bash
$env:PYTHONIOENCODING="utf-8"
cli-hub install <name>
```
