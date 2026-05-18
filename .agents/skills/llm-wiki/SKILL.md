# LLM Wiki Skill

> Ingest documents from USB/external sources and build a searchable knowledge base.

## Purpose

LLM Wiki (`projects/llm_wiki/`) is a self-building knowledge base that ingests documents
and makes them searchable. This skill provides procedures for using it with USB/external files.

## Location

- **Source:** `projects/llm_wiki/`
- **README:** `projects/llm_wiki/README.md`
- **Main docs:** `projects/llm_wiki/llm-wiki.md`

## Prerequisites

```bash
cd projects/llm_wiki
npm install
```

## Usage

### Ingest Documents from USB/External Source

1. **Copy files to ingest directory:**
   ```bash
   # USB drive typically mounted as D:\ or E:\ on Windows
   # Copy to a staging area
   xcopy D:\documents\*.* C:\Users\wifik\Desktop\projects\larger-lab\projects\llm_wiki\ingest\ /E
   ```

2. **Supported formats:** PDF, TXT, MD, HTML, DOCX (check README for full list)

3. **Run ingestion:**
   ```bash
   cd projects/llm_wiki
   npm run ingest -- --dir ./ingest/
   ```

4. **Query the wiki:**
   ```bash
   npm run query -- "your search query"
   ```

### Build Knowledge Base

```bash
# Full build from all ingested documents
npm run build

# Start local server for browsing
npm run dev
```

### Query from Command Line

```bash
# Search for specific topic
npm run query -- "trading strategies"

# Get summary of a document
npm run summary -- "path/to/document.pdf"
```

## Integration with Memory System

After ingesting important documents:
1. Extract key facts → add to `memory/semantic-memory.md`
2. Extract procedures → add to `memory/procedural-memory.md`
3. Note the ingestion event → add to `memory/episodic-memory.md`

## USB Workflow

1. Insert USB drive
2. Identify drive letter: `Get-PSDrive -PSProvider FileSystem`
3. Copy files to `projects/llm_wiki/ingest/`
4. Run ingestion
5. Query and extract insights
6. Update memory files with key findings
7. Clean up ingest directory

## Notes

- LLM Wiki uses local embeddings — no API key needed for basic operation
- For large document collections, ingestion may take several minutes
- The knowledge base persists between sessions (stored in `projects/llm_wiki/data/`)
