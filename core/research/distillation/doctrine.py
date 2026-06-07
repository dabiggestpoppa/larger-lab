"""
L2.7 — Doctrine extractor.

Scans distilled paper notes for recurring patterns.
When ≥3 papers share a CAUSE or METHOD → auto-extract doctrine note.

Usage:
    extractor = DoctrineExtractor()
    doctrines = extractor.extract_from_vault()
    # Returns list of created doctrine paths
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Doctrine extraction thresholds (per TEAM-NOTES §0)
MIN_PAPERS_FOR_DOCTRINE = 3
MIN_METHOD_DIVERSITY = 2  # Pattern must appear across ≥2 different methods

# Vault paths
VAULT_PAPERS_DIR = Path(__file__).resolve().parents[4] / "O2C-VAULT" / "research" / "papers"
VAULT_DOCTRINE_DIR = Path(__file__).resolve().parents[4] / "O2C-VAULT" / "doctrine"


class DoctrineExtractor:
    """
    Extracts doctrine notes from recurring patterns in distilled papers.
    
    Scans O2C-VAULT/research/papers/ for CAUSE/METHOD patterns.
    When ≥3 papers share a pattern across ≥2 different methods → create doctrine note.
    """

    def __init__(
        self,
        min_papers: int = MIN_PAPERS_FOR_DOCTRINE,
        min_method_diversity: int = MIN_METHOD_DIVERSITY,
        vault_root: Optional[Path] = None,
    ):
        self.min_papers = min_papers
        self.min_method_diversity = min_method_diversity
        if vault_root:
            global VAULT_PAPERS_DIR, VAULT_DOCTRINE_DIR
            VAULT_PAPERS_DIR = vault_root / "research" / "papers"
            VAULT_DOCTRINE_DIR = vault_root / "doctrine"

    def extract(self, papers: List[Any], domain: str = "general") -> List[str]:
        """
        Extract doctrine from a list of Paper objects.
        
        Args:
            papers: List of Paper objects
            domain: Domain tag for the doctrine note
            
        Returns:
            List of created doctrine note paths (empty if below threshold)
        """
        if len(papers) < self.min_papers:
            return []

        # Build simple concept frequency map
        concept_counts: Dict[str, int] = defaultdict(int)
        for paper in papers:
            for concept in paper.concepts:
                concept_counts[concept.name] += 1

        # Find recurring concepts (appearing in ≥ min_papers)
        recurring = {
            name: count for name, count in concept_counts.items()
            if count >= self.min_papers
        }

        if not recurring:
            return []

        # Create doctrine note for top recurring concept
        created = []
        top_concept = max(recurring, key=recurring.get)
        note = self._format_doctrine_note(top_concept, papers, domain)
        
        VAULT_DOCTRINE_DIR.mkdir(parents=True, exist_ok=True)
        domain_dir = VAULT_DOCTRINE_DIR / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        path = domain_dir / f"{top_concept.lower().replace(' ', '_')}.md"
        try:
            path.write_text(note, encoding="utf-8")
            created.append(str(path))
        except Exception as e:
            logger.error(f"Failed to write doctrine note: {e}")

        return created

    def extract_from_vault(self) -> List[str]:
        """
        Scan vault for recurring patterns and extract doctrine.
        
        Returns list of created doctrine file paths.
        """
        if not VAULT_PAPERS_DIR.exists():
            logger.warning(f"Vault papers dir not found: {VAULT_PAPERS_DIR}")
            return []

        # Collect all paper notes
        papers = self._collect_papers()
        
        if len(papers) < self.min_papers:
            logger.info(f"Not enough papers for doctrine extraction ({len(papers)} < {self.min_papers})")
            return []

        # Find recurring patterns
        cause_patterns = self._find_cause_patterns(papers)
        method_patterns = self._find_method_patterns(papers)

        # Extract doctrine notes
        created = []
        
        for pattern, paper_ids in cause_patterns.items():
            if len(paper_ids) >= self.min_papers:
                path = self._create_doctrine_note(pattern, paper_ids, papers, "cause")
                if path:
                    created.append(path)

        for pattern, paper_ids in method_patterns.items():
            if len(paper_ids) >= self.min_papers:
                path = self._create_doctrine_note(pattern, paper_ids, papers, "method")
                if path:
                    created.append(path)

        logger.info(f"Doctrine extraction: created {len(created)} doctrine notes")
        return created

    def _collect_papers(self) -> Dict[str, Dict[str, str]]:
        """
        Collect all paper notes from vault.
        
        Returns dict mapping paper_id -> {cause, method, result, ...}
        """
        papers = {}
        
        for md_file in VAULT_PAPERS_DIR.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                parsed = self._parse_note(content)
                if parsed:
                    paper_id = md_file.stem
                    papers[paper_id] = parsed
            except Exception as e:
                logger.debug(f"Failed to parse {md_file}: {e}")

        return papers

    def _parse_note(self, content: str) -> Optional[Dict[str, str]]:
        """Parse a distilled paper note into fields."""
        result = {}
        
        for field in ["CAUSE", "METHOD", "RESULT", "LIMITATIONS", "APPLICATION"]:
            pattern = rf"^{field}:\s*(.+?)(?=\n[A-Z]+:|\nLINKS:|\n#|$)"
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                result[field.lower()] = match.group(1).strip()
        
        return result if result else None

    def _find_cause_patterns(self, papers: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
        """Find recurring CAUSE patterns across papers."""
        pattern_papers: Dict[str, List[str]] = defaultdict(list)
        
        for paper_id, fields in papers.items():
            cause = fields.get("cause", "")
            if cause:
                # Normalize: lowercase, remove stop words
                normalized = self._normalize_pattern(cause)
                if normalized:
                    pattern_papers[normalized].append(paper_id)

        return {k: v for k, v in pattern_papers.items() if len(v) >= self.min_papers}

    def _find_method_patterns(self, papers: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
        """Find recurring METHOD patterns across papers."""
        pattern_papers: Dict[str, List[str]] = defaultdict(list)
        
        for paper_id, fields in papers.items():
            method = fields.get("method", "")
            if method:
                normalized = self._normalize_pattern(method)
                if normalized:
                    pattern_papers[normalized].append(paper_id)

        return {k: v for k, v in pattern_papers.items() if len(v) >= self.min_papers}

    def _normalize_pattern(self, text: str) -> str:
        """Normalize text for pattern matching."""
        text = text.lower().strip()
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "are", "was", "were", "this", "that", "we", "our", "it", "its"}
        words = [w for w in text.split() if w not in stop_words and len(w) > 3]
        return " ".join(words[:5])  # First 5 meaningful words as pattern key

    def _format_doctrine_note(self, concept: str, papers: List[Any], domain: str) -> str:
        """Format a doctrine note from a recurring concept."""
        evidence = []
        for p in papers[:10]:
            title = getattr(p, 'title', str(p))
            abstract = getattr(p, 'abstract', '') or ''
            evidence.append(f"- {title}: {abstract[:100]}")

        return f"""# Doctrine: {concept}

