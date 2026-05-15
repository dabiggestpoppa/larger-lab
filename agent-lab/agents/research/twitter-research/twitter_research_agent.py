#!/usr/bin/env python3
"""
Twitter AI Research Agent
=========================
Autonomous agent that searches Twitter/X for AI updates, tools, tips,
and trending research — then feeds findings into the workspace.

Part of the SRRS+OPH cognitive architecture (Observer Patch pattern).

Usage:
  - As Hermes skill: /twitter-research [keywords] [--hours 24] [--max 50]
  - As standalone:   python twitter_research_agent.py [--keywords AI,LLM]
  - As cron job:     Runs on schedule via Hermes cron system
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# ── Workspace paths ──────────────────────────────────────────────────────────
LAB_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
AGENT_DIR = Path(__file__).resolve().parent
WORKSPACE = AGENT_DIR / "workspace"
KNOWLEDGE_DB = WORKSPACE / "twitter-knowledge.json"
DISCOVERIES_LOG = WORKSPACE / "recent-discoveries.md"
SEEN_CACHE = WORKSPACE / "seen-tweets.json"
OVERLAP_CHANNEL = LAB_ROOT / "shared" / "overlap-log.jsonl"

# Ensure workspace exists
WORKSPACE.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("twitter-research")


# ── Data Models ──────────────────────────────────────────────────────────────

class InsightType(str, Enum):
    TOOL = "tool"
    TIP = "tip"
    RESEARCH = "research"
    ANNOUNCEMENT = "announcement"
    TREND = "trend"
    UNKNOWN = "unknown"


@dataclass
class TweetInsight:
    """A single insight extracted from Twitter."""
    tweet_id: str
    text: str
    author_id: str
    created_at: str
    url: str
    metrics: Dict[str, int] = field(default_factory=dict)
    keywords_matched: List[str] = field(default_factory=list)
    insight_type: str = "unknown"
    relevance_score: float = 0.0
    source: str = "twitter"
    extracted_at: str = ""
    # OPH overlap tracking
    observer_patch: str = "twitter-research"
    overlap_hash: str = ""

    def __post_init__(self):
        if not self.extracted_at:
            self.extracted_at = datetime.now(timezone.utc).isoformat()
        self.overlap_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Content-addressable hash for deduplication across patches."""
        raw = f"{self.tweet_id}:{self.text[:200]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_record(self) -> dict:
        return {
            "tweet_id": self.tweet_id,
            "text": self.text,
            "author_id": self.author_id,
            "created_at": self.created_at,
            "url": self.url,
            "metrics": self.metrics,
            "keywords_matched": self.keywords_matched,
            "insight_type": self.insight_type,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "extracted_at": self.extracted_at,
            "observer_patch": self.observer_patch,
            "overlap_hash": self.overlap_hash,
        }


# ── Twitter Research Agent ───────────────────────────────────────────────────

