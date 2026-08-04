"""
Tests for Reality Lock behavioral gate.
"""
import json
import tempfile
from pathlib import Path
import sys

# Add the backend directory to the path so we can import reality_lock
sys.path.insert(0, str(Path(__file__).parent.parent))

from reality_lock import ready_for_phase_1, get_failure_reasons, _validate_artifact, BOOK_2_SCHEMA, BOOK_3_SCHEMA, APPROVAL_SCHEMA


def test_validate_artifact_valid():
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


def test_validate_artifact_missing_file():
    """Test that missing file fails validation."""
    is_valid, error = _validate_artifact(Path("nonexistent.json"), {"type": "object"})
    assert is_valid == False
    assert "not found" in error


def test_validate_artifact_invalid_json():
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


def test_validate_artifact_schema_mismatch():
    """Test that schema mismatch fails validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"wrong_type": 123}, f)
        temp_path = Path(f.name)
    
    try:
        schema = {"type": "object", "properties": {"correct_type": {"type": "string"}}}
        is_valid, error = _validate_artifact(temp_path, schema)
        assert is_valid == False
        assert "Schema validation failed" in error
    finally:
        temp_path.unlink()


def test_ready_for_phase_1_missing_artifacts():
    """Test that missing artifacts return False."""
    # Temporarily move artifacts if they exist
    backup_dir = Path("tmp_backup")
    backup_dir.mkdir(exist_ok=True)
    
    artifacts = [
        ("Book 2", Path("oce/backend/artifacts/book_2_nautilus_evidence.json")),
        ("Book 3", Path("oce/backend/artifacts/book_3_classification.json")),
        ("Approval", Path("oce/backend/artifacts/independent_approval.json")),
    ]
    
    backed_up = []
    try:
        for name, path in artifacts:
            if path.exists():
                backup_path = backup_dir / path.name
                path.rename(backup_path)
                backed_up.append((path, backup_path))
        
        # Should return False when artifacts are missing
        assert ready_for_phase_1() == False
        
        # Check that we get failure reasons
        reasons = get_failure_reasons()
        assert len(reasons) > 0
        assert any("Missing artifact" in r for r in reasons)
        
    finally:
        # Restore artifacts
        for path, backup_path in backed_up:
            if backup_path.exists():
                backup_path.rename(path)
        backup_dir.rmdir()


def test_ready_for_phase_1_with_valid_artifacts():
    """Test that valid artifacts pass the basic checks (excluding SHA and blockers)."""
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create artifacts directory
        artifacts_dir = temp_path / "oce" / "backend" / "artifacts"
        artifacts_dir.mkdir(parents=True)
        
        # Create evidence directory
        evidence_dir = temp_path / "evidence"
        evidence_dir.mkdir()
        
        # Create valid Book 2
        book_2 = {
            "nautilus_runs": [
                {
                    "run_id": "run_001",
                    "timestamp": "2026-07-30T10:00:00Z",
                    "output": "Profitable trades: 5, Win rate: 80%"
                },
                {
                    "run_id": "run_002",
                    "timestamp": "2026-07-30T11:00:00Z",
                    "output": "Profitable trades: 3, Win rate: 60%"
                }
            ],
            "evidence": "Two runs show consistent profitability"
        }
        book_2_path = artifacts_dir / "book_2_nautilus_evidence.json"
        with open(book_2_path, 'w') as f:
            json.dump(book_2, f)
        
        # Create valid Book 3
        book_3 = {
            "classification": "Tier 1 - High Confidence",
            "evidence_based": True,
            "legacy": False
        }
        book_3_path = artifacts_dir / "book_3_classification.json"
        with open(book_3_path, 'w') as f:
            json.dump(book_3, f)
        
        # Create valid approval
        approval = {
            "approved_by": "Independent Auditor",
            "date": "2026-07-30",
            "statement": "After thorough review, the evidence supports proceeding to Phase 1."
        }
        approval_path = artifacts_dir / "independent_approval.json"
        with open(approval_path, 'w') as f:
            json.dump(approval, f)
        
        # Temporarily override the paths in reality_lock module
        import reality_lock
        original_book_2 = reality_lock.BOOK_2_PATH
        original_book_3 = reality_lock.BOOK_3_PATH
        original_approval = reality_lock.APPROVAL_ARTIFACT_PATH
        original_evidence = reality_lock.EVIDENCE_REPO_PATH
        original_repo_root = reality_lock.REPO_ROOT
        
        try:
            reality_lock.BOOK_2_PATH = book_2_path
            reality_lock.BOOK_3_PATH = book_3_path
            reality_lock.APPROVAL_ARTIFACT_PATH = approval_path
            reality_lock.EVIDENCE_REPO_PATH = evidence_dir
            reality_lock.REPO_ROOT = temp_path
            
            # Should still fail because of SHA check and blockers check
            # but we can at least verify the artifact validation passes
            result = ready_for_phase_1()
            # We expect False because SHA and blockers checks will fail in temp dir
            # but we can check that artifact validation passed by checking failure reasons
            reasons = get_failure_reasons()
            # Should not have any artifact-related errors
            artifact_errors = [r for r in reasons if "Invalid artifact" in r or "Missing artifact" in r]
            assert len(artifact_errors) == 0, f"Unexpected artifact errors: {artifact_errors}"
            
        finally:
            # Restore original paths
            reality_lock.BOOK_2_PATH = original_book_2
            reality_lock.BOOK_3_PATH = original_book_3
            reality_lock.APPROVAL_ARTIFACT_PATH = original_approval
            reality_lock.EVIDENCE_REPO_PATH = original_evidence
            reality_lock.REPO_ROOT = original_repo_root


if __name__ == "__main__":
    # Run tests
    test_validate_artifact_valid()
    print("✓ test_validate_artifact_valid passed")
    
    test_validate_artifact_missing_file()
    print("✓ test_validate_artifact_missing_file passed")
    
    test_validate_artifact_invalid_json()
    print("✓ test_validate_artifact_invalid_json passed")
    
    test_validate_artifact_schema_mismatch()
    print("✓ test_validate_artifact_schema_mismatch passed")
    
    test_ready_for_phase_1_missing_artifacts()
    print("✓ test_ready_for_phase_1_missing_artifacts passed")
    
    test_ready_for_phase_1_with_valid_artifacts()
    print("✓ test_ready_for_phase_1_with_valid_artifacts passed")
    
    print("\nAll tests passed!")