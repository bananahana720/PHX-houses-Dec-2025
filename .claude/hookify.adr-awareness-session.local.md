---
name: adr-awareness-session
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(implement|create|build|add|develop|refactor|fix|write|code|feature|story|E\d+-|epic|sprint)
action: warn
---

## 📋 ADR Pattern Awareness Reminder

**You are starting development work. Review the project's architectural decisions.**

### Quick Reference: ADR-07 through ADR-11
Per `docs/architecture/core-architectural-decisions.md`:

---

### ADR-07: Testing Framework
| Aspect | Standard |
|--------|----------|
| Framework | pytest 9.0.1 |
| Fixtures | Fixture-based DI (conftest.py) |
| Async | pytest-asyncio |
| Mocking | respx for HTTP |
| Coverage | 2,636 tests (2,596 active) |

---

### ADR-08: Package Organization (DDD)
```
src/phx_home_analysis/
├── domain/         ← Pure entities, NO external deps
├── infrastructure/ ← Repositories, API clients
├── services/       ← Business logic
├── application/    ← Orchestrators, use cases
└── presentation/   ← CLI, deal sheets
```

---

### ADR-09: Architecture Patterns
| Pattern | Usage |
|---------|-------|
| Repository | Abstract data access interfaces |
| Strategy | 7 scoring strategies in services/scoring/ |
| Protocol DI | `typing.Protocol` for interfaces |
| Async Retry | Exponential backoff for external calls |

---

### ADR-10: Orchestration Patterns
| Level | Component | Purpose |
|-------|-----------|---------|
| L1 | `PipelineOrchestrator` | Multi-phase workflow |
| L2 | `PhaseController` | Phase execution |
| L3 | Individual services | Business logic |

Phase enum: `COUNTY_LOOKUP → LISTING_EXTRACTION → IMAGE_ASSESSMENT → SYNTHESIS → REPORTING`

---

### ADR-11: Entity Model Conventions
| Aspect | Convention |
|--------|------------|
| Base class | `pydantic.BaseModel` |
| Optionals | `field: Type \| None = None` |
| Distance suffix | `_mi` (not `_miles`) |
| Provenance | `FieldProvenance` class |
| Schema version | `__schema_version__ = "2.0.0"` |

---

### Critical Metrics
| Metric | Value |
|--------|-------|
| Scoring total | 605 points |
| Unicorn tier | ≥484 pts (80%) |
| Contender tier | 363-483 pts |
| HARD kill-switches | 8 criteria |

---

**Read `docs/architecture/core-architectural-decisions.md` for full details before implementing.**