class TwitterResearchAgent:
    """
    Autonomous Twitter research agent.
    Searches for AI/ML updates, extracts tools and tips, feeds workspace.
    """

    def __init__(self, bearer_token: str, workspace_path: str = None):
        self.bearer_token = bearer_token
        self.workspace = Path(workspace_path).expanduser() if workspace_path else WORKSPACE
        self.knowledge_db = self.workspace / "twitter-knowledge.json"
        self.seen_cache_file = self.workspace / "seen-tweets.json"
        self.discoveries_log = self.workspace / "recent-discoveries.md"

        # Load seen tweet IDs for deduplication
        self.seen_tweets: set = self._load_seen_cache()
        self.existing_knowledge: List[dict] = self._load_knowledge()

        # Default search keywords — weighted by priority
        self.default_keywords = [
            "AI agent", "LLM", "machine learning", "prompt engineering",
            "open source AI", "AI tools", "AI research", "fine-tuning",
            "RAG", "vector database", "AI framework", "MCP", "OpenClaw",
            "Hermes agent", "autonomous agent", "multi-agent",
            "trading AI", "quantitative trading", "backtesting",
        ]

        # Classification keywords for insight type
        self.type_keywords = {
            InsightType.TOOL: ["tool", "app", "library", "framework", "sdk", "api", "platform", "github.com", "huggingface.co", "ollama", "langchain", "llamaindex"],
            InsightType.TIP: ["tip", "trick", "hack", "best practice", "pattern", "technique", "how to", "guide"],
            InsightType.RESEARCH: ["paper", "research", "benchmark", "evaluation", "study", "survey", "arxiv"],
            InsightType.ANNOUNCEMENT: ["announced", "launch", "release", "new", "update", "introducing", "just shipped"],
            InsightType.TREND: ["trending", "viral", "explaining", "why everyone", "hot take", "opinion"],
        }

    # ── Initialization helpers ────────────────────────────────────────────

    def _load_seen_cache(self) -> set:
        if self.seen_cache_file.exists():
            try:
                with open(self.seen_cache_file) as f:
                    data = json.load(f)
                    return set(data.get("tweet_ids", []))
            except (json.JSONDecodeError, KeyError):
                return set()
        return set()

    def _load_knowledge(self) -> List[dict]:
        if self.knowledge_db.exists():
            try:
                with open(self.knowledge_db) as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def _save_seen_cache(self):
        """Persist seen tweet IDs (keep last 5000)."""
        self.seen_cache_file.parent.mkdir(parents=True, exist_ok=True)
        recent = list(self.seen_tweets)[-5000:]
        with open(self.seen_cache_file, "w") as f:
            json.dump({"tweet_ids": recent, "updated": datetime.now(timezone.utc).isoformat()}, f)

    def _save_knowledge(self):
        """Persist knowledge base (keep last 2000 entries)."""
        self.knowledge_db.parent.mkdir(parents=True, exist_ok=True)
        self.existing_knowledge = self.existing_knowledge[-2000:]
        with open(self.knowledge_db, "w") as f:
            json.dump(self.existing_knowledge, f, indent=2)

    # ── Twitter API integration ──────────────────────────────────────────

    def _get_client(self):
        """Lazy import and initialize tweepy client."""
        try:
            import tweepy
            client = tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True,
            )
            return client
        except ImportError:
            logger.warning("tweepy not installed — run: pip install tweepy")
            return None

    def search_ai_updates(
        self,
        keywords: Optional[List[str]] = None,
        hours_back: int = 24,
        max_tweets: int = 100,
    ) -> List[TweetInsight]:
        """Search Twitter for relevant AI updates and return insights."""
        client = self._get_client()
        if not client:
            logger.error("Cannot search Twitter — tweepy client unavailable")
            return []

        keywords = keywords or self.default_keywords
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Build search queries with quality filters
        queries = []
        for kw in keywords:
            queries.append(f"{kw} -is:retweet has:links lang:en")
        # Add cross-cutting queries
        queries.extend([
            "AI tools -is:retweet has:links lang:en",
            "machine learning research -is:retweet lang:en",
            "LLM prompting tips -is:retweet lang:en",
            "AI agent framework -is:retweet has:links lang:en",
        ])

        new_insights = []
        per_query = max(1, max_tweets // len(queries))

        for query in queries:
            try:
                tweets = tweepy.Paginator(
                    client.search_recent_tweets,
                    query=query,
                    tweet_fields=["created_at", "author_id", "public_metrics", "entities"],
                    max_results=min(100, per_query),
                    start_time=since_time,
                ).flatten(limit=per_query)

                for tweet in tweets:
                    if tweet.id in self.seen_tweets:
                        continue

                    insight = self._classify_tweet(tweet, keywords)
                    new_insights.append(insight)
                    self.seen_tweets.add(tweet.id)

            except Exception as e:
                logger.warning(f"Twitter search error for '{query[:50]}...': {e}")
                continue

        logger.info(f"Found {len(new_insights)} new insights from Twitter")

        if new_insights:
            self._persist_insights(new_insights)
            self._write_discoveries_markdown(new_insights)
            self._write_overlap_channel(new_insights)

        return new_insights

    def _classify_tweet(self, tweet, keywords: List[str]) -> TweetInsight:
        """Classify a tweet into an insight type and score relevance."""
        text_lower = tweet.text.lower()

        # Determine insight type
        insight_type = InsightType.UNKNOWN
        type_score = 0
        for itype, kws in self.type_keywords.items():
            matches = sum(1 for kw in kws if kw in text_lower)
            if matches > type_score:
                type_score = matches
                insight_type = itype

        # Matched keywords
        matched_kw = [kw for kw in keywords if kw.lower() in text_lower]

        # Relevance score: keyword matches + type confidence + engagement signal
        relevance = len(matched_kw) * 2.0 + type_score * 0.5
        metrics = tweet.public_metrics or {}
        engagement = (
            metrics.get("like_count", 0) * 0.1 +
            metrics.get("retweet_count", 0) * 0.2 +
            metrics.get("reply_count", 0) * 0.05
        )
        relevance += min(engagement, 10.0)  # cap engagement bonus

        return TweetInsight(
            tweet_id=str(tweet.id),
            text=tweet.text,
            author_id=str(tweet.author_id),
            created_at=str(tweet.created_at),
            url=f"https://twitter.com/i/web/status/{tweet.id}",
            metrics={
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "quotes": metrics.get("quote_count", 0),
            },
            keywords_matched=matched_kw,
            insight_type=insight_type.value,
            relevance_score=round(relevance, 2),
        )

    # ── Persistence ──────────────────────────────────────────────────────

    def _persist_insights(self, insights: List[TweetInsight]):
        """Append insights to knowledge base."""
        for insight in insights:
            self.existing_knowledge.append(insight.to_record())
        self._save_knowledge()
        self._save_seen_cache()
        logger.info(f"Persisted {len(insights)} insights to knowledge base")

    def _write_discoveries_markdown(self, insights: List[TweetInsight]):
        """Append discoveries to markdown log for human review."""
        self.discoveries_log.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        with open(self.discoveries_log, "a") as f:
            f.write(f"\n## Twitter Research — {timestamp}\n\n")

            # Group by type
            by_type: Dict[str, List[TweetInsight]] = {}
            for insight in insights:
                by_type.setdefault(insight.insight_type, []).append(insight)

            for itype, group in by_type.items():
                f.write(f"### {itype.upper()}\n\n")
                for item in sorted(group, key=lambda x: x.relevance_score, reverse=True):
                    f.write(f"- **[{item.relevance_score:.1f}]** {item.text[:120]}... ")
                    f.write(f"[🔗]({item.url}) | {', '.join(item.keywords_matched[:3])}\n")
                f.write("\n")

        logger.info(f"Wrote discoveries to {self.discoveries_log}")

    def _write_overlap_channel(self, insights: List[TweetInsight]):
        """Write insights to shared overlap channel for other agents (OPH pattern)."""
        OVERLAP_CHANNEL.parent.mkdir(parents=True, exist_ok=True)

        with open(OVERLAP_CHANNEL, "a") as f:
            for insight in insights:
                record = {
                    "channel": "twitter-research",
                    "timestamp": insight.extracted_at,
                    "overlap_hash": insight.overlap_hash,
                    "observer_patch": insight.observer_patch,
                    "data": insight.to_record(),
                }
                f.write(json.dumps(record) + "\n")

        logger.info(f"Wrote {len(insights)} entries to overlap channel")

    # ── Extraction helpers ────────────────────────────────────────────────

    def extract_tools_and_tips(self, insights: List[TweetInsight]) -> List[dict]:
        """Extract actionable tools and tips from a set of insights."""
        tools = []
        for insight in insights:
            text_lower = insight.text.lower()
            if any(ind in text_lower for ind in [
                "tool:", "app:", "check out", "github.com", "huggingface.co",
                "ollama", "langchain", "llamaindex", "openai", "anthropic",
                "copilot", "cursor", "vscode", "extension", "library",
                "pip install", "npm install",
            ]):
                tools.append({
                    "source": "twitter",
                    "content": insight.text,
                    "url": insight.url,
                    "timestamp": insight.created_at,
                    "relevance_score": insight.relevance_score,
                    "insight_type": insight.insight_type,
                    "overlap_hash": insight.overlap_hash,
                })
        return tools

    def get_top_insights(self, n: int = 10, min_score: float = 3.0) -> List[dict]:
        """Get top insights by relevance score from knowledge base."""
        scored = [
            k for k in self.existing_knowledge
            if k.get("relevance_score", 0) >= min_score
        ]
        scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return scored[:n]

    def search_knowledge(self, query: str, top_n: int = 5) -> List[dict]:
        """Simple keyword search in knowledge base."""
        query_lower = query.lower()
        results = []
        for entry in self.existing_knowledge:
            text = entry.get("text", "").lower()
            if query_lower in text:
                results.append(entry)
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:top_n]


