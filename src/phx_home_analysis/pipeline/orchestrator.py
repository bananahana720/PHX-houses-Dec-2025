"""Pipeline orchestrator for PHX Home Analysis.

This module provides the main AnalysisPipeline class that coordinates the complete
home analysis workflow from data loading through scoring and output generation.

The pipeline executes these stages:
1. Load properties from CSV
2. Load enrichment data from JSON
3. Merge enrichment into properties
4. Apply kill-switch filters
5. Score passing properties
6. Classify tiers
7. Sort by score (descending)
8. Save ranked results
9. Return summary statistics

Usage:
    from phx_home_analysis.pipeline import AnalysisPipeline

    # Run with defaults
    pipeline = AnalysisPipeline()
    result = pipeline.run()
    print(f"Found {len(result.unicorns)} unicorns!")

    # Run with custom config
    config = AppConfig.default(base_dir="/path/to/project")
    pipeline = AnalysisPipeline(config=config)
    result = pipeline.run()
"""

import logging
import time
from dataclasses import dataclass, field

from ..config import AppConfig
from ..domain import Property
from ..repositories import (
    CsvPropertyRepository,
    EnrichmentRepository,
    JsonEnrichmentRepository,
    PropertyRepository,
)
from ..services.analysis import PropertyAnalyzer
from ..services.classification import TierClassifier
from ..services.enrichment import EnrichmentMerger
from ..services.kill_switch import KillSwitchFilter
from ..services.scoring import PropertyScorer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of pipeline execution with summary statistics.

    Attributes:
        total_properties: Total number of properties processed
        passed_count: Number of properties that passed all kill switches
        failed_count: Number of properties that failed at least one kill switch
        unicorns: Properties classified as UNICORN tier (>400 points)
        contenders: Properties classified as CONTENDER tier (300-400 points)
        passed: Properties classified as PASS tier (<300 points)
        failed: Properties that failed kill switch evaluation
        execution_time_seconds: Time taken to execute pipeline
    """

    total_properties: int
    passed_count: int
    failed_count: int
    unicorns: list[Property] = field(default_factory=list)
    contenders: list[Property] = field(default_factory=list)
    passed: list[Property] = field(default_factory=list)
    failed: list[Property] = field(default_factory=list)
    execution_time_seconds: float = 0.0

    def summary_text(self) -> str:
        """Generate human-readable summary of pipeline results.

        Returns:
            Multi-line string with pipeline execution summary
        """
        lines = [
            "="*70,
            "PHX HOME ANALYSIS PIPELINE RESULTS",
            "="*70,
            f"Total Properties Processed: {self.total_properties}",
            f"Execution Time: {self.execution_time_seconds:.2f}s",
            "",
            "KILL SWITCH FILTER RESULTS:",
            f"  Passed: {self.passed_count} ({self.passed_count/self.total_properties*100:.1f}%)" if self.total_properties > 0 else "  Passed: 0",
            f"  Failed: {self.failed_count} ({self.failed_count/self.total_properties*100:.1f}%)" if self.total_properties > 0 else "  Failed: 0",
            "",
            "TIER BREAKDOWN (Passing Properties):",
            f"  UNICORN (>400 pts):   {len(self.unicorns):2d} properties",
            f"  CONTENDER (300-400):  {len(self.contenders):2d} properties",
            f"  PASS (<300 pts):      {len(self.passed):2d} properties",
            "",
        ]

        # Show top 3 scorers if any
        if self.unicorns:
            lines.append("TOP UNICORNS:")
            for i, prop in enumerate(self.unicorns[:3], 1):
                score = prop.score_breakdown.total_score if prop.score_breakdown else 0
                lines.append(f"  {i}. {prop.street} - {score:.1f} pts")
            lines.append("")

        lines.append("="*70)
        return "\n".join(lines)


class AnalysisPipeline:
    """Main pipeline orchestrator for PHX Home Analysis.

    Coordinates the complete home analysis workflow from data loading through
    scoring and output generation. Provides dependency injection for all
    services and repositories to enable testing and customization.

    Example:
        >>> # Run with defaults
        >>> pipeline = AnalysisPipeline()
        >>> result = pipeline.run()
        >>> print(result.summary_text())

        >>> # Run with custom config
        >>> config = AppConfig.default(base_dir="/custom/path")
        >>> pipeline = AnalysisPipeline(config=config)
        >>> result = pipeline.run()

        >>> # Analyze single property
        >>> pipeline = AnalysisPipeline()
        >>> property = pipeline.analyze_single("123 Main St, Phoenix, AZ 85001")
    """

    def __init__(
        self,
        config: AppConfig | None = None,
        property_repo: PropertyRepository | None = None,
        enrichment_repo: EnrichmentRepository | None = None,
        enrichment_merger: EnrichmentMerger | None = None,
        kill_switch_filter: KillSwitchFilter | None = None,
        scorer: PropertyScorer | None = None,
        tier_classifier: TierClassifier | None = None,
        property_analyzer: PropertyAnalyzer | None = None,
    ) -> None:
        """Initialize pipeline with configuration and services.

        All parameters are optional and will use sensible defaults if not provided.
        This enables both simple usage and advanced dependency injection for testing.

        Args:
            config: Application configuration. If None, loads default config.
            property_repo: Property data repository. If None, creates CsvPropertyRepository.
            enrichment_repo: Enrichment data repository. If None, creates JsonEnrichmentRepository.
            enrichment_merger: Enrichment merger service. If None, creates default merger.
            kill_switch_filter: Kill switch filter service. If None, creates default filter.
            scorer: Property scoring service. If None, creates default scorer.
            tier_classifier: Tier classification service. If None, creates default classifier.
            property_analyzer: Single property analyzer. If None, creates default analyzer.
        """
        # Load or use provided config
        self._config = config or AppConfig.default()

        # Initialize repositories with config paths
        self._property_repo = property_repo or CsvPropertyRepository(
            csv_file_path=self._config.paths.input_csv,
            ranked_csv_path=self._config.paths.output_csv,
        )

        self._enrichment_repo = enrichment_repo or JsonEnrichmentRepository(
            json_file_path=self._config.paths.enrichment_json
        )

        # Initialize core services
        self._enrichment_merger = enrichment_merger or EnrichmentMerger()
        self._kill_switch_filter = kill_switch_filter or KillSwitchFilter()
        self._scorer = scorer or PropertyScorer()
        self._tier_classifier = tier_classifier or TierClassifier(self._scorer.thresholds)

        # Initialize property analyzer (orchestrates single-property workflow)
        self._property_analyzer = property_analyzer or PropertyAnalyzer(
            enrichment_merger=self._enrichment_merger,
            kill_switch_filter=self._kill_switch_filter,
            scorer=self._scorer,
            tier_classifier=self._tier_classifier,
        )

        logger.info("AnalysisPipeline initialized")
        logger.info(f"Input CSV: {self._config.paths.input_csv}")
        logger.info(f"Enrichment JSON: {self._config.paths.enrichment_json}")
        logger.info(f"Output CSV: {self._config.paths.output_csv}")

    @property
    def config(self) -> AppConfig:
        """Get pipeline configuration.

        Returns:
            AppConfig instance
        """
        return self._config

    def run(self) -> PipelineResult:
        """Execute complete analysis pipeline.

        Runs all pipeline stages:
        1. Load properties from CSV
        2. Load enrichment data from JSON
        3. Merge enrichment into properties
        4. Apply kill-switch filters
        5. Score passing properties
        6. Classify tiers
        7. Sort by score (descending)
        8. Save ranked results
        9. Return summary statistics

        Returns:
            PipelineResult with execution summary and categorized properties

        Raises:
            DataLoadError: If input files cannot be read
            DataSaveError: If output file cannot be written
        """
        start_time = time.time()
        logger.info("Starting PHX Home Analysis pipeline...")

        # Stage 1: Load properties from CSV
        logger.info("Stage 1/8: Loading properties from CSV...")
        properties = self._property_repo.load_all()
        logger.info(f"Loaded {len(properties)} properties from CSV")

        # Stage 2: Load enrichment data from JSON
        logger.info("Stage 2/8: Loading enrichment data from JSON...")
        enrichment_data = self._enrichment_repo.load_all()
        logger.info(f"Loaded enrichment data for {len(enrichment_data)} properties")

        # Stage 3: Merge enrichment into properties
        logger.info("Stage 3/8: Merging enrichment data into properties...")
        properties = self._enrichment_merger.merge_batch(properties, enrichment_data)
        logger.info(f"Merged enrichment for {len(properties)} properties")

        # Stage 4: Apply kill-switch filters
        logger.info("Stage 4/8: Applying kill-switch filters...")
        passed_properties, failed_properties = self._kill_switch_filter.filter_properties(properties)
        logger.info(f"Kill switch results: {len(passed_properties)} passed, {len(failed_properties)} failed")

        # Stage 5: Score passing properties
        logger.info("Stage 5/8: Scoring passing properties...")
        scored_properties = self._scorer.score_all(passed_properties)
        logger.info(f"Scored {len(scored_properties)} properties")

        # Stage 6: Classify tiers
        logger.info("Stage 6/8: Classifying properties into tiers...")
        self._tier_classifier.classify_batch(scored_properties)
        unicorns, contenders, passed = self._tier_classifier.group_by_tier(scored_properties)
        logger.info(f"Tiers: {len(unicorns)} unicorns, {len(contenders)} contenders, {len(passed)} passed")

        # Stage 7: Sort by score (descending)
        logger.info("Stage 7/8: Sorting properties by score...")
        all_ranked = self._sort_by_score(scored_properties)
        logger.info(f"Sorted {len(all_ranked)} properties by score")

        # Stage 8: Save ranked results
        logger.info("Stage 8/8: Saving ranked results to CSV...")
        self._save_results(all_ranked, failed_properties)
        logger.info(f"Results saved to {self._config.paths.output_csv}")

        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"Pipeline completed in {execution_time:.2f} seconds")

        # Build result object
        result = PipelineResult(
            total_properties=len(properties),
            passed_count=len(passed_properties),
            failed_count=len(failed_properties),
            unicorns=unicorns,
            contenders=contenders,
            passed=passed,
            failed=failed_properties,
            execution_time_seconds=execution_time,
        )

        return result

    def analyze_single(self, full_address: str) -> Property | None:
        """Analyze a specific property by address.

        Loads all properties, finds the matching address, enriches it,
        applies kill switches, and scores it if passing.

        Args:
            full_address: Complete address to search for (e.g., "123 Main St, Phoenix, AZ 85001")

        Returns:
            Property object with complete analysis, or None if not found
        """
        logger.info(f"Analyzing single property: {full_address}")

        # Load all properties and enrichment data
        properties = self._property_repo.load_all()
        enrichment_data = self._enrichment_repo.load_all()

        # Delegate to property analyzer
        return self._property_analyzer.find_and_analyze(
            full_address=full_address,
            all_properties=properties,
            enrichment_lookup=enrichment_data,
        )

    def _sort_by_score(self, properties: list[Property]) -> list[Property]:
        """Sort properties by score in descending order.

        Args:
            properties: List of scored properties

        Returns:
            Sorted list (highest score first)
        """
        return sorted(
            properties,
            key=lambda p: p.score_breakdown.total_score if p.score_breakdown else 0,
            reverse=True,
        )

    def _save_results(
        self,
        ranked_properties: list[Property],
        failed_properties: list[Property],
    ) -> None:
        """Save ranked results to CSV file.

        Args:
            ranked_properties: Scored and sorted properties
            failed_properties: Properties that failed kill switches
        """
        # Combine all properties (ranked first, then failed)
        all_properties = ranked_properties + failed_properties

        # Save to CSV using repository
        self._property_repo.save_all(all_properties)
