---
name: block-secrets-commit
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: (API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)\s*=\s*['""][^'"]+['"]|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}
action: block
---

## 🛑 Secret/Credential Detected - Do Not Commit!

**Security violation per CLAUDE.md:92**

### Detected Pattern
You're writing code that appears to contain:
- Hardcoded API keys
- Secret tokens
- Passwords
- Credentials

### ❌ Never Do This
```python
API_KEY = "sk-abc123..."       # BLOCKED
GITHUB_TOKEN = "ghp_xyz..."    # BLOCKED
DB_PASSWORD = "my-password"    # BLOCKED
```

### ✅ Correct Approach
```python
import os

API_KEY = os.environ["API_KEY"]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
```

### For This Project
Use `.env` file (gitignored):
```bash
# .env (NEVER commit this file)
MARICOPA_ASSESSOR_TOKEN=your-token
GOOGLE_MAPS_API_KEY=your-key
```

Then access via:
```python
from phx_home_analysis.config import settings
token = settings.MARICOPA_ASSESSOR_TOKEN
```

### Remediation
1. Remove the secret from code
2. Add to `.env` file
3. Use environment variable access
4. If accidentally committed: rotate the credential immediately
