# PHX Houses - API Contracts

**Generated:** 2025-12-05
**Architecture:** Service Layer Interfaces

---

## Overview

PHX Houses uses internal service contracts for modularity. This document defines the interfaces between components.

---

## Core Interfaces

### PropertyRepository (Data Access)

```python
from typing import Protocol

class PropertyRepository(Protocol):
    """Interface for property data access."""

    def load_all(self) -> list[Property]:
        """Load all properties from storage.

        Returns:
            List of Property entities.
        """
        ...

    def save_all(self, properties: list[Property]) -> None:
        """Save all properties to storage.

        Args:
            properties: List of Property entities to save.
        """
        ...

    def find_by_address(self, address: str) -> Property | None:
        """Find a property by address.

        Args:
            address: Full address string (normalized).

        Returns:
            Property if found, None otherwise.
        """
        ...
```

**Implementations:**
- `CsvPropertyRepository` - CSV file storage
- `JsonPropertyRepository` - JSON file storage

---

### EnrichmentRepository (Enrichment Data)

```python
class EnrichmentRepository(Protocol):
    """Interface for enrichment data access."""

    def load(self) -> dict[str, dict]:
        """Load all enrichment data.

        Returns:
            Dict mapping address -> enrichment fields.
        """
        ...

    def save(self, data: dict[str, dict]) -> None:
        """Save enrichment data.

        Args:
            data: Dict mapping address -> enrichment fields.
        """
        ...

    def get(self, address: str) -> dict | None:
        """Get enrichment for a specific address.

        Args:
            address: Normalized address string.

        Returns:
            Enrichment dict if found, None otherwise.
        """
        ...

    def update(self, address: str, fields: dict) -> None:
        """Update enrichment for a specific address.

        Args:
            address: Normalized address string.
            fields: Dict of field -> value to update.
        """
        ...
```

**Implementation:** `JsonEnrichmentRepository`

---

### KillSwitchFilter (Filtering)

```python
class KillSwitchFilter:
    """Applies kill-switch criteria to filter properties."""

    def evaluate(self, property: Property) -> KillSwitchResult:
        """Evaluate property against all kill-switch criteria.

        Args:
            property: Property entity to evaluate.

        Returns:
            KillSwitchResult with passed status and failures.
        """
        ...

    def explain(self, property: Property) -> str:
        """Generate human-readable explanation.

        Args:
            property: Property entity.

        Returns:
            Formatted explanation string.
        """
        ...

@dataclass
class KillSwitchResult:
    """Result of kill-switch evaluation."""

    passed: bool
    failures: list[str]
    criteria_results: dict[str, bool]
```

---

### PropertyScorer (Scoring)

```python
class PropertyScorer:
    """Calculates 605-point score for properties."""

    def score(self, property: Property) -> ScoreBreakdown:
        """Calculate complete score breakdown.

        Args:
            property: Property entity with all data.

        Returns:
            ScoreBreakdown with section scores.
        """
        ...

    def score_section(
        self,
        property: Property,
        section: Literal["A", "B", "C"]
    ) -> int:
        """Score a single section.

        Args:
            property: Property entity.
            section: Section identifier (A/B/C).

        Returns:
            Section score (max varies by section).
        """
        ...

    def explain(self, property: Property) -> dict[str, dict]:
        """Generate detailed score explanation.

        Args:
            property: Property entity.

        Returns:
            Dict of strategy -> {score, max, explanation}.
        """
        ...
```

---

### TierClassifier (Classification)

```python
class TierClassifier:
    """Classifies properties into tiers based on score."""

    def classify(self, score: int) -> Tier:
        """Classify score into tier.

        Args:
            score: Total score (0-605).

        Returns:
            Tier enum value.
        """
        ...

    @property
    def thresholds(self) -> dict[Tier, int]:
        """Return tier thresholds.

        Returns:
            Dict of Tier -> minimum score.
        """
        return {
            Tier.UNICORN: 481,
            Tier.CONTENDER: 360,
            Tier.PASS: 0,
        }
```

---

## External API Clients

### CountyAssessorClient

```python
class CountyAssessorClient:
    """Client for Maricopa County Assessor API."""

    async def fetch_property_data(
        self,
        address: str
    ) -> CountyData | None:
        """Fetch property data from county assessor.

        Args:
            address: Property address string.

        Returns:
            CountyData if found, None otherwise.

        Raises:
            RateLimitError: If rate limit exceeded.
            APIError: If API returns error response.
        """
        ...

@dataclass
class CountyData:
    """Data from county assessor API."""

    parcel_id: str
    lot_sqft: int
    year_built: int
    garage_spaces: int
    sewer_type: str
    assessed_value: float
    tax_annual: float
```

**Endpoint:** `https://mcassessor.maricopa.gov/api/v1/properties`

---

### SchoolRatingsClient

```python
class SchoolRatingsClient:
    """Client for GreatSchools API."""

    async def get_nearby_schools(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 2.0
    ) -> list[School]:
        """Get nearby schools with ratings.

        Args:
            lat: Latitude.
            lon: Longitude.
            radius_miles: Search radius.

        Returns:
            List of School objects.
        """
        ...

    async def get_district_rating(
        self,
        lat: float,
        lon: float
    ) -> float | None:
        """Get average district rating.

        Args:
            lat: Latitude.
            lon: Longitude.

        Returns:
            Average rating (1-10) or None.
        """
        ...

@dataclass
class School:
    """School information from GreatSchools."""

    name: str
    type: str  # "elementary", "middle", "high"
    rating: float
    distance_miles: float
    enrollment: int
```

