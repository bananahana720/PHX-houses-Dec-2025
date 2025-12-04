# Monitoring and Detection

### Security Metrics to Track

1. **API Authentication Failures**
   - Track 401 responses
   - Alert on sustained failures (token compromised?)

2. **File System Anomalies**
   - Monitor file access patterns
   - Alert on unexpected path access
   - Track write failures

3. **Rate Limit Violations**
   - Monitor API rate limit headers
   - Track 429 responses
   - Adjust rate limiting as needed

4. **Error Rates**
   - Track error types and frequency
   - Alert on unusual patterns
   - Monitor for security-related errors

### Logging Improvements

```python
import structlog

# Use structured logging for better analysis
logger = structlog.get_logger()

logger.info(
    "api_request",
    endpoint="search_apn",
    address=address,
    status="success",
    duration_ms=123,
)

logger.error(
    "api_request_failed",
    endpoint="get_parcel",
    apn=apn,
    error_type="HTTPStatusError",
    status_code=500,
    duration_ms=456,
)
```

---
