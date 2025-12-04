"""Pipeline orchestration for PHX Home Analysis.

This module provides pipeline orchestrators that coordinate data loading,
enrichment, filtering, scoring, multi-phase execution, and output generation.

Usage:
    # Data pipeline (scoring and filtering)
    from phx_home_analysis.pipeline import AnalysisPipeline, PipelineResult

    pipeline = AnalysisPipeline()
    result = pipeline.run()
    print(result.summary_text())

    # Multi-phase pipeline (agent orchestration)
    from phx_home_analysis.pipeline import PhaseCoordinator, ProgressReporter

    reporter = ProgressReporter()
    coordinator = PhaseCoordinator(progress_reporter=reporter)
    await coordinator.execute_pipeline(properties=["123 Main St, Phoenix, AZ 85001"])
"""

from .orchestrator import AnalysisPipeline, PipelineResult
from .phase_coordinator import Phase, PhaseCoordinator, PhaseResult, PropertyState
from .progress import PipelineStats, ProgressReporter

__all__ = [
    # Data pipeline
    "AnalysisPipeline",
    "PipelineResult",
    # Multi-phase pipeline
    "PhaseCoordinator",
    "Phase",
    "PhaseResult",
    "PropertyState",
    # Progress reporting
    "ProgressReporter",
    "PipelineStats",
]
