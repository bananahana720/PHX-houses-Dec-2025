# CRITICAL Issues (Must Fix Immediately)

### CRIT-001: API Token Committed to Repository

**File:** `.env:6`
**Severity:** CRITICAL
**CVSS Score:** 9.8 (Critical)

```python
# .env (line 6)
MARICOPA_ASSESSOR_TOKEN=0fb33394-8cdb-4ddd-b7bb-ab1e005c2c29
```

**Issue:**
The `.env` file containing production API tokens and proxy credentials is committed to the repository. This file should NEVER be in version control.

**Impact:**
- Exposed API token allows unauthorized access to Maricopa County Assessor API
- Exposed proxy credentials (`PROXY_USERNAME`, `PROXY_PASSWORD`) enable abuse of paid proxy service
- Potential rate limit exhaustion, data exfiltration, service abuse
- Financial liability for proxy usage

**Evidence:**
```bash
# File is tracked in git
git ls-files .env
# Returns: .env

# Contains sensitive credentials
MARICOPA_ASSESSOR_TOKEN=0fb33394-8cdb-4ddd-b7bb-ab1e005c2c29
PROXY_PASSWORD=g2j2p2cv602u
```

**Remediation:**
```bash
# 1. Remove from git history (IMMEDIATELY)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# 2. Force push to remote (coordinate with team)
git push origin --force --all

# 3. Rotate compromised credentials
# - Request new MARICOPA_ASSESSOR_TOKEN from county
# - Reset Webshare proxy password

# 4. Verify .gitignore contains .env
echo ".env" >> .gitignore

# 5. Create template only
cat > .env.example <<EOF
MARICOPA_ASSESSOR_TOKEN=your_token_here
PROXY_SERVER=your_proxy_server
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
EOF
```

**Prevention:**
- Add pre-commit hook to block .env files
- Use git-secrets or similar tools
- Regular secret scanning with TruffleHog or GitGuardian
- Store secrets in secure vaults (HashiCorp Vault, AWS Secrets Manager)

---
