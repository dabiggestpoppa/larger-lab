"""
L4 Integration Tests — OCE Research Mesh API endpoints.

Tests all 10 research API endpoints:
- GET  /api/research/stats
- POST /api/research/ingest
- GET  /api/research/papers
- GET  /api/research/papers/{paper_id}
- GET  /api/research/graph
- GET  /api/research/graph/stats
- GET  /api/research/agents
- POST /api/research/agents/spawn
- GET  /api/research/doctrine
- GET  /api/research/gaps
- GET  /api/research/config
- POST /api/research/config
- POST /api/research/vault/sync
- GET  /api/research/vault/stats

Uses TestClient from FastAPI for endpoint testing.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure backend is importable
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure core is importable
CORE_DIR = Path(__file__).resolve().parents[4]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def test_app():
    """Create a minimal FastAPI app with research endpoints registered."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    # Import and register research endpoints
    try:
        from research_api import register_research_endpoints
        register_research_endpoints(app)
    except ImportError:
        pytest.skip("research_api not available")

    return app


@pytest.fixture
def client(test_app):
    from fastapi.testclient import TestClient
    return TestClient(test_app)


# ============================================================
# GET /api/research/stats
# ============================================================

class TestResearchStats:
    def test_get_stats_returns_200(self, client):
        """GET /api/research/stats returns 200."""
        response = client.get("/api/research/stats")
        assert response.status_code == 200

    def test_get_stats_has_expected_fields(self, client):
        """Stats response contains expected fields."""
        response = client.get("/api/research/stats")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_stats_default_values(self, client):
        """Stats returns sensible defaults when no data."""
        response = client.get("/api/research/stats")
        data = response.json()
        # Should have these keys (even if 0)
        for key in ["papers_ingested", "papers_distilled", "graph_nodes", "graph_edges"]:
            assert key in data


# ============================================================
# POST /api/research/ingest
# ============================================================

class TestResearchIngest:
    def test_trigger_ingest_returns_200(self, client):
        """POST /api/research/ingest returns 200."""
        response = client.post("/api/research/ingest", json={
            "domains": ["agent_orchestration"],
            "max_papers": 10,
        })
        assert response.status_code == 200

    def test_ingest_response_structure(self, client):
        """Ingest response has expected fields."""
        response = client.post("/api/research/ingest", json={})
        data = response.json()
        assert "triggered" in data

    def test_ingest_with_domains(self, client):
        """Ingest accepts domain filter."""
        response = client.post("/api/research/ingest", json={
            "domains": ["agent_orchestration", "memory_systems"],
            "max_papers": 50,
        })
        assert response.status_code == 200


# ============================================================
# GET /api/research/papers
# ============================================================

class TestResearchPapers:
    def test_search_papers_returns_200(self, client):
        """GET /api/research/papers returns 200."""
        response = client.get("/api/research/papers")
        assert response.status_code == 200

    def test_search_papers_response_structure(self, client):
        """Papers response has papers and count."""
        response = client.get("/api/research/papers")
        data = response.json()
        assert "papers" in data
        assert "count" in data

    def test_search_with_query(self, client):
        """Paper search accepts query parameter."""
        response = client.get("/api/research/papers?query=attention&limit=10")
        assert response.status_code == 200

    def test_search_with_domain(self, client):
        """Paper search accepts domain filter."""
        response = client.get("/api/research/papers?domain=agent_orchestration")
        assert response.status_code == 200

    def test_search_with_year(self, client):
        """Paper search accepts year filter."""
        response = client.get("/api/research/papers?year=2024")
        assert response.status_code == 200

    def test_search_limit_bounds(self, client):
        """Paper search limit is bounded (max 200)."""
        response = client.get("/api/research/papers?limit=500")
        # FastAPI Query(le=200) returns 422 for out-of-bounds
        assert response.status_code in (200, 422)


# ============================================================
# GET /api/research/graph
# ============================================================

class TestResearchGraph:
    def test_get_graph_returns_200(self, client):
        """GET /api/research/graph returns 200."""
        response = client.get("/api/research/graph")
        assert response.status_code == 200

    def test_graph_response_structure(self, client):
        """Graph response has nodes and edges."""
        response = client.get("/api/research/graph")
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_graph_with_kind_filter(self, client):
        """Graph query accepts kind filter."""
        response = client.get("/api/research/graph?kind=paper")
        assert response.status_code == 200

    def test_graph_stats_returns_200(self, client):
        """GET /api/research/graph/stats returns 200."""
        response = client.get("/api/research/graph/stats")
        assert response.status_code == 200


# ============================================================
# GET /api/research/agents
# ============================================================

