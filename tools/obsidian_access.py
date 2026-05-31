"""
Obsidian Vault Access — Minimal Python module for all agents/subagents.
No OCE dependencies needed. Pure pathlib file writes.

Usage:
    from tools.obsidian_setup import vault_write
    
    vault_write(
        category="execution",
        title="my_report",
        content="# Report\n\nDetails...",
        tags=["report", "backtest"]
    )
"""

from pathlib import Path

# DEFAULT_OBSIDIAN_VAULT = Path("C:/Users/wifik/Downloads/o2c")
DEFAULT_OBSIDIAN_VAULT = Path("C:/Users/wifik/Downloads/o2c")


def vault_write(
    category: str,
    title: str,
    content: str,
    tags: list[str] = None,
    vault_path: str = None,
) -> str:
    """
    Write a markdown note to the Obsidian vault.
    
    Args:
        category: Folder name (agents, doctrine, execution, failures, etc.)
        title: Note filename (will add .md if missing)
        content: Full markdown content string
        tags: Optional list of tags
        vault_path: Override vault path (defaults to real Obsidian vault)
    
    Returns:
        Absolute path of the written file
    """
    base = Path(vault_path) if vault_path else DEFAULT_OBSIDIAN_VAULT
    folder = base / category
    folder.mkdir(parents=True, exist_ok=True)
    
    fname = title if title.endswith(".md") else f"{title}.md"
    # Sanitize filename
    fname = "".join(c for c in fname if c.isalnum() or c in "._- /").strip()
    filepath = folder / fname
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return str(filepath)


def vault_read(
    category: str,
    title: str,
    vault_path: str = None,
) -> str:
    """Read a markdown note from the Obsidian vault."""
    base = Path(vault_path) if vault_path else DEFAULT_OBSIDIAN_VAULT
    fname = title if title.endswith(".md") else f"{title}.md"
    filepath = base / category / fname
    return filepath.read_text(encoding="utf-8")


def vault_list(category: str = "", vault_path: str = None) -> list[str]:
    """List notes in a category (or all notes if category is empty)."""
    base = Path(vault_path) if vault_path else DEFAULT_OBSIDIAN_VAULT
    results = []
    if category:
        d = base / category
        if d.exists():
            results = [f.name for f in d.iterdir() if f.suffix == ".md"]
    else:
        for d in sorted(base.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                for f in d.iterdir():
                    if f.suffix == ".md":
                        results.append(f"{d.name}/{f.name}")
    return results


# Quick self-test
if __name__ == "__main__":
    print("Available categories:")
    for cat in vault_list():
        if "/" not in cat:
            continue
        print(f"  {cat}")
    print(f"\nReal vault path: {DEFAULT_OBSIDIAN_VAULT}")
    print(f"Real vault exists: {DEFAULT_OBSIDIAN_VAULT.exists()}")
