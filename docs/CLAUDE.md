# docs/CLAUDE.md

---
last_updated: 2025-12-02
updated_by: Claude Code
staleness_hours: 168
---

## Purpose

Technical documentation hub for the PHX Houses Analysis Pipeline project. Contains architecture guides, implementation specs, security audits, testing documentation, API references, configuration guides, and generated artifacts.

## Directory Structure

```
docs/
├── CLAUDE.md                          # This file
├── architecture/                      # Architecture documentation
├── specs/                             # Implementation specifications
├── artifacts/                         # Generated reports and analysis
│   ├── deal_sheets/                  # Property deal sheet examples
│   └── implementation-notes/         # Implementation summaries
├── templates/                         # HTML report templates
│   └── components/                   # Reusable HTML components
└── risk_checklists/                  # Property risk assessment checklists
```

## Key Documents

### Core Technical Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `AI_TECHNICAL_SPEC.md` | Complete project recreation guide for AI agents | Current |
| `CODE_REFERENCE.md` | Code snippets and implementation examples | Current |
| `DATA_ENGINEERING_AUDIT.md` | Data pipeline quality and validation audit | Current |
| `VISUALIZATIONS_GUIDE.md` | Visualization generation and usage guide | Current |

### Architecture & Specifications

| Document | Purpose | Location |
|----------|---------|----------|
| `scoring-improvement-architecture.md` | Scoring system design | `architecture/` |
| `implementation-spec.md` | Implementation requirements | `specs/` |
| `phase-execution-guide.md` | Pipeline phase execution guide | `specs/` |
| `reference-index.md` | Master reference document catalog | `specs/` |

### Configuration & Setup

| Document | Purpose | Status |
|----------|---------|--------|
| `CONFIG_IMPLEMENTATION_GUIDE.md` | Configuration system guide | Current |
| `CONFIG_EXTERNALIZATION_INDEX.md` | Externalized config inventory | Current |
| `CONSTANTS_MIGRATION.md` | Constants migration to config files | Complete |
| `kill_switch_config.md` | Kill-switch criteria configuration | Current |
| `BROWSER_ISOLATION_SETUP.md` | Browser automation isolation setup | Current |

### Security Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `SECURITY.md` | Security best practices | Current |
| `SECURITY_SETUP.md` | Security configuration guide | Current |
| `SECURITY_INDEX.md` | Security documentation index | Current |
| `SECURITY_QUICK_REFERENCE.txt` | Quick security reference | Current |
| `SECURITY_AUDIT_REPORT.md` | Latest security audit findings | Current |

### Testing & Quality

| Document | Purpose | Status |
|----------|---------|--------|
| `TEST_COVERAGE_ANALYSIS.md` | Comprehensive test coverage analysis | Current |
| `RECOMMENDED_TESTS.md` | Recommended test cases and priorities | Current |
| `COVERAGE_ROADMAP.md` | Test coverage improvement roadmap | Current |
| `COVERAGE_SUMMARY.txt` | Quick test coverage overview | Current |
| `TEST_REPOSITORIES_SUMMARY.md` | Test repository patterns | Current |
| `TEST_STANDARDIZER_SUMMARY.md` | Test standardization approach | Current |
| `STANDARDIZER_TESTS_QUICK_REFERENCE.md` | Quick reference for test standards | Current |

### API & Integration Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `MC-Assessor-API-Documentation.md` | Maricopa County Assessor API reference | Current |
| `proxy_extension_setup.md` | Proxy extension setup guide | Current |
| `proxy_extension_architecture.md` | Proxy extension architecture | Current |
| `proxy_extension_quick_reference.md` | Quick proxy extension reference | Current |
| `data-cache-usage.md` | Data caching patterns | Current |

### Cleanup & Maintenance

| Document | Purpose | Status |
|----------|---------|--------|
| `CLEANUP_INDEX.md` | Cleanup task tracking | Current |
| `CLEANUP_REPORT.txt` | Cleanup execution report | Current |
| `enrichment_data_cleanup.md` | Data cleanup procedures | Current |
| `DEPRECATION_GUIDE.md` | Deprecation strategy and timeline | Current |
| `TRASH-FILES.md` | Files marked for deletion | Current |

### Historical & Reference

| Document | Purpose | Status |
|----------|---------|--------|
| `CHANGELOG` | Project change history | Maintained |
| `RENOVATION_GAP_README.md` | Renovation analysis gaps | Reference |
| `image_extraction_orchestrator.md` | Image extraction architecture | Reference |
| `CHANGES_VALUE_ZONE_EXTERNALIZE.md` | Value zone config externalization | Complete |

## Subdirectories

### architecture/

