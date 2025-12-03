# Tech-Gamma: Scraping & Infrastructure Research Report

**Research Agent:** Claude (Opus 4.5)
**Date:** December 3, 2024
**Project:** PHX Houses Analysis Pipeline

---

## Executive Summary

This report presents technical research findings on three critical infrastructure topics for the PHX Houses Analysis Pipeline:

1. **Anti-Bot Detection (TECH-05):** Zillow uses HUMAN Security (formerly PerimeterX) with advanced behavioral analysis, TLS fingerprinting, and ML-based detection. Redfin employs IP rate limiting, CAPTCHA challenges, and user-agent detection. Success rates with stealth tools vary from 60-99% depending on approach.

2. **Residential Proxy Comparison (TECH-06):** Bright Data and Oxylabs lead as premium providers (~99% success rates, $5-15/GB), while IPRoyal and Smartproxy offer better value ($2.20-7/GB). For Zillow/Redfin specifically, residential proxies are essential - datacenter IPs are blocked almost immediately.

3. **RQ vs Celery (TECH-07):** RQ excels for simplicity (Unix-only, Redis-only) with minimal setup. Celery offers 4x better throughput at scale (12s vs 51s for 20k tasks) and advanced features. **Recommendation:** Start with RQ, migrate to Celery when experiencing queue backups or processing >10,000 tasks/minute.

**Key Recommendation for PHX Houses:** Use `nodriver` + `curl_cffi` with rotating residential proxies (IPRoyal or Smartproxy for cost-effectiveness) and RQ for task queuing. This aligns with current project architecture and provides good cost/performance balance.

---

## Table of Contents

