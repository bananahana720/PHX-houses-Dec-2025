# 8. Validation Checklist

Before removal, verify:

- [ ] All code references to each field documented
- [ ] Alternative source identified (LineageTracker, CSV, compute function)
- [ ] Tests updated to not expect removed fields
- [ ] Configuration files reviewed for field name dependencies
- [ ] Deal sheet templates produce same output
- [ ] Scoring unchanged (audit sample of 5 properties)
- [ ] Backup created before applying
- [ ] CI/CD pipeline passes after cleanup

---
