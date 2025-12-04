"""Live tests for external API validation.

These tests call real APIs and are excluded from default pytest runs.
Run with: pytest tests/live/ -m live -v

Required environment:
    MARICOPA_ASSESSOR_TOKEN - County Assessor API token

See tests/live/README.md for full documentation.
"""
