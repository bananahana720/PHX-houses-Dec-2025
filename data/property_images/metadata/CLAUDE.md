---
last_updated: 2025-12-05T22:15:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# metadata

## Purpose
Pipeline state tracking and image indexing for property image extraction. Contains run history, deduplication indexes, and address-to-folder lookups.

## Contents
| File | Purpose |
|------|---------|
| `extraction_state.json` | Current pipeline state: completed/failed properties, last checked |
| `hash_index.json` | LSH-based perceptual hash index for image deduplication |
| `address_folder_lookup.json` | Address -> 8-char hash folder mapping |
| `url_tracker.json` | Tracks extracted URLs per property |
| `pipeline_runs.json` | Summary of all extraction runs |
| `image_manifest.json` | Master manifest of all extracted images |
| `run_history/` | Per-run JSON logs with timestamps and metrics |

## Key Patterns
- **Atomic writes**: All JSON updates use tempfile + os.replace() pattern
- **Address normalization**: Lowercase, whitespace-trimmed before hashing
- **Run isolation**: Each extraction run gets unique `run_{timestamp}_{hash}.json`

## Tasks
- [ ] Add run_history retention policy (keep last 30 days) `P:M`
- [ ] Implement extraction_state backup before modifications `P:H`

## Learnings
- **hash_index.json**: Uses LSH buckets for O(1) near-duplicate detection
- **extraction_state.json**: Only stores failed properties; completed tracked via work_items.json
- **Run history**: Useful for debugging extraction failures and tracking success rates

## Refs
- State management: `src/phx_home_analysis/services/image_extraction/state_manager.py`
- Hash computation: `src/phx_home_analysis/services/image_extraction/validators.py`
- Parent data dir: `../../../CLAUDE.md`

## Deps
<- imports: None (data files only)
-> used by: extract_images.py, image extraction orchestrator, reconciliation scripts
