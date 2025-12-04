# TECH-01: Maricopa County Permit API Access

### Overview

**Confidence Level: [High]**

Maricopa County does NOT provide a direct API for building permit data. The county launched its new online "Permit Center" system in June 2024, consolidating multiple department systems into a single Accela-based platform.

### Permit Center System (June 2024)

**Confidence Level: [High]**

The Maricopa County Permit Center is an Accela-based system serving multiple departments:

| Department | Code | Permit Types |
|------------|------|--------------|
| Environmental Services | ENV | Environmental permits |
| Planning & Development | PND | Building, mechanical, electrical, plumbing |
| Flood Control District | FCD | Drainage, flood-related |
| Transportation | MCDOT | Right-of-way, road work |

**Key URLs:**
- Permit Center: https://www.maricopa.gov/6003/Maricopa-Countys-Permit-Center
- Historical Permits (1999-June 2024): https://apps.pnd.maricopa.gov/PermitViewer
- Accela Citizen Access: https://accela.maricopa.gov/CitizenAccessMCOSS/

### Permit Types for HVAC/Roof Determination

**Confidence Level: [Medium]**

Arizona building code requires permits for:
- **Mechanical Permits**: HVAC system installation, replacement, or repair
- **Roofing Permits**: Roof replacement (typically required for re-roofing)
- **Building Permits**: Major structural work

Permit records typically include:
- Permit type (Building, Mechanical, Plumbing, Electrical)
- Issue date and expiration date
- Contractor name and license number
- Work description
- Property address/parcel number
- Inspection status

**Limitation:** Without API access, determining HVAC/roof replacement dates requires manual permit search or public records requests.

### Alternative: Maricopa County Assessor API

**Confidence Level: [High]**

While no permit API exists, the **Maricopa County Assessor** provides a robust property data API:

| Feature | Details |
|---------|---------|
| Authentication | API key required (free, request via contact form) |
| Python Wrapper | `mcaapi` package on PyPI |
| Data Available | Parcel details, ownership, valuations, physical features, zoning |
| Documentation | https://mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf |

**API Request Process:**
1. Visit https://preview.mcassessor.maricopa.gov/contact/
2. Set Subject to "API Token/Question"
3. Provide name, number, and brief note
4. Receive API key via email

### City of Phoenix Permits (Alternative)

**Confidence Level: [Medium]**

For properties within Phoenix city limits (not unincorporated Maricopa County):

| Resource | URL | Access Type |
|----------|-----|-------------|
| PDD Online Permit Search | https://apps-secure.phoenix.gov/pdd/search/permits | Web portal |
| Issued Permits Search | https://apps-secure.phoenix.gov/PDD/Search/IssuedPermit | Web portal + CSV export |
| Phoenix Open Data | https://www.phoenixopendata.com | CKAN API (limited permit data) |

**Note:** Phoenix Open Data includes building permit datasets from the HUD SOCDS database, but these are aggregate statistics, not individual permit records.

### Data Access Options Summary

| Method | Data Freshness | Automation | Cost |
|--------|---------------|------------|------|
| Permit Center Web Portal | Real-time | Manual only | Free |
| Historical Permit Viewer | 1999-2024 | Manual only | Free |
| Public Records Request | Varies | Batch requests | Free |
| Accela API (if enabled) | Real-time | Full automation | Unknown |
| Web Scraping | Real-time | Semi-automated | Free (legal concerns) |

---
