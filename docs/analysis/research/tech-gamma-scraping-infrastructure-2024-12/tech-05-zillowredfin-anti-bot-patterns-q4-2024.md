# TECH-05: Zillow/Redfin Anti-Bot Patterns (Q4 2024)

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
