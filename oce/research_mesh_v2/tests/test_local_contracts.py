from oce.research_mesh_v2.identity import evidence_identity
from oce.research_mesh_v2.models import ResearchResult, SourceStatus
from oce.research_mesh_v2.service import ResearchMesh


def test_identity_is_deterministic():
    a = evidence_identity("openalex", "W1", "A title")
    b = evidence_identity("openalex", "W1", "A title")
    assert a == b
    assert a.startswith("ev_")


def test_unknown_provider_is_not_configured(tmp_path):
    mesh = ResearchMesh(tmp_path / "e.sqlite3")
    try:
        result = mesh.search("x", source="does-not-exist")
        assert result.status is SourceStatus.NOT_CONFIGURED
        assert result.records == ()
    finally:
        mesh.close()


def test_local_store_empty_query_is_safe(tmp_path):
    mesh = ResearchMesh(tmp_path / "e.sqlite3")
    try:
        assert mesh.query_local("nothing") == []
    finally:
        mesh.close()
