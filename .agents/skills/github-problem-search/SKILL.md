# GitHub Problem-Based Search Tools

Search GitHub by intent/problem rather than just keywords. Find repos that solve specific problems.

## Tools

### 1. RepoFinder Integration
AI-powered intent-based discovery for GitHub repositories.

**Use when:** You need to find starter templates or libraries for a known problem.

**Examples:**
- "I need an auth system with OAuth + JWT"
- "SaaS starters"
- "AI/ML templates"
- "Beginner friendly Python projects"

### 2. GitHub Advanced Search
Native GitHub search with operators for precise filtering.

**Operators:**
- `"monte carlo" trading language:Python` - Search with quotes and filters
- `stars:>100` - Filter by stars
- `pushed:>2024-01-01` - Filter by last push date
- `is:public fork:false` - Exclude forks

### 3. CrewAI GitHub Search Tool
Programmatic semantic search using RAG embeddings.

**Use when:** Building agents that auto-discover tools.

### 4. Self-Hosted Vector Search
Custom solution using sentence-transformers + Qdrant for deep repo indexing.

## Quick Commands

```bash
# Find Python Monte Carlo trading libraries
"monte carlo" trading language:Python stars:>100 pushed:>2024-01-01

# Search READMEs specifically
site:github.com "monte carlo simulation" "trading" in:readme
```

## Best Practices

1. Start with RepoFinder for broad discovery
2. Use GitHub Advanced Search for filtering
3. Apply RepoWiki/OpenDeepWiki for deep-dive analysis
4. Combine tools for comprehensive discovery