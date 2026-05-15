#!/usr/bin/env python3
"""
GitHub Search Tools for Problem-Based Discovery
Supports RepoFinder, GitHub Advanced Search, and vector-based semantic search
"""

import requests
import json
from typing import List, Dict, Optional
from urllib.parse import quote_plus


class GitHubSearch:
    """GitHub search tools for finding repos by problem/intent."""
    
    GITHUB_API = "https://api.github.com/search/repositories"
    
    def __init__(self, token: Optional[str] = None):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "larger-lab-agents"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def search_by_problem(self, problem: str, 
                          language: str = "python",
                          min_stars: int = 10,
                          limit: int = 5) -> List[Dict]:
        """
        Search GitHub by problem statement.
        
        Args:
            problem: Natural language problem description
            language: Programming language filter
            min_stars: Minimum star threshold
            limit: Max results to return
            
        Returns:
            List of repo dicts with name, stars, description, url
        """
        query = f"{problem} language:{language} stars:>{min_stars}"
        return self._search(query, limit)
    
    def advanced_search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Direct GitHub Advanced Search.
        
        Args:
            query: Full GitHub search query string
            limit: Max results to return
            
        Returns:
            List of repo dicts
        """
        return self._search(query, limit)
    
    def _search(self, query: str, limit: int) -> List[Dict]:
        """Execute GitHub search and format results."""
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        try:
            response = requests.get(self.GITHUB_API, 
                                    headers=self.headers, 
                                    params=params)
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "name": item["full_name"],
                    "stars": item["stargazers_count"],
                    "description": item["description"] or "No description",
                    "url": item["html_url"],
                    "language": item["language"],
                    "updated": item["updated_at"][:10]
                }
                for item in data.get("items", [])
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def trading_queries(self) -> Dict[str, str]:
        """Pre-defined trading-related search queries."""
        return {
            "monte_carlo": "monte carlo position sizing trading python",
            "kelly_criterion": "kelly criterion simulation library",
            "portfolio_optimization": "portfolio optimization backtesting python",
            "nautilus_examples": "nautilus trader strategy examples",
            "vectorbt": "vectorbt backtest optimization",
            "risk_management": "trading risk management python",
            "backtesting": "python backtesting library trading"
        }


def format_results(results: List[Dict]) -> str:
    """Format search results for Telegram display."""
    if not results or "error" in results[0]:
        return f"❌ Error: {results[0].get('error', 'Unknown error')}"
    
    lines = ["🔍 **GitHub Search Results**\n"]
    for i, repo in enumerate(results, 1):
        lines.append(
            f"{i}. **{repo['name']}** ⭐{repo['stars']}\n"
            f"   {repo['description'][:80]}...\n"
            f"   {repo['language']} | Updated: {repo['updated']}\n"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    gh = GitHubSearch()
    
    # Quick problem search
    results = gh.search_by_problem("monte carlo trading simulation")
    print(format_results(results))