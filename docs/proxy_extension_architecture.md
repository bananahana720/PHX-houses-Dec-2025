# Proxy Extension Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         BrowserPool                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ __init__(proxy_url="http://user:pass@host:port")          │ │
│  │   - Parse proxy_url                                        │ │
│  │   - Set _proxy_has_auth = True (if @ in URL)              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ get_browser()                                              │ │
│  │   if _proxy_has_auth:                                      │ │
│  │     ┌─────────────────────────────────────────────┐       │ │
│  │     │ ProxyExtensionBuilder.from_url(proxy_url)  │       │ │
│  │     │   - Parse host, port, username, password   │       │ │
│  │     │   - Create temp directory                   │       │ │
│  │     │   - Copy manifest.json                      │       │ │
│  │     │   - Generate background.js with creds       │       │ │
│  │     │   - Return extension path                   │       │ │
│  │     └─────────────────────────────────────────────┘       │ │
│  │     - Add Chrome args:                                     │ │
│  │       --load-extension={path}                              │ │
│  │       --disable-extensions-except={path}                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ close()                                                    │ │
│  │   - Stop browser                                           │ │
│  │   - Cleanup extension (remove temp directory)              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

```
project/
├── src/phx_home_analysis/services/infrastructure/
│   ├── __init__.py
│   │   └── exports: BrowserPool, ProxyExtensionBuilder
│   ├── browser_pool.py
│   │   └── class BrowserPool:
│   │       ├── __init__()      # Detect auth
│   │       ├── get_browser()   # Create extension
│   │       └── close()         # Cleanup extension
│   ├── proxy_extension_builder.py
│   │   └── class ProxyExtensionBuilder:
│   │       ├── __init__(host, port, username, password)
│   │       ├── from_url(proxy_url) → ProxyExtensionBuilder
│   │       ├── create_extension() → Path
│   │       └── cleanup()
│   └── proxy_extension/                    # Template directory
│       ├── manifest.json                   # Extension manifest
│       └── background.js                   # Template with placeholders
│
├── docs/
│   ├── proxy_extension_setup.md           # Full documentation
│   ├── proxy_extension_quick_reference.md # Quick reference
│   └── proxy_extension_architecture.md    # This file
│
├── examples/
│   └── proxy_browser_example.py           # Usage examples
│
└── PROXY_EXTENSION_IMPLEMENTATION.md      # Implementation summary
```

## Data Flow

### Extension Creation

```
1. User creates BrowserPool
   │
   ├─→ proxy_url = "http://user:pass@p.webshare.io:80"
   │
   └─→ BrowserPool.__init__()
       ├─→ Detect "@" in URL
       └─→ Set _proxy_has_auth = True

2. User calls get_browser()
   │
   └─→ BrowserPool.get_browser()
       ├─→ if _proxy_has_auth:
       │   │
       │   └─→ ProxyExtensionBuilder.from_url(proxy_url)
       │       ├─→ Parse: "user:pass@host:port"
       │       │   ├─→ host = "p.webshare.io"
       │       │   ├─→ port = 80
       │       │   ├─→ username = "user"
       │       │   └─→ password = "pass"
       │       │
       │       └─→ create_extension()
       │           ├─→ Create temp dir: /tmp/proxy_ext_xyz123/
       │           ├─→ Copy manifest.json
       │           ├─→ Read background.js template
       │           ├─→ Replace placeholders:
       │           │   ├─→ "PROXY_HOST" → "p.webshare.io"
       │           │   ├─→ PROXY_PORT → 80
       │           │   ├─→ "PROXY_USERNAME" → "user"
       │           │   └─→ "PROXY_PASSWORD" → "pass"
       │           ├─→ Write background.js
       │           └─→ Return Path(/tmp/proxy_ext_xyz123/)
       │
       └─→ Add Chrome args:
           ├─→ --load-extension=/tmp/proxy_ext_xyz123/
           └─→ --disable-extensions-except=/tmp/proxy_ext_xyz123/

3. Chrome starts with extension
   │
   └─→ Extension loads
       ├─→ Read background.js
       ├─→ Execute service worker
       ├─→ Configure proxy: p.webshare.io:80
       └─→ Listen for auth requests

4. Browser navigates to URL
   │
   └─→ Chrome makes proxy request
       ├─→ Proxy requires authentication
       ├─→ Extension handles auth automatically
       │   └─→ Returns: {username: "user", password: "pass"}
       └─→ Request succeeds

5. User closes browser
   │
   └─→ BrowserPool.close()
       ├─→ Stop browser
       └─→ Cleanup extension
           └─→ Remove /tmp/proxy_ext_xyz123/
```

