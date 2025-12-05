# Image Data Loss Investigation Report

**Date:** 2025-12-04
**Property:** 4560 E Sunrise Dr, Phoenix, AZ 85044
**Folder:** f4e29e2c
**Severity:** HIGH (97% data loss)

## Executive Summary

94 image files were accidentally deleted in git commit `d7f9976` ("Add comprehensive tests for Property and scoring services") on December 3, 2025. The commit was intended to add test files but inadvertently included a mass deletion of property images.

## Timeline

| Date | Event |
|------|-------|
| 2025-12-02 | Original images downloaded (103 images per manifest) |
| 2025-12-03 01:06 | Images moved to archive in commit `0a05a3b` |
| 2025-12-03 10:51 | **94 files deleted** in commit `d7f9976` |
| 2025-12-04 15:32 | New extraction run downloaded only 3 new images (41 marked as duplicates in manifest) |
| 2025-12-04 15:58 | **Recovery completed** - 117 files restored |

## Root Cause Analysis

### What Happened

1. Commit `d7f9976` was titled "Add comprehensive tests for Property and scoring services"
2. The commit included many additions (BMAD files, test files)
3. It also included **94 deletions** from `data/property_images/processed/f4e29e2c/`
4. This was likely due to:
   - IDE auto-staging all changes
   - Large commit not carefully reviewed
   - Binary files (images) not inspected during commit

### Why It Wasn't Caught

1. Commit message didn't mention image deletions
2. Large commits (100+ files) are harder to review
3. No pre-commit hook to protect `data/property_images/` from mass deletions
4. No automated backup of extracted images

### The Cleanup Script is NOT the Culprit

The `--clean-images` flag in `extract_images.py` was initially suspected, but investigation confirmed:
- The cleanup function (`cleanup_old_images()`) operates on manifest timestamps
- It only deletes files older than 14 days
- It requires explicit `--clean-images` flag
- It has `--dry-run` protection
- The actual cause was git commit, not cleanup script

## Recovery Actions Taken

### 1. Files Recovered

| Source | Files Recovered |
|--------|-----------------|
| Git history (commit 83eec13) | 43 files |
| Archive run_20251202_205502 | 71 files |
| Archive run_20251202_221951 | additional unique files |
| **Total Recovered** | **117 files** |

### 2. Commands Used

```bash
# Restore from git
git restore --source=83eec13 -- "data/property_images/processed/f4e29e2c/*.png"

# Copy from archives
cp archive/run_20251202_205502/images/processed/f4e29e2c/*.png data/property_images/processed/f4e29e2c/
cp archive/run_20251202_221951/images/processed/f4e29e2c/*.png data/property_images/processed/f4e29e2c/
```

### 3. Metadata Updated

- `address_folder_lookup.json`: Updated image_count from 40 to 117
- Added `recovered_at` and `recovery_note` fields

## Prevention Measures Implemented

### 1. Reconciliation Script Created

New script: `scripts/reconcile_image_manifest.py`

```bash
# Check for discrepancies
python scripts/reconcile_image_manifest.py --check -v

# Repair discrepancies
python scripts/reconcile_image_manifest.py --repair --backup
```

### 2. Recommended Additional Safeguards

1. **Pre-commit hook** to warn on mass deletions in `data/property_images/`
2. **Automated backups** of `data/property_images/` before extraction runs
3. **Git LFS** for large binary files (images) to improve diff visibility
4. **Commit size limits** - flag commits with >50 file changes for manual review

## Files Affected

### Before Recovery: 3 files
- 10ed2bee-65d5-4acc-92c7-1dd97bbb4e0e.png
- 7deeeea2-036f-4d83-b223-517562bdb7c8.png
- f3f29ad7-211f-443d-8712-71e0801a8072.png

### After Recovery: 117 files
Full list available via: `ls data/property_images/processed/f4e29e2c/*.png`

## Lessons Learned

1. **Large commits are dangerous** - Always review `git status` before committing
2. **Binary files need special attention** - Consider Git LFS or separate tracking
3. **Archives are valuable** - The archive folder saved us from permanent data loss
4. **Manifest-to-filesystem checks** - Regular reconciliation prevents silent data loss

## Related Commits

| Commit | Description |
|--------|-------------|
| d7f9976 | **BAD** - Accidentally deleted 94 files |
| 0a05a3b | Moved files to archive (cleanup commit) |
| 83eec13 | Last known good state of images |

## Follow-up Actions

- [ ] Add pre-commit hook to protect `data/property_images/` from mass deletions
- [ ] Consider adding `data/property_images/processed/` to `.gitignore` and using backup strategy
- [ ] Run `reconcile_image_manifest.py --check` as part of CI/CD
- [ ] Update image manifest to match recovered files

---

**Investigation completed by:** Claude Code
**Recovery status:** COMPLETE
**Files recovered:** 117 (from 3)
**Data loss:** 0% (after recovery)
