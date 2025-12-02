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
from pathlib import Path
from typing import List, Optional

from ..config import AppConfig
from ..domain import EnrichmentData, Orientation, Property, SewerType, SolarStatus, Tier
from ..repositories import (
    CsvPropertyRepository,
    EnrichmentRepository,
    JsonEnrichmentRepository,
    PropertyRepository,
)
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
    unicorns: List[Property] = field(default_factory=list)
    contenders: List[Property] = field(default_factory=list)
    passed: List[Property] = field(default_factory=list)
    failed: List[Property] = field(default_factory=list)
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
        config: Optional[AppConfig] = None,
        property_repo: Optional[PropertyRepository] = None,
        enrichment_repo: Optional[EnrichmentRepository] = None,
        kill_switch_filter: Optional[KillSwitchFilter] = None,
        scorer: Optional[PropertyScorer] = None,
    ) -> None:
        """Initialize pipeline with configuration and services.

        All parameters are optional and will use sensible defaults if not provided.
        This enables both simple usage and advanced dependency injection for testing.

        Args:
            config: Application configuration. If None, loads default config.
            property_repo: Property data repository. If None, creates CsvPropertyRepository.
            enrichment_repo: Enrichment data repository. If None, creates JsonEnrichmentRepository.
            kill_switch_filter: Kill switch filter service. If None, creates default filter.
            scorer: Property scoring service. If None, creates default scorer.
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

        # Initialize services
        self._kill_switch_filter = kill_switch_filter or KillSwitchFilter()
        self._scorer = scorer or PropertyScorer()

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
        properties = self._merge_enrichment(properties, enrichment_data)
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
        unicorns, contenders, passed = self._classify_by_tier(scored_properties)
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

    def analyze_single(self, full_address: str) -> Optional[Property]:
        """Analyze a specific property by address.

        Loads all properties, finds the matching address, enriches it,
        applies kill switches, and scores it if passing.

        Args:
            full_address: Complete address to search for (e.g., "123 Main St, Phoenix, AZ 85001")

        Returns:
            Property object with complete analysis, or None if not found
        """
        logger.info(f"Analyzing single property: {full_address}")

        # Load all properties
        properties = self._property_repo.load_all()

        # Find matching property
        matching_property = None
        for prop in properties:
            if prop.full_address.lower() == full_address.lower():
                matching_property = prop
                break

        if not matching_property:
            logger.warning(f"Property not found: {full_address}")
            return None

        # Enrich property
        enrichment_data = self._enrichment_repo.load_all()
        enriched = self._merge_enrichment([matching_property], enrichment_data)

        if not enriched:
            logger.warning(f"Could not enrich property: {full_address}")
            return None

        property_obj = enriched[0]

        # Apply kill switches
        passed, failures = self._kill_switch_filter.evaluate(property_obj)
        property_obj.kill_switch_passed = passed
        property_obj.kill_switch_failures = failures

        # Score if passed
        if passed:
            score_breakdown = self._scorer.score(property_obj)
            property_obj.score_breakdown = score_breakdown
            property_obj.tier = self._classify_tier(score_breakdown.total_score)
            logger.info(f"Property scored: {score_breakdown.total_score:.1f} pts ({property_obj.tier.value})")
        else:
            logger.info(f"Property failed kill switches: {', '.join(failures)}")

        return property_obj

    def _merge_enrichment(
        self,
        properties: List[Property],
        enrichment_data: dict[str, "EnrichmentData"],
    ) -> List[Property]:
        """Merge enrichment data into property objects.

        Matches properties to enrichment data by full_address and updates
        property attributes with enrichment values.

        Args:
            properties: List of Property objects from CSV
            enrichment_data: Dictionary mapping full_address to EnrichmentData objects

        Returns:
            List of properties with enrichment data merged
        """
        for property_obj in properties:
            # Look up enrichment by full address
            enrichment = enrichment_data.get(property_obj.full_address)

            if not enrichment:
                logger.debug(f"No enrichment data for: {property_obj.full_address}")
                continue

            # Merge enrichment fields into property (use direct attribute access)
            # County assessor data
            if enrichment.lot_sqft is not None:
                property_obj.lot_sqft = enrichment.lot_sqft
            if enrichment.year_built is not None:
                property_obj.year_built = enrichment.year_built
            if enrichment.garage_spaces is not None:
                property_obj.garage_spaces = enrichment.garage_spaces
            if enrichment.sewer_type is not None:
                # Convert string to enum if needed
                if isinstance(enrichment.sewer_type, str):
                    try:
                        property_obj.sewer_type = SewerType(enrichment.sewer_type.lower())
                    except ValueError:
                        property_obj.sewer_type = SewerType.UNKNOWN
                else:
                    property_obj.sewer_type = enrichment.sewer_type
            if enrichment.tax_annual is not None:
                property_obj.tax_annual = enrichment.tax_annual

            # HOA and location data
            if enrichment.hoa_fee is not None:
                property_obj.hoa_fee = enrichment.hoa_fee
            if enrichment.commute_minutes is not None:
                property_obj.commute_minutes = enrichment.commute_minutes
            if enrichment.school_district is not None:
                property_obj.school_district = enrichment.school_district
            if enrichment.school_rating is not None:
                property_obj.school_rating = enrichment.school_rating
            if enrichment.orientation is not None:
                # Convert string to enum if needed
                if isinstance(enrichment.orientation, str):
                    try:
                        property_obj.orientation = Orientation(enrichment.orientation.lower())
                    except ValueError:
                        property_obj.orientation = None
                else:
                    property_obj.orientation = enrichment.orientation
            if enrichment.distance_to_grocery_miles is not None:
                property_obj.distance_to_grocery_miles = enrichment.distance_to_grocery_miles
            if enrichment.distance_to_highway_miles is not None:
                property_obj.distance_to_highway_miles = enrichment.distance_to_highway_miles

            # Arizona-specific features
            if enrichment.solar_status is not None:
                # Convert string to enum if needed
                if isinstance(enrichment.solar_status, str):
                    try:
                        property_obj.solar_status = SolarStatus(enrichment.solar_status.lower())
                    except ValueError:
                        property_obj.solar_status = None
                else:
                    property_obj.solar_status = enrichment.solar_status
            if enrichment.solar_lease_monthly is not None:
                property_obj.solar_lease_monthly = enrichment.solar_lease_monthly
            if enrichment.has_pool is not None:
                property_obj.has_pool = enrichment.has_pool
            if enrichment.pool_equipment_age is not None:
                property_obj.pool_equipment_age = enrichment.pool_equipment_age
            if enrichment.roof_age is not None:
                property_obj.roof_age = enrichment.roof_age
            if enrichment.hvac_age is not None:
                property_obj.hvac_age = enrichment.hvac_age

        return properties

    def _classify_by_tier(
        self, properties: List[Property]
    ) -> tuple[List[Property], List[Property], List[Property]]:
        """Classify properties into tier categories.

        Args:
            properties: List of scored properties

        Returns:
            Tuple of (unicorns, contenders, passed) lists
        """
        unicorns = [p for p in properties if p.tier == Tier.UNICORN]
        contenders = [p for p in properties if p.tier == Tier.CONTENDER]
        passed = [p for p in properties if p.tier == Tier.PASS]

        return unicorns, contenders, passed

    def _classify_tier(self, score: float) -> Tier:
        """Classify a score into a tier.

        Args:
            score: Total score value

        Returns:
            Tier classification
        """
        if score > self._scorer.thresholds.unicorn_min:
            return Tier.UNICORN
        elif score >= self._scorer.thresholds.contender_min:
            return Tier.CONTENDER
        else:
            return Tier.PASS

    def _sort_by_score(self, properties: List[Property]) -> List[Property]:
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
        ranked_properties: List[Property],
        failed_properties: List[Property],
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
