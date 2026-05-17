# LLM Wiki — Self-Building Knowledge Base

> **Version**: 1.0.0
> **Based on**: Karpathy's llm-wiki pattern, nashsu/llm_wiki
> **Purpose**: Auto-generate a structured, queryable knowledge base from raw documents using LLMs

---

## Table of Contents

1. [What is LLM Wiki](#1-what-is-llm-wiki)
2. [Knowledge Base Architecture](#2-knowledge-base-architecture)
3. [Operations](#3-operations)
4. [Integration with OCE](#4-integration-with-oce)
5. [Setup and Usage](#5-setup-and-usage)

---

## 1. What is LLM Wiki

LLM Wiki is a **self-building knowledge base** that uses Large Language Models to automatically ingest raw documents, extract structured knowledge, and produce a queryable, interlinked wiki. Inspired by Andrej Karpathy's llm-wiki concept and the nashsu/llm_wiki implementation, it transforms unstructured text into a living knowledge graph.

### Core Idea

Drop documents into a folder. The system reads them, generates structured wiki pages with summaries, key facts, and cross-references, then maintains an index and operation log. The result is a searchable, lintable, compressible knowledge base that grows organically.

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│  Layer 3: Schema                                 │
│  Rules, config, conventions, style guides        │
├─────────────────────────────────────────────────┤
│  Layer 2: Wiki                                   │
│  LLM-generated structured pages with wikilinks   │
├─────────────────────────────────────────────────┤
│  Layer 1: Raw Sources                            │
│  Immutable original documents (never modified)   │
└─────────────────────────────────────────────────┘
```

### Core Operations

| Operation | Description |
|-----------|-------------|
| **Ingest** | Add documents → auto-generate wiki pages |
| **Query** | Semantic search, graph traversal, timeline view |
| **Lint** | Quality checks, broken link detection, stale entry flagging |
| **Export** | Markdown, JSON, YAML output formats |
| **Compress** | Summarize old entries, merge duplicates, deduplicate |

### Wikilink Syntax

Pages reference each other using `[[Page Name]]` syntax, creating a knowledge graph:

```markdown
See also: [[Neural Networks]], [[Backpropagation]], [[Gradient Descent]]
```

This is compatible with **Obsidian**, **Logseq**, and other markdown-based knowledge tools. The wikilinks form edges in an implicit graph that can be traversed for related-content discovery.

### Key Properties

- **Self-building**: Drop documents, get a wiki
- **Immutable sources**: Raw documents are never modified
- **LLM-generated**: Wiki pages are synthesized, not just indexed
- **Cross-linked**: Automatic `[[wikilink]]` generation between related pages
- **Obsidian-compatible**: Works with existing markdown knowledge tools
- **Compressible**: Old entries can be summarized to control growth
- **Queryable**: Semantic search + graph traversal + timeline

---

## 2. Knowledge Base Architecture

### Directory Structure

```
llm_wiki/
├── raw/                  # Layer 1: Raw Sources (immutable)
│   ├── papers/
│   ├── docs/
│   ├── notes/
│   └── imports/
├── wiki/                 # Layer 2: Generated Wiki Pages
│   ├── Index.md          # Content catalog (auto-generated)
│   ├── Log.md            # Chronological operation record
│   ├── Neural-Networks.md
│   ├── Backpropagation.md
│   └── ...
├── schema/               # Layer 3: Rules & Conventions
│   ├── config.yaml       # Wiki configuration
│   ├── style-guide.md    # Writing conventions
│   └── templates/        # Page templates
│       ├── default.md
│       ├── concept.md
│       └── reference.md
├── cache/                # LLM response cache
│   └── embeddings/       # Vector embeddings for search
└── scripts/              # Automation scripts
    ├── ingest.py
    ├── query.py
    ├── lint.py
    ├── export.py
    └── compress.py
```

### Layer 1: Raw Sources (Immutable)

The `raw/` directory contains original documents in any format (PDF, TXT, MD, HTML). These files are **never modified** by the system. They are the ground truth.

```
raw/
├── papers/
│   ├── attention-is-all-you-need.pdf
│   ├── bert-pre-training.pdf
│   └── gpt-3-language-models.pdf
├── docs/
│   ├── api-reference.md
│   ├── architecture-overview.md
│   └── deployment-guide.md
├── notes/
│   ├── meeting-2024-01-15.md
│   └── research-ideas.md
└── imports/
    └── (auto-imported content)
```

**Rules:**
- Never edit files in `raw/`
- Use subdirectories to organize by source type
- File names should be descriptive (used for page titles)
- Support format conversion: PDF → TXT, HTML → MD before ingestion

### Layer 2: Wiki (Generated Pages)

The `wiki/` directory contains LLM-generated structured pages. Each page includes:

```markdown
# Page Title

> **Source**: [[raw/papers/attention-is-all-you-need.pdf]]
> **Generated**: 2024-01-15T10:30:00Z
> **Tags**: #nlp #transformers #attention
> **Confidence**: high

## Summary
[2-3 paragraph LLM-generated summary of the source]

## Key Facts
- Fact 1 with supporting detail
- Fact 2 with supporting detail
- Fact 3 with supporting detail

## Key Concepts
- [[Concept A]] — brief description
- [[Concept B]] — brief description

## See Also
- [[Related Page 1]]
- [[Related Page 2]]
- [[Related Page 3]]

## Source Excerpts
> "Direct quote from the source document..."
```

**Index.md** — Auto-generated content catalog:

```markdown
# Wiki Index

## By Category
### Machine Learning
- [[Neural Networks]] — Foundation of deep learning
- [[Backpropagation]] — Training algorithm for neural nets
- [[Transformers]] — Attention-based architecture

### Systems
- [[Distributed Training]] — Scaling model training
- [[Model Serving]] — Deploying models in production

## By Date
### 2024-01
- [[Attention Is All You Need]] (Jan 15)
- [[BERT Pre-training]] (Jan 10)

## Statistics
- Total pages: 42
- Total wikilinks: 187
- Last updated: 2024-01-15T10:30:00Z
```

**Log.md** — Chronological operation record:

```markdown
# Wiki Operation Log

## 2024-01-15T10:30:00Z — Ingest
- Added: [[Attention Is All You Need]]
- Source: raw/papers/attention-is-all-you-need.pdf
- Wikilinks created: 5

## 2024-01-15T10:25:00Z — Ingest
- Added: [[BERT Pre-training]]
- Source: raw/papers/bert-pre-training.pdf
- Wikilinks created: 3

## 2024-01-14T09:00:00Z — Lint
- Checked: 40 pages
- Broken links: 2 (fixed)
- Stale entries: 1 (flagged)
```

### Layer 3: Schema (Rules & Conventions)

The `schema/` directory defines how the wiki is structured and maintained:

**config.yaml:**
```yaml
wiki:
  name: "My Knowledge Base"
  version: "1.0"
  llm:
    model: "gpt-4o"
    temperature: 0.3
    max_tokens: 4096
  ingest:
    chunk_size: 8000
    overlap: 500
    supported_formats: ["pdf", "txt", "md", "html"]
  query:
    search_mode: "hybrid"  # semantic + keyword
    max_results: 10
    min_score: 0.6
  lint:
    stale_days: 90
    check_interval: 86400  # seconds
  compress:
    summarize_after_days: 180
    merge_similarity_threshold: 0.85
```

**Style Guide** (`style-guide.md`):
- Page titles use Title Case
- Summaries are 2-3 paragraphs, neutral tone
- Key facts are bullet points, max 10 per page
- Wikilinks use `[[Exact Page Name]]` format
- Tags use lowercase with hyphens: `#machine-learning`
- Every page must have a `## See Also` section

### Knowledge Graph

The wikilinks form an implicit directed graph:

```
[Neural Networks] ──→ [Backpropagation]
      │                      │
      ▼                      ▼
[Deep Learning] ◄── [Gradient Descent]
      │
      ▼
[Transformers] ──→ [Attention Mechanism]
```

This graph enables:
- **Related content discovery**: "Pages that link here"
- **Graph search**: Shortest path between concepts
- **Orphan detection**: Pages with no incoming links
- **Hub detection**: Pages with many outgoing links (good index pages)

---

## 3. Operations

### Ingest

The ingest pipeline processes raw documents into wiki pages:

```bash
# Ingest a single file
python scripts/ingest.py --file raw/papers/attention-is-all-you-need.pdf

# Ingest an entire directory
python scripts/ingest.py --dir raw/papers/

# Ingest with custom template
python scripts/ingest.py --file raw/docs/api.md --template schema/templates/reference.md

# Auto-watch mode (continuous ingestion)
python scripts/ingest.py --watch raw/ --interval 60
```

**Ingest Pipeline Steps:**

1. **Format Detection** — Identify file type (PDF, MD, HTML, TXT)
2. **Text Extraction** — Convert to plain text (pdfplumber, beautifulsoup)
3. **Chunking** — Split into overlapping chunks (configurable size)
4. **LLM Processing** — For each chunk, generate:
   - Summary paragraph
   - Key facts list
   - Concept tags
   - Suggested wikilinks
5. **Page Assembly** — Combine chunks into a single wiki page
6. **Wikilink Resolution** — Match `[[links]]` to existing pages or create stubs
7. **Index Update** — Add entry to `Index.md`
8. **Log Entry** — Record operation in `Log.md`

**Ingest Script Example:**

```python
# scripts/ingest.py (simplified)
import os
import yaml
from pathlib import Path
from llm import generate_wiki_page, extract_key_facts, suggest_links

def ingest_file(file_path, config):
    """Ingest a single document into the wiki."""
    # 1. Extract text
    text = extract_text(file_path)
    
    # 2. Chunk
    chunks = chunk_text(text, config['chunk_size'], config['overlap'])
    
    # 3. Generate wiki content
    page_title = Path(file_path).stem.replace('-', ' ').replace('_', ' ').title()
    
    wiki_content = f"# {page_title}\n\n"
    wiki_content += f"> **Source**: [[{file_path}]]\n"
    wiki_content += f"> **Generated**: {now_iso()}\n\n"
    
    # 4. LLM generation
    summary = generate_wiki_page(chunks, config['model'])
    wiki_content += f"## Summary\n{summary['summary']}\n\n"
    wiki_content += f"## Key Facts\n"
    for fact in summary['key_facts']:
        wiki_content += f"- {fact}\n"
    wiki_content += "\n## See Also\n"
    for link in summary['related_pages']:
        wiki_content += f"- [[{link}]]\n"
    
    # 5. Write page
    wiki_path = f"wiki/{page_title.replace(' ', '-')}.md"
    Path(wiki_path).write_text(wiki_content)
    
    # 6. Update index and log
    update_index(page_title, summary['tags'])
    append_log("Ingest", page_title, file_path)
    
    return wiki_path
```

### Query

Three search modes for finding information:

```bash
# Semantic search (vector similarity)
python scripts/query.py --semantic "how does attention work in transformers"

# Keyword search (BM25 / full-text)
python scripts/query.py --keyword "backpropagation gradient"

# Graph search (wikilink traversal)
python scripts/query.py --graph "Neural Networks" --depth 2

# Timeline view (chronological)
python scripts/query.py --timeline --since "2024-01-01"

# Combined hybrid search (default)
python scripts/query.py "transformer architecture"
```

**Query Script Example:**

```python
# scripts/query.py (simplified)
def semantic_search(query, max_results=10, min_score=0.6):
    """Search wiki pages using vector similarity."""
    query_embedding = embed(query)
    results = []
    for page_file in Path("wiki").glob("*.md"):
        if page_file.name in ("Index.md", "Log.md"):
            continue
        content = page_file.read_text()
        page_embedding = embed(content)
        score = cosine_similarity(query_embedding, page_embedding)
        if score >= min_score:
            results.append({
                "page": page_file.stem,
                "score": score,
                "snippet": content[:200]
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)[:max_results]

def graph_search(start_page, depth=2):
    """Traverse wikilink graph from a starting page."""
    visited = set()
    queue = [(start_page, 0)]
    results = []
    
    while queue:
        page_name, current_depth = queue.pop(0)
        if page_name in visited or current_depth > depth:
            continue
        visited.add(page_name)
        
        page_file = Path(f"wiki/{page_name}.md")
        if page_file.exists():
            content = page_file.read_text()
            links = extract_wikilinks(content)
            results.append({
                "page": page_name,
                "depth": current_depth,
                "links": links
            })
            for link in links:
                queue.append((link, current_depth + 1))
    
    return results
```

### Lint

Quality assurance for the wiki:

```bash
# Full lint check
python scripts/lint.py

# Check specific issues
python scripts/lint.py --check broken-links
python scripts/lint.py --check stale-entries
python scripts/lint.py --check orphans
python scripts/lint.py --check format

# Auto-fix issues
python scripts/lint.py --fix
```

**Lint Checks:**

| Check | Description | Auto-fix |
|-------|-------------|----------|
| **Broken Links** | `[[Page Name]]` pointing to non-existent page | Create stub |
| **Orphan Pages** | Pages with no incoming wikilinks | Flag for review |
| **Stale Entries** | Pages not updated in N days | Flag for refresh |
| **Format Violations** | Missing sections, bad headers | Reformat |
| **Duplicate Content** | Near-duplicate pages | Suggest merge |
| **Empty Pages** | Pages with minimal content | Flag for expansion |

**Lint Script Example:**

```python
# scripts/lint.py (simplified)
def lint_broken_links():
    """Find and fix broken wikilinks."""
    broken = []
    for page_file in Path("wiki").glob("*.md"):
        content = page_file.read_text()
        links = extract_wikilinks(content)
        for link in links:
            target = Path(f"wiki/{link}.md")
            if not target.exists():
                broken.append({
                    "source": page_file.name,
                    "broken_link": link,
                    "suggestion": f"Create stub: wiki/{link}.md"
                })
    return broken

def lint_orphans():
    """Find pages with no incoming wikilinks."""
    all_pages = set()
    linked_pages = set()
    
    for page_file in Path("wiki").glob("*.md"):
        if page_file.name in ("Index.md", "Log.md"):
            continue
        all_pages.add(page_file.stem)
        content = page_file.read_text()
        linked_pages.update(extract_wikilinks(content))
    
    orphans = all_pages - linked_pages
    return [{"page": p, "incoming_links": 0} for p in orphans]
```

### Export

Output the wiki in various formats:

```bash
# Export all pages as markdown (default)
python scripts/export.py --format markdown --output export/

# Export as JSON (for programmatic use)
python scripts/export.py --format json --output export/wiki.json

# Export as YAML
python scripts/export.py --format yaml --output export/wiki.yaml

# Export specific pages
python scripts/export.py --pages "Neural-Networks,Transformers" --format json

# Export the knowledge graph
python scripts/export.py --format graph --output export/graph.json
```

**JSON Export Format:**

```json
{
  "wiki": {
    "name": "My Knowledge Base",
    "version": "1.0",
    "pages": [
      {
        "title": "Neural Networks",
        "source": "raw/papers/nn-foundations.pdf",
        "generated": "2024-01-15T10:30:00Z",
        "tags": ["machine-learning", "deep-learning"],
        "summary": "Neural networks are...",
        "key_facts": ["Fact 1", "Fact 2"],
        "links": ["Backpropagation", "Deep Learning"],
        "content": "# Neural Networks\n\n..."
      }
    ],
    "graph": {
      "nodes": ["Neural Networks", "Backpropagation", "Deep Learning"],
      "edges": [
        {"from": "Neural Networks", "to": "Backpropagation"},
        {"from": "Neural Networks", "to": "Deep Learning"}
      ]
    }
  }
}
```

### Compress

Control wiki growth by summarizing and merging:

```bash
# Summarize pages older than 180 days
python scripts/compress.py --summarize --older-than 180

# Merge near-duplicate pages
python scripts/compress.py --merge --threshold 0.85

# Full compression pipeline
python scripts/compress.py --full

# Dry run (show what would change)
python scripts/compress.py --full --dry-run
```

**Compression Pipeline:**

1. **Identify candidates**: Pages older than N days or with high similarity
2. **Summarize**: Re-generate page with shorter summary, fewer facts
3. **Merge**: Combine near-duplicate pages, redirect wikilinks
4. **Deduplicate**: Remove redundant content across pages
5. **Archive**: Move compressed originals to `archive/`
6. **Log**: Record all changes in `Log.md`

---

## 4. Integration with OCE

### Integration with Structural Memory

LLM Wiki's `wiki/` layer maps directly to OCE's Structural Memory:

```
LLM Wiki                          OCE Structural Memory
─────────                         ─────────────────────
wiki/*.md pages        →          Memory entries (key-value + metadata)
[[wikilink]] graph     →          Memory relationships (edges)
Index.md               →          Memory index / catalog
Log.md                 →          Memory operation log
schema/config.yaml     →          Memory schema / config
```

**Sync Pattern:**

```python
# Sync LLM Wiki → OCE Structural Memory
def sync_wiki_to_oce(wiki_dir, oce_memory):
    for page_file in Path(wiki_dir).glob("*.md"):
        if page_file.name in ("Index.md", "Log.md"):
            continue
        content = page_file.read_text()
        metadata = extract_metadata(content)
        oce_memory.store(
            key=f"wiki:{page_file.stem}",
            value=content,
            tags=metadata.get("tags", []),
            source=str(page_file),
            timestamp=metadata.get("generated")
        )
        for link in extract_wikilinks(content):
            oce_memory.add_edge(
                from_key=f"wiki:{page_file.stem}",
                to_key=f"wiki:{link}",
                type="wikilink"
            )
```

### Integration with AgentMemory

LLM Wiki can use AgentMemory as its persistent backend:

```python
# Use AgentMemory as LLM Wiki storage backend
from agentmemory import AgentMemory

memory = AgentMemory(project_name="llm_wiki")

# Store wiki page
memory.add(
    content=wiki_page_content,
    tags=["wiki", "generated"] + page_tags,
    metadata={
        "title": page_title,
        "source": source_file,
        "wikilinks": wikilinks
    }
)

# Search wiki pages
results = memory.search(
    query="transformer attention mechanism",
    n_results=5,
    filter_tags=["wiki"]
)
```

### Auto-Ingesting OCE Documentation

Set up automatic ingestion of OCE project docs:

```bash
# Ingest OCE backend docs
python scripts/ingest.py --dir oce/backend/ --template schema/templates/code-doc.md

# Ingest OCE API docs
python scripts/ingest.py --file oce/docs/api-reference.md

# Ingest OCE architecture docs
python scripts/ingest.py --dir oce/docs/ --recursive

# Watch OCE docs for changes
python scripts/ingest.py --watch oce/docs/ --interval 300
```

**OCE Template Example:** `schema/templates/code-doc.md` generates pages with Overview, API Endpoints, Key Functions, Dependencies, and See Also sections from source code.

### Wiki Export to KNOWLEDGE Layer

Export the wiki to OCE's KNOWLEDGE layer for cross-agent access:

```bash
# Export wiki to OCE knowledge directory
python scripts/export.py --format markdown --output oce/knowledge/wiki/

# Export to shared knowledge base
python scripts/export.py --format json --output shared-conversations/knowledge/wiki.json

# Generate knowledge graph for OCE topology
python scripts/export.py --format graph --output oce/knowledge/graph.json
```

---

## 5. Setup and Usage

### Prerequisites

```bash
# Python 3.10+
python --version

# Install dependencies
pip install openai tiktoken numpy scikit-learn
pip install pdfplumber beautifulsoup4  # for document parsing
pip install watchdog  # for auto-watch mode
```

### Clone and Setup

```bash
# Clone the reference implementation
git clone https://github.com/nashsu/llm_wiki.git
cd llm_wiki

# Or create from scratch
mkdir -p llm_wiki/{raw/{papers,docs,notes},wiki,schema/templates,cache/embeddings,scripts}
cd llm_wiki

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Configuration

Create `schema/config.yaml`:

```yaml
wiki:
  name: "My Knowledge Base"
  version: "1.0"
  
llm:
  provider: "openai"           # openai, anthropic, ollama, openrouter
  model: "gpt-4o"
  api_key_env: "OPENAI_API_KEY"
  temperature: 0.3
  max_tokens: 4096
  
ingest:
  chunk_size: 8000
  overlap: 500
  supported_formats: ["pdf", "txt", "md", "html"]
  default_template: "default"
  
query:
  search_mode: "hybrid"        # semantic, keyword, hybrid, graph
  max_results: 10
  min_score: 0.6
  embedding_model: "text-embedding-3-small"
  
lint:
  stale_days: 90
  check_interval: 86400
  auto_fix: false
  
compress:
  summarize_after_days: 180
  merge_similarity_threshold: 0.85
  archive_dir: "archive"
  
paths:
  raw: "raw"
  wiki: "wiki"
  schema: "schema"
  cache: "cache"
  archive: "archive"
```

Set your API key:

```bash
# Linux/Mac
export OPENAI_API_KEY="sk-..."

# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."

# Or create .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

### Running the Ingest Pipeline

```bash
# Step 1: Add documents to raw/
cp ~/Documents/research-paper.pdf raw/papers/
cp ~/Documents/notes.md raw/notes/

# Step 2: Ingest single file
python scripts/ingest.py --file raw/papers/research-paper.pdf

# Step 3: Ingest entire directory
python scripts/ingest.py --dir raw/papers/

# Step 4: Check the generated wiki
cat wiki/Research-Paper.md

# Step 5: Review the index
cat wiki/Index.md

# Step 6: Check the log
cat wiki/Log.md
```

### Querying the Knowledge Base

```bash
# Semantic search
python scripts/query.py "how do transformers handle long sequences"

# Find related pages via graph
python scripts/graph.py --from "Neural Networks" --depth 2

# Timeline of recent additions
python scripts/query.py --timeline --limit 20

# List all pages
python scripts/query.py --list

# Show page details
python scripts/query.py --show "Neural-Networks"
```

### Example Workflow

```bash
# 1. Setup
mkdir my-wiki && cd my-wiki
python -m llm_wiki init

# 2. Add and ingest
cp ~/Downloads/*.pdf raw/papers/
python scripts/ingest.py --dir raw/papers/

# 3. Query, lint, export, compress
python scripts/query.py "attention mechanism"
python scripts/lint.py --fix
python scripts/export.py --format markdown --output export/
python scripts/compress.py --summarize --older-than 90
```

### Tips

- **Start small**: Ingest 2-3 documents first, review quality, then scale
- **Review generated pages**: LLM output is a starting point — edit for accuracy
- **Use templates**: Create domain-specific templates for consistent output
- **Run lint regularly**: Catch broken links and stale entries early
- **Compress periodically**: Prevent unbounded wiki growth
- **Version control**: Commit `wiki/` and `schema/` to git (ignore `cache/` and `raw/` if large)
- **Obsidian integration**: Open the `wiki/` folder as an Obsidian vault for visual graph exploration

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `ingest.py --file X` | Ingest single document |
| `ingest.py --dir X` | Ingest directory |
| `ingest.py --watch X` | Auto-watch for new files |
| `query.py "text"` | Search the wiki |
| `query.py --graph X` | Graph traversal from page X |
| `lint.py` | Quality checks |
| `lint.py --fix` | Auto-fix issues |
| `export.py --format X` | Export in format X |
| `compress.py --full` | Full compression pipeline |
