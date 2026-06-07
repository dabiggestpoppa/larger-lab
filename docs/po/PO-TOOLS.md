# PO-TOOLS.md — Primary Observer Capability Reference

> **Agent:** PO (Primary Observer) — `core/observer/po_agent.py`
> **Last Updated:** 2026-06-07
> **Total Tools:** 80+ across 12 categories + dynamic MCP

---

## Architecture

PO uses a **dynamic tool registry** (`oce/backend/po_tool_registry.py`) that merges:
1. **Original 20 tools** — hardcoded in `po_agent.py` (backward compat)
2. **80+ dynamic tools** — from `po_capabilities.py` execution engine
3. **MCP server tools** — dynamically discovered from connected MCP servers

Tools are exposed to the LLM via OpenAI function calling format. The registry auto-generates schemas.

**Key files:**
- `oce/backend/po_tool_registry.py` — Tool definitions + OpenAI schemas
- `oce/backend/po_capabilities.py` — Execution engine (all tool implementations)
- `oce/backend/po_mcp_client.py` — MCP server bridge
- `oce/backend/po_tools_api.py` — FastAPI REST endpoints
- `core/observer/po_agent.py` — PO agent with tool-calling loop

---

## Tool Categories

### 1. File Operations (`file`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `list_directory` | List files/dirs | `path`, `max_depth`, `max_items` |
| `read_file` | Read file contents | `path`, `start_line`, `max_lines` |
| `write_file` | Write/create file | `path`, `content` |
| `edit_file` | Replace exact text | `path`, `old_text`, `new_text` |
| `multi_edit_file` | Multiple replacements | `path`, `edits[]` |
| `create_directory` | Create directory tree | `path` |
| `delete_file` | Delete file or dir | `path`, `recursive` |
| `file_exists` | Check existence | `path` |

**Safety:** All paths resolved relative to repo root. Path traversal blocked. Max file size 10MB.

### 2. Git Operations (`git`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `git_status` | Show working tree status | — |
| `git_log` | Commit history | `count` |
| `git_diff` | Show changes | `file_path`, `cached` |
| `git_commit` | Stage and commit | `message`, `files[]` |
| `git_push` | Push to remote | `remote`, `branch`, `force` |
| `git_pull` | Pull from remote | `remote`, `branch` |
| `git_branch` | Branch operations | `action` (list/create/delete/checkout), `name` |
| `git_stash` | Stash operations | `action` (push/pop/list/clear), `message` |
| `git_blame` | Line-by-line attribution | `file_path` |

### 3. Execution (`exec`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `run_command` | Run shell command (PowerShell) | `command`, `timeout`, `cwd`, `env` |
| `execute_python` | Execute Python in venv | `code`, `timeout`, `args` |
| `run_python_file` | Run .py file in venv | `path`, `timeout`, `args` |
| `install_python_package` | pip install | `package`, `upgrade` |

**Safety:** Dangerous commands blocked (rm -rf /, format, shutdown, etc.). Max output 10K chars. Default timeout 30s.

### 4. Search (`search`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `search_files` | Find files by glob | `pattern`, `path`, `max_results` |
| `search_content` | Text search in files | `query`, `path`, `file_pattern`, `case_sensitive`, `is_regex` |
| `grep_search` | Fast regex search | `query`, `path`, `file_pattern`, `max_results` |
| `web_search` | DuckDuckGo web search | `query`, `max_results` |
| `web_fetch` | Fetch URL content | `url`, `query` |

### 5. GitHub (`github`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `github_pr_list` | List PRs | `state`, `limit` |
| `github_pr_create` | Create PR | `title`, `body`, `head`, `base`, `draft` |
| `github_pr_view` | View PR details | `number` |
| `github_pr_merge` | Merge PR | `number`, `method` |
| `github_issue_list` | List issues | `state`, `limit` |
| `github_issue_create` | Create issue | `title`, `body`, `labels` |
| `github_ci_status` | CI workflow status | `limit` |
| `github_search` | Search issues/PRs | `query`, `type` |
| `github_repo_info` | Repository metadata | — |

Uses `gh` CLI. Returns error if gh not installed.