1. [TECH-05: Zillow/Redfin Anti-Bot Patterns](#tech-05-zillowredfin-anti-bot-patterns-q4-2024)
2. [TECH-06: Residential Proxy Service Comparison](#tech-06-residential-proxy-service-comparison)
3. [TECH-07: RQ vs Celery Scaling Thresholds](#tech-07-rq-vs-celery-scaling-thresholds)
4. [Recommendations for PHX Houses](#recommendations-for-phx-houses-infrastructure)
5. [Source Citations](#full-source-citations)

---

## TECH-05: Zillow/Redfin Anti-Bot Patterns (Q4 2024)

### Zillow Anti-Bot Protection

**Primary Protection:** HUMAN Security (formerly PerimeterX) [High Confidence]

Zillow uses PerimeterX/HUMAN Bot Defender, one of the most sophisticated anti-bot solutions available. The system employs multiple detection layers:

#### Detection Techniques

| Technique | Description | Confidence |
|-----------|-------------|------------|
| **IP Reputation Analysis** | Scores IPs based on provider type (datacenter vs residential), location, and historical behavior | High |
| **TLS Fingerprinting** | Analyzes TLS handshake parameters (cipher suites, TLS versions, extensions) to identify bot-like signatures | High |
| **JavaScript Challenge** | Injects JS snippets that analyze browser behavior and capabilities | High |
| **Device/Browser Fingerprinting** | Collects unique browser and device characteristics | High |
| **Behavioral Analysis** | Monitors mouse movements, clicks, keystroke patterns, scrolling behavior | High |
| **Machine Learning** | Real-time ML algorithms detect anomalies and suspicious patterns | High |

**Rate Limiting Behavior:** [High Confidence]
- Monitors request frequency per IP
- 429 (Too Many Requests) responses trigger temporary blocks
- 403 (Forbidden) indicates IP/session flagged - requires IP rotation
- PerimeterX assigns trust scores; once flagged, the bot is blocked "indefinitely"

**HUMAN Challenge (CAPTCHA):** [Medium Confidence]
- Lightweight compared to other CAPTCHAs
- Gains access to page activities/events for continued behavioral monitoring
- Triggers when trust score drops below threshold

### Redfin Anti-Bot Protection

**Protection Level:** Moderate (compared to Zillow) [Medium Confidence]

Redfin implements standard anti-scraping measures but without the sophisticated ML-based detection of HUMAN Security:

| Measure | Details | Confidence |
|---------|---------|------------|
| **IP Rate Limiting** | Blocks after "a couple of requests" from same IP | High |
| **CAPTCHA Challenges** | Standard CAPTCHA implementation | Medium |
| **User-Agent Detection** | Identifies non-browser user agents | High |
| **Honeypot Traps** | Hidden elements to catch bots | Medium |
| **AJAX-Heavy Architecture** | Data loads dynamically, requiring headless browsers | High |

**robots.txt Compliance:** [High Confidence]
- `Crawl-delay: 1` - 1 second between requests
- `Allow: /s/sitemap*` - Some crawling permitted
- Terms of Service explicitly prohibit automated scraping

### Successful Bypass Strategies

#### 1. Stealth Headless Browsers

**nodriver** [High Confidence - Current Project Choice]
- Successor to undetected-chromedriver
- Direct browser communication (no WebDriver/Selenium)
- Asynchronous architecture for concurrent scraping
- Better stealth - removes WebDriver automation signals
- **Limitation:** Anti-bot companies monitor open-source solutions; expect ~6 month shelf life before patches

```python
# nodriver example (conceptual)
import nodriver as uc
browser = await uc.start()
page = await browser.get('https://target-site.com')
```

**undetected-chromedriver** [Medium Confidence]
- Patches Selenium ChromeDriver
- Fixes TLS, HTTP, and JavaScript fingerprints
- Works against basic protection but detected by advanced systems

#### 2. TLS Fingerprint Spoofing

**curl_cffi** [High Confidence - Current Project Choice]
- Python bindings for curl-impersonate
- Mimics browser TLS/JA3/HTTP2 fingerprints
- Supports Chrome, Safari, Edge impersonation
- **Success Rate:** 60-70% on basic sites, lower on advanced protection
- **Limitation:** Cannot execute JavaScript; not suitable for AJAX-heavy sites

```python
from curl_cffi import requests
response = requests.get("https://zillow.com", impersonate="chrome110")
```

#### 3. Combined Approach (Recommended)

| Tool | Use Case | Success Rate |
|------|----------|--------------|
| nodriver | Full page rendering, AJAX content, behavioral simulation | ~85-95% with proxies |
| curl_cffi | Static content, API endpoints, initial requests | 60-70% |
| Residential Proxies | IP rotation, geographic targeting | Essential for both |

### Community Observations (r/webscraping, GitHub)

**Conflicting Data:** [Medium Confidence]
- Some report Zillow blocks within 10-20 requests even with residential proxies
- Others claim sustained scraping with proper session management
- Success highly dependent on: request patterns, session reuse, proxy quality

**Key Learnings:**
1. Session/cookie reuse critical - maintain TCP connections
2. Randomized delays between requests (1-5 seconds minimum)
3. Rotate user agents from real browser distributions
4. Geographic proxy targeting (US residential IPs)
5. Avoid peak hours for target sites

---

## TECH-06: Residential Proxy Service Comparison

### Provider Comparison Matrix

| Provider | Pool Size | Price/GB | US Coverage | Success Rate | Best For |
|----------|-----------|----------|-------------|--------------|----------|
| **Bright Data** | 72M+ | $4.20-5.88 | Excellent | ~99% | Enterprise, advanced features |
| **Oxylabs** | 102M+ | $5-15 | Excellent | 99.82% | Enterprise, real estate scraping |
| **Smartproxy/Decodo** | 115M+ | $2.20-4.90 | Good | 99.86% | Best value, good support |
| **IPRoyal** | 32M+ | $2.45-7 | Good | 99.7% | Budget, non-expiring traffic |
| **DataImpulse** | N/A | $1-2 | Moderate | N/A | Ultra-budget |

### Detailed Provider Analysis

#### Bright Data (Premium) [High Confidence]

**Pricing:**
- Pay-as-you-go: $5.88/GB
- Subscription plans (50% discount first 3 months):
  - $499/mo = 141 GB (~$3.54/GB)
  - $999/mo = 332 GB (~$3.01/GB)
  - $1,999/mo = 798 GB (~$2.50/GB)

**Strengths:**
- Largest proxy network (195+ countries)
- Web Unlocker tool with CAPTCHA solving (~99% Zillow success)
- Advanced proxy management tools
- "Best Platform for Proxies" award 2024

**Weaknesses:**
- Complex pricing (city/ASN targeting costs extra)
- Premium pricing compared to alternatives
- Learning curve for advanced features

**Real Estate Scraping:** Excellent - purpose-built tools for protected sites

#### Oxylabs (Premium) [High Confidence]

**Pricing:**
- Pay-as-you-go: $8/GB (minimum)
- Subscription: $300/mo for 20 GB ($15/GB)
- Volume: $5,000/mo for 1 TB ($5/GB)

**Strengths:**
- Next-Gen Residential Proxies with auto-retry
- 99.82% success rate, 0.41s response time
- Web Unblocker specifically for real estate
- SOCKS5 support
- 24/7 live chat support
- Ethically sourced IPs

**Weaknesses:**
- High entry cost ($300/mo minimum subscription)
- Overkill for small-scale projects

**Real Estate Scraping:** Excellent - explicit support for real estate scraping APIs

#### Smartproxy/Decodo (Best Value) [High Confidence]

**Pricing:**
- Pay-as-you-go: $3.50-7/GB
- Subscription:
  - $75/mo = 5 GB ($15/GB) - Micro plan
  - $245/mo = 50 GB ($4.90/GB)
  - $450/mo = 100 GB ($4.50/GB)
  - $3,000/mo = 1,000 GB ($3/GB)

**Strengths:**
- 115M+ IP pool, 195 countries
- 99.86% success rate, 99.99% uptime
- Site Unblocker (100% claimed success)
- Chrome/Firefox extensions included
- 14-day money-back guarantee
- "Best proxy provider" - Proxyway (3 consecutive years)

**Weaknesses:**
- Sticky sessions limited (1, 10, 30 minutes only)
- KYC procedure required

**Real Estate Scraping:** Very good - Site Unblocker handles protected sites

#### IPRoyal (Budget) [High Confidence]

**Pricing:**
- No minimum commitment
- $7/GB (1 GB)
- $2.45/GB (bulk orders)
- Non-expiring traffic (unique feature)

**Strengths:**
- 32M+ IPs, 195 countries
- Flexible sticky sessions (1 second to 7 days)
- No monthly minimums or contracts
- 99.7% success rate
- Cryptocurrency payments accepted

**Weaknesses:**
- Smaller IP pool than premium providers
- Less advanced tooling

**Real Estate Scraping:** Good - suitable for moderate-scale projects

### Pricing Model Comparison

| Model | Description | Best For |
|-------|-------------|----------|
| **Per GB** | Pay for bandwidth consumed | Variable workloads, testing |
| **Per Request** | Pay per API call | Predictable request patterns |
| **Subscription** | Monthly commitment, lower $/GB | Sustained high-volume scraping |
| **Non-expiring** | Traffic never expires | Intermittent usage (IPRoyal) |

### US Residential IP Coverage [High Confidence]

All major providers cover US extensively:
- **Bright Data:** City/state/ZIP targeting (premium)
- **Oxylabs:** Country, city, state, ZIP, coordinates, ASN
- **Smartproxy:** Country, state, city targeting
- **IPRoyal:** Country, state, city targeting

### Success Rates for Real Estate Sites

| Provider | Zillow | Redfin | General Real Estate |
|----------|--------|--------|---------------------|
| Bright Data | ~99% | ~99% | ~99% |
| Oxylabs | ~99% | ~99% | ~99% |
| Smartproxy | ~95% | ~97% | ~99% |
| IPRoyal | ~90% | ~95% | ~97% |

*Note: Success rates are approximate and depend heavily on implementation quality.* [Medium Confidence]

### Recommendation for PHX Houses

**Primary Choice: Smartproxy/Decodo** [High Confidence]
- Best price/performance ratio
- Site Unblocker for difficult targets
- 14-day money-back guarantee for testing
- Sufficient for ~50-100 properties/day

**Budget Alternative: IPRoyal**
- Non-expiring traffic ideal for intermittent analysis
- Lower cost for development/testing

**Scale-Up Path: Oxylabs**
- When needing 100% success guarantee
- Web Unblocker specifically designed for real estate

---

## TECH-07: RQ vs Celery Scaling Thresholds

### Overview Comparison

| Feature | RQ (Redis Queue) | Celery |
|---------|------------------|--------|
| **Broker Support** | Redis only | Redis, RabbitMQ, SQS, etc. |
| **OS Support** | Unix only (fork required) | Cross-platform |
| **Language Support** | Python only | Multi-language |
| **Learning Curve** | Minimal | Substantial |
| **Installation Size** | ~200KB | ~2.5MB |
| **Built-in Scheduling** | No (requires rq-scheduler) | Yes (celery beat) |
| **Priority Queues** | Simple, effective | Requires multiple workers |

### Performance Benchmarks [High Confidence]

**Test Conditions:** 20,000 jobs, 10 workers, MacBook Pro M2 Pro 16GB, Redis broker

| Task Queue | Time to Complete | Tasks/Second |
|------------|------------------|--------------|
| Dramatiq | ~5s | ~4,000 |
| Taskiq | ~5s | ~4,000 |
| Huey | ~6s | ~3,333 |
| Celery (threads) | ~12s | ~1,667 |
| Celery (processes) | ~18s | ~1,111 |
| **RQ** | **~51s** | **~392** |

**Key Finding:** RQ is approximately 4x slower than Celery for high-throughput scenarios.

### Redis Throughput with Celery [High Confidence]

- Redis sustains **7,000+ tasks/second** with 100 parallel workers
- Message acknowledgment: <10ms (Redis) vs up to 40ms (RabbitMQ)
- Redis outperforms RabbitMQ for latency but lacks durability guarantees

### Memory Considerations

**RQ Limitation:** [High Confidence]
- All messages stored in Redis memory
- Redis can fill up and stop accepting writes under heavy load
- One team reported "consistently dealing with RQ breaking because Redis was full"

**Celery Solutions:**
- RabbitMQ broker offloads messages to disk
- `worker_max_tasks_per_child` - restart workers after N tasks
- `worker_max_memory_per_child` - restart workers at memory threshold
- **Issue:** Celery Flower monitoring has memory leak issues

### Operational Complexity

**RQ:** [High Confidence]
```
Simple setup:
1. Install RQ
2. Start Redis
3. Define tasks as functions
4. Start workers
```

**Celery:** [High Confidence]
```
Complex setup:
1. Install Celery + dependencies
2. Configure broker (Redis/RabbitMQ)
3. Configure result backend
4. Define Celery app with settings
5. Define tasks with decorators
6. Configure task routing
7. Start workers with proper concurrency
8. (Optional) Start beat scheduler
9. (Optional) Start Flower monitoring
```

### When to Migrate from RQ to Celery

**Remain on RQ when:** [High Confidence]
- Processing <1,000 tasks/hour
- Tasks are independent (no complex workflows)
- Already using Redis for caching
- Team prefers simplicity over features
- Unix-only deployment acceptable

**Migrate to Celery when:** [High Confidence]
- Processing >10,000 tasks/minute consistently
- Experiencing queue backups / increasing latency
- Need message durability guarantees
- Require periodic task scheduling
- Complex task workflows (chains, groups, chords)
- Multi-language task producers
- Need Windows support

### Scaling Guidelines

| Scale | Recommendation | Notes |
|-------|---------------|-------|
| <100 tasks/hour | RQ | Minimal overhead |
| 100-1,000/hour | RQ | Add workers as needed |
| 1,000-10,000/hour | RQ or Celery | Monitor queue latency |
| >10,000/hour | Celery | RQ will struggle |
| >100,000/hour | Celery + RabbitMQ | Redis memory limits |

### Autoscaling Approaches

**RQ:** Manual horizontal scaling (add more workers)

**Celery Built-in:**
```bash
celery -A app worker --autoscale=10,3  # Scale 3-10 processes
```
*Note: Built-in autoscaling reported as unreliable by some users* [Medium Confidence]

**Kubernetes + KEDA:** [High Confidence]
- Event-driven autoscaling based on queue metrics
- Scale based on `(active_tasks + queue_length) / available_workers`
- Proactive scaling before queue buildup

### Recommendation for PHX Houses

**Current Recommendation: RQ** [High Confidence]

Rationale:
- PHX Houses processes ~50-100 properties at a time
- Each property = ~5-10 tasks (county, listing, map, images, synthesis)
- Total: ~500-1,000 tasks per analysis run
- This is well within RQ's comfortable range

**Migration Trigger Points:**
1. Queue latency consistently >30 seconds
2. Redis memory consistently >80% utilized
3. Need for scheduled recurring analysis
4. Multi-region deployment requirements

---

## Recommendations for PHX Houses Infrastructure

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

## Full Source Citations

### TECH-05: Anti-Bot Sources

1. [ZenRows - How to Bypass PerimeterX](https://www.zenrows.com/blog/perimeterx-bypass) - PerimeterX detection techniques and bypass methods
2. [ScrapFly - How to Bypass PerimeterX](https://scrapfly.io/blog/posts/how-to-bypass-perimeterx-human-anti-scraping) - HUMAN Security technical details
3. [ProxiesAPI - Bypass PerimeterX 2024](https://proxiesapi.com/articles/how-to-bypass-perimeterx-in-2024) - 2024 bypass strategies
4. [ScrapFly - How to Bypass DataDome](https://scrapfly.io/blog/posts/how-to-bypass-datadome-anti-scraping) - DataDome detection methods
5. [Oxylabs - PerimeterX Bypass](https://oxylabs.io/blog/bypass-perimeterx) - Technical bypass analysis
6. [ScrapeOps - Redfin Scraping Overview](https://scrapeops.io/websites/redfin) - Redfin protection measures
7. [WebScraping.AI - Redfin Human Behavior](https://webscraping.ai/faq/redfin-scraping/how-can-i-mimic-human-behavior-to-prevent-detection-while-scraping-redfin) - Behavioral mimicry techniques
8. [GitHub - nodriver](https://github.com/ultrafunkamsterdam/nodriver) - nodriver documentation and features
9. [ZenRows - nodriver Tutorial](https://www.zenrows.com/blog/nodriver) - nodriver usage guide
10. [ZenRows - curl_cffi Tutorial](https://www.zenrows.com/blog/curl-cffi) - curl_cffi documentation
11. [Bright Data - curl_cffi Web Scraping](https://brightdata.com/blog/web-data/web-scraping-with-curl-cffi) - TLS fingerprinting with curl_cffi
12. [Oxylabs - Zillow Request Blocked](https://oxylabs.io/resources/error-codes/zillow-request-blocked-crawler-detected) - Zillow blocking patterns
13. [WebScraping.AI - Zillow Limitations](https://webscraping.ai/faq/zillow-scraping/what-are-the-limitations-of-zillow-scraping) - Zillow scraping challenges
14. [ScrapFly - How to Scrape Zillow](https://scrapfly.io/blog/posts/how-to-scrape-zillow) - Zillow scraping techniques
15. [DataDome - 2024 Bot Security Report](https://www.businesswire.com/news/home/20240917270727/en/DataDome-95-of-Advanced-Bots-Go-Undetected-on-Websites) - 95% of advanced bots undetected
16. [HUMAN Security Merger](https://www.humansecurity.com/human-perimeterx-merger/) - PerimeterX/HUMAN merger details

### TECH-06: Proxy Sources

17. [Bright Data - Residential Proxy Pricing](https://brightdata.com/pricing/proxy-network/residential-proxies) - Official pricing
18. [Proxyway - Bright Data Review](https://proxyway.com/reviews/bright-data-proxies) - Performance tests and analysis
19. [Proxyway - Oxylabs Review](https://proxyway.com/reviews/oxylabs-proxies) - Performance tests and analysis
20. [Geekflare - Oxylabs Review](https://geekflare.com/proxy/oxylabs-review/) - Feature analysis
21. [IPRoyal vs Smartproxy Comparison](https://iproyal.com/blog/iproyal-vs-smartproxy/) - Direct comparison
22. [Proxyway - Best Residential Proxies 2025](https://proxyway.com/best/residential-proxies) - Provider rankings
23. [Decodo/Smartproxy Pricing](https://decodo.com/proxies/residential-proxies/pricing) - Official pricing
24. [Medium - Best Residential Proxy Providers](https://medium.com/@datajournal/best-residential-proxy-providers-in-2024-5af2e8fc77cf) - 2024 comparison
25. [ScraperAPI - Best Proxies for Real Estate](https://www.scraperapi.com/blog/best-proxies-for-real-estate-scraping/) - Real estate-specific recommendations
26. [ProxiesData - Zillow Scrapers 2024](https://proxiesdata.com/web-scraping-tools/zillow/) - Zillow scraping tools
27. [ProxyRack - Best Proxies for Zillow](https://www.proxyrack.com/blog/best-proxies-for-scraping-zillow/) - Zillow proxy recommendations

### TECH-07: Task Queue Sources

28. [Stack Overflow - Celery vs RQ](https://stackoverflow.com/questions/13440875/pros-and-cons-to-use-celery-vs-rq) - Community discussion
29. [Generalist Programmer - Celery vs RQ 2024](https://generalistprogrammer.com/comparisons/celery-vs-rq) - 2024 comparison
30. [Judoscale - Choosing Python Task Queue](https://judoscale.com/blog/choose-python-task-queue) - Decision guide
31. [Frappe - Why We Moved from Celery to RQ](https://frappe.io/blog/technology/why-we-moved-from-celery-to-rq) - Real-world migration
32. [Steven Yue - Task Queue Load Tests](https://stevenyue.com/blogs/exploring-python-task-queue-libraries-with-load-test) - Benchmark data
33. [Medium - Celery vs RQ](https://medium.com/@iamlal/python-celery-vs-python-rq-for-distributed-tasks-processing-20041c346e6) - Distributed processing comparison
34. [MoldStud - Celery Performance Analysis](https://moldstud.com/articles/p-celery-performance-under-load-insights-from-stress-testing) - Stress test insights
35. [Celery Documentation - Optimizing](https://docs.celeryq.dev/en/stable/userguide/optimizing.html) - Official optimization guide
36. [DEV - Scaling Celery in Production](https://dev.to/dhananjayharidas/scaling-celery-based-application-in-production-jak) - Production scaling
37. [Judoscale - Celery Autoscaling](https://judoscale.com/python/celery-autoscaling) - Autoscaling best practices
38. [KEDA Celery Scaler](https://github.com/klippa-app/keda-celery-scaler) - Kubernetes autoscaling
39. [Hacker News Discussion](https://news.ycombinator.com/item?id=12942303) - Community experience moving RQ to Celery

---

*Report generated: December 3, 2024*
*Research methodology: WebSearch with 2024 date targeting, multiple source cross-validation*
*Confidence levels based on source agreement and recency*
