# Quick Start

### Prerequisites
- Python 3.11 or higher
- Git
- Chrome/Chromium browser (for stealth automation)
- Maricopa County Assessor API token
- (Optional) Virtual display for browser isolation

### Installation

```bash
# Clone repository
cd PHX-houses-Dec-2025

# Install dependencies using uv
uv sync

# Install development dependencies
uv sync --group dev

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
export MARICOPA_ASSESSOR_TOKEN=<your-token>
```

### Running the System

```bash
# Main analysis pipeline
python scripts/phx_home_analyzer.py

# County data extraction (Phase 0)
python scripts/extract_county_data.py --all

# Image extraction (Phase 1)
python scripts/extract_images.py --all

# Generate deal sheets
python -m scripts.deal_sheets

# Multi-agent orchestrated analysis
/analyze-property --all
```

---
