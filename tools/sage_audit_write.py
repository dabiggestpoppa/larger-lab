"""
SAGE Audit — Write audit findings to Obsidian vault
"""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from core.obsidian.vault_writer import VaultWriter

vw = VaultWriter(vault_path='C:/Users/wifik/Downloads/o2c')

title = "SAGE_AUDIT_Environment_Utilization"

content = {
    "cause": """OWL has TWO parallel persistence systems:
- Obsidian Vault (C:/Users/wifik/Downloads/o2c) — declared PRIMARY continuity substrate
- Local MD files (progress/*.md, workspace paths) — treated as primary in practice

Pattern: OWL defaults to local files, treats Obsidian as secondary.

Evidence:
- progress/ contains 47 MD files with ALL operational progress tracking
- execution/ in vault has only 7 files (mostly static guides, not live logs)
- doctrine/ has only 3 imported files, none written during active operations
- Track A progress (most recent major work) written to progress/track_a_progress.md NOT to vault
- journals/daily_runtime/ is EMPTY
- journals/backtest_logs/ is EMPTY
- journals/forward_test_logs/ is EMPTY
- memory/error_corrections/ is EMPTY
- memory/spawn_history/ is EMPTY
- memory/consensus_failures/ is EMPTY

The Obsidian vault is structurally complete but operationally nearly EMPTY.""",

    "fix": """MANDATORY RULES FOR ALL FUTURE OWL OPERATIONS:

1. EVERY progress update goes to Obsidian vault/execution/ FIRST, progress/ secondarily
2. Every backtest result gets a note in vault/journals/backtest_logs/
3. Every spawn gets logged in vault/memory/spawn_history/
4. Every failure gets logged in vault/memory/error_corrections/ or vault/failures/
5. Daily operational summaries go to vault/journals/daily_runtime/
6. MEMORY.md stays as working memory but key decisions must be mirrored to vault/memory/
7. Subagents MUST receive vault_path in their task briefs with explicit write instructions
8. After every major task: write to vault AND update MEMORY.md — both, not either/or
9. VaultWriter usage is MANDATORY, not optional — no more raw file writes to workspace for operational logs
10. Weekly: reconcile progress/ files with vault/execution/ — anything missing gets copied over""",

    "result": """AUDIT SUMMARY:

| Metric | Local Files | Obsidian Vault |
|--------|-------------|----------------|
| Progress tracking files | 47 | 0 (track_a not synced) |
| Execution logs | 0 | 7 (mostly guides) |
| Doctrine files | Multiple in workspace | 3 (imported) |
| Backtest logs | quant-lab/reports/ | 0 (empty dir) |
| Daily journals | 0 | 0 (empty dir) |
| Error corrections | memory/memory-bank/ | 0 (empty dir) |
| Spawn history | 0 | 0 (empty dir) |

SEVERITY: HIGH — OWL is violating its own Obsidian Directive (SOUL.md primary memory policy)

RECOMMENDATION: Immediate migration of recent operational notes from progress/ and MEMORY.md to Obsidian vault. Going forward, vault-first policy with zero exceptions.

SPECIFIC ACTIONS:
1. Migrate progress/track_a_progress.md summary to vault/execution/Track_A_Build_Complete.md
2. Migrate latest MEMORY.md decisions to vault/memory/OPERATIONAL_STATE_20260531.md
3. Write daily runtime entry for today to vault/journals/daily_runtime/
4. Update subagent spawn template to require vault writes as deliverable checkpoint""",

    "links": [
        "OC2_VAULT_ACCESS_GUIDE.md",
        "Live_Deployment_Status.md",
        "FOUNDATIONAL_PRINCIPLES.md"
    ]
}

result = vw.write_note(
    category='doctrine',
    title=title,
    content=content,
    tags=['sage', 'audit', 'environment', 'vault', 'obsidian', 'critical', 'owl']
)

print(f"Written: {result['path']}")
print(f"Audit complete.")
