"""Archive current real estate data and reset for new listings.

Creates timestamped archive of:
- Property listings (phx_homes.csv)
- Enrichment data and lineage
- Extracted images and metadata
- Generated reports (deal sheets, visualizations)
- Pipeline state files

Then resets data files to initial state for new listing pool.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


def main():
    """Archive current data and reset for new listings."""
    project_root = Path(__file__).parent.parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create archive directory structure
    archive_dir = project_root / "archive" / f"run_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating archive: {archive_dir.name}")
    print("=" * 60)

    # Archive data files
    data_archive = archive_dir / "data"
    data_archive.mkdir(exist_ok=True)

    data_files = [
        "data/phx_homes.csv",
        "data/enrichment_data.json",
        "data/field_lineage.json",
        "data/work_items.json",
        "data/phx_homes_ranked.csv",
    ]

    print("\n1. Archiving data files...")
    for file_path in data_files:
        src = project_root / file_path
        if src.exists():
            dst = data_archive / src.name
            shutil.copy2(src, dst)
            print(f"   ✓ {src.name}")
        else:
            print(f"   ⚠ {src.name} not found (skipped)")

    # Archive property images and metadata
    images_archive = archive_dir / "images"
    images_src = project_root / "data" / "property_images"

    if images_src.exists():
        print("\n2. Archiving property images and metadata...")
        shutil.copytree(images_src, images_archive, dirs_exist_ok=True)

        # Count images
        processed_dir = images_src / "processed"
        if processed_dir.exists():
            image_count = len(list(processed_dir.rglob("*.png")))
            folder_count = len([d for d in processed_dir.iterdir() if d.is_dir()])
            print(f"   ✓ {folder_count} property folders")
            print(f"   ✓ {image_count} images")

        # Count metadata files
        metadata_dir = images_src / "metadata"
        if metadata_dir.exists():
            metadata_count = len(list(metadata_dir.rglob("*.json")))
            print(f"   ✓ {metadata_count} metadata files")
    else:
        print("\n2. No property images to archive")

    # Archive reports
    reports_archive = archive_dir / "reports"
    reports_archive.mkdir(exist_ok=True)

    print("\n3. Archiving generated reports...")

    # Deal sheets
    deal_sheets_src = project_root / "reports" / "deal_sheets"
    if deal_sheets_src.exists():
        deal_sheets_dst = reports_archive / "deal_sheets"
        shutil.copytree(deal_sheets_src, deal_sheets_dst, dirs_exist_ok=True)
        html_count = len(list(deal_sheets_dst.glob("*.html")))
        print(f"   ✓ {html_count} deal sheets")

    # Visualizations
    viz_src = project_root / "reports" / "html"
    if viz_src.exists():
        viz_dst = reports_archive / "visualizations"
        shutil.copytree(viz_src, viz_dst, dirs_exist_ok=True)
        viz_count = len(list(viz_dst.glob("*.html")))
        print(f"   ✓ {viz_count} visualizations")

    # Create archive manifest
    manifest = {
        "archive_timestamp": timestamp,
        "archive_date": datetime.now().isoformat(),
        "archived_files": {
            "data_files": [f for f in data_files if (project_root / f).exists()],
            "property_image_folders": folder_count if images_src.exists() else 0,
            "total_images": image_count if images_src.exists() else 0,
            "deal_sheets": html_count if deal_sheets_src.exists() else 0,
            "visualizations": viz_count if viz_src.exists() else 0,
        },
        "reason": "Reset for new listing pool",
    }

    manifest_path = archive_dir / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print("\n   ✓ Archive manifest created")

    # Reset data files
    print("\n" + "=" * 60)
    print("RESETTING DATA FILES FOR NEW LISTINGS")
    print("=" * 60)

    # Reset phx_homes.csv (keep header only)
    csv_path = project_root / "data" / "phx_homes.csv"
    if csv_path.exists():
        csv_header = "full_address,list_price,beds,baths,sqft,lot_sqft,year_built,listing_url\n"
        csv_path.write_text(csv_header)
        print("\n1. ✓ phx_homes.csv reset (header only)")

    # Reset enrichment_data.json (empty array)
    enrichment_path = project_root / "data" / "enrichment_data.json"
    enrichment_path.write_text("[]")
    print("2. ✓ enrichment_data.json reset (empty)")

    # Reset field_lineage.json (empty object)
    lineage_path = project_root / "data" / "field_lineage.json"
    lineage_path.write_text("{}")
    print("3. ✓ field_lineage.json reset (empty)")

    # Reset work_items.json (initial structure)
    work_items_initial = {
        "session": {
            "started_at": None,
            "last_updated": None,
            "mode": "idle"
        },
        "properties": {},
        "summary": {
            "total_properties": 0,
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "failed": 0
        }
    }
    work_items_path = project_root / "data" / "work_items.json"
    work_items_path.write_text(json.dumps(work_items_initial, indent=2))
    print("4. ✓ work_items.json reset (initial state)")

    # Reset image metadata (images already archived, deletion optional)
    images_path = project_root / "data" / "property_images"
    if images_path.exists():
        metadata = images_path / "metadata"

        # Reset extraction_state.json
        extraction_state = metadata / "extraction_state.json"
        if extraction_state.exists():
            initial_state = {
                "properties": {},
                "last_updated": None,
                "total_properties": 0,
                "completed": 0,
                "failed": 0
            }
            extraction_state.write_text(json.dumps(initial_state, indent=2))

        # Clear other metadata files but keep structure
        for meta_file in ["hash_index.json", "url_tracker.json", "image_manifest.json"]:
            meta_path = metadata / meta_file
            if meta_path.exists():
                meta_path.write_text("{}")

        print("5. ✓ Image metadata reset")
        print("   Note: Image folders archived but not deleted (Windows permissions)")
        print("   To manually clear: delete data/property_images/processed/*/")

    # Clear reports
    if deal_sheets_src.exists():
        for html_file in deal_sheets_src.glob("*.html"):
            html_file.unlink()
        # Keep data.json for reference
        print("6. ✓ Deal sheets cleared")

    if viz_src.exists():
        for html_file in viz_src.glob("*.html"):
            html_file.unlink()
        print("7. ✓ Visualizations cleared")

    # Final summary
    print("\n" + "=" * 60)
    print("ARCHIVE & RESET COMPLETE")
    print("=" * 60)
    print(f"\nArchive location: archive/{archive_dir.name}/")
    print("\nArchived:")
    print(f"  • {len([f for f in data_files if (project_root / f).exists()])} data files")
    if images_src.exists():
        print(f"  • {folder_count} property folders ({image_count} images)")
    if deal_sheets_src.exists():
        print(f"  • {html_count} deal sheets")
    if viz_src.exists():
        print(f"  • {viz_count} visualizations")

    print("\nReset for new listings:")
    print("  • phx_homes.csv (header only)")
    print("  • enrichment_data.json (empty)")
    print("  • field_lineage.json (empty)")
    print("  • work_items.json (initial state)")
    print("  • Image metadata (reset)")
    print("  • Reports (cleared)")

    print("\n✓ Ready for new listing pool!")
    print(f"\nTo restore this archive, copy files from: archive/{archive_dir.name}/")
    print("\nOptional cleanup:")
    print("  • Manually delete data/property_images/processed/*/ if desired")
    print("    (already archived, but kept due to Windows permissions)")


if __name__ == "__main__":
    main()
