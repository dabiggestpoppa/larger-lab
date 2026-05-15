#!/usr/bin/env python3
"""
GitHub Discovery Agent
======================
Autonomous agent that searches GitHub for repos, tools, and code
relevant to the agent's current goals — then feeds findings into workspace.

Part of the SRRS+OPH cognitive architecture (Observer Patch pattern).

Usage:
  - As Hermes skill: /github-discover <concept> [--niche] [--stars 10]
  - As standalone:   python github_discovery_agent.py <concept>
  - As cron job:     Runs on schedule via Hermes cron system
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from urllib.parse import quote

# ── Workspace paths ──────────────────────────────────────────────────────────
LAB_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
AGENT_DIR = Path(__file__).resolve().parent
WORKSPACE = AGENT_DIR / "workspace"
DISCOVERIES_LOG = WORKSPACE / "github-discoveries.md"
KNOWN_REPOS = WORKSPACE / "known-repos.json"
OVERLAP_CHANNEL = LAB_ROOT / "shared" / "overlap-log.jsonl"

WORKSPACE.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("github-discovery")


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class RepoInsight:
    """A single repository insight discovered from GitHub."""
    repo_id: int
    full_name: str
    description: str
    url: str
    stars: int = 0
    forks: int = 0
    language: str = ""
    last_updated: str = ""
    topics: List[str] = field(default_factory=list)
    has_license: bool = False
    license_name: str = ""
    readme_available: bool = False
    relevance_score: float = 0.0
    discovery_query: str = ""
    source: str = "github"
    extracted_at: str = ""
    # OPH overlap tracking
    observer_patch: str = "github-discovery"
    overlap_hash: str = ""

    def __post_init__(self):
        if not self.extracted_at:
            self.extracted_at = datetime.now(timezone.utc).isoformat()
        self.overlap_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        raw = f"{self.repo_id}:{self.full_name}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_record(self) -> dict:
        return {
            "repo_id": self.repo_id,
            "full_name": self.full_name,
            "description": self.description,
            "url": self.url,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "last_updated": self.last_updated,
            "topics": self.topics,
            "has_license": self.has_license,
            "license_name": self.license_name,
            "readme_available": self.readme_available,
            "relevance_score": self.relevance_score,
            "discovery_query": self.discovery_query,
            "source": self.source,
            "extracted_at": self.extracted_at,
            "observer_patch": self.observer_patch,
            "overlap_hash": self.overlap_hash,
        }


# ── GitHub Discovery Agent ───────────────────────────────────────────────────

class GitHubDiscoveryAgent:
    """
    Autonomous GitHub discovery agent.
    Searches for repos, tools, and code relevant to current goals.
    """

    def __init__(self, github_token: str, workspace_path: str = None):
        self.github_token = github_token
        self.workspace = Path(workspace_path).expanduser() if workspace_path else WORKSPACE
        self.discoveries_log = self.workspace / "github-discoveries.md"
        self.known_repos_file = self.workspace / "known-repos.json"

        # Load known repos for deduplication
        self.known_repos: Dict[int, dict] = self._load_known_repos()

        # GitHub API headers
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Search strategies for niche discovery
        self.search_strategies = [
            "{concept} in:name,description stars:10..500",
            "{concept} language:python language:javascript",
            "{concept} topic:machine-learning topic:deep-learning",
            "awesome {concept}",
            "{concept} tutorial example implementation",
            "{concept} library framework tool",
            "{concept} alternative lightweight",
        ]

    def _load_known_repos(self) -> Dict[int, dict]:
        if self.known_repos_file.exists():
            try:
                with open(self.known_repos_file) as f:
                    data = json.load(f)
                    return {r["repo_id"]: r for r in data}
            except (json.JSONDecodeError, KeyError):
                return {}
        return {}

    def _save_known_repos(self):
        """Persist known repos (keep last 1000)."""
        repos = list(self.known_repos.values())[-1000:]
        self.known_repos_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.known_repos_file, "w") as f:
            json.dump(repos, f, indent=2)

    # ── GitHub API ────────────────────────────────────────────────────────

    def _api_get(self, url: str, params: dict = None) -> Optional[dict]:
        """Make authenticated GitHub API request."""
        try:
            import requests
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                logger.warning("GitHub API rate limit hit")
                return None
            elif resp.status_code == 401:
                logger.error("GitHub token invalid or expired")
                return None
            else:
                logger.warning(f"GitHub API {resp.status_code}: {resp.text[:200]}")
                return None
        except ImportError:
            logger.error("requests not installed — run: pip install requests")
            return None
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None

    def search_repositories(self, query: str, sort: str = "stars",
                            order: str = "desc", per_page: int = 30) -> List[dict]:
        """Search GitHub repositories."""
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
        }
        result = self._api_get(url, params)
        if result and "items" in result:
            return result["items"]
        return []

    def get_repo_details(self, owner: str, repo: str) -> Optional[dict]:
        """Get detailed info about a specific repo."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        return self._api_get(url)

    def get_repo_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch README content for a repo."""
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        resp = self._api_get(url)
        if resp and "content" in resp:
            import base64
            try:
                return base64.b64decode(resp["content"]).decode("utf-8", errors="replace")
            except Exception:
                return None
        return None

    # ── Discovery Logic ───────────────────────────────────────────────────

    def discover(self, concept: str, niche: bool = True,
                 max_results: int = 30) -> List[RepoInsight]:
        """
        Discover repositories related to a concept.

        Args:
            concept: The idea/technology to search for
            niche: If True, use strategies to find lesser-known but valuable repos
            max_results: Maximum number of results to return
        """
        discoveries = []
        queries = self._search_strategies(concept, niche)

        repos_seen = set()

        for query in queries:
            if len(discoveries) >= max_results:
                break

            repos = self.search_repositories(query)
            for repo_data in repos:
                repo_id = repo_data.get("id", 0)

                # Deduplicate
                if repo_id in repos_seen or repo_id in self.known_repos:
                    continue
                repos_seen.add(repo_id)

                # Score the repo
                score = self._score_repo(repo_data, concept)
                description = repo_data.get("description", "") or ""

                insight = RepoInsight(
                    repo_id=repo_id,
                    full_name=repo_data.get("full_name", ""),
                    description=description,
                    url=repo_data.get("html_url", ""),
                    stars=repo_data.get("stargazers_count", 0),
                    forks=repo_data.get("forks_count", 0),
                    language=repo_data.get("language", "") or "",
                    last_updated=repo_data.get("updated_at", ""),
                    topics=repo_data.get("topics", []),
                    has_license=repo_data.get("license") is not None,
                    license_name=(repo_data.get("license") or {}).get("spdx_id", ""),
                    readme_available=repo_data.get("has_readme", False),
                    relevance_score=score,
                    discovery_query=query,
                )
                discoveries.append(insight)

        # Sort by relevance
        discoveries.sort(key=lambda x: x.relevance_score, reverse=True)
        logger.info(f"Discovered {len(discoveries)} repos for '{concept}'")

        if discoveries:
            self._persist_discoveries(discoveries)
            self._write_discoveries_markdown(discoveries)
            self._write_overlap_channel(discoveries)

        return discoveries

    def _search_strategies(self, concept: str, niche: bool) -> List[str]:
        """Build search queries using multiple strategies."""
        queries = []
        for strategy in self.search_strategies:
            queries.append(strategy.format(concept=concept))

        if niche:
            # Add niche-specific queries
            queries.extend([
                f"{concept} stars:5..50 pushed:>2024-01-01",
                f"{concept} in:readme language:python stars:10..200",
                f"alternative to {concept}",
                f"{concept} minimal simple clean",
            ])

        return queries

    def _score_repo(self, repo: dict, concept: str) -> float:
        """Score a repository for relevance and quality."""
        score = 0.0
        concept_lower = concept.lower()

        # Recency boost (recently updated repos are more relevant)
        updated = repo.get("updated_at", "")
        if updated:
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                days_old = (datetime.now(timezone.utc) - updated_dt).days
                score += max(0, 30 - days_old) * 0.5
            except Exception:
                pass

        # README quality
        desc = repo.get("description", "") or ""
        if concept_lower in desc.lower():
            score += 15
        score += min(10, len(desc) / 30)

        # License (indicates serious project)
        if repo.get("license"):
            score += 10

        # Stars (popularity signal)
        stars = repo.get("stargazers_count", 0)
        if stars > 0:
            score += min(20, stars ** 0.3)

        # Stars-to-forks ratio (quality indicator)
        forks = repo.get("forks_count", 0)
        if forks > 0 and stars > 0:
            ratio = stars / forks
            score += min(10, ratio * 2)

        # Topic match
        topics = repo.get("topics", [])
        topic_hits = sum(1 for t in topics if concept_lower in t.lower())
        score += topic_hits * 5

        # Has README
        if repo.get("has_readme"):
            score += 5

        return round(score, 2)

    # ── Persistence ──────────────────────────────────────────────────────

    def _persist_discoveries(self, discoveries: List[RepoInsight]):
        """Add discoveries to known repos."""
        for d in discoveries:
            self.known_repos[d.repo_id] = d.to_record()
        self._save_known_repos()

    def _write_discoveries_markdown(self, discoveries: List[RepoInsight]):
        """Append discoveries to markdown log."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        with open(self.discoveries_log, "a", encoding="utf-8") as f:
            f.write(f"\n## GitHub Discovery — {timestamp}\n\n")

            for item in discoveries[:20]:  # Top 20 in the log
                license_str = f" ({item.license_name})" if item.has_license else ""
                topics_str = ", ".join(item.topics[:5]) if item.topics else ""
                f.write(f"- **[{item.relevance_score:.1f}]** **{item.full_name}**  ")
                f.write(f"{item.description[:100]}...  ")
                f.write(f"\n  [stars]{item.stars} [forks]{item.forks} `{item.language}`{license_str}  ")
                f.write(f"[Link]({item.url})\n")
                if topics_str:
                    f.write(f"  Topics: {topics_str}\n")
                f.write("\n")

    def _write_overlap_channel(self, discoveries: List[RepoInsight]):
        """Write discoveries to shared overlap channel for other agents."""
        OVERLAP_CHANNEL.parent.mkdir(parents=True, exist_ok=True)

        with open(OVERLAP_CHANNEL, "a") as f:
            for d in discoveries:
                record = {
                    "channel": "github-discovery",
                    "timestamp": d.extracted_at,
                    "overlap_hash": d.overlap_hash,
                    "observer_patch": d.observer_patch,
                    "data": d.to_record(),
                }
                f.write(json.dumps(record) + "\n")

    # ── Query helpers ─────────────────────────────────────────────────────

    def find_niche_tools(self, concept: str) -> List[RepoInsight]:
        """Specifically search for lesser-known but valuable tools."""
        return self.discover(concept, niche=True, max_results=20)

    def search_known(self, query: str, top_n: int = 5) -> List[dict]:
        """Search already-discovered repos."""
        query_lower = query.lower()
        results = []
        for repo in self.known_repos.values():
            text = f"{repo.get('full_name', '')} {repo.get('description', '')} {repo.get('topics', [])}".lower()
            if query_lower in text:
                results.append(repo)
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:top_n]

    def get_stats(self) -> dict:
        """Return agent statistics."""
        return {
            "known_repos": len(self.known_repos),
            "discoveries_log_exists": self.discoveries_log.exists(),
            "last_updated": max(
                (r.get("extracted_at", "") for r in self.known_repos.values()),
                default="never",
            ),
        }


