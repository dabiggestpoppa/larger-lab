"""
Phase 1.5 — Argument Structurer

Structures reasoning into argument trees.
Supports: claim → evidence → reasoning → conclusion
Detects logical gaps and weak evidence.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.argument")


@dataclass
class Evidence:
    """Evidence supporting a claim."""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str = ""
    source: str = ""
    strength: float = 0.5  # 0-1
    evidence_type: str = "empirical"  # empirical, logical, testimonial, statistical


@dataclass
class ArgumentNode:
    """A node in an argument tree."""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str = ""
    node_type: str = "claim"  # claim, evidence, reasoning, conclusion
    confidence: float = 0.5
    children: List[ArgumentNode] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)


@dataclass
class ArgumentStructure:
    """A complete argument tree."""
    argument_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    root: Optional[ArgumentNode] = None
    gaps: List[str] = field(default_factory=list)
    overall_strength: float = 0.0

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram of argument structure."""
        lines = ["graph TD"]
        if self.root:
            self._node_to_mermaid(self.root, lines, "root")
        return "\n".join(lines)

    def _node_to_mermaid(self, node: ArgumentNode, lines: List[str], parent_id: str):
        node_label = node.text[:50].replace('"', "'")
        lines.append(f'    {node.node_id}["{node.text[:40]} ({node.confidence:.0%})"]')
        lines.append(f'    {parent_id} --> {node.node_id}')
        for child in node.children:
            self._node_to_mermaid(child, lines, node.node_id)


class ArgumentStructurer:
    """
    Structures reasoning into argument trees.
    
    Usage:
        structurer = ArgumentStructure()
        argument = structurer.structure(
            claim="Semantic memory improves agent reasoning",
            evidence_list=[ev1, ev2, ev3],
        )
    """

    def structure(
        self,
        claim: str,
        evidence_list: List[Evidence],
        reasoning: str = "",
    ) -> ArgumentStructure:
        """Build an argument tree from claim + evidence."""
        root = ArgumentNode(
            text=claim,
            node_type="claim",
            confidence=self._compute_claim_confidence(evidence_list),
        )

        # Add evidence nodes
        for evidence in evidence_list:
            evidence_node = ArgumentNode(
                text=evidence.text[:200],
                node_type="evidence",
                confidence=evidence.strength,
                sources=[evidence.source] if evidence.source else [],
            )
            root.children.append(evidence_node)

        # Add reasoning node if provided
        if reasoning:
            reasoning_node = ArgumentNode(
                text=reasoning[:200],
                node_type="reasoning",
                confidence=root.confidence * 0.9,
            )
            root.children.append(reasoning_node)

        # Detect gaps
        gaps = self._detect_gaps(root, evidence_list)

        # Overall strength
        overall = root.confidence if root.children else 0.0

        return ArgumentStructure(
            root=root,
            gaps=gaps,
            overall_strength=overall,
        )

    def _compute_claim_confidence(self, evidence_list: List[Evidence]) -> float:
        """Compute overall claim confidence from evidence."""
        if not evidence_list:
            return 0.1

        # Average evidence strength, with bonus for multiple sources
        avg_strength = sum(e.strength for e in evidence_list) / len(evidence_list)
        source_bonus = min(0.3, len(evidence_list) * 0.1)
        return min(1.0, avg_strength + source_bonus)

    def _detect_gaps(self, root: ArgumentNode, evidence_list: List[Evidence]) -> List[str]:
        """Detect logical gaps in the argument."""
        gaps = []

        if not evidence_list:
            gaps.append("No evidence provided for claim")
        elif len(evidence_list) < 2:
            gaps.append("Only one evidence source — more needed for strong argument")

        weak_evidence = [e for e in evidence_list if e.strength < 0.3]
        if weak_evidence:
            gaps.append(f"{len(weak_evidence)} weak evidence items (strength < 0.3)")

        # Check for missing reasoning
        has_reasoning = any(c.node_type == "reasoning" for c in root.children)
        if not has_reasoning and len(evidence_list) > 1:
            gaps.append("No explicit reasoning connecting evidence to claim")

        return gaps