# ── Standalone execution ─────────────────────────────────────────────────────

def main():
    """Run the Twitter research agent standalone."""
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        print("ERROR: Set TWITTER_BEARER_TOKEN environment variable")
        print("Get it from: https://developer.twitter.com/en/portal/dashboard")
        sys.exit(1)

    agent = TwitterResearchAgent(bearer_token)

    # Run search
    import argparse
    parser = argparse.ArgumentParser(description="Twitter AI Research Agent")
    parser.add_argument("--keywords", "-k", nargs="+", help="Search keywords")
    parser.add_argument("--hours", type=int, default=24, help="Hours back to search")
    parser.add_argument("--max", type=int, default=100, help="Max tweets to fetch")
    parser.add_argument("--extract-tools", action="store_true", help="Extract tools from results")
    parser.add_argument("--top", type=int, default=10, help="Show top N insights")
    parser.add_argument("--search", type=str, help="Search existing knowledge base")
    args = parser.parse_args()

    if args.search:
        results = agent.search_knowledge(args.search)
        print(f"\n🔍 Knowledge search for '{args.search}':\n")
        for r in results:
            print(f"  [{r.get('relevance_score', 0):.1f}] {r.get('text', '')[:100]}...")
            print(f"         {r.get('url', '')}\n")
        return

    keywords = args.keywords
    insights = agent.search_ai_updates(
        keywords=keywords,
        hours_back=args.hours,
        max_tweets=args.max,
    )

    print(f"\n✅ Collected {len(insights)} new insights")

    if args.extract_tools:
        tools = agent.extract_tools_and_tips(insights)
        print(f"\n🔧 Extracted {len(tools)} tool mentions:\n")
        for t in tools:
            print(f"  [{t['insight_type']}] {t['content'][:100]}...")
            print(f"         {t['url']}\n")

    # Show top insights
    top = agent.get_top_insights(n=args.top)
    if top:
        print(f"\n⭐ Top {min(args.top, len(top))} insights by relevance:\n")
        for item in top:
            print(f"  [{item.get('relevance_score', 0):.1f}] [{item.get('insight_type', '?')}] "
                  f"{item.get('text', '')[:100]}...")
            print(f"         {item.get('url', '')}\n")


if __name__ == "__main__":
    main()