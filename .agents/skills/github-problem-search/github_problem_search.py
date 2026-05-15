"""
GitHub Problem-Based Search Tools for Agents
Search GitHub by intent/problem rather than just keywords.
"""

import requests
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus

@dataclass
class GitHubRepo:
    """Container for GitHub repository information."""
    name: str
    full_name: str
    description: str
    url: str
    stars: int
    language: str
    pushed_at: str
    topics: List[str]
    
    def __str__(self) -> str:
        return f"{self.full_name} ⭐{self.stars} | {self.description[:80]}..."

class GitHubProblemSearch:
    """
    Tools for searching GitHub by problem/intent rather than keywords.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the GitHub search tools.
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits
        """
        self.token = github_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Agent-GitHub-Search"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def search_by_problem(self, problem: str, 
                          language: str = None,
                          min_stars: int = 10,
                          max_results: int = 10) -> List[GitHubRepo]:
        """
        Search GitHub for repositories that solve a specific problem.
        
        Args:
            problem: Natural language description of the problem
            language: Optional language filter
            min_stars: Minimum stars threshold
            max_results: Maximum number of results
            
        Returns:
            List of GitHubRepo objects
        """
        # Build search query
        query_parts = [problem]
        if language:
            query_parts.append(f"language:{language}")
        query_parts.append(f"stars:>={min_stars}")
        query_parts.append("fork:false")
        query_parts.append("archived:false")
        
        query = " ".join(query_parts)
        encoded_query = quote_plus(query)
        
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={max_results}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
        
        data = response.json()
        repos = []
        
        for item in data.get("items", []):
            repo = GitHubRepo(
                name=item["name"],
                full_name=item["full_name"],
                description=item.get("description", "") or "",
                url=item["html_url"],
                stars=item["stargazers_count"],
                language=item.get("language", "") or "",
                pushed_at=item["pushed_at"],
                topics=[]  # Would need separate API call for topics
            )
            repos.append(repo)
        
        return repos
    
    def search_monte_carlo_trading(self, max_results: int = 10) -> List[GitHubRepo]:
        """
        Find repositories for Monte Carlo simulations in trading.
        
        Args:
            max_results: Maximum number of results
            
        Returns:
            List of GitHubRepo objects
        """
        queries = [
            "monte carlo trading simulation python",
            "kelly criterion position sizing",
            "portfolio optimization backtesting",
            "risk management trading python"
        ]
        
        all_repos = []
        seen = set()
        
        for query in queries:
            repos = self.search_by_problem(query, language="Python", min_stars=5, max_results=max_results//2)
            for repo in repos:
                if repo.full_name not in seen:
                    all_repos.append(repo)
                    seen.add(repo.full_name)
        
        return all_repos[:max_results]
    
    def search_auth_systems(self, auth_type: str = "oauth", max_results: int = 10) -> List[GitHubRepo]:
        """
        Find authentication system repositories.
        
        Args:
            auth_type: Type of auth (oauth, jwt, saml, etc.)
            max_results: Maximum number of results
            
        Returns:
            List of GitHubRepo objects
        """
        query = f"auth {auth_type} jwt security"
        return self.search_by_problem(query, min_stars=50, max_results=max_results)
    
    def search_ai_agent_frameworks(self, max_results: int = 10) -> List[GitHubRepo]:
        """
        Find AI agent framework repositories.
        
        Args:
            max_results: Maximum number of results
            
        Returns:
            List of GitHubRepo objects
        """
        query = "ai agent framework autonomous"
        return self.search_by_problem(query, language="Python", min_stars=100, max_results=max_results)
    
    def get_repo_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repository details
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code}")
        
        return response.json()
    
    def search_in_readme(self, query: str, max_results: int = 10) -> List[GitHubRepo]:
        """
        Search specifically in README files using Google search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of GitHubRepo objects (limited info from Google results)
        """
        # This would require Google Custom Search API
        # For now, return empty list with note
        return []

def format_results(repos: List[GitHubRepo]) -> str:
    """Format repository results for display."""
    if not repos:
        return "No repositories found."
    
    output = []
    for i, repo in enumerate(repos, 1):
        output.append(f"{i}. **{repo.full_name}** ⭐{repo.stars}")
        output.append(f"   {repo.description}")
        output.append(f"   Language: {repo.language} | Updated: {repo.pushed_at[:10]}")
        output.append(f"   URL: {repo.url}")
        output.append("")
    
    return "\n".join(output)

# Example usage
if __name__ == "__main__":
    searcher = GitHubProblemSearch()
    
    print("🔍 Finding Monte Carlo trading libraries...")
    repos = searcher.search_monte_carlo_trading(5)
    print(format_results(repos))
    
    print("\n🔍 Finding auth systems...")
    repos = searcher.search_auth_systems(5)
    print(format_results(repos))