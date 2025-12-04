---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 48
---
# docs/sprint_artifacts/stories

## Purpose

Story definition files for sprint planning and development tracking. Contains detailed user stories with acceptance criteria, technical tasks, dependencies, and test requirements that serve as development contracts and completion checklists for team members.

## Contents

| Path | Purpose |
|------|---------|
| `e2-s7-api-integration-infrastructure.md` | Epic 2, Story 7: API client base class with auth, rate limiting, response caching, and exponential backoff (50.8 KB, comprehensive spec) |

## Story Structure

**Story Format (YAML Front Matter + Markdown):**
```
# [Epic].[Story]: [Title]
- Status: [Backlog | Drafted | Ready for Review | Ready for Dev | In Progress | Review | Done]
- Epic: Epic N - [Name]
- Priority: P0 | P1 | P2
- Estimated Points: N
- Dependencies: [Other stories]
- Functional Requirements: FRN, FRN+1, FRN+2
```

**Standard Sections:**
- User Story (persona, goal, value)
- Acceptance Criteria (AC1-ACN with Given-When-Then format)
- Technical Tasks (per-file implementation details)
- Test Plan (unit, integration, edge cases)
- Risks & Mitigation

## E2.S7: API Integration Infrastructure

**Status:** Ready for Review | **Points:** 8 | **Dependencies:** E1.S6 (Transient Error Recovery)

**Functional Requirements:** FR58, FR59, FR60

**User Story:** As a system user, I want robust API integration with authentication, rate limiting, and caching, so that external data sources are accessed reliably and cost-efficiently.

**Key Acceptance Criteria:**
- AC1: Credentials from env vars (`*_API_KEY`, `*_TOKEN` patterns), never logged
- AC2: Proactive rate limit throttling at 80% threshold with warning logs
- AC3: Exponential backoff on 429 with Retry-After header respect
- AC4: Response caching with configurable TTL (default 7 days)
- AC5: Cache hit rate logging at DEBUG level with stats via `get_cache_stats()`
- AC6: APIClient base class with inherited auth/rate-limit/cache/retry for subclasses

**Technical Tasks:**
1. APIClient base class (~50 lines) - credentials, rate limiter integration, async context manager
2. RateLimit configuration (~30 lines) - per-second/minute/day limits, throttle config
3. RateLimiter implementation (~100 lines) - proactive throttling, statistics
4. ResponseCache + CacheConfig (~120 lines) - SHA256 key generation, TTL enforcement
5. Unit tests (975 lines across 3 modules) - 87 tests covering all components

## Tasks

- [x] Document story structure and AC format `P:H`
- [x] Map E2.S7 requirements to test coverage `P:H`
- [ ] Add E2.S8, E2.S9, E2.S10 story files when drafted `P:M`
- [ ] Create story template with pre-filled sections `P:L`

## Learnings

- **Acceptance Criteria precision critical:** Each AC should be testable (Given-When-Then format ensures this)
- **Dependencies must be explicit:** E2.S7 depends on E1.S6 for `@retry_with_backoff` decorator
- **Story files are contracts:** Developers use ACs as completion checklist, QA uses them for test design
- **Technical tasks bridge story to code:** Per-file tasks with line counts enable realistic estimation
- **Test plan integration:** Story includes test matrix ensuring all paths covered before Done

## Refs

- Story file: `e2-s7-api-integration-infrastructure.md:1-50` (header + AC definitions)
- AC details: `e2-s7-api-integration-infrastructure.md:14-60` (6 acceptance criteria)
- Technical tasks: `e2-s7-api-integration-infrastructure.md:59-200` (per-file implementation)
- Test plan: `e2-s7-api-integration-infrastructure.md:200-300` (unit + integration)
- Sprint tracking: `../sprint-status.yaml` (E2.S7 status tracking)

## Deps

← Imported by:
- Sprint status tracker: `docs/sprint_artifacts/sprint-status.yaml` (references story definitions)
- CI/CD pipeline: Story completion validates against AC checklist
- Development team: Story files guide implementation and acceptance testing

→ Relates to:
- Infrastructure tests: `tests/unit/services/api_client/` (validates story requirements)
- Source code: `src/phx_home_analysis/services/api_client/` (E2.S7 implementation target)