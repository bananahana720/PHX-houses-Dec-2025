# 3. Test Levels Strategy

### 3.1 Recommended Split

Based on the DDD architecture with strong domain isolation:

| Level | Target | Rationale |
|-------|--------|-----------|
| **Unit Tests** | 65% | Domain entities, scoring strategies, kill-switch criteria, value objects, repositories |
| **Integration Tests** | 25% | Pipeline orchestration, API clients, file I/O, agent communication |
| **E2E Tests** | 10% | Full pipeline runs, CLI commands, report generation |

### 3.2 Unit Tests (65%)

**Focus Areas:**
- Kill-switch criteria (7 individual criterion classes)
- Scoring strategies (22 strategy classes)
- Tier classification logic
- Address normalization
- Data validation (Pydantic schemas)
- Configuration loading
- Repository CRUD operations (with mock data)
- Error handling utilities

**Framework:** pytest
**Coverage Target:** 80% line coverage for `src/phx_home_analysis/`

**Example Test Categories:**

| Component | Test Count | Est. Hours |
|-----------|------------|------------|
| Kill-switch criteria (7 classes x 5 tests) | 35 | 8 |
| Scoring strategies (22 classes x 4 tests) | 88 | 20 |
| Tier classifier | 10 | 2 |
| Repository operations | 25 | 6 |
| Configuration loading | 15 | 4 |
| Validation schemas | 20 | 5 |
| **Total Unit** | ~200 | ~45 |

### 3.3 Integration Tests (25%)

**Focus Areas:**
- Pipeline phase coordination
- County Assessor API client (mocked HTTP)
- Listing extraction (mocked responses)
- Map analysis service
- State management (work_items.json manipulation)
- Data aggregation from multiple sources
- Agent spawning coordination

**Framework:** pytest + respx (HTTP mocking) + pytest-asyncio
**Coverage Target:** Critical paths fully covered

**Example Test Categories:**

| Component | Test Count | Est. Hours |
|-----------|------------|------------|
| Pipeline orchestration | 15 | 10 |
| API client integration (mocked) | 20 | 8 |
| State management | 15 | 6 |
| Data aggregation/merge | 12 | 5 |
| Phase coordination | 10 | 6 |
| **Total Integration** | ~70 | ~35 |

### 3.4 E2E Tests (10%)

**Focus Areas:**
- Full pipeline run (--test mode with 5 properties)
- CLI command validation
- Deal sheet generation
- Resume from checkpoint
- Report output verification

**Framework:** pytest + subprocess for CLI
**Environment:** Isolated test directory with fixtures

**Example Test Categories:**

| Component | Test Count | Est. Hours |
|-----------|------------|------------|
| CLI smoke tests | 5 | 3 |
| Full pipeline (--test) | 3 | 5 |
| Resume capability | 3 | 3 |
| Report generation | 5 | 4 |
| **Total E2E** | ~16 | ~15 |

---
