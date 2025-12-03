# Chrome Proxy Extension - Quick Reference

## TL;DR

Chrome extension for proxy authentication with nodriver. Automatically created and cleaned up by BrowserPool.

## Usage

### Automatic (Recommended)

```python
from phx_home_analysis.services.infrastructure import BrowserPool

# With authentication - extension auto-created
proxy_url = "http://user:pass@p.webshare.io:80"

async with BrowserPool(proxy_url=proxy_url, headless=True) as pool:
    browser = await pool.get_browser()
    tab = await pool.new_tab("https://example.com")
    # Extension handles auth automatically
```

### Manual

```python
from phx_home_analysis.services.infrastructure import ProxyExtensionBuilder

# Create extension
builder = ProxyExtensionBuilder.from_url("http://user:pass@proxy:80")
ext_path = builder.create_extension()

# Use with Chrome: --load-extension={ext_path}

# Cleanup
builder.cleanup()
```

## Environment Setup

**.env:**
```bash
PROXY_SERVER=p.webshare.io:80
PROXY_USERNAME=svcvoqpm-US-rotate
PROXY_PASSWORD=g2j2p2cv602u
```

**Code:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

proxy_url = (
    f"http://{os.getenv('PROXY_USERNAME')}:"
    f"{os.getenv('PROXY_PASSWORD')}@"
    f"{os.getenv('PROXY_SERVER')}"
)
```

## Files

```
src/phx_home_analysis/services/infrastructure/
├── proxy_extension/
│   ├── manifest.json         # Extension manifest
│   └── background.js         # Auth handler (template)
├── proxy_extension_builder.py  # Builder class
└── browser_pool.py           # Auto-integration
```

## How It Works

1. BrowserPool detects `@` in proxy URL → authenticated proxy
2. Creates ProxyExtensionBuilder from URL
3. Extension generated in temp directory
4. Chrome loads extension with `--load-extension`
5. Extension configures proxy + handles auth requests
6. Cleanup on close removes temp files

## ProxyExtensionBuilder API

```python
# Constructor
builder = ProxyExtensionBuilder(host, port, username, password)

# From URL
builder = ProxyExtensionBuilder.from_url("http://user:pass@host:port")

# Create extension
ext_path = builder.create_extension()  # Returns Path

# Cleanup
builder.cleanup()  # Removes temp directory

# Config access
builder.config.host      # str
builder.config.port      # int
builder.config.username  # str
builder.config.password  # str
```

## BrowserPool Changes

### New Attributes

```python
pool._proxy_extension       # ProxyExtensionBuilder | None
pool._proxy_has_auth        # bool
```

### Detection Logic

```python
# Automatic auth detection in __init__
self._proxy_has_auth = bool(
    proxy_url and "@" in proxy_url and "://" in proxy_url
)
```

### Extension Lifecycle

```python
# In get_browser()
if proxy_url and _proxy_has_auth:
    self._proxy_extension = ProxyExtensionBuilder.from_url(proxy_url)
    ext_path = self._proxy_extension.create_extension()
    config.add_argument(f"--load-extension={ext_path}")
    config.add_argument(f"--disable-extensions-except={ext_path}")

# In close()
if self._proxy_extension:
    self._proxy_extension.cleanup()
    self._proxy_extension = None
```

## Error Handling

```python
# Invalid URL
try:
    builder = ProxyExtensionBuilder.from_url("invalid")
except ValueError as e:
    # "Invalid proxy URL format..."

# Missing credentials
try:
    builder = ProxyExtensionBuilder.from_url("http://proxy:80")
except ValueError as e:
    # "Proxy URL must include credentials..."

# Double create
builder.create_extension()
try:
    builder.create_extension()  # Error!
except RuntimeError as e:
    # "Extension already created. Call cleanup()..."

# Missing templates
try:
    builder.create_extension()
except FileNotFoundError as e:
    # "Template directory not found..." or
    # "Template manifest not found..."
```

## Testing

```bash
# Quick test
python -c "
import sys
sys.path.insert(0, 'src')
import importlib.util
spec = importlib.util.spec_from_file_location(
    'proxy_extension_builder',
    'src/phx_home_analysis/services/infrastructure/proxy_extension_builder.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

builder = module.ProxyExtensionBuilder.from_url('http://user:pass@proxy:80')
ext_path = builder.create_extension()
print(f'Extension: {ext_path}')
builder.cleanup()
print('SUCCESS!')
"
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs will show:
# - Extension creation path
# - Chrome arguments added
# - Cleanup operations
```

### Check Generated Files

```python
builder = ProxyExtensionBuilder.from_url(proxy_url)
ext_path = builder.create_extension()

# Inspect files
print((ext_path / "manifest.json").read_text())
print((ext_path / "background.js").read_text())

# Verify substitutions
bg = (ext_path / "background.js").read_text()
assert "PROXY_HOST" not in bg, "Placeholder not replaced!"
```

### Verify Chrome Extension

Non-headless mode:
1. Navigate to `chrome://extensions`
2. Enable "Developer mode"
3. Find "Proxy Auth Helper"
4. Click "service worker" to view console
5. Look for: "Proxy Auth Helper loaded - proxy configured for ..."

## Proxy Types

### With Authentication (Extension)

```python
# Extension auto-created
proxy_url = "http://user:pass@host:port"
```

### Without Authentication (Standard)

```python
# Standard --proxy-server flag
proxy_url = "http://host:port"
```

## Security Notes

- Credentials written to temp file (OS default permissions)
- Cleaned up on close
- Use environment variables (never hardcode)
- Always use context manager for auto-cleanup
- Orphaned extensions: check temp dir for `proxy_ext_*`

## Common Patterns

### From Environment

```python
import os
from dotenv import load_dotenv

load_dotenv()

proxy_url = f"http://{os.getenv('PROXY_USERNAME')}:{os.getenv('PROXY_PASSWORD')}@{os.getenv('PROXY_SERVER')}"

async with BrowserPool(proxy_url=proxy_url) as pool:
    # ...
```

### Manual Cleanup

```python
pool = BrowserPool(proxy_url=proxy_url)
try:
    browser = await pool.get_browser()
    # ...
finally:
    await pool.close()  # Ensures extension cleanup
```

### Multiple Sessions

```python
# Each session gets new extension
for url in urls:
    async with BrowserPool(proxy_url=proxy_url) as pool:
        browser = await pool.get_browser()
        # Extension created
    # Extension cleaned up
```

## Documentation

- **Full Documentation**: `docs/proxy_extension_setup.md`
- **Implementation Summary**: `PROXY_EXTENSION_IMPLEMENTATION.md`
- **Examples**: `examples/proxy_browser_example.py`

## Status

- **Version**: 1.0.0
- **Status**: Production-ready
- **Tested**: Extension builder, URL parsing, BrowserPool integration
- **Date**: 2025-11-30
