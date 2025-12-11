"""Reporting layer for PHX Home Analysis.

This module provides report generation capabilities for property analysis results.
Supports multiple output formats: HTML, CSV, console, and deal sheets.

Reporters:
    - ConsoleReporter: Terminal output with ANSI colors
    - CsvReporter: CSV export for spreadsheet analysis
    - RiskCsvReporter: Risk-focused CSV export
    - HtmlReportGenerator: Web-ready HTML reports
    - DealSheetReporter: Comprehensive deal sheet generation (E7 stub)

Utilities:
    - ScoringFormatter: Score display formatting utilities
    - TierDisplayInfo: Tier badge styling information
"""

from .base import Reporter
from .console_reporter import ConsoleReporter
from .csv_reporter import CsvReporter, RiskCsvReporter
from .deal_sheet_reporter import DealSheetReporter
from .html_reporter import HtmlReportGenerator
from .scoring_formatter import ScoringFormatter, TierDisplayInfo

__all__ = [
    # Base interface
    "Reporter",
    # Concrete reporters
    "ConsoleReporter",
    "CsvReporter",
    "RiskCsvReporter",
    "HtmlReportGenerator",
    "DealSheetReporter",
    # Utilities
    "ScoringFormatter",
    "TierDisplayInfo",
]
