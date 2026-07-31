# 🎵 Music Agent — Synthesized Build Plan

> **RL Synthesis** — 2026-06-12
> Standalone project (not OCE). OpenRouter LLM. Local-first + container-ready.

---

## 1. Project Charter

An autonomous AI music agent that:
1. **Downloads** music from authorized sources (YouTube via yt-dlp, SoundCloud, direct URLs)
2. **Discovers** artist discographies via MusicBrainz + Spotify
3. **Organizes** a local library with proper metadata tagging
4. **Creates** playlists (M3U local + Spotify)
5. **Runs** as CLI, MCP server, or autonomous agent loop

**Legal boundary:** Only downloads authorized content. Rights-aware by design.

---

## 2. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.12+ | Existing project convention |
| LLM | OpenRouter (via `openai` SDK) | Multi-model, single endpoint |
| Agent Loop | Custom state machine (no LangGraph) | Lighter weight, fewer deps |
| Download Engine | yt-dlp (Python package) | Best-in-class, actively maintained |
| Metadata | MusicBrainz (free) + Spotify API | Comprehensive coverage |
| Tagging | mutagen | Standard Python ID3 library |
| Database | SQLite (via SQLModel) | Zero config, single file |
| CLI | Typer + Rich | Modern Python CLI |
| MCP | FastMCP | For Claude Desktop / Cursor integration |
| Container | Docker + docker-compose | Local dev + deployment |

---

## 3. Project Structure

```
music-agent/                    # NEW top-level project (standalone)
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
│
├── src/
│   └── music_agent/
│       ├── __init__.py
│       ├── main.py              # CLI entry (Typer)
│       ├── config.py            # Settings (pydantic-settings)
│       │
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── orchestrator.py  # Intent classification + routing
│       │   ├── planner.py       # OpenRouter LLM calls
│       │   └── prompts.py       # System prompts
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── downloader.py   # yt-dlp wrapper
│       │   ├── searcher.py      # YouTube Music search
│       │   ├── metadata.py      # MusicBrainz + Spotify
│       │   ├── tagger.py        # mutagen tagging
│       │   └── organizer.py     # File system organization
│       │
│       ├── discovery/
│       │   ├── __init__.py
│       │   ├── musicbrainz.py  # Discography lookup
│       │   ├── spotify.py      # Spotify API
│       │   └── youtube_music.py # ytmusicapi
│       │
│       ├── library/
│       │   ├── __init__.py
│       │   ├── db.py           # SQLModel models + DB ops
│       │   └── playlists.py    # Playlist CRUD + M3U export
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── server.py       # FastMCP server
│       │
│       └── safety/
│           ├── __init__.py
│           └── rights.py       # Rights verification engine
│
├── data/                        # Runtime data (gitignored)
│   ├── library.db
│   ├── downloads/
│   └── playlists/
│
└── tests/
    ├── test_downloader.py
    ├── test_metadata.py
    ├── test_library.py
    └── test_rights.py
```

---

## 4. OpenRouter Integration

```python
# src/music_agent/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4"  # or any OR model
    
    # Spotify (optional)
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    
    # Paths
    data_dir: str = "./data"
    download_dir: str = "./data/downloads"
    playlist_dir: str = "./data/playlists"
    db_path: str = "./data/library.db"
    
    # Download
    audio_format: str = "mp3"
    audio_quality: str = "320"
    max_concurrent: int = 3
    
    # Safety
    require_rights_verified: bool = True
    allow_youtube: bool = True  # Only for authorized content
    
    class Config:
        env_file = ".env"
```

The agent uses OpenRouter via the standard `openai` Python client:

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=settings.openrouter_base_url,
    api_key=settings.openrouter_api_key,
)

response = await client.chat.completions.create(
    model=settings.openrouter_model,
    messages=[...],
)
```

---

## 5. Agent Orchestrator (Lightweight)

No LangGraph dependency — a simple intent router:

```python
# src/music_agent/agent/orchestrator.py
class Orchestrator:
    """Routes user intent to the right tool pipeline."""
    
    async def handle(self, user_input: str) -> dict:
        # 1. Classify intent via OpenRouter
        intent = await self.planner.classify_intent(user_input)
        
        # 2. Route
        match intent["type"]:
            case "download_list":
                return await self._handle_download_list(intent)
            case "artist_discography":
                return await self._handle_discography(intent)
            case "create_playlist":
                return await self._handle_playlist(intent)
            case "search_library":
                return await self._handle_library_search(intent)
            case "download_url":
                return await self._handle_single_download(intent)
            case _:
                return await self._handle_freeform(user_input)
