# Testing Strategy

### Unit Tests (`tests/unit/`)
- Domain entities and value objects
- Scoring strategies (each strategy tested independently)
- Kill-switch criteria (hard and soft)
- Data repositories (with mock data)
- Validators and normalizers

### Integration Tests (`tests/integration/`)
- Complete pipeline workflow
- Multi-source data merging
- Kill-switch chain evaluation
- Deal sheet generation
- Proxy extension builder

### Benchmarks (`tests/benchmarks/`)
- LSH performance for deduplication
- Image hash performance
- Cache performance

### Test Coverage
- Target: 80%+ coverage
- Current: ~75% (estimated)
- Gaps: External API integrations (mocked), browser automation
