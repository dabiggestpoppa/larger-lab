# DeepWiki Skill

> **Purpose:** Generate AI-powered interactive wikis for any GitHub/GitLab/BitBucket repository. Use for code understanding, documentation, architecture diagrams, and Q&A about any repo.

## What It Does
- Analyzes any code repository and generates a comprehensive wiki
- Creates Mermaid diagrams for architecture visualization
- Provides RAG-powered Q&A ("Ask" feature) about any repo
- Supports DeepResearch for complex multi-turn investigation

## Setup
- **Location:** `tools/deepwiki-open/`
- **Frontend:** Next.js on port 3000 (`npm run dev`)
- **Backend:** Python FastAPI (`python -m api.main`)
- **Config:** `.env` file with API keys (GOOGLE_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY)

## Usage
1. Start backend: `cd tools/deepwiki-open && python -m api.main`
2. Start frontend: `cd tools/deepwiki-open && npm run dev`
3. Open http://localhost:3000
4. Enter any GitHub repo URL → Generate Wiki
5. Use "Ask" tab to ask questions about the repo

## API Keys Needed
- Google AI Studio key (free): https://makersuite.google.com/app/apikey
- OpenAI key: https://platform.openai.com/api-keys
- OpenRouter key: https://openrouter.ai/keys

## Integration
- All agents should use DeepWiki to understand new repos before working with it
- RA maintains the resource index — ask RA for any repo summaries
- Use `tools/deepwiki-open/` for local wiki generation

## Alternatives
- For quick repo summaries without running DeepWiki: use `gh api` or web_fetch on the repo
- For code search: use GitHub's search API
