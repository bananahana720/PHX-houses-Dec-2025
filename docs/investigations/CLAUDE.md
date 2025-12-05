---
last_updated: 2025-12-04T15:58:00Z
updated_by: agent
staleness_hours: 24
line_target: 60
flags: []
---
# investigations

## Purpose
Root-cause analysis reports for bugs, data loss incidents, and anomalies discovered during development and testing. Preserves incident response context for future reference and prevention.

## Contents
| File | Purpose |
|------|---------|
| `IMAGE_DATA_LOSS_2025-12-04.md` | Accidental deletion of 94 image files in git commit d7f9976; recovery procedures |

## Key Patterns
- **Timeline + RCA**: Event sequence, root cause hypothesis, lessons learned
- **Recovery Documentation**: Commands, sources (git history, archives), metadata updates
- **Prevention Measures**: Concrete safeguards (pre-commit hooks, scripts, CI checks)

## Tasks
- [ ] Implement pre-commit hook to warn on mass deletions in `data/property_images/` `P:H`
- [ ] Add `reconcile_image_manifest.py` check to CI/CD pipeline `P:H`
- [ ] Consider Git LFS for binary files (images) to improve diff visibility `P:M`

## Learnings
- **Large commits are dangerous**: Binary file deletions invisible in large commits; always review `git status` before committing
- **Archives as failsafe**: Archive folder from extraction runs saved 71 files; proves value of backup strategy
- **Manifest-to-filesystem sync**: Silent data loss occurs when git and manifest drift; reconciliation script essential

## Refs
- Recovery script: `scripts/reconcile_image_manifest.py`
- Image storage: `data/property_images/processed/{folder_id}/`
- Manifest tracking: `data/address_folder_lookup.json`

## Deps
← imports from: git history, archive directories, manifest files
→ used by: prevention workflows, backup strategies
