# Executive Summary

This report presents technical research findings on three critical infrastructure topics for the PHX Houses Analysis Pipeline:

1. **Anti-Bot Detection (TECH-05):** Zillow uses HUMAN Security (formerly PerimeterX) with advanced behavioral analysis, TLS fingerprinting, and ML-based detection. Redfin employs IP rate limiting, CAPTCHA challenges, and user-agent detection. Success rates with stealth tools vary from 60-99% depending on approach.

2. **Residential Proxy Comparison (TECH-06):** Bright Data and Oxylabs lead as premium providers (~99% success rates, $5-15/GB), while IPRoyal and Smartproxy offer better value ($2.20-7/GB). For Zillow/Redfin specifically, residential proxies are essential - datacenter IPs are blocked almost immediately.

3. **RQ vs Celery (TECH-07):** RQ excels for simplicity (Unix-only, Redis-only) with minimal setup. Celery offers 4x better throughput at scale (12s vs 51s for 20k tasks) and advanced features. **Recommendation:** Start with RQ, migrate to Celery when experiencing queue backups or processing >10,000 tasks/minute.

**Key Recommendation for PHX Houses:** Use `nodriver` + `curl_cffi` with rotating residential proxies (IPRoyal or Smartproxy for cost-effectiveness) and RQ for task queuing. This aligns with current project architecture and provides good cost/performance balance.

---
