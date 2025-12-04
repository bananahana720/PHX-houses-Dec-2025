# Getting Started

### Installation
```bash
# Clone repository
cd PHX-houses-Dec-2025

# Install dependencies (using uv)
uv sync

# Set environment variables
export MARICOPA_ASSESSOR_TOKEN=<token>
```

### Basic Usage
```bash
# Run main analysis pipeline
python scripts/phx_home_analyzer.py

# Extract county data for all properties
python scripts/extract_county_data.py --all

# Extract images from listing sites
python scripts/extract_images.py --all

# Generate deal sheets
python -m scripts.deal_sheets

# Multi-agent analysis (orchestrated)
/analyze-property --all
```

### Adding New Properties
1. Add listing to `data/phx_homes.csv`
2. Run county data extraction: `python scripts/extract_county_data.py --address "123 Main St"`
3. Run image extraction: `python scripts/extract_images.py --address "123 Main St"`
4. Run multi-agent analysis: `/analyze-property "123 Main St"`
