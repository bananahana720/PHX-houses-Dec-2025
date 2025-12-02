"""Pipeline orchestration for PHX Home Analysis.

This module provides the complete pipeline orchestrator that coordinates data
loading, enrichment, filtering, scoring, and output generation.

Usage:
    from phx_home_analysis.pipeline import AnalysisPipeline, PipelineResult

    # Run complete analysis
    pipeline = AnalysisPipeline()
    result = pipeline.run()
    print(result.summary_text())

    # Analyze single property
    property = pipeline.analyze_single("123 Main St, Phoenix, AZ 85001")
"""

from .orchestrator import AnalysisPipeline, PipelineResult

__all__ = [
    "AnalysisPipeline",
    "PipelineResult",
]
