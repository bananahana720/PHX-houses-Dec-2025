"""Core settings and configuration for PHX Home Analysis pipeline.

This module defines all application settings including file paths, buyer criteria,
map configuration, and Arizona-specific context.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class BrowserIsolationMode(Enum):
    """Browser window isolation mode for stealth automation.

    Controls how the browser window is isolated to prevent interference
    with user input during non-headless stealth browser operations.

    Attributes:
        VIRTUAL_DISPLAY: Position on virtual display (VDD) - best isolation
        SECONDARY_DISPLAY: Position on secondary monitor if available
        OFF_SCREEN: Position off-screen to the right of primary display
        MINIMIZE: Minimize browser window (less stealthy, may be detected)
        NONE: No isolation (browser visible on primary display)
    """

    VIRTUAL_DISPLAY = "virtual_display"
    SECONDARY_DISPLAY = "secondary_display"
    OFF_SCREEN = "off_screen"
    MINIMIZE = "minimize"
    NONE = "none"


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

    NOTE: Cost-related constants have been moved to:
          src/phx_home_analysis/services/cost_estimation/rates.py

    This class is retained for potential future use but is currently empty
    as all active constants are now in the cost_estimation module.
    """
    pass


# Common viewport sizes for randomization (resolution, usage share)
# Based on StatCounter Global Stats 2024-2025
VIEWPORT_SIZES = [
    (1280, 720),   # 720p - common laptop/monitor
    (1366, 768),   # Most common laptop resolution
    (1440, 900),   # 16:10 laptop/monitor
    (1536, 864),   # 1.5x scaling on 1024x576
    (1920, 1080),  # 1080p - very common desktop
]


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

    Browser Isolation (for non-headless mode):
        isolation_mode: How to isolate browser window from user input
        fallback_to_minimize: If preferred isolation fails, use minimize mode
        virtual_display_offset_x: X offset for virtual display positioning
        virtual_display_offset_y: Y offset for virtual display positioning

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

    # Browser isolation (for non-headless mode)
    isolation_mode: BrowserIsolationMode = BrowserIsolationMode.VIRTUAL_DISPLAY
    fallback_to_minimize: bool = True
    virtual_display_offset_x: int = 1920  # Position after primary monitor
    virtual_display_offset_y: int = 0

    # Human behavior simulation
    human_delay_min: float = 1.0
    human_delay_max: float = 3.0

    # CAPTCHA handling
    captcha_hold_min: float = 4.5
    captcha_hold_max: float = 8.5

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
            BROWSER_ISOLATION: Isolation mode (virtual_display, secondary_display,
                              off_screen, minimize, none)

        Returns:
            StealthExtractionConfig instance
        """
        # Parse isolation mode from environment
        isolation_str = os.getenv("BROWSER_ISOLATION", "virtual_display").lower()
        try:
            isolation_mode = BrowserIsolationMode(isolation_str)
        except ValueError:
            isolation_mode = BrowserIsolationMode.VIRTUAL_DISPLAY

        return cls(
            proxy_server=os.getenv("PROXY_SERVER", ""),
            proxy_username=os.getenv("PROXY_USERNAME", ""),
            proxy_password=os.getenv("PROXY_PASSWORD", ""),
            browser_headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            isolation_mode=isolation_mode,
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

    @staticmethod
    def get_random_viewport() -> tuple[int, int]:
        """Get randomized viewport size from common resolutions.

        Randomization helps avoid fingerprinting by varying browser characteristics
        across requests. Uses common desktop/laptop resolutions to appear natural.

        Returns:
            Tuple of (width, height) in pixels

        Example:
            >>> width, height = StealthExtractionConfig.get_random_viewport()
            >>> width in [1280, 1366, 1440, 1536, 1920]
            True
            >>> height in [720, 768, 900, 864, 1080]
            True
        """
        return random.choice(VIEWPORT_SIZES)


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
    """

    paths: ProjectPaths
    buyer: BuyerProfile
    arizona: ArizonaContext

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
        )
