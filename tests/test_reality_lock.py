"""
Tests for the Reality Lock module.

These tests verify the Phase 1 readiness gate functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from capital_routing.backend.reality_lock import (
    _validate_artifact,
    ready_for_phase_1,
    get_failure_reasons,
    BOOK_2_SCHEMA,
    BOOK_3_SCHEMA,
    APPROVAL_SCHEMA,
)


class TestValidateArtifact:
    """Test the _validate_artifact function."""

    def test_validate_artifact_valid(self):
        """Test that valid JSON passes validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "value"}, f)
            temp_path = Path(f.name)
        
        try:
            # Simple schema for testing
            schema = {"type": "object", "properties": {"test": {"type": "string"}}}
            is_valid, error = _validate_artifact(temp_path, schema)
            assert is_valid == True
            assert error is None
        finally:
            temp_path.unlink()

    def test_validate_artifact_missing_file(self):
        """Test that missing file fails validation."""
        is_valid, error = _validate_artifact(Path("nonexistent.json"), {"type": "object"})
        assert is_valid == False
        assert "not found" in error

    def test_validate_artifact_invalid_json(self):
        """Test that invalid JSON fails validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)
        
        try:
            is_valid, error = _validate_artifact(temp_path, {"type": "object"})
            assert is_valid == False
            assert "Invalid JSON" in error
        finally:
            temp_path.unlink()

    def test_validate_artifact_schema_mismatch(self):
        """Test that schema mismatch fails validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"wrong_type": 123}, f)
            temp_path = Path(f.name)
        
        try:
            schema = {"type": "object", "required": ["correct_type"], "properties": {"correct_type": {"type": "string"}}}
            is_valid, error = _validate_artifact(temp_path, schema)
            assert is_valid == False
            assert "Schema validation failed" in error
        finally:
            temp_path.unlink()


