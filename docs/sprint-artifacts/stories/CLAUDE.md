---
last_updated: 2025-12-07
updated_by: agent
---

# stories

## Purpose
User stories (42 total across 7 epics) capturing detailed requirements and acceptance criteria for Phase 4 implementation. Each story represents a sized, ready-for-development task with test plan and success metrics.

## Contents

| Story File | Epic | Status | Focus |
|------------|------|--------|-------|
| E1-S1-configuration-system-setup.md | Epic 1 | Done | YAML config loader, env overrides, validation |
| E1-S2-property-data-storage-layer.md | Epic 1 | Done | JSON enrichment, Pydantic schemas, CRUD ops |
| E1-S3-data-provenance-lineage.md | Epic 1 | Done | Source tracking, confidence scoring, field provenance |
| E1-S4-pipeline-state-checkpointing.md | Epic 1 | Done | Atomic writes, work_items.json, recovery checkpoints |
| E1-S5-pipeline-resume-capability.md | Epic 1 | Done | Resume from phase, crash recovery, state hydration |
| E1-S6-transient-error-recovery.md | Epic 1 | Done | Retry logic, backoff strategies, exponential delays |
| E2-S1-batch-analysis-cli.md | Epic 2 | Done | --dry-run, --json, CSV validation, ETA calculation |
| E2-S2-maricopa-county-assessor-api.md | Epic 2 | Done | Phase 0 County API integration, lot/year/garage data |
| E2-S3-zillow-redfin-extraction.md | Epic 2 | Done | Listing browser, UA rotation, CAPTCHA handling |
| E2-S4-property-image-download-caching.md | Epic 2 | Done | Content-addressed storage, lineage, file locking |
| E2-S5-google-maps-geographic.md | Epic 2 | Done | Coordinates, orientation (sun), proximity calc |
| E2-S6-greatschools-api-school-ratings.md | Epic 2 | Done | School ratings API, geocoding, quality scores |
| E2-R1-zillow-zpid-direct-extraction.md | Epic 2 | Done | ZPID direct lookup, CAPTCHA bypass fallback |
| E2-S7-api-integration-infrastructure.md | Epic 2 | Done | HTTP client, retries, rate limiting, mocking |
| E3 Stories (5) | Epic 3 | Backlog | Kill-switch validation (separate files) |
| E4-S1-three-dimension-scoring.md | Epic 4 | Backlog | Location (250pts), Systems (175pts), Interior (180pts) |
| E5-S1-pipeline-orchestrator-cli.md | Epic 5 | Backlog | Typer CLI, parallel waves, async orchestration |
| E7-S1-deal-sheet-html-generation.md | Epic 7 | Backlog | HTML report generation, Jinja2 templates |
| story-live-testing-infrastructure.md | E3.S1 | Backlog | Live test infrastructure, mock validation |
| test-design-epic-2-7.md | Testing | Reference | Test design patterns, coverage strategy |
| atdd-checklist-epic-2.md | Testing | Reference | ATDD acceptance test checklist |
| sprint-0-architecture-prerequisites.md | Foundation | Reference | Architecture foundation, schema design |

## Key Status (2025-12-07)

- **Epics Complete**: 2/7 (E1 Foundation, E2 Data Acquisition)
- **Stories Done**: 19/42 (45%)
- **Epic 2**: All 7 stories PASS, 19 unit + 67 integration tests
- **Remaining Backlog**: E3-E7 (23 stories), estimated 8-12 weeks

## Tasks

- [ ] Link E3 stories to kill-switch implementation roadmap `P:H`
- [ ] Create story decomposition templates `P:M`
- [ ] Draft E4 scoring story specifications `P:M`

## Learnings

- **Story completeness critical**: Full context (AC, test plan, blockers) in story file enables async agent development
- **Status synchronization vital**: Story completion requires updates to sprint-status.yaml and workflow-status.yaml
- **E2 parallel execution validated**: 3 API stories (S3/S5/S6) implemented in parallel; 72 tests provide confidence
- **Content-addressed storage**: E2.S4 approach prevents duplicate downloads, enables fast reruns

## Refs

- Sprint tracking: `../sprint-status.yaml`
- Workflow status: `../workflow-status.yaml`
- Story format: `.bmad/bmm/workflows/create-epics-and-stories.md`
- Architecture: `../../architecture/`

## Deps

← `../sprint-status.yaml` (epic/story progress tracking)
← `../workflow-status.yaml` (phase gates, decisions)
← `.bmad/` (story creation workflows)
→ Implementation agents (dev-story workflow consumers)
→ Sprint retrospectives (completion validators)
