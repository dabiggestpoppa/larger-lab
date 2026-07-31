-- O2C Research Mesh — SQLite Schema
-- Run: sqlite3 data/research/papers.db < data/research/schema.sql
-- Run: sqlite3 data/research/citations.db < data/research/schema.sql (for graph_store)

-- ============================================================
-- PAPERS DB (data/research/papers.db)
-- ============================================================

CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,                    -- OpenAlex ID (W...) or DOI
    doi TEXT UNIQUE,                        -- Digital Object Identifier (canonical)
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    published_date TEXT,                    -- ISO 8601
    source TEXT NOT NULL,                   -- 'openalex' | 'arxiv' | 's2'
    source_id TEXT,                         -- Original ID from source
    url TEXT,
    pdf_url TEXT,
    language TEXT DEFAULT 'en',
    citation_count INTEGER DEFAULT 0,
    referenced_count INTEGER DEFAULT 0,
    is_open_access INTEGER DEFAULT 0,       -- 0 or 1
    operational_relevance INTEGER DEFAULT 0, -- 0-5 score (0 = not yet scored)
    status TEXT DEFAULT 'pending',          -- 'pending' | 'distilled' | 'skipped' | 'error'
    distilled_at TEXT,                      -- ISO 8601 timestamp
    vault_path TEXT,                        -- Relative path in O2C-VAULT/research/papers/
    raw_json TEXT,                          -- Full API response JSON (for re-processing)
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_source ON papers(source);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);
CREATE INDEX IF NOT EXISTS idx_papers_relevance ON papers(operational_relevance);

CREATE TABLE IF NOT EXISTS authors (
    id TEXT PRIMARY KEY,                    -- OpenAlex author ID
    name TEXT NOT NULL,
    orcid TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    position INTEGER DEFAULT 0,             -- 0 = first author
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,                    -- OpenAlex concept ID
    name TEXT NOT NULL,
    level INTEGER DEFAULT 0,
    parent_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS paper_concepts (
    paper_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    score REAL DEFAULT 0.0,                 -- OpenAlex concept score
    PRIMARY KEY (paper_id, concept_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (concept_id) REFERENCES concepts(id)
);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    query TEXT,
    papers_found INTEGER DEFAULT 0,
    papers_new INTEGER DEFAULT 0,
    papers_dup INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    duration_seconds REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- CITATIONS DB (data/research/citations.db)
-- ============================================================

CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,                    -- openalex:W... or doi:10.xxxx or concept:slug
    kind TEXT NOT NULL,                     -- 'paper' | 'author' | 'concept' | 'method' | 'institution'
    label TEXT NOT NULL,
    metadata JSON,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_nodes_kind ON graph_nodes(kind);

CREATE TABLE IF NOT EXISTS graph_edges (
    src_id TEXT NOT NULL,
    dst_id TEXT NOT NULL,
    kind TEXT NOT NULL,                     -- 'cites' | 'authored' | 'introduces' | 'extends' | 'contradicts' | 'uses'
    weight REAL DEFAULT 1.0,
    metadata JSON,
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (src_id, dst_id, kind),
    FOREIGN KEY (src_id) REFERENCES graph_nodes(id),
    FOREIGN KEY (dst_id) REFERENCES graph_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON graph_edges(src_id);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON graph_edges(dst_id);
CREATE INDEX IF NOT EXISTS idx_edges_kind ON graph_edges(kind);

-- ============================================================
-- AGENTS DB (data/research/agents.db)
-- ============================================================

CREATE TABLE IF NOT EXISTS research_tasks (
    id TEXT PRIMARY KEY,                    -- UUID
    gap_id TEXT,                            -- Reference to gap_detector output
    query TEXT NOT NULL,
    domains JSON,                           -- List of domain strings
    status TEXT DEFAULT 'pending',          -- 'pending' | 'running' | 'completed' | 'failed' | 'abandoned'
    priority INTEGER DEFAULT 3,             -- 1-5
    assigned_to TEXT,                       -- Agent ID
    result_json TEXT,                       -- Finding output
    confidence REAL DEFAULT 0.0,            -- Evaluator score
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON research_tasks(priority);

CREATE TABLE IF NOT EXISTS agent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,                   -- 'spawn' | 'execute' | 'evaluate' | 'write_vault' | 'error'
    detail TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agent_log_task ON agent_log(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_action ON agent_log(action);

-- ============================================================
-- DAILY CAPS TABLE (enforced by AS safety layer)
-- ============================================================

CREATE TABLE IF NOT EXISTS daily_caps (
    date TEXT PRIMARY KEY,                  -- YYYY-MM-DD
    vault_writes INTEGER DEFAULT 0,
    llm_tokens_input INTEGER DEFAULT 0,
    llm_tokens_output INTEGER DEFAULT 0,
    llm_cost_usd REAL DEFAULT 0.0,
    papers_ingested INTEGER DEFAULT 0,
    papers_distilled INTEGER DEFAULT 0,
    agents_spawned INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
