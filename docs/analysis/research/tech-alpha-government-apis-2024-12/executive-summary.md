# Executive Summary

This report provides technical research findings on government APIs relevant to the PHX Houses Analysis Pipeline project. The research covers two primary areas:

1. **Maricopa County Permit Data** - No direct permit API exists. The county uses the Accela-based Permit Center system (launched June 2024) with web portal access only. However, the **Maricopa County Assessor API** provides excellent property data access with a Python wrapper available.

2. **FEMA National Flood Hazard Layer (NFHL)** - Free, no-authentication REST API access available through ArcGIS services at `hazards.fema.gov`. Direct coordinate-based queries return flood zone designations in JSON format.

**Key Recommendation:** Integrate FEMA NFHL API for flood zone lookup (free, no auth required). For permits, use web scraping or public records requests as no API is available.

---