> **Domain:** {domain} | **Papers:** {len(papers)} | **Extracted:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
> **Tier:** 2 (auto-extracted, AS review pending)

## Pattern

The concept "{concept}"" appears across {len(papers)} papers in the {domain} domain.

## Evidence

{chr(10).join(evidence)}

## Synthesis

[AS to review and synthesize]

## Application

[How OCE/PO can use this doctrine]

#doctrine #tier/2 #domain/{domain} #auto_extracted
"""

    def _create_doctrine_note(
        self,
        pattern: str,
        paper_ids: List[str],
        papers: Dict[str, Dict[str, str]],
        pattern_type: str,
    ) -> Optional[str]:
        """
        Create a doctrine note from a recurring pattern.
        
        Returns path to created file, or None if creation failed.
        """
        # Determine domain from paper paths
        domain = self._infer_domain(paper_ids)
        
        # Build doctrine note
        title = pattern.title()[:60]
        slug = re.sub(r"[^\w\s-]", "", pattern.lower())[:40].strip().replace(" ", "_")
        
        # Collect evidence
        evidence = []
        for pid in paper_ids[:10]:  # Cap evidence at 10 papers
            fields = papers.get(pid, {})
            evidence.append(f"- {pid}: {fields.get('result', 'N/A')}")

        note = f"""# Doctrine: {title}

> **Type:** {pattern_type} | **Papers:** {len(paper_ids)} | **Extracted:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
> **Tier:** 2 (auto-extracted, AS review pending)

## Pattern

{pattern}

## Evidence

{chr(10).join(evidence)}

## Synthesis

[AS to review and synthesize]

## Application

[How OCE/PO can use this doctrine]

#doctrine #tier/2 #domain/{domain} #auto_extracted
"""

        # Write to vault
        doctrine_dir = VAULT_DOCTRINE_DIR / domain
        doctrine_dir.mkdir(parents=True, exist_ok=True)
        
        path = doctrine_dir / f"{slug}.md"
        try:
            path.write_text(note, encoding="utf-8")
            logger.info(f"Created doctrine note: {path}")
            return str(path.relative_to(VAULT_DOCTRINE_DIR.parent.parent))
        except Exception as e:
            logger.error(f"Failed to create doctrine note: {e}")
            return None

    def _infer_domain(self, paper_ids: List[str]) -> str:
        """Infer domain from paper IDs (using folder structure)."""
        # Default domain
        return "general"