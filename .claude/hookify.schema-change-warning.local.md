---
name: schema-change-warning
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (domain/entities|domain/value_objects|domain/enums|validation/.*schemas?)\.py$
action: warn
---

## ⚠️ Schema/Domain Model Change Detected

**You are modifying a core schema or domain model file.**

### ADR-11 Field Naming Convention (MANDATORY)
Per `docs/architecture/core-architectural-decisions.md`:
- **Distance fields**: Use `_mi` suffix (e.g., `school_distance_mi`, NOT `_miles`)
- **Provenance fields**: Use `FieldProvenance` class pattern from `domain/entities.py:14-40`
- **Optional fields**: Use `field_name: str | None = None` pattern
- **Schema version**: Increment version in `__schema_version__` when adding fields

### Impact Assessment Required

Schema changes can affect:
1. **Data serialization** - JSON repository `_to_dict()` / `_from_dict()` methods
2. **API contracts** - Field names, types, and optionality
3. **Database migrations** - If schema changes require data migration
4. **Test fixtures** - Existing test data may become invalid
5. **Documentation** - CLAUDE.md files reference schema fields

### Pre-Change Checklist
- [ ] Is this a breaking change? (removing/renaming fields)
- [ ] Does new field follow `_mi` suffix for distances?
- [ ] Does provenance use `FieldProvenance` class pattern?
- [ ] Are serializers updated? (`json_repository.py`)
- [ ] Are test fixtures updated?
- [ ] Is documentation updated?
- [ ] Is `__schema_version__` incremented?

### Post-Change Requirements
1. Run full test suite: `pytest tests/ -v`
2. Check mypy: `mypy src/phx_home_analysis/domain/`
3. Update CLAUDE.md if field semantics change
4. Consider data migration if existing data affected

### Schema Evolution Reference
See `docs/architecture/schema-evolution-plan.md` for:
- v2.0.0 → v2.1.0 → v2.2.0 → v3.0.0 migration path
- 63 new fields planned (osm_*, places_*, air_quality_*, school_*, census_*)
- Backward compatibility requirements

**Proceed with caution and test thoroughly.**
