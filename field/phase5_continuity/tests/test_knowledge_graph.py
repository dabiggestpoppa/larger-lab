"""Test for knowledge_graph."""
from field.phase5_continuity.knowledge_graph import KnowledgeGraphModule


def test_knowledge_graph_init():
    """Module initializes with default config."""
    mod = KnowledgeGraphModule()
    assert mod.config.enabled is True
    assert mod.running is False


def test_knowledge_graph_start_stop():
    """Module start/stop toggles running state."""
    mod = KnowledgeGraphModule()
    mod.start()
    assert mod.running is True
    mod.stop()
    assert mod.running is False
