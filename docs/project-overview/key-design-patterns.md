# Key Design Patterns

### 1. Repository Pattern
Abstracts data access from business logic:
```python
PropertyRepository (abstract)
├── CsvPropertyRepository (CSV)
└── [Future: DatabaseRepository]

EnrichmentRepository (abstract)
├── JsonEnrichmentRepository (JSON)
└── [Future: DatabaseRepository]
```

### 2. Strategy Pattern
Each scoring component is an independent strategy:
```python
ScoringStrategy (base class)
├── SchoolDistrictScorer (42pts)
├── QuietnessScorer (30pts)
├── CrimeIndexScorer (47pts)
└── [18 other strategies]
```

### 3. Domain-Driven Design
Clean separation of concerns:
```
Domain Layer (entities, value objects, enums)
    ↓
Service Layer (kill-switch, scoring, enrichment)
    ↓
Pipeline Layer (orchestration)
    ↓
Presentation Layer (reporters)
```

### 4. Multi-Agent Orchestration
Claude Code agents for parallel data extraction:
- **listing-browser (Haiku):** Fast, cost-effective for scraping
- **map-analyzer (Haiku):** Parallel with listing-browser
- **image-assessor (Sonnet):** Visual analysis requires stronger model
