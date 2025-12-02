"""Deal Sheet Generator Package for PHX Home Analysis.

Generates one-page HTML reports for each property with:
- Traffic light kill-switch indicators
- Scoring breakdown by category
- Key metrics and feature highlights
- Master index page with all properties

Usage:
    # As module
    from scripts.deal_sheets import main
    main()

    # Or via CLI
    python -m scripts.deal_sheets

Package Structure:
- templates.py: HTML/CSS templates (Jinja2)
- data_loader.py: CSV/JSON loading utilities
- renderer.py: HTML generation functions
- utils.py: Helper functions (slugify, extract_features)
- generator.py: Main orchestration logic
"""

from .generator import main, generate_deal_sheets

__all__ = ["main", "generate_deal_sheets"]
