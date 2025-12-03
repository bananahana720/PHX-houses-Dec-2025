"""CLI entry point for deal_sheets package.

Allows running the package as:
    python -m scripts.deal_sheets
"""

from .generator import main

if __name__ == '__main__':
    main()
