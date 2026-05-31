"""
Write OC2 Vault Access Guide to Obsidian vault.
Run once to populate the vault with access instructions for all agents.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from core.obsidian.vault_writer import VaultWriter

vw = VaultWriter(vault_path='C:/Users/wifik/Downloads/o2c')

GUIDE_LINES = [
    "---",
    "title: OC2 Vault Access Guide",
    "date: 2026-05-31",
    "author: OC2/OWL",
    "tags: [vault, obsidian, access, guide, team, subagent]",
    "---",
    "",
    "# OC2 Vault Access Guide",
    "",
    "> All subagents and team members can write directly to the Obsidian vault.",
    "> No need to route through OWL.",
    "",
    "## Two Vault Locations",
    "",
    "| Vault | Path | Purpose |",
    "|-------|------|---------|",
    "| **Real Obsidian** | `C:\\Users\\wifik\\Downloads\\o2c` | Obsidian app watches this |",
    "| **Default (workspace)** | `O2C-VAULT/` | Internal workspace vault |",
    "",
    "## How to Write (Python)",
    "",
    "```python",
    "from core.obsidian.vault_writer import VaultWriter",
    "vw = VaultWriter(vault_path='C:/Users/wifik/Downloads/o2c')",
    "vw.write_note(category='execution', title='Agent Report',",
    "    content={'cause':'...','fix':'...','result':'...'},",
    "    tags=['agent','report'])",
    "```",
    "",
    "## How to Write (REST API)",
    "",
    "```bash",
    "# Real Obsidian vault",
    "POST /api/vault/write?vault=obsidian",
    "# Default workspace vault",
    "POST /api/vault/write",
    "```",
    "",
    "## Available Categories",
    "",
    "agents, architecture, doctrine, execution, failures, graphs,",
    "heuristics, journals, memory, ontology, routing, skills",
    "",
    "## Subagent Spawn Template",
    "",
    "When spawning subagents, include this in their task brief:",
    "",
    "```",
    "OBSIDIAN_VAULT = 'C:/Users/wifik/Downloads/o2c'",
    "from core.obsidian.vault_writer import VaultWriter",
    "vw = VaultWriter(vault_path=OBSIDIAN_VAULT)",
    "# Write your output directly",
    "vw.write_note(category='YOUR_CATEGORY', title='YOUR_TITLE',",
    "    content={...}, tags=['your','tags'])",
    "```",
    "",
    "## Vault Structure",
    "",
    "```",
    "o2c/",
    "├── agents/          - Agent-specific notes and meditations",
    "├── architecture/    - System architecture docs",
    "├── doctrine/        - Operational doctrine and principles",
    "├── execution/       - Execution logs and reports",
    "├── failures/        - Failure index and error analysis",
    "├── graphs/          - Relationship graphs",
    "├── heuristics/      - Heuristic rules and patterns",
    "├── journals/        - Daily/backtest/forward-test logs",
    "├── memory/          - Memory chains and continuity",
    "├── ontology/        - Strategy ontology",
    "├── routing/         - Routing logic and capital flow",
    "└── skills/          - Skill definitions and documentation",
    "```",
]

content_text = "\n".join(GUIDE_LINES)

r = vw.write_note(
    category='execution',
    title='OC2_VAULT_ACCESS_GUIDE',
    content={
        'cause': 'Subagents need direct Obsidian write access',
        'fix': 'VaultWriter with vault_path parameter',
        'result': 'All agents can write directly to real Obsidian vault',
        'full_guide': content_text,
    },
    tags=['vault', 'obsidian', 'access', 'guide', 'team', 'subagent'],
)
print("Written:", r.get('path', 'OK'))

# Also write to agents category for visibility
r2 = vw.write_note(
    category='agents',
    title='OC2_VAULT_ACCESS_GUIDE',
    content={
        'cause': 'Subagents need direct Obsidian write access',
        'fix': 'VaultWriter with vault_path parameter',
        'result': 'All agents can write directly to real Obsidian vault',
    },
    tags=['vault', 'obsidian', 'access', 'guide'],
)
print("Written:", r2.get('path', 'OK'))