## Template Substitution

### Input Template (background.js)

```javascript
const config = {
    host: "PROXY_HOST",
    port: PROXY_PORT,
    username: "PROXY_USERNAME",
    password: "PROXY_PASSWORD"
};
```

### After Substitution

```javascript
const config = {
    host: "p.webshare.io",
    port: 80,
    username: "svcvoqpm-US-rotate",
    password: "g2j2p2cv602u"
};
```

### Replacement Logic

```python
# Read template
template = read("background.js")

# Replace placeholders (including quotes in template)
content = template.replace('"PROXY_HOST"', f'"{host}"')
content = content.replace('PROXY_PORT', str(port))
content = content.replace('"PROXY_USERNAME"', f'"{username}"')
content = content.replace('"PROXY_PASSWORD"', f'"{password}"')

# Write configured file
write("background.js", content)
```

## Chrome Extension Flow

```
Chrome Browser
├── Extension: "Proxy Auth Helper"
│   ├── Manifest V3
│   ├── Permissions: proxy, webRequest, webRequestAuthProvider
│   └── Service Worker (background.js)
│       │
│       ├─→ On Load:
│       │   └─→ chrome.proxy.settings.set()
│       │       └─→ Configure: http://p.webshare.io:80
│       │
│       └─→ On Auth Request:
│           └─→ chrome.webRequest.onAuthRequired
│               └─→ Return credentials: {user, pass}
│
└── Page Navigation
    ├─→ Request via proxy
    ├─→ Proxy requires auth
    ├─→ Extension provides credentials
    └─→ Request succeeds
```

## Proxy Detection Logic

```python
def detect_proxy_auth(proxy_url: str) -> bool:
    """Detect if proxy URL contains authentication."""

    # Example URLs:
    # "http://user:pass@host:port"  → True (has auth)
    # "http://host:port"            → False (no auth)
    # "socks5://user:pass@host:port" → True (has auth)

    return bool(
        proxy_url and          # URL exists
        "@" in proxy_url and   # Has @ separator
        "://" in proxy_url     # Has scheme
    )

# Usage:
proxy_url = "http://user:pass@p.webshare.io:80"
has_auth = detect_proxy_auth(proxy_url)  # True

if has_auth:
    # Create extension
    builder = ProxyExtensionBuilder.from_url(proxy_url)
    ext_path = builder.create_extension()
else:
    # Use standard proxy flag
    chrome_args = [f"--proxy-server={proxy_url}"]
```

## State Management

### BrowserPool States

```
State 1: Initialized
├─→ _browser = None
├─→ _proxy_extension = None
└─→ _proxy_has_auth = bool (determined in __init__)

State 2: Browser Created (with auth)
├─→ _browser = Browser instance
├─→ _proxy_extension = ProxyExtensionBuilder instance
│   └─→ extension_dir = Path(/tmp/proxy_ext_xyz/)
└─→ _proxy_has_auth = True

State 3: Browser Created (no auth)
├─→ _browser = Browser instance
├─→ _proxy_extension = None
└─→ _proxy_has_auth = False

State 4: Closed
├─→ _browser = None
├─→ _proxy_extension = None
└─→ _proxy_has_auth = bool (unchanged)
```

### ProxyExtensionBuilder States

```
State 1: Initialized
├─→ config = ProxyConfig(host, port, username, password)
└─→ extension_dir = None

State 2: Extension Created
├─→ config = ProxyConfig (unchanged)
└─→ extension_dir = Path(/tmp/proxy_ext_xyz/)

State 3: Cleaned Up
├─→ config = ProxyConfig (unchanged)
└─→ extension_dir = None
```

## Error Paths

