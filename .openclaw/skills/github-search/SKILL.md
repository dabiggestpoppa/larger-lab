# GitHub Search Skill — Problem-Based Discovery

## Purpose
Search GitHub by intent/problem to find repositories that solve specific trading/agent development needs.

## Usage

### Quick Discovery
```
/github-find "monte carlo position sizing trading python"
```
Uses RepoFinder-style intent matching to return relevant repos.

### Advanced Search
```
/github-search "kelly criterion simulation" language:python stars:>100
```
Direct GitHub Advanced Search with operators.

### Deep Dive
```
/github-analyze owner/repo-name
```
Generate wiki-style analysis of a specific repository.

## Implementation Options

### Option 1: RepoFinder Integration
- URL: https://airepofinder.vercel.app/
- Best for: Quick starter template discovery
- Categories: "SaaS starters", "Auth systems", "AI/ML templates"

### Option 2: CrewAI GitHubSearchTool
```python
from crewai_tools import GithubSearchTool

github_tool = GithubSearchTool(
    github_repo="*",
    content_description="Python library for Monte Carlo simulation with risk management"
)
results = github_tool.run()
```

### Option 3: Self-Hosted Vector Search
```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer('all-MiniLM-L6-v2')
qdrant = QdrantClient(":memory:")

def find_repos_for_problem(problem: str, top_k=5):
    query_vec = model.encode(problem)
    results = qdrant.search(query_vector=query_vec, limit=top_k)
    return [r.payload for r in results]
```

## Trading-Specific Queries

| Query | Purpose |
|-------|---------|
| "monte carlo position sizing trading python" | Risk management libraries |
| "kelly criterion simulation library" | Optimal position sizing |
| "portfolio optimization backtesting python" | Portfolio strategies |
| "nautilus trader strategy examples" | Nautilus-specific code |
| "vectorbt backtest optimization" | VectorBT workflows |

## Output Format
Returns top 5 repos with:
- Name and owner
- Star count
- Description
- Primary language
- Last updated date