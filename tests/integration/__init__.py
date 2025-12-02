"""Integration tests for PHX Home Analysis pipeline.

This package contains integration tests that validate the complete pipeline
from CSV input through enrichment, kill-switch filtering, scoring, and output.

Test modules:
- test_pipeline: End-to-end pipeline validation
- test_kill_switch_chain: Kill-switch severity accumulation and thresholds
- test_deal_sheets: Deal sheet generation and HTML output

Each test uses fixtures from tests/conftest.py and validates the interaction
of multiple components working together.
"""