```
Error Path 1: Invalid Proxy URL
├─→ BrowserPool.__init__(proxy_url="invalid")
└─→ get_browser()
    └─→ ProxyExtensionBuilder.from_url("invalid")
        └─→ ValueError: "Invalid proxy URL format"

Error Path 2: Missing Credentials
├─→ BrowserPool.__init__(proxy_url="http://host:port")
└─→ get_browser()
    └─→ ProxyExtensionBuilder.from_url("http://host:port")
        └─→ ValueError: "Proxy URL must include credentials"

Error Path 3: Missing Template
├─→ get_browser()
└─→ create_extension()
    └─→ FileNotFoundError: "Template directory not found"

Error Path 4: Double Create
├─→ create_extension()  # Success
└─→ create_extension()  # Error!
    └─→ RuntimeError: "Extension already created"
```

## Performance Considerations

### Extension Creation

```
Operation                          Time
────────────────────────────────────────
Create temp directory              <1ms
Copy manifest.json                 <1ms
Read background.js template        <1ms
String substitution (4 replaces)   <1ms
Write background.js                <1ms
────────────────────────────────────────
Total                              ~5ms
```

### Cleanup

```
Operation                          Time
────────────────────────────────────────
Remove temp directory              <10ms
────────────────────────────────────────
Total                              ~10ms
```

### Memory

```
Component                          Size
────────────────────────────────────────
ProxyExtensionBuilder instance     <1KB
manifest.json                      ~300B
background.js (template)           ~1KB
background.js (generated)          ~1KB
────────────────────────────────────────
Total                              ~3KB
```

## Security Model

```
Credentials Flow:
1. User provides proxy_url with credentials
   │
   ├─→ Stored in memory (BrowserPool.proxy_url)
   │
   └─→ Parsed by ProxyExtensionBuilder
       ├─→ Stored in memory (ProxyConfig)
       │
       └─→ Written to temp file (background.js)
           ├─→ File permissions: User-only (OS default)
           ├─→ Location: OS temp directory
           ├─→ Duration: Until cleanup()
           └─→ Cleanup: On BrowserPool.close()

Risk Mitigation:
- Use environment variables for credentials
- Temp file auto-cleaned on close
- Context manager ensures cleanup
- OS-level file permissions
```

## Integration Points

### With BrowserPool

```python
# BrowserPool uses ProxyExtensionBuilder internally
async with BrowserPool(proxy_url=auth_proxy) as pool:
    browser = await pool.get_browser()
    # Extension created and loaded automatically
```

### With nodriver

```python
# Extension path passed to nodriver config
config = uc.Config()
config.add_argument(f"--load-extension={extension_path}")
config.add_argument(f"--disable-extensions-except={extension_path}")
browser = await uc.start(config=config)
```

### With Chrome

```bash
# Chrome launched with extension
chrome \
  --load-extension=/tmp/proxy_ext_xyz123/ \
  --disable-extensions-except=/tmp/proxy_ext_xyz123/
```

## Future Enhancements

### Proxy Rotation

```python
class ProxyRotator:
    def __init__(self, proxy_urls: list[str]):
        self.builders = [
            ProxyExtensionBuilder.from_url(url)
            for url in proxy_urls
        ]

    def get_next(self) -> Path:
        builder = next(self.builders)
        return builder.create_extension()
```

### Extension Caching

```python
class CachedExtensionBuilder:
    _cache: dict[str, Path] = {}

    def get_or_create(self, proxy_url: str) -> Path:
        if proxy_url in self._cache:
            return self._cache[proxy_url]

        builder = ProxyExtensionBuilder.from_url(proxy_url)
        path = builder.create_extension()
        self._cache[proxy_url] = path
        return path
```

### SOCKS5 Support

```javascript
// In background.js template
const config = {
    scheme: "PROXY_SCHEME",  // "http" or "socks5"
    host: "PROXY_HOST",
    port: PROXY_PORT,
    // ...
};

chrome.proxy.settings.set({
    value: {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: config.scheme,
                host: config.host,
                port: config.port
            }
        }
    }
});
```

---

**Architecture Version**: 1.0.0
**Last Updated**: 2025-11-30
**Status**: Production-ready
