---
last_updated: 2025-12-04T18:30:00Z
updated_by: agent
staleness_hours: 168
line_target: 80
flags: []
---
# infrastructure

## Purpose
Cross-cutting infrastructure for stealth extraction: User-Agent rotation, Playwright MCP fallback, and HTTP client utilities supporting the 3-tier fallback chain (nodriver -> curl-cffi -> Playwright).

## Contents
| File | Purpose |
|------|---------|
| `user_agent_pool.py` | Thread-safe UA rotation with 24 signatures (Chrome, Firefox, Safari, Edge) |
| `playwright_mcp.py` | Playwright MCP client wrapper for fallback extraction (3rd tier) |
| `stealth_http_client.py` | curl-cffi HTTP client with TLS fingerprinting (2nd tier) |

## Key Patterns
- **Singleton UA Rotator**: Thread-safe `UserAgentRotator` with Lock for concurrent access
- **MCP Dynamic Imports**: `PlaywrightMcpClient` gracefully degrades if MCP tools unavailable
- **Fallback Chain**: nodriver (primary) -> curl-cffi (TLS fingerprint) -> Playwright MCP (minimal anti-bot)

## Tasks
- [x] Implement thread-safe UA rotation `P:H`
- [x] Create Playwright MCP fallback wrapper `P:H`
- [x] Expand UA pool to 20+ signatures `P:H`
- [ ] Add proxy rotation integration `P:M`
- [ ] Add metrics/telemetry for fallback cascade `P:L`

## Learnings
- **24 UAs required**: Minimum 20 for anti-fingerprinting, covering Chrome/Firefox/Safari/Edge on Windows/macOS/Linux/iOS/Android
- **MCP dynamic imports**: Use `importlib` for MCP tools to avoid hard dependency on MCP server availability
- **TLS fingerprinting**: curl-cffi with `impersonate="chrome120"` matches real Chrome TLS handshake

## Refs
- UA pool: `user_agent_pool.py:1-176`
- MCP client: `playwright_mcp.py:1-305`
- Stealth HTTP: `stealth_http_client.py:52-339`
- UA config: `config/user_agents.txt` (24 signatures)

## Deps
<- imports: `asyncio`, `threading`, `curl_cffi`, MCP tools (optional)
-> used by: `services/image_extraction/extractors/`, `scripts/extract_images.py`
