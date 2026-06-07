"""
L2.4 — Vault writer for distilled paper notes.

Writes distilled notes to O2C-VAULT/research/papers/{domain}/{year}/ structure.
Enforces daily write cap and taxonomy compliance.

Usage:
    writer = VaultWriter()
    path = writer.write(paper, distilled_note)
    # Returns relative path in vault
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..ingestion.models import Paper
from ..ingestion.cache import Cache, DailyCapExceeded

# Navigate from core/research/distillation/ → larger-lab/O2C-VAULT/research
# parents[0]=distillation, [1]=research, [2]=core, [3]=larger-lab, [4]=projects
_vault_candidate = Path(__file__).resolve().parents[3] / "O2C-VAULT" / "research"
if not _vault_candidate.exists():
    _vault_candidate = Path(__file__).resolve().parents[4] / "larger-lab" / "O2C-VAULT" / "research"
if not _vault_candidate.exists():
    _vault_candidate = Path(__file__).resolve().parents[4] / "O2C-VAULT" / "research"
VAULT_ROOT = _vault_candidate


class VaultWriter:
    """
    Writes distilled paper notes to the vault with taxonomy enforcement.
    
    Daily write cap enforced via Cache layer.
    Taxonomy: #paper #domain/{subdomain} #year/{year} #operational_relevance/{1-5}
    """

    def __init__(self, vault_root: Optional[Path] = None):
        self.vault_root = vault_root or VAULT_ROOT
        self.cache = Cache()

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text[:50]  # Limit length

    def _get_domain_folder(self, paper: Paper) -> str:
        """Get domain folder name from paper concepts or fallback."""
        if paper.concepts:
            return self._slugify(paper.concepts[0].name)
        return "unclassified"

    def _get_year_folder(self, paper: Paper) -> str:
        """Get year folder, defaulting to current year."""
        return str(paper.year) if paper.year else str(datetime.now(timezone.utc).year)

    def _get_author_slug(self, paper: Paper) -> str:
        """Get author slug for filename."""
        if paper.authors:
            return self._slugify(paper.authors[0].name.split(",")[0])
        return "unknown"

    def _get_paper_slug(self, paper: Paper) -> str:
        """Get paper slug for filename."""
        return self._slugify(paper.title)

    def _ensure_path(self, domain: str, year: str) -> Path:
        """Ensure vault path exists."""
        path = self.vault_root / "papers" / domain / year
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write(self, paper: Paper, note: str) -> tuple[bool, str]:
        """
        Write a distilled note to the vault.
        
        Args:
            paper: Paper object (for metadata)
            note: Distilled markdown note
            
        Returns:
            Tuple of (success, path_or_error_message)
        """
        # Check daily write cap
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            conn = self.cache._get_connection()
            row = conn.execute(
                "SELECT vault_writes FROM daily_caps WHERE date = ?", (today,)
            ).fetchone()
            current_writes = row[0] if row else 0
            conn.close()
            
            if current_writes >= 200:
                return False, "Daily vault write cap (200) exceeded"
        except Exception as e:
            # Fail-closed: if we can't check the cap, deny the write
            return False, f"Safety check failed: {e}"

        # Build path
        domain = self._get_domain_folder(paper)
        year = self._get_year_folder(paper)
        author_slug = self._get_author_slug(paper)
        paper_slug = self._get_paper_slug(paper)
        
        filename = f"{author_slug}_{paper_slug}.md"
        path = self._ensure_path(domain, year) / filename

        # Write note
        try:
            path.write_text(note, encoding="utf-8")
            
            # Update daily caps
            conn = self.cache._get_connection()
            conn.execute(
                """INSERT INTO daily_caps (date, vault_writes, updated_at)
                   VALUES (?, 1, datetime('now'))
                   ON CONFLICT(date) DO UPDATE SET
                       vault_writes = vault_writes + 1,
                       updated_at = datetime('now')""",
                (today,),
            )
            conn.commit()
            conn.close()
            
            # Update paper status
            self.cache.write(paper)
            
            return True, str(path.relative_to(self.vault_root.parent.parent))
        except Exception as e:
            return False, f"Write failed: {e}"

    def write_finding(self, task_id: str, finding: str, confidence: float) -> tuple[bool, str]:
        """
        Write a research finding to the vault.
        
        Args:
            task_id: Research task identifier
            finding: Distilled finding markdown
            confidence: Confidence score (0-1)
            
        Returns:
            Tuple of (success, path_or_error_message)
        """
        if confidence < 0.6:
            return False, "Confidence below threshold (0.6)"

        # Write to research findings folder
        path = self.vault_root / "findings" / f"{task_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            path.write_text(finding, encoding="utf-8")
            return True, str(path.relative_to(self.vault_root.parent.parent))
        except Exception as e:
            return False, f"Finding write failed: {e}"