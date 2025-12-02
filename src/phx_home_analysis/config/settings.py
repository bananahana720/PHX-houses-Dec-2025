"""Core settings and configuration for PHX Home Analysis pipeline.

This module defines all application settings including file paths, buyer criteria,
map configuration, and Arizona-specific context.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """File paths for the PHX Home Analysis pipeline.

    All paths are relative to base_dir, which defaults to the current working
    directory but can be overridden via PHX_BASE_DIR environment variable.

    Attributes:
        base_dir: Project root directory
        input_csv: Raw listing data from Zillow/Redfin
        enrichment_json: Manual enrichment data (county records, schools, etc.)
        output_csv: Ranked properties with scores and tier classifications
    """

    base_dir: Path
    input_csv: Path
    enrichment_json: Path
    output_csv: Path

    @classmethod
    def from_base_dir(cls, base_dir: Path | str | None = None) -> "ProjectPaths":
        """Create ProjectPaths from base directory.

        Args:
            base_dir: Base directory for project. If None, uses PHX_BASE_DIR
                     environment variable or current working directory.

        Returns:
            ProjectPaths instance with all paths configured
        """
        if base_dir is None:
            base_dir = os.getenv("PHX_BASE_DIR", os.getcwd())

        base = Path(base_dir)

        return cls(
            base_dir=base,
            input_csv=base / "data" / "phx_homes.csv",
            enrichment_json=base / "data" / "enrichment_data.json",
            output_csv=base / "reports" / "csv" / "phx_homes_ranked.csv",
        )


@dataclass(frozen=True)
class MapConfig:
    """Configuration for map visualization and geocoding.

    Attributes:
        center_lat: Phoenix metropolitan area center latitude
        center_lon: Phoenix metropolitan area center longitude
        default_zoom: Default zoom level for maps
        tile_provider: Map tile provider (e.g., 'OpenStreetMap', 'CartoDB')
    """

    center_lat: float = 33.4484  # Phoenix, AZ
    center_lon: float = -112.0740
    default_zoom: int = 10
    tile_provider: str = "OpenStreetMap"


@dataclass(frozen=True)
class BuyerProfile:
    """Target buyer profile and hard kill-switch criteria.

    Properties failing any kill-switch criterion are automatically excluded
    from consideration regardless of scoring.

    Financial Criteria:
        max_monthly_payment: Maximum monthly mortgage payment
        down_payment: Cash available for down payment
        mortgage_years: Mortgage term in years

    Kill Switch Criteria (Must Pass All):
        min_bedrooms: Minimum number of bedrooms required
        min_bathrooms: Minimum number of bathrooms required
        min_garage_spaces: Minimum garage spaces required
        min_lot_sqft: Minimum lot size in square feet
        max_lot_sqft: Maximum lot size in square feet
        allow_hoa: Whether HOA is acceptable (False = no HOA allowed)
        require_city_sewer: Whether city sewer is required (True = no septic)
        max_year_built: Maximum year built (excludes new construction)
    """

    # Financial criteria
    max_monthly_payment: int = 4_000
    down_payment: int = 50_000
    mortgage_years: int = 30

    # Kill switches - Property requirements
    min_bedrooms: int = 4
    min_bathrooms: float = 2.0
    min_garage_spaces: int = 2

    # Kill switches - Lot requirements
    min_lot_sqft: int = 7_000
    max_lot_sqft: int = 15_000

    # Kill switches - Deal breakers
    allow_hoa: bool = False  # NO HOA allowed
    require_city_sewer: bool = True  # City sewer only, no septic
    max_year_built: int = datetime.now().year - 1  # No new builds (exclude current year)


@dataclass(frozen=True)
class ArizonaContext:
    """Arizona-specific considerations for home analysis.

    These factors are unique to the Arizona climate and real estate market,
    affecting both property value and ongoing costs.

    Solar Panel Considerations:
        solar_lease_penalty: Monthly cost burden for leased solar panels

    Pool Maintenance:
        pool_service_monthly: Monthly pool service cost
        pool_equipment_replacement_cost: Average equipment replacement cost
        pool_energy_monthly_summer: Summer energy costs for pool

    HVAC Lifecycle:
        hvac_lifespan_years: Expected HVAC lifespan in Arizona climate
        hvac_replacement_cost: Average HVAC replacement cost

    Sun Orientation Impact:
        west_facing_penalty: Cooling cost penalty for west-facing homes
        north_facing_bonus: Cooling cost advantage for north-facing homes

    Reference Locations:
        reference_commute_location: Target commute destination
        reference_grocery_chains: Preferred grocery store chains
    """

    # Solar considerations
    solar_lease_penalty: int = 150  # $/month burden

    # Pool maintenance costs
    pool_service_monthly: int = 125
    pool_equipment_replacement_cost: int = 5_500
    pool_energy_monthly_summer: int = 75

    # HVAC considerations
    hvac_lifespan_years: int = 12  # Shorter in AZ heat
    hvac_replacement_cost: int = 8_000

    # Sun orientation impact on cooling costs
    west_facing_penalty: int = -15  # Higher afternoon cooling costs
    north_facing_bonus: int = 15  # Lower cooling costs

    # Reference locations for scoring
    reference_commute_location: str = "Desert Ridge, Phoenix, AZ"
    reference_grocery_chains: tuple[str, ...] = (
        "Fry's",
        "Safeway",
        "Sprouts",
        "Trader Joe's",
        "Whole Foods",
    )


@dataclass(frozen=True)
class StealthExtractionConfig:
    """Configuration for stealth browser extraction (nodriver + curl_cffi).

    Controls anti-detection settings for bypassing PerimeterX on Zillow/Redfin.

    Proxy Settings:
        proxy_server: Proxy server address (host:port)
        proxy_username: Proxy authentication username
        proxy_password: Proxy authentication password

    Browser Settings:
        browser_headless: Run browser in headless mode
        viewport_width: Browser viewport width in pixels
        viewport_height: Browser viewport height in pixels

    Human Behavior Simulation:
        human_delay_min: Minimum delay between actions (seconds)
        human_delay_max: Maximum delay between actions (seconds)

    CAPTCHA Handling:
        captcha_hold_min: Minimum hold duration for Press & Hold (seconds)
        captcha_hold_max: Maximum hold duration for Press & Hold (seconds)

    Request Settings:
        request_timeout: HTTP request timeout (seconds)
        max_retries: Maximum retry attempts
    """

    # Proxy settings
    proxy_server: str = ""
    proxy_username: str = ""
    proxy_password: str = ""

    # Browser settings
    browser_headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720

    # Human behavior simulation
    human_delay_min: float = 1.0
    human_delay_max: float = 3.0

    # CAPTCHA handling
    captcha_hold_min: float = 4.0
    captcha_hold_max: float = 7.0

    # Request settings
    request_timeout: float = 30.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "StealthExtractionConfig":
        """Load configuration from environment variables.

        Environment Variables:
            PROXY_SERVER: Proxy server address (host:port)
            PROXY_USERNAME: Proxy username
            PROXY_PASSWORD: Proxy password
            BROWSER_HEADLESS: "true" or "false"

        Returns:
            StealthExtractionConfig instance
        """
        return cls(
            proxy_server=os.getenv("PROXY_SERVER", ""),
            proxy_username=os.getenv("PROXY_USERNAME", ""),
            proxy_password=os.getenv("PROXY_PASSWORD", ""),
            browser_headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
        )

    @property
    def proxy_url(self) -> str | None:
        """Build full proxy URL with authentication.

        Returns:
            Proxy URL in format http://user:pass@host:port, or None if not configured
        """
        if not self.proxy_server:
            return None
        if self.proxy_username and self.proxy_password:
            return f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_server}"
        return f"http://{self.proxy_server}"

    @property
    def is_configured(self) -> bool:
        """Check if proxy is configured."""
        return bool(self.proxy_server)


@dataclass(frozen=True)
class ImageExtractionConfig:
    """Configuration for image extraction pipeline.

    Controls behavior of multi-source image download, processing, and deduplication
    for property photos from county assessor, MLS, and listing sites.

    Storage Paths:
        images_base_dir: Base directory for all image storage (raw, processed, metadata)

    Processing Settings:
        max_image_dimension: Maximum width/height for processed images (pixels)
        output_format: Image format for processed images (PNG, JPEG, etc.)

    Deduplication:
        hash_similarity_threshold: Maximum Hamming distance for perceptual hash matching

    Rate Limiting:
        download_delay_ms: Milliseconds delay between downloads
        max_concurrent_downloads: Maximum parallel image downloads
        max_concurrent_properties: Maximum properties processed simultaneously

    Retry Settings:
        max_retries: Maximum retry attempts for failed downloads
        retry_base_delay: Base delay in seconds for exponential backoff

    Timeouts:
        download_timeout: Timeout for individual image downloads (seconds)
        browser_timeout: Timeout for browser-based extraction (seconds)

    Source Configuration:
        enabled_sources: Tuple of enabled data sources
    """

    # Storage paths
    images_base_dir: Path

    # Processing settings
    max_image_dimension: int = 1024
    output_format: str = "PNG"

    # Deduplication
    hash_similarity_threshold: int = 8  # Hamming distance

    # Rate limiting
    download_delay_ms: int = 500
    max_concurrent_downloads: int = 5
    max_concurrent_properties: int = 3

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0

    # Timeouts
    download_timeout: int = 30
    browser_timeout: int = 30

    # Source configuration
    enabled_sources: tuple[str, ...] = (
        "maricopa_assessor",
        "phoenix_mls",
        "zillow",
        "redfin",
    )

    @classmethod
    def default(cls, base_dir: Path) -> "ImageExtractionConfig":
        """Create default image extraction configuration.

        Args:
            base_dir: Project base directory (images stored under data/images)

        Returns:
            ImageExtractionConfig instance with default settings
        """
        return cls(images_base_dir=base_dir / "data" / "images")

    @property
    def raw_dir(self) -> Path:
        """Directory for raw downloaded images."""
        return self.images_base_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        """Directory for processed/resized images."""
        return self.images_base_dir / "processed"

    @property
    def metadata_dir(self) -> Path:
        """Directory for extraction metadata and state files."""
        return self.images_base_dir / "metadata"

    @property
    def hash_index_path(self) -> Path:
        """Path to perceptual hash index for deduplication."""
        return self.metadata_dir / "hash_index.json"

    @property
    def manifest_path(self) -> Path:
        """Path to image manifest (all downloaded images)."""
        return self.metadata_dir / "image_manifest.json"

    @property
    def state_path(self) -> Path:
        """Path to extraction state file (resume capability)."""
        return self.metadata_dir / "extraction_state.json"


@dataclass(frozen=True)
class AppConfig:
    """Complete application configuration.

    Aggregates all configuration components into a single object for
    easy access throughout the pipeline.

    Attributes:
        paths: File paths configuration
        buyer: Buyer profile and kill-switch criteria
        arizona: Arizona-specific context
        maps: Map visualization configuration
    """

    paths: ProjectPaths
    buyer: BuyerProfile
    arizona: ArizonaContext
    maps: MapConfig

    @classmethod
    def default(cls, base_dir: Path | str | None = None) -> "AppConfig":
        """Create default application configuration.

        Args:
            base_dir: Base directory for project. If None, uses PHX_BASE_DIR
                     environment variable or current working directory.

        Returns:
            AppConfig instance with all defaults
        """
        return cls(
            paths=ProjectPaths.from_base_dir(base_dir),
            buyer=BuyerProfile(),
            arizona=ArizonaContext(),
            maps=MapConfig(),
        )
