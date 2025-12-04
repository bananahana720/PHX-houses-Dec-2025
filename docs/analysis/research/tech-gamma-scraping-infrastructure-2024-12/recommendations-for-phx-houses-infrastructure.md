# Recommendations for PHX Houses Infrastructure

### Current Architecture Alignment

The project already uses:
- **nodriver** for stealth browsing
- **curl_cffi** for TLS fingerprint spoofing
- Redis (implied by RQ consideration)

This aligns well with research findings.

### Recommended Stack

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| **Task Queue** | RQ | Project scale fits; simplicity wins |
| **Browser Automation** | nodriver | Already in use; best stealth |
| **HTTP Client** | curl_cffi | TLS spoofing for API calls |
| **Proxy Provider** | Smartproxy/Decodo | Best value, real estate support |
| **Backup Proxy** | IPRoyal | Non-expiring for dev/test |

### Implementation Guidelines

1. **Rate Limiting Strategy:**
   - Minimum 1-2 second delay between Zillow requests
   - Random jitter (0.5-2s additional)
   - Session reuse with cookie persistence
   - Geographic IP targeting (Arizona residential)

2. **Proxy Rotation:**
   - New IP per property (not per request)
   - Sticky sessions: 5-10 minutes
   - Immediate rotation on 403/429 responses

3. **Monitoring Thresholds:**
   - Alert if queue latency >30 seconds
   - Alert if Redis memory >70%
   - Track success rate per target site

### Cost Estimates

| Scenario | Properties/Month | Proxy Cost/Month | Task Queue |
|----------|------------------|------------------|------------|
| Development | 50 | $35-50 (IPRoyal) | RQ |
| Production | 500 | $150-250 (Smartproxy) | RQ |
| Scale | 5,000 | $500-1,000 (Oxylabs) | Consider Celery |

### Risk Factors

1. **Anti-Bot Arms Race:** [High Confidence]
   - nodriver/curl_cffi may be detected in 6-12 months
   - Mitigation: Monitor success rates; budget for commercial solutions

2. **Terms of Service:** [High Confidence]
   - Both Zillow and Redfin ToS prohibit scraping
   - Mitigation: Use data responsibly; consider commercial data providers

3. **IP Reputation:** [Medium Confidence]
   - Shared proxy IPs may have degraded reputation
   - Mitigation: Premium proxy tiers; dedicated IPs for production

---