# ── Standalone execution ─────────────────────────────────────────────────────

def main():
    """Run the GitHub discovery agent standalone."""
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("ERROR: Set GITHUB_TOKEN environment variable")
        print("Create one at: https://github.com/settings/tokens")
        print("Needs only: repo (read) + public_repo scopes")
        sys.exit(1)

    agent = GitHubDiscoveryAgent(github_token)

    import argparse
    parser = argparse.ArgumentParser(description="GitHub Discovery Agent")
    parser.add_argument("concept", nargs="?", help="Concept/technology to search for")
    parser.add_argument("--niche", action="store_true", help="Find niche/lesser-known repos")
    parser.add_argument("--max", type=int, default=30, help="Max results")
    parser.add_argument("--known-search", type=str, help="Search already-known repos")
    parser.add_argument("--stats", action="store_true", help="Show agent stats")
    args = parser.parse_args()

    if args.stats:
        stats = agent.get_stats()
        print(f"\n📊 GitHub Discovery Agent Stats:\n")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return

    if args.known_search:
        results = agent.search_known(args.known_search)
        print(f"\n🔍 Known repos matching '{args.known_search}':\n")
        for r in results:
            print(f"  ⭐{r.get('stars', 0)} {r.get('full_name', '')}")
            print(f"    {r.get('description', '')[:80]}...")
            print(f"    {r.get('url', '')}\n")
        return

    if not args.concept:
        parser.print_help()
        return

    discoveries = agent.discover(args.concept, niche=args.niche, max_results=args.max)

    print(f"\n✅ Discovered {len(discoveries)} repos for '{args.concept}':\n")
    for d in discoveries[:15]:
        print(f"  [{d.relevance_score:.1f}] {d.full_name} — {d.description[:60]}...")
        print(f"       ⭐{d.stars} 🍴{d.forks} `{d.language}` {d.url}\n")


if __name__ == "__main__":
    main()