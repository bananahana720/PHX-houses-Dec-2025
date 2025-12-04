# API Specification Tables

### FEMA NFHL REST API

| Specification | Value |
|---------------|-------|
| Base URL | `https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query` |
| Protocol | HTTPS (TLS 1.2 required) |
| Method | GET |
| Authentication | None |
| Response Format | JSON only |
| Max Records | 2,000 per request |
| Rate Limit | Not documented |

### Maricopa County Assessor API

| Specification | Value |
|---------------|-------|
| Base URL | `https://api.mcassessor.maricopa.gov/` |
| Protocol | HTTPS |
| Method | GET |
| Authentication | API Key (header: `Authorization: Token <key>`) |
| Response Format | JSON |
| Python Package | `mcaapi` |
| Documentation | https://mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf |

### Accela Construct API (If Maricopa Enables)

| Specification | Value |
|---------------|-------|
| Base URL | `https://apis.accela.com` |
| Protocol | HTTPS |
| Method | REST (GET, POST, PUT, DELETE) |
| Authentication | OAuth 2.0 |
| Documentation | https://developer.accela.com/docs/api_reference/api-index.html |

**Note:** Maricopa County's Accela implementation may not have API access enabled for public use.

---