---

### GoogleMapsClient

```python
class GoogleMapsClient:
    """Client for Google Maps Distance Matrix API."""

    async def calculate_distance(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: str = "driving"
    ) -> DistanceResult:
        """Calculate distance and duration.

        Args:
            origin: (lat, lon) tuple.
            destination: (lat, lon) tuple.
            mode: Travel mode ("driving", "walking", "transit").

        Returns:
            DistanceResult with distance and duration.
        """
        ...

@dataclass
class DistanceResult:
    """Result from distance calculation."""

    distance_miles: float
    duration_minutes: int
    traffic_duration_minutes: int | None
```

---

### ImageExtractionOrchestrator

```python
class ImageExtractionOrchestrator:
    """Orchestrates image extraction from multiple sources."""

    async def extract_images(
        self,
        property: Property,
        sources: list[ImageSource] = None
    ) -> ImageExtractionResult:
        """Extract images from listing sources.

        Args:
            property: Property entity.
            sources: List of sources to try (default: all).

        Returns:
            ImageExtractionResult with downloaded images.
        """
        ...

    async def extract_batch(
        self,
        properties: list[Property],
        concurrency: int = 5
    ) -> list[ImageExtractionResult]:
        """Extract images for multiple properties.

        Args:
            properties: List of properties.
            concurrency: Max concurrent extractions.

        Returns:
            List of extraction results.
        """
        ...

@dataclass
class ImageExtractionResult:
    """Result of image extraction."""

    address: str
    images_downloaded: int
    sources_tried: list[ImageSource]
    source_used: ImageSource | None
    errors: list[str]
    manifest_updated: bool
```

---

## Pipeline Interfaces

### AnalysisPipeline

```python
class AnalysisPipeline:
    """Main analysis pipeline orchestrator."""

    def run(
        self,
        addresses: list[str] | None = None
    ) -> PipelineResult:
        """Execute full analysis pipeline.

        Args:
            addresses: Specific addresses to analyze (default: all).

        Returns:
            PipelineResult with summary statistics.
        """
        ...

    def run_phase(
        self,
        phase: Phase,
        addresses: list[str] | None = None
    ) -> PhaseResult:
        """Execute a single pipeline phase.

        Args:
            phase: Phase to execute (COUNTY, LISTING, etc.).
            addresses: Specific addresses (default: all).

        Returns:
            PhaseResult with phase-specific results.
        """
        ...

@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    total_properties: int
    passed_count: int
    failed_count: int
    unicorns: list[Property]
    contenders: list[Property]
    passed: list[Property]
    failed: list[Property]
    execution_time_seconds: float
```

---

### PhaseCoordinator

```python
class PhaseCoordinator:
    """Coordinates multi-phase pipeline execution."""

    async def execute_pipeline(
        self,
        addresses: list[str],
        start_phase: Phase = Phase.COUNTY,
        end_phase: Phase = Phase.REPORT
    ) -> PipelineResult:
        """Execute pipeline phases in sequence.

        Args:
            addresses: Addresses to process.
            start_phase: First phase to execute.
            end_phase: Last phase to execute.

        Returns:
            PipelineResult with final statistics.
        """
        ...

    def checkpoint(self, address: str, phase: Phase) -> None:
        """Save checkpoint for crash recovery.

        Args:
            address: Property address.
            phase: Completed phase.
        """
        ...
```

---

### ResumePipeline

```python
class ResumePipeline:
    """Handles crash recovery and resume."""

    def can_resume(self) -> bool:
        """Check if there's resumable state.

        Returns:
            True if state file exists with pending work.
        """
        ...

    def get_pending_addresses(self) -> list[str]:
        """Get addresses that need processing.

        Returns:
            List of pending addresses.
        """
        ...

    def reset_stale_items(
        self,
        timeout_minutes: int = 30
    ) -> int:
        """Reset items stuck in processing.

        Args:
            timeout_minutes: Threshold for stale detection.

        Returns:
            Number of items reset.
        """
        ...
```

---

## Error Handling

### Error Classification

```python
def is_transient_error(error: Exception) -> bool:
    """Classify error as transient (retryable) or permanent.

    Args:
        error: Exception to classify.

    Returns:
        True if error is transient and should be retried.
    """
    transient_types = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadError,
        RateLimitError,
        ServiceUnavailableError,
    )
    return isinstance(error, transient_types)
```

### Retry Decorator

```python
def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    retryable_exceptions: tuple = (Exception,)
):
    """Decorator for retrying failed operations.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential: Use exponential backoff.
        retryable_exceptions: Exception types to retry.

    Returns:
        Decorator function.
    """
    ...
```

---

## Rate Limiting

### RateLimiter

```python
class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        requests_per_second: float,
        burst_size: int = 1
    ):
        """Initialize rate limiter.

        Args:
            requests_per_second: Sustained request rate.
            burst_size: Maximum burst size.
        """
        ...

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        ...

    def available(self) -> bool:
        """Check if a token is available."""
        ...
```
