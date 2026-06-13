"""
Multi-source paper ingestion for the RCE pipeline.

Pulls from ALL 3 sources (OpenAlex, arXiv, S2) simultaneously,
deduplicates by DOI/title, merges metadata, and returns unified Paper objects.

This is the default ingestion layer — no agent should ever need to write
a script to pull from all 3 sources. Just call `fetch_papers()`.

Usage:
    from core.research.cognition.multi_source import MultiSourceFetcher
    
    fetcher = MultiSourceFetcher()
    papers = await fetcher.fetch_papers("information theory trading systems", per_source=10)
    # Returns papers from OpenAlex + arXiv + S2, deduplicated and merged
"""

from __future__ import annotations

import asyncio
import logging
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set

from ..ingestion.models import Paper
from ..ingestion.openalex_client import OpenAlexClient
from ..ingestion.arxiv_client import ArxivClient
from ..ingestion.s2_client import S2Client

logger = logging.getLogger("oce.rce.multi_source")


class MultiSourceFetcher:
    """
    Fetches papers from all 3 sources simultaneously.
    
    Features:
    - Parallel async queries to OpenAlex, arXiv, S2
    - DOI-based deduplication (same paper from multiple sources = merged)
    - Title-based fuzzy deduplication for papers without DOI
    - Source provenance tracking (which sources found each paper)
    - Merged metadata (citations from S2, concepts from OpenAlex, etc.)
    """
    
    def __init__(
        self,
        openalex_mailto: str = "ops@larger-lab.local",
        s2_api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.openalex_mailto = openalex_mailto
        self.s2_api_key = s2_api_key
        self.timeout = timeout
    
    async def fetch_papers(
        self,
        query: str,
        per_source: int = 10,
        year_from: int = 2015,
        open_access_only: bool = True,
    ) -> List[Paper]:
        """
        Fetch papers from all 3 sources for a query.
        
        Args:
            query: Search query string
            per_source: Max results per source (default 10)
            year_from: Minimum publication year
            open_access_only: Only return open access papers
            
        Returns:
            Deduplicated, merged list of Paper objects
        """
        # Query all 3 sources in parallel
        results = await asyncio.gather(
            self._fetch_openalex(query, per_source, year_from, open_access_only),
            self._fetch_arxiv(query, per_source, year_from),
            self._fetch_s2(query, per_source, year_from),
            return_exceptions=True,
        )
        
        # Collect papers, handling any source failures gracefully
        all_papers: List[Paper] = []
        source_names = ["openalex", "arxiv", "s2"]
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Source {source_names[i]} failed: {result}")
                continue
            all_papers.extend(result)
            logger.info(f"Source {source_names[i]}: {len(result)} papers")
        
        # Deduplicate and merge
        merged = self._deduplicate_and_merge(all_papers)
        logger.info(f"After deduplication: {len(merged)} unique papers from {len(all_papers)} total")
        
        # Filter by relevance to the query
        relevant = self._filter_by_relevance(merged, query)
        logger.info(f"After relevance filter: {len(relevant)} relevant papers from {len(merged)} total")
        
        return relevant
    
    async def fetch_multi_topic(
        self,
        queries: List[str],
        per_source: int = 10,
        year_from: int = 2015,
    ) -> Dict[str, List[Paper]]:
        """
        Fetch papers for multiple topics.
        
        Args:
            queries: List of search queries
            per_source: Max results per source per query
            year_from: Minimum publication year
            
        Returns:
            Dict mapping query → list of Papers
        """
        results = {}
        for i, query in enumerate(queries):
            if i > 0:
                # Delay between topics to avoid S2 rate limits
                await asyncio.sleep(3)
            papers = await self.fetch_papers(query, per_source, year_from)
            results[query] = papers
        return results
    
    # ─── Source-specific fetchers ───
    
    async def _fetch_openalex(
        self, query: str, per_page: int, year_from: int, open_access: bool
    ) -> List[Paper]:
        """Fetch from OpenAlex."""
        async with OpenAlexClient(mailto=self.openalex_mailto, timeout=self.timeout) as client:
            papers = await client.search(
                query,
                per_page=per_page,
            )
            # Filter by year if needed
            if year_from:
                papers = [p for p in papers if p.year >= year_from]
            for p in papers:
                p.source = "openalex"
            return papers
    
    async def _fetch_arxiv(
        self, query: str, max_results: int, year_from: int
    ) -> List[Paper]:
        """
        Fetch from arXiv using category-only search.
        
        arXiv's abs: search matches individual words, not phrases,
        so we search by category only and let the relevance filter
        handle topic matching. This returns more papers but they're
        at least from the right domain.
        """
        categories = self._get_arxiv_categories(query)
        
        all_papers: List[Paper] = []
        seen_ids: Set[str] = set()
        
        async with ArxivClient(timeout=self.timeout) as client:
            # Search each category separately for best results
            for category in categories[:3]:  # Top 3 categories
                try:
                    papers = await client.search_by_category(
                        category,
                        max_results=max_results,
                    )
                    for p in papers:
                        if p.id not in seen_ids:
                            seen_ids.add(p.id)
                            all_papers.append(p)
                except Exception as e:
                    logger.warning(f"arXiv category {category} failed: {e}")
        
        if year_from:
            all_papers = [p for p in all_papers if p.year >= year_from]
        for p in all_papers:
            p.source = "arxiv"
        return all_papers
    
    def _get_arxiv_categories(self, query: str) -> List[str]:
        """Determine which arXiv categories to search based on query."""
        query_lower = query.lower()
        cats = set()
        
        # Finance/economics topics
        if any(w in query_lower for w in ["financial", "trading", "market", "finance", "contagion", "systemic risk"]):
            cats.update(["q-fin.TR", "q-fin.ST", "q-fin.RM", "q-fin.EC"])
        
        # Information theory / entropy
        if any(w in query_lower for w in ["entropy", "information theory", "transfer entropy"]):
            cats.update(["cs.IT", "math.IT", "cs.LG"])
        
        # Geopolitics / political risk
        if any(w in query_lower for w in ["geopolitical", "political risk", "emerging market"]):
            cats.update(["econ.GN", "q-fin.EC"])
        
        # Network / topology
        if any(w in query_lower for w in ["network", "topology", "graph"]):
            cats.update(["cs.SI", "cs.NI", "math.CO"])
        
        # Default
        if not cats:
            cats = {"cs.LG", "cs.AI", "q-fin.TR"}
        
        return sorted(cats)
    
    def _build_arxiv_query(self, query: str) -> str:
        """
        Convert a natural language query to arXiv search syntax.
        
        Uses phrase-level matching with "all:" to require all key phrases
        appear in the abstract, reducing false positives from single-word matches.
        """
        query_lower = query.strip().lower()
        
        # Map multi-word key phrases to arXiv categories
        # Order matters: more specific phrases first
        category_rules = [
            (["financial market", "trading system", "market microstructure", "systemic risk", "financial contagion"], ["q-fin.TR", "q-fin.ST", "q-fin.RM"]),
            (["information theory", "transfer entropy", "shannon entropy", "mutual information"], ["cs.IT", "math.IT"]),
            (["geopolitical", "political risk", "geopolitics"], ["econ.GN", "q-fin.EC"]),
            (["emerging market", "developing countr"], ["econ.GN", "q-fin.EC"]),
            (["machine learning", "deep learning", "neural network"], ["cs.LG", "cs.AI"]),
            (["multi-agent", "agent orchestration"], ["cs.AI", "cs.MA"]),
            (["network topology", "graph theory"], ["cs.SI", "math.CO"]),
            (["reinforcement learning"], ["cs.LG", "cs.AI"]),
            (["causal inference", "causal discovery"], ["cs.LG", "stat.ME"]),
        ]
        
        matched_cats = set()
        for keywords, cats in category_rules:
            if any(kw in query_lower for kw in keywords):
                matched_cats.update(cats)
        
        # Default: broad CS + finance if no match
        if not matched_cats:
            matched_cats = {"cs.LG", "cs.AI", "q-fin.TR"}
        
        # Build category filter
        cat_filter = "+OR+".join(f"cat:{cat}" for cat in sorted(matched_cats))
        
        # Extract key phrases (multi-word) for abstract search
        # These are the specific phrases that must appear in the abstract
        key_phrases = []
        all_phrases = [
            "transfer entropy", "information theory", "systemic risk",
            "financial contagion", "market microstructure", "trading",
            "geopolitical risk", "political risk", "emerging market",
            "capital flow", "financial crisis", "network topology",
            "entropy", "causal", "contagion",
        ]
        for phrase in all_phrases:
            if phrase in query_lower:
                key_phrases.append(phrase)
        
        # If no specific phrases found, use individual words
        if not key_phrases:
            words = [w for w in query_lower.split() if len(w) > 4]
            key_phrases = words[:3]
        
        # Build abstract filter using "all:" (all phrases must appear)
        # This is stricter than default OR matching
        abs_filter = "+AND+".join(f'abs:"{phrase}"' for phrase in key_phrases[:4])
        
        if abs_filter:
            return f"({cat_filter})+AND+({abs_filter})"
        return f"({cat_filter})"
    
    async def _fetch_s2(
        self, query: str, limit: int, year_from: int
    ) -> List[Paper]:
        """Fetch from Semantic Scholar with rate limit retry."""
        async with S2Client(api_key=self.s2_api_key, timeout=self.timeout) as client:
            papers = []
            for attempt in range(3):
                try:
                    papers = await client.search_by_query(
                        query,
                        limit=limit,
                    )
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 2:
                        wait = 2 ** (attempt + 1)  # 2s, 4s
                        logger.warning(f"S2 rate limited (attempt {attempt+1}), waiting {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        if attempt == 2:
                            logger.warning(f"S2 failed after 3 attempts: {e}")
                        break
            
            if year_from:
                papers = [p for p in papers if p.year >= year_from]
            for p in papers:
                p.source = "s2"
            return papers
    
    # ─── Relevance Filtering ───
    
    def _filter_by_relevance(
        self, papers: List[Paper], query: str, min_score: float = 0.08
    ) -> List[Paper]:
        """
        Filter papers by relevance to the query.
        
        Uses keyword overlap between query and paper title/abstract.
        Papers below the minimum score are discarded.
        Keeps at least 5 papers even if scores are low (better to have
        slightly off-topic papers than no papers at all).
        """
        # Extract key phrases from query (multi-word phrases are more specific)
        stop_words = {
            "and", "the", "for", "with", "from", "this", "that", "are",
            "was", "were", "been", "have", "has", "had", "will", "would",
            "could", "should", "their", "these", "those", "about", "into",
            "through", "between", "under", "over", "also", "only", "very",
            "just", "more", "most", "some", "any", "each", "every", "all",
            "both", "few", "many", "much", "several", "other", "such", "than",
        }
        
        # First try multi-word phrases
        key_phrases = []
        all_phrases = [
            "transfer entropy", "information theory", "systemic risk",
            "financial contagion", "market microstructure", "trading system",
            "geopolitical risk", "political risk", "emerging market",
            "capital flow", "financial crisis", "network topology",
        ]
        query_lower = query.lower()
        for phrase in all_phrases:
            if phrase in query_lower:
                key_phrases.append(phrase)
        
        # Then add individual words
        query_terms = set(
            w.lower() for w in query.split()
            if len(w) >= 3 and w.lower() not in stop_words
        )
        
        scored_papers = []
        for paper in papers:
            # Combine title and abstract for scoring
            text = f"{paper.title} {paper.abstract}".lower()
            
            # Count query terms found in paper text
            term_matches = sum(1 for term in query_terms if term in text)
            score = term_matches / max(len(query_terms), 1)
            
            # Bonus for key phrase matches (more specific)
            phrase_matches = sum(1 for phrase in key_phrases if phrase in text)
            score += phrase_matches * 0.2
            
            # Boost if paper has concepts that match query
            if paper.concepts:
                concept_names = {c.name.lower() for c in paper.concepts}
                concept_matches = sum(1 for term in query_terms if term in concept_names)
                score += concept_matches * 0.15
            
            # Boost if paper source is openalex (better metadata)
            if paper.source == "openalex":
                score += 0.05
            
            scored_papers.append((score, paper))
        
        # Sort by relevance score (highest first)
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        
        # Keep papers above threshold, but always keep at least 5
        filtered = [paper for score, paper in scored_papers if score >= min_score]
        if len(filtered) < 5 and len(scored_papers) >= 5:
            # Fall back to top 5 by score
            filtered = [paper for _, paper in scored_papers[:5]]
        elif len(filtered) < 2 and len(scored_papers) >= 2:
            # Fall back to top 2
            filtered = [paper for _, paper in scored_papers[:2]]
        
        return filtered
    
    # ─── Deduplication & Merging ───
    
    def _deduplicate_and_merge(self, papers: List[Paper]) -> List[Paper]:
        """
        Deduplicate papers by DOI and fuzzy title matching.
        When the same paper appears from multiple sources, merge metadata.
        """
        # Group by DOI first
        doi_groups: Dict[str, List[Paper]] = {}
        no_doi_papers: List[Paper] = []
        
        for paper in papers:
            if paper.doi and paper.doi.strip():
                doi_key = paper.doi.strip().lower()
                if doi_key not in doi_groups:
                    doi_groups[doi_key] = []
                doi_groups[doi_key].append(paper)
            else:
                no_doi_papers.append(paper)
        
        # Merge DOI groups
        merged: List[Paper] = []
        for doi_key, group in doi_groups.items():
            merged.append(self._merge_paper_group(group))
        
        # Fuzzy title dedup for papers without DOI
        if no_doi_papers:
            title_groups = self._group_by_title(no_doi_papers)
            for group in title_groups:
                merged.append(self._merge_paper_group(group))
        
        # Final DOI dedup (in case title matching caught DOI papers too)
        final: List[Paper] = []
        seen_dois: Set[str] = set()
        for paper in merged:
            doi_key = paper.doi.strip().lower() if paper.doi else ""
            if doi_key and doi_key in seen_dois:
                continue
            if doi_key:
                seen_dois.add(doi_key)
            final.append(paper)
        
        return final
    
    def _group_by_title(self, papers: List[Paper]) -> List[List[Paper]]:
        """Group papers by fuzzy title matching."""
        groups: List[List[Paper]] = []
        used: Set[int] = set()
        
        for i, paper_a in enumerate(papers):
            if i in used:
                continue
            
            group = [paper_a]
            used.add(i)
            
            for j, paper_b in enumerate(papers):
                if j in used:
                    continue
                
                similarity = SequenceMatcher(
                    None,
                    paper_a.title.lower(),
                    paper_b.title.lower(),
                ).ratio()
                
                if similarity >= 0.85:  # Near-duplicate titles
                    group.append(paper_b)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _merge_paper_group(self, papers: List[Paper]) -> Paper:
        """
        Merge multiple versions of the same paper from different sources.
        Takes the best metadata from each source.
        """
        if len(papers) == 1:
            return papers[0]
        
        # Sort by completeness (most complete first)
        papers.sort(key=lambda p: self._paper_completeness(p), reverse=True)
        
        # Use the most complete paper as base
        base = papers[0]
        
        # Merge authors from all sources
        all_authors = {a.name.lower(): a for a in base.authors}
        for p in papers[1:]:
            for author in p.authors:
                if author.name.lower() not in all_authors:
                    all_authors[author.name.lower()] = author
        base.authors = list(all_authors.values())
        
        # Merge concepts from all sources
        all_concepts = {c.name.lower(): c for c in base.concepts}
        for p in papers[1:]:
            for concept in p.concepts:
                key = concept.name.lower()
                if key not in all_concepts or concept.score > all_concepts[key].score:
                    all_concepts[key] = concept
        base.concepts = list(all_concepts.values())
        
        # Take highest citation count
        for p in papers[1:]:
            if p.citation_count > base.citation_count:
                base.citation_count = p.citation_count
        
        # Take longest abstract
        for p in papers[1:]:
            if len(p.abstract) > len(base.abstract):
                base.abstract = p.abstract
        
        # Take PDF URL if available
        if not base.pdf_url:
            for p in papers[1:]:
                if p.pdf_url:
                    base.pdf_url = p.pdf_url
                    break
        
        # Track source provenance
        sources = [p.source for p in papers if p.source]
        base.source = "+".join(sorted(set(sources)))
        
        return base
    
    def _paper_completeness(self, paper: Paper) -> int:
        """Score how complete a paper's metadata is."""
        score = 0
        if paper.title:
            score += 1
        if paper.abstract and len(paper.abstract) > 100:
            score += 2
        if paper.doi:
            score += 1
        if paper.authors:
            score += 1
        if paper.year:
            score += 1
        if paper.concepts:
            score += 1
        if paper.pdf_url:
            score += 1
        return score
