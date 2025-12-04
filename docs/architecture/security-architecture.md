# Security Architecture

### Credential Management

**Environment Variables (.env):**

```bash
# API Keys - NEVER commit to Git
MARICOPA_ASSESSOR_TOKEN=<secret>
GOOGLE_MAPS_API_KEY=<secret>
WALKSCORE_API_KEY=<secret>
AIRNOW_API_KEY=<secret>

# Proxy Configuration
PROXY_SERVER=host:port
PROXY_USERNAME=<secret>
PROXY_PASSWORD=<secret>

# Claude API
ANTHROPIC_API_KEY=<secret>
```

**Security Rules:**
1. `.env` file is gitignored
2. No credentials in code or comments
3. Pre-commit hook scans for leaked secrets
4. Rotate tokens if exposed

### Pre-Commit Hook Protection

```python
# .claude/hooks/env_file_protection_hook.py
"""Block commits containing API keys or credentials."""

import re
import sys

PATTERNS = [
    r'(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
    r'sk-[a-zA-Z0-9]{32,}',  # OpenAI/Anthropic keys
    r'[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}',  # JWT
]

def check_diff(diff_text: str) -> list[str]:
    violations = []
    for pattern in PATTERNS:
        if re.search(pattern, diff_text):
            violations.append(pattern)
    return violations
```

---
