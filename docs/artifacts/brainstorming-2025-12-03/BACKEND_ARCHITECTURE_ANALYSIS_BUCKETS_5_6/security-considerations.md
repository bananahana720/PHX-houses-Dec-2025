# Security Considerations

### User Isolation (Future)

When multi-user support added:

1. **Job ownership**: job.user_id = authenticated user
2. **Access control**: Only user can view/cancel own job
3. **Quotas**: Per-user max concurrent jobs, max images/day
4. **Audit trail**: Log all extraction requests with user + timestamp

### Sensitive Data

**Images may contain**:
- Interior layouts (security risk)
- License plates
- Personal information in signs

**Mitigations**:
- Images stored in private filesystem (not public CDN)
- Access logs for image downloads
- EXIF data stripped (existing: standardizer does this)
- Retention policy (>90 days = archive/delete)

### API Security

When exposing `/api/extraction/` endpoints:

1. Require authentication (OAuth/API key)
2. Rate limit per user (10 jobs/hour)
3. Validate input (source, properties exist)
4. Sanitize error messages (don't expose internal paths)
5. Use HTTPS only

---
