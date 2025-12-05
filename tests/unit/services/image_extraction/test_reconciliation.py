"""Tests for data reconciliation."""
import json

from phx_home_analysis.services.image_extraction.reconciliation import (
    DataReconciler,
    ReconciliationReport,
    run_reconciliation,
)
from phx_home_analysis.services.image_extraction.validators import compute_property_hash


def test_reconciliation_report_properties():
    """Test ReconciliationReport computed properties."""
    report = ReconciliationReport(
        manifest_image_count=100,
        disk_file_count=100,
        url_tracker_count=50,
    )

    # Perfect scores by default
    assert report.accuracy_score == 100.0
    assert report.completeness_score == 100.0
    assert report.consistency_score == 100.0
    assert report.overall_quality == 100.0
    assert report.is_healthy


def test_reconciliation_report_with_discrepancies():
    """Test quality scores with discrepancies."""
    report = ReconciliationReport(
        manifest_image_count=100,
        disk_file_count=105,  # 5 extra files
        url_tracker_count=50,
    )

    # Add discrepancies
    report.orphan_files = ["file1.png", "file2.png"]  # 2 orphan files
    report.ghost_entries = ["ghost1", "ghost2", "ghost3"]  # 3 ghosts
    report.hash_mismatches = [{"image_id": "img1", "address": "addr", "stored_hash": "abc", "expected_hash": "def"}]

    # Recalculate quality scores
    total = max(report.manifest_image_count, 1)

    # Accuracy: 99% (1 hash mismatch out of 100)
    report.accuracy_score = (total - len(report.hash_mismatches)) / total * 100

    # Completeness: 97% (3 ghosts out of 100)
    report.completeness_score = (total - len(report.ghost_entries)) / total * 100

    # Consistency: 98.1% (2 orphans out of 105)
    report.consistency_score = (
        (report.disk_file_count - len(report.orphan_files))
        / report.disk_file_count * 100
    )

    assert report.accuracy_score == 99.0
    assert report.completeness_score == 97.0
    assert report.consistency_score == pytest.approx(98.095, rel=1e-2)

    # Overall: weighted average
    expected_overall = 99.0 * 0.4 + 97.0 * 0.35 + 98.095 * 0.25
    assert report.overall_quality == pytest.approx(expected_overall, rel=1e-2)

    # Still healthy (>90%)
    assert report.is_healthy


def test_reconciliation_report_unhealthy():
    """Test is_healthy flag with low quality."""
    report = ReconciliationReport(
        manifest_image_count=100,
        disk_file_count=100,
    )

    # Add many discrepancies
    report.orphan_files = [f"file{i}.png" for i in range(50)]  # 50 orphans
    report.ghost_entries = [f"ghost{i}" for i in range(30)]  # 30 ghosts
    report.hash_mismatches = [{"image_id": f"img{i}", "address": f"addr{i}", "stored_hash": f"hash{i}", "expected_hash": f"exp{i}"} for i in range(20)]  # 20 mismatches

    # Recalculate
    report.accuracy_score = 80.0
    report.completeness_score = 70.0
    report.consistency_score = 50.0

    # Overall: 68.5%
    expected_overall = 80.0 * 0.4 + 70.0 * 0.35 + 50.0 * 0.25
    assert report.overall_quality == pytest.approx(68.5, rel=1e-2)

    # Not healthy (<90%)
    assert not report.is_healthy


def test_reconciliation_report_to_dict():
    """Test conversion to dictionary."""
    report = ReconciliationReport(
        manifest_image_count=10,
        disk_file_count=10,
        url_tracker_count=5,
    )

    report.orphan_files = ["orphan.png"]
    report.ghost_entries = ["ghost1"]

    data = report.to_dict()

    assert data["counts"]["manifest_images"] == 10
    assert data["counts"]["disk_files"] == 10
    assert data["counts"]["url_tracker"] == 5
    assert data["discrepancies"]["orphan_files"] == ["orphan.png"]
    assert data["discrepancies"]["ghost_entries"] == ["ghost1"]
    assert "quality_scores" in data
    assert "is_healthy" in data


