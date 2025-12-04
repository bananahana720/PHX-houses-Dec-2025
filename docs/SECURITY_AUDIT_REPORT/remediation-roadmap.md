# Remediation Roadmap

### Phase 1: Critical & High Priority (Immediate - 1 Week)

1. **H-1: Implement Magic Byte Validation** (2 days)
   - File: `standardizer.py`
   - Add `_validate_magic_bytes()` method
   - Update `standardize()` to check before PIL opens file

2. **H-2: Strip EXIF Metadata** (1 day)
   - File: `standardizer.py`
   - Add `exif=b''` to PIL save call
   - Test with sample EXIF-laden images

3. **H-3: Sanitize Credentials in Logs** (2 days)
   - Files: All logging statements
   - Create `sanitize_url()` helper
   - Audit all log statements for credential leaks
   - Add unit tests

### Phase 2: Medium Priority (2-4 Weeks)

4. **M-1: URL Redirect Validation** (3 days)
   - File: `stealth_http_client.py`
   - Disable redirects or re-validate on redirect
   - Test with redirect chains

5. **M-4: Fix Symlink Race Condition** (2 days)
   - File: `symlink_views.py`
   - Use atomic `os.symlink()` without existence check
   - Handle `FileExistsError`

6. **M-6: Token Rotation Support** (3 days)
   - File: `maricopa_assessor.py`
   - Add `_get_token()` with refresh callback
   - Document token rotation process

7. **M-8: State File Integrity** (4 days)
   - File: `state_manager.py`
   - Implement HMAC verification
   - Add `STATE_INTEGRITY_KEY` environment variable
   - Update documentation

8. **M-10: Certificate Pinning** (3 days)
   - File: `orchestrator.py`
   - Implement pinned transport
   - Document pin extraction process
   - Plan for pin rotation

### Phase 3: Low Priority & Enhancements (Ongoing)

9. **L-1, L-2, L-3: Documentation & Optimizations**
   - Add symlink behavior docs
   - Implement state backup
   - Enable HTTP/2
   - Other minor improvements

10. **Security Testing**
    - Penetration testing of image pipeline
    - Fuzzing image parsers
    - Load testing with malicious inputs

---