Architecture design documents and system diagrams.

**Contents:**
- `scoring-improvement-architecture.md` - Scoring system redesign (605-point system, kill-switches, cost efficiency)

### specs/

Implementation specifications and execution guides.

**Contents:**
- `implementation-spec.md` - Detailed implementation requirements
- `phase-execution-guide.md` - Multi-phase pipeline execution guide
- `reference-index.md` - Master index of all reference materials and research (~15+ documents)

### artifacts/

Generated reports, analysis outputs, and implementation notes.

**Key Subdirectories:**
- `deal_sheets/` - Example property deal sheets with scores and recommendations
- `implementation-notes/` - Wave-by-wave implementation summaries and deliverables

**Notable Files:**
- `CONSOLIDATION_SUMMARY.md` - Documentation consolidation report
- `DELIVERABLES.md` - Project deliverables tracking
- `TESTING_SUMMARY.md` - Testing implementation summary
- `TESTING_QUICK_START.md` - Quick start guide for testing
- `SCORING_QUICK_REFERENCE.md` - Scoring system quick reference
- `VALUE_SPOTTER_RADAR_UPDATE.md` - Value spotter visualization updates

### templates/

HTML templates for report generation (Jinja2).

**Contents:**
- `base.html` - Base template layout
- `risk_report.html` - Risk assessment report template
- `renovation_report.html` - Renovation analysis report template
- `components/` - Reusable HTML components
  - `risk_badge.html` - Risk level badge component
  - `score_breakdown.html` - Score breakdown table component
  - `property_card.html` - Property card component

### risk_checklists/

Property-specific risk assessment checklists (generated outputs).

**Format:** `{address}_checklist.txt`

**Example Properties:**
- 8714 E Plaza Ave, Scottsdale, AZ 85250
- 16814 N 31st Ave, Phoenix, AZ 85053
- 5522 W Carol Ave, Glendale, AZ 85302

## Pending Tasks

- [ ] Consolidate duplicate security audit reports (OLD vs NEW)
- [ ] Archive historical proxy extension docs if no longer needed
- [ ] Review and clean up old implementation-notes in artifacts/
- [ ] Ensure all test coverage docs are synchronized
- [ ] Add examples to VISUALIZATIONS_GUIDE.md for each chart type

## Key Learnings

### Documentation Organization

- **Master indexes are critical**: `reference-index.md`, `CLEANUP_INDEX.md`, `CONFIG_EXTERNALIZATION_INDEX.md` provide navigable entry points
- **Quick references save time**: `.txt` quick reference files (`SECURITY_QUICK_REFERENCE.txt`, `COVERAGE_SUMMARY.txt`) are faster to scan than full `.md` files
- **Separate specs from artifacts**: Keep specifications (intent) separate from artifacts (outcomes)
- **Version control for audits**: Security audit reports should be timestamped and versioned (not OLD/NEW)

### Testing Documentation

- Test standardization efforts documented in `TEST_STANDARDIZER_SUMMARY.md` provide consistent patterns
- Coverage roadmap (`COVERAGE_ROADMAP.md`) prioritizes testing work effectively
- Quick start guides (`TESTING_QUICK_START.md`) lower barrier to entry for new contributors

### Configuration Management

- Externalization index tracks all hardcoded-to-config migrations
- Migration guides (`CONSTANTS_MIGRATION.md`) document the "why" not just the "what"
- Quick reference guides accelerate common configuration tasks

### Security Practices

- Consolidated security documentation in one place improves compliance
- Security setup guides should include verification steps
- Regular security audits create audit trail

## References

### Tool Usage for Documentation

- **Reading docs**: Use `Read` tool, never `bash cat`
- **Searching docs**: Use `Grep` tool with `output_mode: content` for context
- **Finding docs**: Use `Glob` tool with patterns like `docs/**/*.md`

### Key Code References

- Scoring system: `src/phx_home_analysis/config/scoring_weights.py`
- Kill-switch logic: `scripts/lib/kill_switch.py:45-89`
- Configuration loading: `src/phx_home_analysis/config/constants.py`
- Report generation: `scripts/deal_sheets/`
- Visualization scripts: `scripts/generate_all_visualizations.py`

### Related Project Files

- Main project docs: `../CLAUDE.md`
- Agent instructions: `../.claude/AGENT_BRIEFING.md`
- Protocols: `../.claude/protocols.md`
- Toolkit reference: `../.claude/knowledge/toolkit.json`
- Context management: `../.claude/knowledge/context-management.json`

---

**Navigation:**
- **Parent directory**: `C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\`
- **Main project CLAUDE.md**: `../CLAUDE.md`
- **Agent configuration**: `../.claude/`
