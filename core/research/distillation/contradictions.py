"""
L2.8 — Contradiction detector.

Detects papers with opposing RESULTS for the same METHOD.
Writes contradiction notes to O2C-VAULT/research/contradictions/.

Usage:
    detector = ContradictionDetector()
    contradictions = detector.detect(papers)
    # Returns list of contradiction dicts
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Contradiction detection thresholds
MIN_SHARED_METHOD_WORDS = 3  # Minimum words shared in METHOD to flag
CONTRADICTION_INDICATORS = [
    "however", "but", "in contrast", "unlike", "contrary",
    "opposite", "reverse", "inverse", "negatively", "adversely",
    "worse", "lower", "decreased", "reduced", "failed",
]

VAULT_CONTRADICTIONS_DIR = Path(__file__).resolve().parents[4] / "O2C-VAULT" / "research" / "contradictions"


class ContradictionDetector:
    """
    Detects contradictions between papers.
    
    Requires shared METHOD to flag as contradiction (not just superficial differences).
    Tags as #contradiction #candidate or #contradiction #verified.
    """

    def __init__(self, min_shared_method_words: int = MIN_SHARED_METHOD_WORDS):
        self.min_shared_method_words = min_shared_method_words

    def detect(self, papers: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Detect contradictions among a set of papers.
        
        Args:
            papers: List of dicts with 'id', 'method', 'result', 'title' keys
            
        Returns:
            List of contradiction dicts with paper_a, paper_b, method, description
        """
        contradictions = []
        
        # Group papers by similar method
        method_groups = self._group_by_method(papers)
        
        for method_key, group in method_groups.items():
            if len(group) < 2:
                continue
            
            # Check for opposing results within group
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    contradiction = self._check_pair(group[i], group[j])
                    if contradiction:
                        contradictions.append(contradiction)
        
        logger.info(f"Contradiction detection: found {len(contradictions)} potential contradictions")
        return contradictions

    def detect_from_vault(self) -> List[Dict[str, Any]]:
        """
        Detect contradictions from vault papers.
        
        Reads all paper notes from O2C-VAULT/research/papers/ and checks for contradictions.
        """
        papers_dir = Path(__file__).resolve().parents[4] / "O2C-VAULT" / "research" / "papers"
        
        if not papers_dir.exists():
            logger.warning(f"Vault papers dir not found: {papers_dir}")
            return []

        papers = []
        for md_file in papers_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                parsed = self._parse_note(content)
                if parsed:
                    parsed["id"] = md_file.stem
                    papers.append(parsed)
            except Exception as e:
                logger.debug(f"Failed to parse {md_file}: {e}")

        return self.detect(papers)

    def write_contradiction_note(self, contradiction: Dict[str, Any]) -> Optional[str]:
        """
        Write a contradiction note to the vault.
        
        Returns path to created file, or None if creation failed.
        """
        topic = contradiction.get("method", "unknown")[:30]
        slug = re.sub(r"[^\w\s-]", "", topic.lower())[:40].strip().replace(" ", "_")
        
        note = f"""# Contradiction: {topic}

> **Detected:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
> **Status:** candidate (LLM verification pending)
> **Papers:** {contradiction.get('paper_a', 'unknown')} vs {contradiction.get('paper_b', 'unknown')}

## Shared Method

{contradiction.get('method', 'Not specified')}

## Contradiction

{contradiction.get('description', 'Not specified')}

## Paper A Result

{contradiction.get('result_a', 'Not specified')}

## Paper B Result

{contradiction.get('result_b', 'Not specified')}

## Analysis

[AS to review: is this a true contradiction or different experimental conditions?]

#contradiction #candidate
"""

        VAULT_CONTRADICTIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = VAULT_CONTRADICTIONS_DIR / f"{slug}.md"
        
        try:
            path.write_text(note, encoding="utf-8")
            return str(path.relative_to(VAULT_CONTRADICTIONS_DIR.parent.parent))
        except Exception as e:
            logger.error(f"Failed to write contradiction note: {e}")
            return None

    def _group_by_method(self, papers: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Group papers by similar method descriptions."""
        groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        
        for paper in papers:
            method = paper.get("method", "")
            if method:
                # Create method key from first few meaningful words
                key = self._method_key(method)
                groups[key].append(paper)
        
        return groups

    def _method_key(self, method: str) -> str:
        """Create a method grouping key."""
        words = method.lower().split()
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "are", "we", "our", "it"}
        meaningful = [w for w in words if w not in stop_words and len(w) > 3]
        return " ".join(meaningful[:self.min_shared_method_words])

    def _check_pair(self, paper_a: Dict[str, str], paper_b: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Check if two papers have opposing results for the same method."""
        result_a = paper_a.get("result", "").lower()
        result_b = paper_b.get("result", "").lower()
        
        if not result_a or not result_b:
            return None
        
        # Check for contradiction indicators
        has_contradiction = False
        for indicator in CONTRADICTION_INDICATORS:
            if indicator in result_a or indicator in result_b:
                has_contradiction = True
                break
        
        # Check for opposing directions (increase vs decrease)
        opposing_patterns = [
            (r"\b(increased?|higher|improved?|better|positive)\b", r"\b(decreased?|lower|worse|reduced?|negative)\b"),
            (r"\b(faster|speedup)\b", r"\b(slower|overhead|cost)\b"),
            (r"\b(accurate|precision|recall)\b", r"\b(error|inaccurate|noise)\b"),
        ]
        
        for pos_pattern, neg_pattern in opposing_patterns:
            a_has_pos = bool(re.search(pos_pattern, result_a))
            a_has_neg = bool(re.search(neg_pattern, result_a))
            b_has_pos = bool(re.search(pos_pattern, result_b))
            b_has_neg = bool(re.search(neg_pattern, result_b))
            
            if (a_has_pos and b_has_neg) or (a_has_neg and b_has_pos):
                has_contradiction = True
                break
        
        if has_contradiction:
            return {
                "paper_a": paper_a.get("id", "unknown"),
                "paper_b": paper_b.get("id", "unknown"),
                "method": paper_a.get("method", ""),
                "result_a": paper_a.get("result", ""),
                "result_b": paper_b.get("result", ""),
                "description": f"Opposing results detected for similar method",
                "status": "candidate",
            }
        
        return None

    def _parse_note(self, content: str) -> Optional[Dict[str, str]]:
        """Parse a distilled paper note into fields."""
        result = {}
        
        for field in ["CAUSE", "METHOD", "RESULT", "LIMITATIONS", "APPLICATION"]:
            pattern = rf"^{field}:\s*(.+?)(?=\n[A-Z]+:|\nLINKS:|\n#|$)"
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                result[field.lower()] = match.group(1).strip()
        
        return result if result else None