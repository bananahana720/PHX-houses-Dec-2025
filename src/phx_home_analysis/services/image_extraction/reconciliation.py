"""Post-extraction reconciliation and data quality verification."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .validators import compute_property_hash

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationReport:
    """Report of data quality reconciliation."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Counts
    manifest_image_count: int = 0
    disk_file_count: int = 0
    url_tracker_count: int = 0

    # Discrepancies
    orphan_files: list[str] = field(default_factory=list)  # Files on disk not in manifest
    ghost_entries: list[str] = field(default_factory=list)  # Manifest entries without files
    hash_mismatches: list[dict[str, str]] = field(default_factory=list)  # Hash doesn't match address

    # Quality scores (0-100)
    accuracy_score: float = 100.0
    completeness_score: float = 100.0
    consistency_score: float = 100.0

    @property
    def overall_quality(self) -> float:
        """Weighted average quality score."""
        return (
            self.accuracy_score * 0.4 +
            self.completeness_score * 0.35 +
            self.consistency_score * 0.25
        )

    @property
    def is_healthy(self) -> bool:
        """Check if data quality is acceptable (>90%)."""
        return self.overall_quality >= 90.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "counts": {
                "manifest_images": self.manifest_image_count,
                "disk_files": self.disk_file_count,
                "url_tracker": self.url_tracker_count,
            },
            "discrepancies": {
                "orphan_files": self.orphan_files,
                "ghost_entries": self.ghost_entries,
                "hash_mismatches": self.hash_mismatches,
            },
            "quality_scores": {
                "accuracy": round(self.accuracy_score, 2),
                "completeness": round(self.completeness_score, 2),
                "consistency": round(self.consistency_score, 2),
                "overall": round(self.overall_quality, 2),
            },
            "is_healthy": self.is_healthy,
        }


class DataReconciler:
    """Cross-reference validation across all data stores."""

    def __init__(
        self,
        manifest_path: Path,
        processed_dir: Path,
        url_tracker_path: Path | None = None,
    ):
        self.manifest_path = manifest_path
        self.processed_dir = processed_dir
        self.url_tracker_path = url_tracker_path

    def reconcile(self) -> ReconciliationReport:
        """
        Full reconciliation across manifest, disk, and URL tracker.

        Checks:
        1. Every manifest entry has corresponding file on disk
        2. Every file on disk is in manifest
        3. Property hashes match addresses
        """
        report = ReconciliationReport()

        # Load manifest
        manifest = self._load_manifest()
        manifest_images = self._index_manifest(manifest)
        report.manifest_image_count = len(manifest_images)

        # Scan disk
        disk_files = self._scan_disk()
        report.disk_file_count = len(disk_files)

        # Load URL tracker if available
        if self.url_tracker_path and self.url_tracker_path.exists():
            url_tracker = self._load_url_tracker()
            report.url_tracker_count = len(url_tracker.get("urls", {}))

        # Find orphans (files without manifest entries)
        manifest_paths = {img.get("local_path", "") for img in manifest_images.values()}
        for disk_path in disk_files:
            if disk_path not in manifest_paths:
                report.orphan_files.append(disk_path)

        # Find ghosts (manifest entries without files)
        for image_id, img in manifest_images.items():
            local_path = img.get("local_path", "")
            full_path = self.processed_dir.parent / local_path
            if not full_path.exists():
                report.ghost_entries.append(image_id)

        # Check hash consistency
        for image_id, img in manifest_images.items():
            address = img.get("property_address", "")
            stored_hash = img.get("property_hash", "")
            if address and stored_hash:
                expected_hash = compute_property_hash(address)
                if stored_hash != expected_hash:
                    report.hash_mismatches.append({
                        "image_id": image_id,
                        "address": address,
                        "stored_hash": stored_hash,
                        "expected_hash": expected_hash,
                    })

        # Calculate quality scores
        total = max(report.manifest_image_count, 1)

        # Accuracy: % without hash mismatches
        report.accuracy_score = (total - len(report.hash_mismatches)) / total * 100

        # Completeness: % of manifest entries with files
        report.completeness_score = (total - len(report.ghost_entries)) / total * 100

        # Consistency: % of files accounted for
        if report.disk_file_count > 0:
            report.consistency_score = (
                (report.disk_file_count - len(report.orphan_files))
                / report.disk_file_count * 100
            )

        return report

    def _load_manifest(self) -> dict[str, Any]:
        """Load manifest JSON."""
        if not self.manifest_path.exists():
            return {"properties": {}}
        with open(self.manifest_path) as f:
            data: dict[str, Any] = json.load(f)
            return data

    def _index_manifest(self, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Index all images by image_id."""
        index: dict[str, dict[str, Any]] = {}
        for address, images in manifest.get("properties", {}).items():
            for img in images:
                image_id = img.get("image_id", "")
                if image_id:
                    img["_manifest_address"] = address
                    index[image_id] = img
        return index

    def _scan_disk(self) -> list[str]:
        """Scan processed directory for image files."""
        paths = []
        if self.processed_dir.exists():
            for img_file in self.processed_dir.rglob("*.png"):
                # Convert to relative path matching manifest format
                rel_path = f"processed/{img_file.parent.name}/{img_file.name}"
                paths.append(rel_path)
        return paths

    def _load_url_tracker(self) -> dict[str, Any]:
        """Load URL tracker JSON."""
        if not self.url_tracker_path or not self.url_tracker_path.exists():
            return {"urls": {}}
        with open(self.url_tracker_path) as f:
            data: dict[str, Any] = json.load(f)
            return data


def run_reconciliation(base_dir: Path) -> ReconciliationReport:
    """
    Run reconciliation and log results.

    Args:
        base_dir: Base directory for property images

    Returns:
        ReconciliationReport with quality scores
    """
    reconciler = DataReconciler(
        manifest_path=base_dir / "metadata" / "image_manifest.json",
        processed_dir=base_dir / "processed",
        url_tracker_path=base_dir / "metadata" / "url_tracker.json",
    )

    report = reconciler.reconcile()

    # Log summary
    logger.info(f"Reconciliation complete: {report.overall_quality:.1f}% quality")
    logger.info(f"  Manifest: {report.manifest_image_count} images")
    logger.info(f"  Disk: {report.disk_file_count} files")

    if report.orphan_files:
        logger.warning(f"  Orphan files: {len(report.orphan_files)}")
    if report.ghost_entries:
        logger.warning(f"  Ghost entries: {len(report.ghost_entries)}")
    if report.hash_mismatches:
        logger.warning(f"  Hash mismatches: {len(report.hash_mismatches)}")

    if not report.is_healthy:
        logger.error(f"Data quality below threshold: {report.overall_quality:.1f}% < 90%")

    return report