class TestReadyForPhase1:
    """Test the ready_for_phase_1 function."""

    def test_ready_for_phase_1_with_valid_artifacts(self):
        """Test that valid artifacts pass the basic checks (excluding SHA and blockers)."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create artifacts directory
            artifacts_dir = temp_path / "artifacts"
            artifacts_dir.mkdir()
            
            # Create evidence directory
            evidence_dir = temp_path / "evidence"
            evidence_dir.mkdir()
            
            # Create valid Book 2 artifact
            book_2_path = artifacts_dir / "book_2_nautilus_evidence.json"
            book_2_data = {
                "nautilus_runs": [
                    {"run_id": "run1", "timestamp": "2026-01-01T00:00:00Z", "output": "test output 1"},
                    {"run_id": "run2", "timestamp": "2026-01-02T00:00:00Z", "output": "test output 2"},
                ],
                "evidence": "Test evidence"
            }
            with open(book_2_path, 'w', encoding='utf-8') as f:
                json.dump(book_2_data, f)
            
            # Create valid Book 3 artifact
            book_3_path = artifacts_dir / "book_3_classification.json"
            book_3_data = {
                "classification": "Test classification",
                "evidence_based": True,
                "legacy": False
            }
            with open(book_3_path, 'w', encoding='utf-8') as f:
                json.dump(book_3_data, f)
            
            # Create valid approval artifact
            approval_path = artifacts_dir / "independent_approval.json"
            approval_data = {
                "approved_by": "Test Approver",
                "date": "2026-01-01",
                "statement": "Test approval statement"
            }
            with open(approval_path, 'w', encoding='utf-8') as f:
                json.dump(approval_data, f)
            
            # Temporarily replace the global paths
            import capital_routing.backend.reality_lock as reality_lock_module
            original_artifacts_dir = reality_lock_module.ARTIFACTS_DIR
            original_book_2_path = reality_lock_module.BOOK_2_PATH
            original_book_3_path = reality_lock_module.BOOK_3_PATH
            original_approval_path = reality_lock_module.APPROVAL_ARTIFACT_PATH
            original_evidence_repo = reality_lock_module.EVIDENCE_REPO_PATH
            original_repo_root = reality_lock_module.REPO_ROOT
            
            try:
                reality_lock_module.ARTIFACTS_DIR = artifacts_dir
                reality_lock_module.BOOK_2_PATH = book_2_path
                reality_lock_module.BOOK_3_PATH = book_3_path
                reality_lock_module.APPROVAL_ARTIFACT_PATH = approval_path
                reality_lock_module.EVIDENCE_REPO_PATH = evidence_dir
                reality_lock_module.REPO_ROOT = temp_path
                
                # Test the function
                result = ready_for_phase_1()
                assert result == True
            finally:
                # Restore original paths
                reality_lock_module.ARTIFACTS_DIR = original_artifacts_dir
                reality_lock_module.BOOK_2_PATH = original_book_2_path
                reality_lock_module.BOOK_3_PATH = original_book_3_path
                reality_lock_module.APPROVAL_ARTIFACT_PATH = original_approval_path
                reality_lock_module.EVIDENCE_REPO_PATH = original_evidence_repo
                reality_lock_module.REPO_ROOT = original_repo_root

    def test_ready_for_phase_1_missing_artifact(self):
        """Test that missing artifacts cause failure."""
        # Temporarily replace the global paths
        import capital_routing.backend.reality_lock as reality_lock_module
        original_artifacts_dir = reality_lock_module.ARTIFACTS_DIR
        original_book_2_path = reality_lock_module.BOOK_2_PATH
        original_book_3_path = reality_lock_module.BOOK_3_PATH
        original_approval_path = reality_lock_module.APPROVAL_ARTIFACT_PATH
        original_evidence_repo = reality_lock_module.EVIDENCE_REPO_PATH
        original_repo_root = reality_lock_module.REPO_ROOT
        
        try:
            # Create artifacts directory but don't create artifacts
            with tempfile.TemporaryDirectory() as temp_dir:
                artifacts_dir = Path(temp_dir) / "artifacts"
                artifacts_dir.mkdir()
                evidence_dir = Path(temp_dir) / "evidence"
                evidence_dir.mkdir()
                
                reality_lock_module.ARTIFACTS_DIR = artifacts_dir
                reality_lock_module.BOOK_2_PATH = artifacts_dir / "book_2_nautilus_evidence.json"
                reality_lock_module.BOOK_3_PATH = artifacts_dir / "book_3_classification.json"
                reality_lock_module.APPROVAL_ARTIFACT_PATH = artifacts_dir / "independent_approval.json"
                reality_lock_module.EVIDENCE_REPO_PATH = evidence_dir
                reality_lock_module.REPO_ROOT = Path(temp_dir)
                
                # Test the function
                result = ready_for_phase_1()
                assert result == False
                
                # Check failure reasons
                reasons = get_failure_reasons()
                assert len(reasons) > 0
                assert any("Missing artifact" in r for r in reasons)
        finally:
            # Restore original paths
            reality_lock_module.ARTIFACTS_DIR = original_artifacts_dir
            reality_lock_module.BOOK_2_PATH = original_book_2_path
            reality_lock_module.BOOK_3_PATH = original_book_3_path
            reality_lock_module.APPROVAL_ARTIFACT_PATH = original_approval_path
            reality_lock_module.EVIDENCE_REPO_PATH = original_evidence_repo
            reality_lock_module.REPO_ROOT = original_repo_root

    def test_ready_for_phase_1_invalid_artifact(self):
        """Test that invalid artifacts cause failure."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create artifacts directory
            artifacts_dir = temp_path / "artifacts"
            artifacts_dir.mkdir()
            evidence_dir = temp_path / "evidence"
            evidence_dir.mkdir()
            
            # Create invalid Book 2 artifact (wrong schema)
            book_2_path = artifacts_dir / "book_2_nautilus_evidence.json"
            book_2_data = {
                "wrong_field": "wrong value"  # Missing required fields
            }
            with open(book_2_path, 'w', encoding='utf-8') as f:
                json.dump(book_2_data, f)
            
            # Create valid Book 3 artifact
            book_3_path = artifacts_dir / "book_3_classification.json"
            book_3_data = {
                "classification": "Test classification",
                "evidence_based": True,
                "legacy": False
            }
            with open(book_3_path, 'w', encoding='utf-8') as f:
                json.dump(book_3_data, f)
            
            # Create valid approval artifact
            approval_path = artifacts_dir / "independent_approval.json"
            approval_data = {
                "approved_by": "Test Approver",
                "date": "2026-01-01",
                "statement": "Test approval statement"
            }
            with open(approval_path, 'w', encoding='utf-8') as f:
                json.dump(approval_data, f)
            
            # Temporarily replace the global paths
            import capital_routing.backend.reality_lock as reality_lock_module
            original_artifacts_dir = reality_lock_module.ARTIFACTS_DIR
            original_book_2_path = reality_lock_module.BOOK_2_PATH
            original_book_3_path = reality_lock_module.BOOK_3_PATH
            original_approval_path = reality_lock_module.APPROVAL_ARTIFACT_PATH
            original_evidence_repo = reality_lock_module.EVIDENCE_REPO_PATH
            original_repo_root = reality_lock_module.REPO_ROOT
            
            try:
                reality_lock_module.ARTIFACTS_DIR = artifacts_dir
                reality_lock_module.BOOK_2_PATH = book_2_path
                reality_lock_module.BOOK_3_PATH = book_3_path
                reality_lock_module.APPROVAL_ARTIFACT_PATH = approval_path
                reality_lock_module.EVIDENCE_REPO_PATH = evidence_dir
                reality_lock_module.REPO_ROOT = temp_path
                
                # Test the function
                result = ready_for_phase_1()
                assert result == False
                
                # Check failure reasons
                reasons = get_failure_reasons()
                assert len(reasons) > 0
                assert any("Invalid artifact" in r for r in reasons)
            finally:
                # Restore original paths
                reality_lock_module.ARTIFACTS_DIR = original_artifacts_dir
                reality_lock_module.BOOK_2_PATH = original_book_2_path
                reality_lock_module.BOOK_3_PATH = original_book_3_path
                reality_lock_module.APPROVAL_ARTIFACT_PATH = original_approval_path
                reality_lock_module.EVIDENCE_REPO_PATH = original_evidence_repo
                reality_lock_module.REPO_ROOT = original_repo_root