def test_data_reconciler_empty(tmp_path):
    """Test reconciler with no data."""
    manifest_path = tmp_path / "image_manifest.json"
    processed_dir = tmp_path / "processed"

    # No files exist
    reconciler = DataReconciler(
        manifest_path=manifest_path,
        processed_dir=processed_dir,
    )

    report = reconciler.reconcile()

    assert report.manifest_image_count == 0
    assert report.disk_file_count == 0
    assert len(report.orphan_files) == 0
    assert len(report.ghost_entries) == 0
    assert report.is_healthy


def test_data_reconciler_with_orphans(tmp_path):
    """Test reconciler detects orphan files."""
    manifest_path = tmp_path / "image_manifest.json"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)

    # Create manifest with one image
    address = "1234 Main St, Phoenix, AZ 85001"
    property_hash = compute_property_hash(address)
    property_dir = processed_dir / property_hash
    property_dir.mkdir()

    manifest_data = {
        "properties": {
            address: [
                {
                    "image_id": "img1",
                    "property_address": address,
                    "property_hash": property_hash,
                    "local_path": f"processed/{property_hash}/img1.png",
                }
            ]
        }
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)

    # Create the expected file
    (property_dir / "img1.png").write_bytes(b"fake image 1")

    # Create an orphan file not in manifest
    (property_dir / "orphan.png").write_bytes(b"orphan image")

    reconciler = DataReconciler(
        manifest_path=manifest_path,
        processed_dir=processed_dir,
    )

    report = reconciler.reconcile()

    assert report.manifest_image_count == 1
    assert report.disk_file_count == 2
    assert len(report.orphan_files) == 1
    assert f"processed/{property_hash}/orphan.png" in report.orphan_files
    assert len(report.ghost_entries) == 0


def test_data_reconciler_with_ghosts(tmp_path):
    """Test reconciler detects ghost entries."""
    manifest_path = tmp_path / "image_manifest.json"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)

    # Create manifest with image that doesn't exist
    address = "1234 Main St, Phoenix, AZ 85001"
    property_hash = compute_property_hash(address)

    manifest_data = {
        "properties": {
            address: [
                {
                    "image_id": "ghost_img",
                    "property_address": address,
                    "property_hash": property_hash,
                    "local_path": f"processed/{property_hash}/ghost.png",
                }
            ]
        }
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)

    # Don't create the file

    reconciler = DataReconciler(
        manifest_path=manifest_path,
        processed_dir=processed_dir,
    )

    report = reconciler.reconcile()

    assert report.manifest_image_count == 1
    assert report.disk_file_count == 0
    assert len(report.orphan_files) == 0
    assert len(report.ghost_entries) == 1
    assert "ghost_img" in report.ghost_entries


def test_data_reconciler_with_hash_mismatch(tmp_path):
    """Test reconciler detects hash mismatches."""
    manifest_path = tmp_path / "image_manifest.json"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)

    # Create manifest with wrong hash
    address = "1234 Main St, Phoenix, AZ 85001"
    correct_hash = compute_property_hash(address)
    wrong_hash = "wronghash"

    property_dir = processed_dir / correct_hash
    property_dir.mkdir()

    manifest_data = {
        "properties": {
            address: [
                {
                    "image_id": "img1",
                    "property_address": address,
                    "property_hash": wrong_hash,  # Wrong hash
                    "local_path": f"processed/{correct_hash}/img1.png",
                }
            ]
        }
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)

    # Create the file
    (property_dir / "img1.png").write_bytes(b"fake image")

    reconciler = DataReconciler(
        manifest_path=manifest_path,
        processed_dir=processed_dir,
    )

    report = reconciler.reconcile()

    assert report.manifest_image_count == 1
    assert len(report.hash_mismatches) == 1
    assert report.hash_mismatches[0]["stored_hash"] == wrong_hash
    assert report.hash_mismatches[0]["expected_hash"] == correct_hash


def test_run_reconciliation_integration(tmp_path):
    """Test run_reconciliation function."""
    base_dir = tmp_path / "property_images"
    metadata_dir = base_dir / "metadata"
    processed_dir = base_dir / "processed"

    metadata_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    # Create empty manifest
    manifest_path = metadata_dir / "image_manifest.json"
    manifest_path.write_text('{"properties": {}}')

    report = run_reconciliation(base_dir)

    assert isinstance(report, ReconciliationReport)
    assert report.is_healthy


# Import pytest at the top for annotations
import pytest
