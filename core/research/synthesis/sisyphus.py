"""
Phase 1.5 — Sisyphus Academica

Multi-source research synthesis engine.
Moves beyond summarization into research reasoning,
synthesis, citation cognition, and argument structuring.

Takes a research question + multiple source documents.
Produces structured synthesis with citations, confidence scores,
and contradiction detection.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.sisyphus")


@dataclass
class SourceDocument:
    """A source document for synthesis."""
    doc_id: str
    title: str
    text: str
    source: str = ""  # e.g., "openalex", "vault", "document"
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


@dataclass
class Claim:
    """A single claim/findings from synthesis."""
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str = ""
    confidence: float = 0.5  # 0-1
    supporting_sources: List[str] = field(default_factory=list)  # doc_ids
    contradicting_sources: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)  # text snippets


@dataclass
class SynthesisResult:
    """Complete synthesis output."""
    synthesis_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    query: str = ""
    executive_summary: str = ""
    key_findings: List[Claim] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, str]] = field(default_factory=list)
    source_count: int = 0
    confidence: float = 0.0
    gaps: List[str] = field(default_factory=list)  # identified knowledge gaps

    def to_dict(self) -> dict:
        return {
            "synthesis_id": self.synthesis_id,
            "query": self.query,
            "executive_summary": self.executive_summary,
            "key_findings": [
                {
                    "text": f.text,
                    "confidence": f.confidence,
                    "sources": f.supporting_sources,
                    "evidence": f.evidence[:3],  # top 3 evidence snippets
                }
                for f in self.key_findings
            ],
            "contradictions": self.contradictions,
            "citations": self.citations,
            "source_count": self.source_count,
            "confidence": self.confidence,
            "gaps": self.gaps,
        }


class SisyphusEngine:
    """
    Multi-source research synthesis engine.
    
    Usage:
        sisyphus = SisyphusEngine(embedding_engine=embedder)
        result = sisyphus.synthesize(
            query="How does semantic memory improve agent reasoning?",
            sources=[doc1, doc2, doc3],
        )
    """

    def __init__(
        self,
        embedding_engine=None,
        chunker=None,
        max_sources: int = 20,
        min_confidence: float = 0.3,
    ):
        self.embedding_engine = embedding_engine
        self.chunker = chunker
        self.max_sources = max_sources
        self.min_confidence = min_confidence

    def synthesize(
        self,
        query: str,
        sources: List[SourceDocument],
    ) -> SynthesisResult:
        """
        Synthesize multiple sources into a coherent research result.
        
        Pipeline:
        1. Chunk sources (if chunker available)
        2. Extract key claims from each source
        3. Cross-reference claims across sources
        4. Detect agreements and contradictions
        5. Generate executive summary
        6. Identify knowledge gaps
        """
        logger.info(f"Sisyphus: synthesizing {len(sources)} sources for query: {query[:80]}")

        if not sources:
            return SynthesisResult(query=query, confidence=0.0)

        result = SynthesisResult(
            query=query,
            source_count=len(sources),
        )

        # 1. Extract claims from each source
        all_claims: List[Claim] = []
        for source in sources:
            claims = self._extract_claims(source, query)
            all_claims.extend(claims)

        # 2. Cross-reference: group similar claims
        claim_groups = self._group_similar_claims(all_claims)

        # 3. Build key findings from groups
        for group in claim_groups:
            if len(group) == 0:
                continue
            # Merge claims in group
            merged = self._merge_claims(group)
            if merged.confidence >= self.min_confidence:
                result.key_findings.append(merged)

        # 4. Sort by confidence
        result.key_findings.sort(key=lambda f: f.confidence, reverse=True)

        # 5. Detect contradictions
        result.contradictions = self._detect_contradictions(all_claims)

        # 6. Build citations
        result.citations = self._build_citations(sources)

        # 7. Generate summary
        result.executive_summary = self._generate_summary(result)

        # 8. Overall confidence
        if result.key_findings:
            result.confidence = sum(f.confidence for f in result.key_findings) / len(result.key_findings)

        # 9. Identify gaps
        result.gaps = self._identify_gaps(result)

        logger.info(
            f"Synthesis complete: {len(result.key_findings)} findings, "
            f"{len(result.contradictions)} contradictions, "
            f"confidence={result.confidence:.2f}"
        )

        return result

    def _extract_claims(self, source: SourceDocument, query: str) -> List[Claim]:
        """Extract key claims from a source document."""
        claims = []

        # Use chunks if available, otherwise split text
        text_segments = source.chunks if source.chunks else self._simple_chunk(source.text)

        for segment in text_segments:
            # Skip very short segments
            if len(segment) < 50:
                continue

            # Simple heuristic: sentences that look like claims
            # (contain assertion keywords)
            sentences = segment.split(". ")
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 30:
                    continue
                if self._is_claim(sentence):
                    claims.append(Claim(
                        text=sentence,
                        confidence=0.5,  # base confidence
                        supporting_sources=[source.doc_id],
                        evidence=[sentence[:200]],
                    ))

        return claims[:10]  # limit per source

    def _is_claim(self, text: str) -> bool:
        """Heuristic: does this text look like a claim/assertion?"""
        claim_indicators = [
            "show", "demonstrate", "prove", "find", "result", "suggest",
            "indicate", "reveal", "confirm", "support", "evidence",
            "imply", "conclude", "observe", "discover", "propose",
            "argue", "claim", "assert", "hypothesize", "theory",
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in claim_indicators)

    def _simple_chunk(self, text: str, max_chars: int = 1000) -> List[str]:
        """Simple text chunking by paragraphs."""
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > max_chars:
                if current:
                    chunks.append(current)
                current = para
            else:
                current += "\n\n" + para if current else para
        if current:
            chunks.append(current)
        return chunks

    def _group_similar_claims(self, claims: List[Claim]) -> List[List[Claim]]:
        """Group semantically similar claims."""
        if not self.embedding_engine or len(claims) < 2:
            return [[c] for c in claims]

        groups: List[List[Claim]] = []
        used = set()

        for i, claim in enumerate(claims):
            if i in used:
                continue
            group = [claim]
            used.add(i)

            # Find similar claims
            for j, other in enumerate(claims):
                if j in used:
                    continue
                similarity = self._text_similarity(claim.text, other.text)
                if similarity > 0.7:
                    group.append(other)
                    used.add(j)

            groups.append(group)

        return groups

    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity between two texts using embeddings."""
        if not self.embedding_engine:
            # Fallback: Jaccard similarity on words
            words_a = set(text_a.lower().split())
            words_b = set(text_b.lower().split())
            if not words_a or not words_b:
                return 0.0
            intersection = words_a & words_b
            union = words_a | words_b
            return len(intersection) / len(union)

        try:
            emb_a = self.embedding_engine.embed(text_a)
            emb_b = self.embedding_engine.embed(text_b)
            return self._cosine_similarity(emb_a, emb_b)
        except Exception:
            return 0.0

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _merge_claims(self, group: List[Claim]) -> Claim:
        """Merge a group of similar claims into one."""
        if len(group) == 1:
            return group[0]

        # Use the longest claim as the base (usually most detailed)
        base = max(group, key=lambda c: len(c.text))

        # Merge supporting sources
        all_sources = set()
        all_evidence = []
        for claim in group:
            all_sources.update(claim.supporting_sources)
            all_evidence.extend(claim.evidence)

        # Confidence increases with more supporting sources
        source_bonus = min(0.3, len(all_sources) * 0.1)
        confidence = min(1.0, base.confidence + source_bonus)

        return Claim(
            text=base.text,
            confidence=confidence,
            supporting_sources=list(all_sources),
            evidence=all_evidence[:5],
        )

    def _detect_contradictions(self, claims: List[Claim]) -> List[Dict[str, Any]]:
        """Detect contradicting claims."""
        contradictions = []

        # Simple heuristic: look for negation patterns
        negation_words = ["not", "no", "never", "cannot", "doesn't", "don't", "won't", "isn't", "aren't"]

        for i, claim_a in enumerate(claims):
            for j, claim_b in enumerate(claims):
                if i >= j:
                    continue
                # Check if one claim negates the other
                text_a = claim_a.text.lower()
                text_b = claim_b.text.lower()

                # Simple contradiction detection
                has_neg_a = any(w in text_a for w in negation_words)
                has_neg_b = any(w in text_b for w in negation_words)

                if has_neg_a != has_neg_b:
                    # One has negation, the other doesn't — possible contradiction
                    similarity = self._text_similarity(text_a, text_b)
                    if similarity > 0.5:  # talking about same topic
                        contradictions.append({
                            "claim_a": claim_a.text[:200],
                            "claim_b": claim_b.text[:200],
                            "similarity": similarity,
                            "severity": "medium" if similarity > 0.7 else "low",
                        })

        return contradictions

    def _build_citations(self, sources: List[SourceDocument]) -> List[Dict[str, str]]:
        """Build citation list from sources."""
        citations = []
        for source in sources:
            citation = {
                "id": source.doc_id,
                "title": source.title,
                "source": source.source,
            }
            if source.metadata.get("doi"):
                citation["doi"] = source.metadata["doi"]
            if source.metadata.get("authors"):
                citation["authors"] = ", ".join(source.metadata["authors"][:3])
            if source.metadata.get("publication_date"):
                citation["year"] = source.metadata["publication_date"][:4]
            citations.append(citation)
        return citations

    def _generate_summary(self, result: SynthesisResult) -> str:
        """Generate executive summary from synthesis result."""
        if not result.key_findings:
            return "No significant findings from the available sources."

        top_findings = result.key_findings[:5]
        summary_parts = []

        for i, finding in enumerate(top_findings, 1):
            confidence_label = "high" if finding.confidence > 0.7 else "medium" if finding.confidence > 0.5 else "low"
            summary_parts.append(f"{i}. [{confidence_label}] {finding.text[:150]}")

        if result.contradictions:
            summary_parts.append(f"\nNote: {len(result.contradictions)} potential contradictions detected.")

        return "\n".join(summary_parts)

    def _identify_gaps(self, result: SynthesisResult) -> List[str]:
        """Identify knowledge gaps from the synthesis."""
        gaps = []

        # Low confidence across findings
        if result.confidence < 0.4:
            gaps.append("Low overall confidence — more sources needed")

        # Few sources
        if result.source_count < 3:
            gaps.append(f"Only {result.source_count} sources — broader search recommended")

        # Contradictions without resolution
        if result.contradictions:
            gaps.append(f"{len(result.contradictions)} unresolved contradictions — deeper analysis needed")

        return gaps