### 6. System (`system`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `system_env` | Get/set env vars | `action` (get/set/list), `name`, `value` |
| `system_processes` | List processes | `filter` |
| `system_kill_process` | Kill process | `pid` or `name`, `force` |
| `system_disk_usage` | Disk space info | `path` |
| `system_info` | OS, Python, CPU, memory | — |

### 7. Memory (`memory`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `memory_read` | Read memory file | `path` (relative to /memories/) |
| `memory_write` | Write memory file | `path`, `content` |
| `memory_list` | List memory files | `scope` (user/session/repo) |
| `memory_search` | Search memory files | `query`, `scope` |

Scopes: `user` (/memories/), `session` (/memories/session/), `repo` (/memories/repo/).

### 8. Vault (`memory`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `vault_search` | Search Obsidian vault | `query`, `max_results` |
| `vault_read` | Read vault note | `path` |

Vault location: `O2C-VAULT/`

### 9. VS Code (`vscode`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `vscode_run_command` | Run VS Code command | `command_id`, `args` |
| `vscode_get_errors` | Python syntax check | `file_path` (optional) |

### 10. Notebook (`notebook`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `notebook_list` | List .ipynb files | `path` |
| `notebook_read` | Read notebook structure | `path` |

### 11. PDF (`pdf`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `pdf_extract_text` | Extract text from PDF | `path`, `pages` |
| `pdf_merge` | Merge PDFs | `files[]`, `output` |
| `pdf_split` | Split PDF | `path`, `output_dir`, `pages` |
| `pdf_compress` | Compress PDF | `path`, `output`, `quality` |

Requires PyPDF2 / pikepdf (graceful fallback if not installed).

### 12. Tasks (`system`)

| Tool | Description | Key Params |
|------|-------------|------------|
| `task_list` | Get current task list | — |
| `task_update` | Update task list | `tasks[]` (id, title, status) |

---

## MCP Server Tools (Dynamic)

PO connects to MCP servers on startup. Tools are discovered automatically.

### Configured MCP Servers

| Server | Command | Tools |
|--------|---------|-------|
| `time` | `uvx mcp-server-time` | Timezone-aware time |
| `ddg-search` | `uvx duckduckgo-mcp-server` | Web search |
| `hermes-mcp` | `python tools/mcp_server.py` | Gateway status, memory sync |

### Adding New MCP Servers

1. Add config to `BUILTIN_MCP_SERVERS` in `po_mcp_client.py`
2. Or add to `.vscode/mcp.json` (auto-discovered)
3. Or add to `vtuber_integration/Open-LLM-VTuber/mcp_servers.json`

PO will auto-discover and register tools on next startup.

---

## REST API Endpoints

All tools are also available via REST for external clients:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/po/tools` | GET | List all tools (filter: `?category=`) |
| `/api/po/tools/schema` | GET | OpenAI-format schemas |
| `/api/po/tools/execute` | POST | Execute tool: `{"tool_name": "...", "arguments": {...}}` |
| `/api/po/tools/categories` | GET | List categories |
| `/api/po/tools/{name}` | GET | Get tool details |
| `/api/po/mcp/tools` | GET | List MCP tools |
| `/api/po/mcp/call` | POST | Call MCP tool: `server`, `tool_name`, `arguments` |

---

## Usage Rules

1. **Read before edit** — always `read_file` before `edit_file`
2. **Small changes → edit_file**, full rewrites → `write_file`
3. **Run tests after code changes** — use `run_command` with pytest
4. **Be concise** — summarize tool outputs in Telegram responses
5. **Never exfiltrate private data**
6. **Ask before destructive operations** — rm, force push, delete
7. **Use real data when available** — simulate only when no real data exists
8. **Path safety** — all paths are relative to repo root, traversal blocked
9. **Command safety** — dangerous patterns (rm -rf /, format, shutdown) are blocked
10. **Output limits** — max 10K chars per tool result, max 10MB file read

---

## Model Chain

PO uses this model fallback chain:
1. Configured model (`data/po_model.json`)
2. `inclusionai/ring-2.6-1t`
3. `openrouter/owl-alpha`
4. `minimax/minimax-m2.5`

Each model gets 2 retry attempts before falling back. Rate limited (429) and timeout errors trigger retry with backoff.