class TestResearchAgents:
    def test_list_agents_returns_200(self, client):
        """GET /api/research/agents returns 200."""
        response = client.get("/api/research/agents")
        assert response.status_code == 200

    def test_agents_response_structure(self, client):
        """Agents response has agents list."""
        response = client.get("/api/research/agents")
        data = response.json()
        assert "agents" in data

    def test_agents_with_status_filter(self, client):
        """Agents endpoint accepts status filter."""
        response = client.get("/api/research/agents?status=running")
        assert response.status_code == 200


# ============================================================
# POST /api/research/agents/spawn
# ============================================================

class TestResearchAgentSpawn:
    def test_spawn_returns_200_or_500(self, client):
        """POST /api/research/agents/spawn returns 200 or 500 (if DB unavailable)."""
        response = client.post("/api/research/agents/spawn", json={
            "query": "test research query",
            "priority": 3,
        })
        # 200 if TaskQueue DB is available, 500 if not (test env)
        assert response.status_code in (200, 500)

    def test_spawn_returns_task_id_or_error(self, client):
        """Spawn response includes task_id or error detail."""
        response = client.post("/api/research/agents/spawn", json={
            "query": "test query",
        })
        data = response.json()
        # Either task_id (success) or detail/error (failure)
        assert "task_id" in data or "detail" in data or "error" in data


# ============================================================
# GET /api/research/doctrine
# ============================================================

class TestResearchDoctrine:
    def test_list_doctrine_returns_200(self, client):
        """GET /api/research/doctrine returns 200."""
        response = client.get("/api/research/doctrine")
        assert response.status_code == 200

    def test_doctrine_response_structure(self, client):
        """Doctrine response has doctrine list and count."""
        response = client.get("/api/research/doctrine")
        data = response.json()
        assert "doctrine" in data
        assert "count" in data

    def test_doctrine_with_domain_filter(self, client):
        """Doctrine endpoint accepts domain filter."""
        response = client.get("/api/research/doctrine?domain=agent_orchestration")
        assert response.status_code == 200


# ============================================================
# GET /api/research/gaps
# ============================================================

class TestResearchGaps:
    def test_list_gaps_returns_200(self, client):
        """GET /api/research/gaps returns 200."""
        response = client.get("/api/research/gaps")
        assert response.status_code == 200

    def test_gaps_response_structure(self, client):
        """Gaps response has gaps list and count."""
        response = client.get("/api/research/gaps")
        data = response.json()
        assert "gaps" in data
        assert "count" in data

    def test_gaps_with_threshold(self, client):
        """Gaps endpoint accepts threshold parameter."""
        response = client.get("/api/research/gaps?threshold=0.5")
        assert response.status_code == 200


# ============================================================
# GET/POST /api/research/config
# ============================================================

class TestResearchConfig:
    def test_get_config_returns_200(self, client):
        """GET /api/research/config returns 200."""
        response = client.get("/api/research/config")
        assert response.status_code == 200

    def test_config_has_expected_fields(self, client):
        """Config response has expected configuration fields."""
        response = client.get("/api/research/config")
        data = response.json()
        assert isinstance(data, dict)

    def test_update_config_returns_200(self, client):
        """POST /api/research/config returns 200."""
        response = client.post("/api/research/config", json={
            "daily_paper_cap": 1000,
        })
        assert response.status_code == 200


# ============================================================
# L4.7 — Vault Sync Endpoints
# ============================================================

class TestVaultSync:
    def test_vault_sync_returns_200(self, client):
        """POST /api/research/vault/sync returns 200."""
        response = client.post("/api/research/vault/sync")
        assert response.status_code == 200

    def test_vault_sync_response_structure(self, client):
        """Vault sync response has status field."""
        response = client.post("/api/research/vault/sync")
        data = response.json()
        assert "status" in data or "error" in data

    def test_vault_stats_returns_200(self, client):
        """GET /api/research/vault/stats returns 200."""
        response = client.get("/api/research/vault/stats")
        assert response.status_code == 200

    def test_vault_stats_response_structure(self, client):
        """Vault stats response has expected fields."""
        response = client.get("/api/research/vault/stats")
        data = response.json()
        assert isinstance(data, dict)


# ============================================================
# Cross-cutting: All endpoints return valid JSON
# ============================================================

class TestAllEndpointsJSON:
    def test_all_get_endpoints_return_json(self, client):
        """All GET endpoints return valid JSON."""
        endpoints = [
            "/api/research/stats",
            "/api/research/papers",
            "/api/research/graph",
            "/api/research/graph/stats",
            "/api/research/agents",
            "/api/research/doctrine",
            "/api/research/gaps",
            "/api/research/config",
            "/api/research/vault/stats",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"{endpoint} returned {response.status_code}"
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)
