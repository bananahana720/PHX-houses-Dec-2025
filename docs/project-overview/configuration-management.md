# Configuration Management

### Centralized Constants
All magic numbers live in `src/phx_home_analysis/config/constants.py`:
- Scoring thresholds and tier boundaries
- Kill-switch severity weights
- Confidence/quality thresholds
- Cost estimation rates (Arizona-specific)
- Arizona constants (HVAC lifespan, pool costs, etc.)
- Image processing settings
- Stealth extraction parameters

### Environment Variables
```bash
# Required for Phase 0
MARICOPA_ASSESSOR_TOKEN=<token>

# Optional for proxy support
PROXY_SERVER=host:port
PROXY_USERNAME=username
PROXY_PASSWORD=password

# Browser automation
BROWSER_HEADLESS=true  # or false
BROWSER_ISOLATION=virtual_display  # or secondary_display, off_screen, minimize, none
```