```

---

## 6. Build Phases

### Phase 1 — Core CLI + Library (Week 1)
- [ ] Project scaffold + pyproject.toml
- [ ] Config (pydantic-settings + .env)
- [ ] SQLite database (SQLModel)
- [ ] Local file scanner
- [ ] M3U playlist creation
- [ ] Basic CLI commands: `scan`, `organize`, `playlist create`

**Milestone:** Can scan, organize, and create local playlists.

### Phase 2 — Metadata Search (Week 1-2)
- [ ] MusicBrainz adapter (artist search, discography)
- [ ] Spotify adapter (search, recommendations)
- [ ] YouTube Music search (ytmusicapi)
- [ ] CLI commands: `search artist`, `search track`, `discography`

**Milestone:** Can search artists, albums, tracks across sources.

### Phase 3 — Download Engine (Week 2)
- [ ] yt-dlp wrapper (async, single + batch)
- [ ] Rights verification engine
- [ ] Metadata tagging (mutagen)
- [ ] File organizer (Artist/Album/Track structure)
- [ ] CLI commands: `download url`, `download search`, `download list`

**Milestone:** Can download authorized music with proper tagging.

### Phase 4 — OpenRouter Agent (Week 3)
- [ ] Intent classification via OpenRouter
- [ ] Orchestrator with tool routing
- [ ] Confirmation gates for large operations
- [ ] CLI command: `agent "<natural language request>"`

**Milestone:** Can say "download the entire discography of X" and it works.

### Phase 5 — MCP Server (Week 3-4)
- [ ] FastMCP server exposing all tools
- [ ] Claude Desktop / Cursor integration
- [ ] Tool schemas for: search, download, playlist, library

**Milestone:** Works as MCP tool in Claude Desktop.

### Phase 6 — Containerization (Week 4)
- [ ] Dockerfile (Python 3.12 slim)
- [ ] docker-compose.yml (agent + optional web UI)
- [ ] Volume mounts for data persistence
- [ ] Health check endpoint

**Milestone:** `docker compose up` runs the full agent.

---

## 7. Docker Setup

```dockerfile
# Dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ ./src/

VOLUME ["/app/data"]

ENTRYPOINT ["music-agent"]
CMD ["--help"]
```

```yaml
# docker-compose.yml
version: "3.9"

services:
  music-agent:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
    stdin_open: true
    tty: true
    
  # Optional: web UI
  # music-web:
  #   build: ./web
  #   ports: ["8080:8080"]
  #   depends_on: [music-agent]
```

---

## 8. CLI Command Design

```bash
# Download
music-agent download url "https://youtube.com/watch?v=..."
music-agent download search "Daft Punk - Get Lucky"
music-agent download list songs.txt

# Artist
music-agent artist "Daft Punk" --discography
music-agent artist "Daft Punk" --download --types album,ep

# Library
music-agent library scan
music-agent library search "daft punk"
music-agent library stats

# Playlist
music-agent playlist create "Chill Vibes" --genre "lo-fi"
music-agent playlist create "Daft Punk Mix" --artist "Daft Punk"
music-agent playlist export "Chill Vibes" --format m3u

# Agent (OpenRouter-powered)
music-agent agent "download the entire discography of Pink Floyd"
music-agent agent "make me a playlist like Daft Punk and Kavinsky"

# MCP Server
music-agent mcp serve
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **No LangGraph** | Overkill for this use case. Simple intent router + tool calls is sufficient. |
| **OpenRouter via `openai` SDK** | Drop-in compatible, no custom client needed. Swap model via config. |
| **SQLModel over raw SQLite** | Type-safe ORM with Pydantic integration, still SQLite underneath. |
| **yt-dlp as Python package** | Better than subprocess — proper error handling, progress hooks. |
| **MusicBrainz primary, Spotify secondary** | MB is free + open. Spotify needs API keys but has better search. |
| **Rights engine as gate** | Every download passes through rights check. Configurable strictness. |
| **Separate from OCE** | Clean boundaries. Can be integrated later via MCP if needed. |

---

## 10. Dependencies (Minimal)

```toml
# pyproject.toml dependencies
dependencies = [
    # Core
    "typer>=0.12",
    "rich>=13.7",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlmodel>=0.0.21",
    
    # LLM
    "openai>=1.40",          # OpenRouter via openai SDK
    
    # Download
    "yt-dlp>=2024.8",
    
    # Metadata
    "musicbrainzngs>=0.7.1",
    "spotipy>=2.24.0",
    "ytmusicapi>=1.7.0",
    "mutagen>=1.47.0",
    
    # MCP (optional)
    "mcp[cli]>=1.0",
]
```

---

## 11. What NOT to Build (Yet)

- ❌ 4K Downloader integration (GUI automation is fragile)
- ❌ Web UI (CLI + MCP first)
- ❌ Discord/Telegram bots (Phase 2 feature)
- ❌ Navidrome/Jellyfin integration (nice-to-have)
- ❌ Audio fingerprinting (overkill for MVP)
- ❌ LangGraph / CrewAI (unnecessary complexity)

---

## 12. Immediate Next Steps

1. **Scaffold the project** — `music-agent/` directory with pyproject.toml
2. **Implement Phase 1** — Config, DB, CLI skeleton, file scanner
3. **Test locally** — Verify download + tagging pipeline works
4. **Add OpenRouter** — Intent classification + agent loop
5. **Containerize** — Dockerfile + docker-compose

---

*This plan prioritizes a working MVP over feature completeness. Each phase delivers a usable increment.*
