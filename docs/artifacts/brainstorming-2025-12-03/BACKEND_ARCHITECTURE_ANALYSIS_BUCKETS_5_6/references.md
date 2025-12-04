# References

**Current Code**:
- Image extraction: `src/phx_home_analysis/services/image_extraction/`
- Orchestrator: `src/phx_home_analysis/services/image_extraction/orchestrator.py`
- CLI script: `scripts/extract_images.py`
- Stealth extraction: `src/phx_home_analysis/services/infrastructure/stealth_http_client.py`
- Deduplication: `src/phx_home_analysis/services/image_extraction/deduplicator.py`
- Naming: `src/phx_home_analysis/services/image_extraction/naming.py`

**Metadata**:
- Address lookup: `data/property_images/metadata/address_folder_lookup.json`
- Image manifest: `data/property_images/metadata/image_manifest.json`
- Extraction state: `data/property_images/metadata/extraction_state.json`
- Pipeline runs: `data/property_images/metadata/pipeline_runs.json`

**External Documentation**:
- [RQ (Redis Queue) Documentation](https://python-rq.org/)
- [Celery Distributed Task Queue](https://docs.celeryproject.org/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Locality Sensitive Hashing (LSH)](https://en.wikipedia.org/wiki/Locality-sensitive_hashing)
- [nodriver (UC Browser Automation)](https://github.com/ultrafunkamsterdam/nodriver)

