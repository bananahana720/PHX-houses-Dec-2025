# CI/CD Ready

### GitHub Actions Example
```yaml
- name: Test ImageDeduplicator
  run: |
    python -m pytest tests/unit/test_deduplicator.py \
      --cov=phx_home_analysis.services.image_extraction.deduplicator \
      --cov-fail-under=90 \
      -v
```

### Local Pre-commit Hook
```bash
#!/bin/bash
python -m pytest tests/unit/test_deduplicator.py -q
```

---
