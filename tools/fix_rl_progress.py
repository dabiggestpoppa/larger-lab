import pathlib
p = pathlib.Path(r'C:\Users\wifik\Desktop\projects\larger-lab\progress\rl-progress.md')
content = p.read_text(encoding='utf-8')

old = "#### 🦉 [RL] 2026-05-16 — Scrapling Skill Installed for All Agents"
new = """#### 🦉 [RL] 2026-05-16 — Violin Video Translation Skill Installed
- Installed `violin` v0.1.1 + fixed f-string syntax bug in `pipeline/costs.py` (Python 3.11 compat)
- Verified `violin --help` and `violin-api` both work
- Created `skills/violin/SKILL.md` -- concise reference for all agents
- Copied to `.agents/skills/violin/SKILL.md` for agent harness loading
- Updated `TOOLS.md` with Violin section (also restored file after corruption)
- Posted announcement to `shared-conversations/team-chat.md`
- **Note:** Requires `TOGETHER_API_KEY` env var to actually translate videos

#### 🦉 [RL] 2026-05-16 — Scrapling Skill Installed for All Agents"""

content = content.replace(old, new)
p.write_text(content, encoding='utf-8')
print('Done')
