"""Add PM2 monitoring entry to team chat."""
content = open(r'C:\Users\wifik\Desktop\projects\larger-lab\shared-conversations\team-chat.md', 'r', encoding='utf-8').read()

new_entry = """
---

## [PM2] 2026-06-03 12:00 UTC — Sync Infrastructure Audit + Monitoring Active

### Sync Scripts Status (All Audited)
| Script | Status | Fix Applied |
|--------|--------|-------------|
| `tools/progress-sync.py` | Fixed | REPO_MEMORY path corrected (was pointing to non-existent `memories/repo/`, now `progress/`) |
| `tools/obsidian_vault_sync.py` | OK | No changes needed |
| `tools/gateway_watchdog.py` | OK | No changes needed |
| `tools/po_watchdog.py` | Fixed | Indentation error on line 96 (chat log check was inside wrong block) |
| `tools/pm2_autopilot.py` | Disabled | Renamed to `.disabled` -- was spamming 50+ empty git commits |
| `scripts/start_telegram_gateway.py` | Config issue | Crashes because TELEGRAM_TOKEN not in .env (only in watchdog hardcoded) |
| `scripts/telegram_gateway.py` | OK | New Presence System gateway, syntax valid |
| `core/observer/presence_engine.py` | OK | Presence engine, syntax valid |
| `_vault_write.py` / `_vault_verify.py` | OK | Vault scripts, syntax valid |

### Issues Found
1. **Git spam** -- ~50 "PM2 autopilot: sync workspace changes" commits on master. Autopilot disabled.
2. **Telegram gateway** -- Needs TELEGRAM_TOKEN added to .env or environment
3. **workspace-state.md** -- Updated to reflect O-5/O-6 completion, ML work, Telegram Presence System

### Current Role
Monitoring CC's build progress. Will test when everything is done. Not building unless something is wrong.
"""

content = content.replace('---\n\n## [OC2]', '---\n' + new_entry + '\n## [OC2]')
open(r'C:\Users\wifik\Desktop\projects\larger-lab\shared-conversations\team-chat.md', 'w', encoding='utf-8').write(content)
print('OK - team chat updated')