class TestGetFailureReasons:
    """Test the get_failure_reasons function."""

    def test_get_failure_reasons_with_valid_artifacts(self):
        """Test that valid artifacts return no failure reasons."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create artifacts directory
            artifacts_dir = temp_path / "artifacts"
            artifacts_dir.mkdir()
            evidence_dir = temp_path / "evidence"
            evidence_dir.mkdir()
            
            # Create valid Book 2 artifact
            book_2_path = artifacts_dir / "book_2_nautilus_evidence.json"
            book_2_data = {
                "nautilus_runs": [
                    {"run_id": "run1", "timestamp": "2026-01-01T00:00:00Z", "output": "test output 1"},
                    {"run_id": "run2", "timestamp": "2026-01-02T00:00:00Z", "output": "test output 2"},
                ],
                "evidence": "Test evidence"
            }
            with open(book_2_path, 'w', encoding='utf-8') as f:
                json.dump(book_2_data, f)
            
            # Create valid Book 3 artifact
            book_3_path = artifacts_dir / "book_3_classification.json"
            book_3_data = {
                "classification": "Test classification",
                "evidence_based": True,
                "legacy": False
            }
            with open(book_3_path, 'w', encoding='utf-8') as f:
                json.dump(book_3_data, f)
            
            # Create valid approval artifact
            approval_path = artifacts_dir / "independent_approval.json"
            approval_data = {
                "approved_by": "Test Approver",
                "date": "2026-01-01",
                "statement": "Test approval statement"
            }
            with open(approval_path, 'w', encoding='utf-8') as f:
                json.dump(approval_data, f)
            
            # Temporarily replace the global paths
            import capital_routing.backend.reality_lock as reality_lock_module
            original_artifacts_dir = reality_lock_module.ARTIFACTS_DIR
            original_book_2_path = reality_lock_module.BOOK_2_PATH
            original_book_3_path = reality_lock_module.BOOK_3_PATH
            original_approval_path = reality_lock_module.APPROVAL_ARTIFACT_PATH
            original_evidence_repo = reality_lock_module.EVIDENCE_REPO_PATH
            original_repo_root = reality_lock_module.REPO_ROOT
            
            try:
                reality_lock_module.ARTIFACTS_DIR = artifacts_dir
                reality_lock_module.BOOK_2_PATH = book_2_path
                reality_lock_module.BOOK_3_PATH = book_3_path
                reality_lock_module.APPROVAL_ARTIFACT_PATH = approval_path
                reality_lock_module.EVIDENCE_REPO_PATH = evidence_dir
                reality_lock_module.REPO_ROOT = temp_path
                
                # Test the function
                reasons = get_failure_reasons()
                assert len(reasons) == 0
            finally:
                # Restore original paths
                reality_lock_module.ARTIFACTS_DIR = original_artifacts_dir
                reality_lock_module.BOOK_2_PATH = original_book_2_path
                reality_lock_module.BOOK_3_PATH = original_book_3_path
                reality_lock_module.APPROVAL_ARTIFACT_PATH = original_approval_path
                reality_lock_module.EVIDENCE_REPO_PATH = original_evidence_repo
                reality_lock_module.REPO_ROOT = original_repo_root

    def test_get_failure_reasons_missing_artifact(self):
        """Test that missing artifacts return appropriate failure reasons."""
        # Temporarily replace the global paths
        import capital_routing.backend.reality_lock as reality_lock_module
        original_artifacts_dir = reality_lock_module.ARTIFACTS_DIR
        original_book_2_path = reality_lock_module.BOOK_2_PATH
        original_book_3_path = reality_lock_module.BOOK_3_PATH
        original_approval_path = reality_lock_module.APPROVAL_ARTIFACT_PATH
        original_evidence_repo = reality_lock_module.EVIDENCE_REPO_PATH
        original_repo_root = reality_lock_module.REPO_ROOT
        
        try:
            # Create artifacts directory but don't create artifacts
            with tempfile.TemporaryDirectory() as temp_dir:
                artifacts_dir = Path(temp_dir) / "artifacts"
                artifacts_dir.mkdir()
                evidence_dir = Path(temp_dir) / "evidence"
                evidence_dir.mkdir()
                
                reality_lock_module.ARTIFACTS_DIR = artifacts_dir
                reality_lock_module.BOOK_2_PATH = artifacts_dir / "book_2_nautilus_evidence.json"
                reality_lock_module.BOOK_3_PATH = artifacts_dir / "book_3_classification.json"
                reality_lock_module.APPROVAL_ARTIFACT_PATH = artifacts_dir / "independent_approval.json"
                reality_lock_module.EVIDENCE_REPO_PATH = evidence_dir
                reality_lock_module.REPO_ROOT = Path(temp_dir)
                
                # Test the function
                reasons = get_failure_reasons()
                assert len(reasons) > 0
                assert any("Missing artifact" in r for r in reasons)
        finally:
            # Restore original paths
            reality_lock_module.ARTIFACTS_DIR = original_artifacts_dir
            reality_lock_module.BOOK_2_PATH = original_book_2_path
            reality_lock_module.BOOK_3_PATH = original_book_3_path
            reality_lock_module.APPROVAL_ARTIFACT_PATH = original_approval_path
            reality_lock_module.EVIDENCE_REPO_PATH = original_evidence_repo
            reality_lock_module.REPO_ROOT = original_repo_root


if __name__ == "__main__":
    pytest.main([__file__, "-v"])