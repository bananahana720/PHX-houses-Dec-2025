"""AI-powered image categorization using Claude Vision.

Categorizes real estate listing images by location (exterior/interior/systems/features)
and subject type (kitchen, master bedroom, pool, etc.) for organized storage and
retrieval.

Cost-effective batch processing using Claude 3.5 Haiku for high throughput.
"""

import asyncio
import base64
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ImageLocation(Enum):
    """High-level image location classification."""

    EXTERIOR = "ext"
    INTERIOR = "int"
    SYSTEMS = "sys"
    FEATURES = "feat"

    @classmethod
    def from_string(cls, value: str) -> "ImageLocation":
        """Parse location from string value.

        Args:
            value: String like 'exterior', 'ext', 'interior', etc.

        Returns:
            ImageLocation enum value
        """
        mapping = {
            "exterior": cls.EXTERIOR,
            "ext": cls.EXTERIOR,
            "interior": cls.INTERIOR,
            "int": cls.INTERIOR,
            "systems": cls.SYSTEMS,
            "sys": cls.SYSTEMS,
            "features": cls.FEATURES,
            "feat": cls.FEATURES,
        }
        return mapping.get(value.lower().strip(), cls.EXTERIOR)


class ImageSubject(Enum):
    """Specific image subject/room type classification."""

    # Exterior subjects
    FRONT = "front"
    REAR = "rear"
    POOL = "pool"
    GARAGE = "garage"
    YARD = "yard"
    AERIAL = "aerial"
    DRIVEWAY = "driveway"
    PATIO = "patio"
    COURTYARD = "courtyard"

    # Interior subjects
    KITCHEN = "kitchen"
    MASTER = "master"
    MASTER_BATH = "master_bath"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    LIVING = "living"
    DINING = "dining"
    LAUNDRY = "laundry"
    OFFICE = "office"
    ENTRY = "entry"
    HALLWAY = "hallway"
    CLOSET = "closet"
    STAIRS = "stairs"
    BONUS = "bonus"

    # Systems subjects
    HVAC = "hvac"
    HVAC_LABEL = "hvac_label"
    ELECTRICAL = "electrical"
    WATER_HEATER = "water_heater"
    ROOF = "roof"
    PLUMBING = "plumbing"
    ATTIC = "attic"

    # Features subjects
    FIREPLACE = "fireplace"
    SOLAR = "solar"
    POOL_EQUIP = "pool_equip"
    CEILING_FAN = "ceiling_fan"
    BUILT_IN = "built_in"
    FLOORING = "flooring"

    # Fallback
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "ImageSubject":
        """Parse subject from string value.

        Args:
            value: String subject name

        Returns:
            ImageSubject enum value
        """
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.UNKNOWN

    @property
    def default_location(self) -> ImageLocation:
        """Get the default location for this subject type.

        Returns:
            ImageLocation that typically contains this subject
        """
        exterior = {
            ImageSubject.FRONT,
            ImageSubject.REAR,
            ImageSubject.POOL,
            ImageSubject.GARAGE,
            ImageSubject.YARD,
            ImageSubject.AERIAL,
            ImageSubject.DRIVEWAY,
            ImageSubject.PATIO,
            ImageSubject.COURTYARD,
        }
        systems = {
            ImageSubject.HVAC,
            ImageSubject.HVAC_LABEL,
            ImageSubject.ELECTRICAL,
            ImageSubject.WATER_HEATER,
            ImageSubject.ROOF,
            ImageSubject.PLUMBING,
            ImageSubject.ATTIC,
        }
        features = {
            ImageSubject.FIREPLACE,
            ImageSubject.SOLAR,
            ImageSubject.POOL_EQUIP,
            ImageSubject.CEILING_FAN,
            ImageSubject.BUILT_IN,
            ImageSubject.FLOORING,
        }

        if self in exterior:
            return ImageLocation.EXTERIOR
        elif self in systems:
            return ImageLocation.SYSTEMS
        elif self in features:
            return ImageLocation.FEATURES
        else:
            return ImageLocation.INTERIOR


@dataclass
class CategoryResult:
    """Result of image categorization."""

    location: ImageLocation
    subject: ImageSubject
    confidence: float
    features_detected: list[str] = field(default_factory=list)
    alternative_categories: list[tuple[ImageSubject, float]] = field(default_factory=list)
    model_version: str = "claude-haiku-4-5-20251001"
    raw_response: dict | None = None
    error: str | None = None
    categorized_at: str | None = None

    def __post_init__(self) -> None:
        """Set categorized timestamp if not provided."""
        if self.categorized_at is None:
            self.categorized_at = datetime.now().astimezone().isoformat()

    @property
    def confidence_percent(self) -> int:
        """Confidence as integer percentage (0-99).

        Returns:
            Integer confidence for filename use
        """
        return min(99, max(0, int(self.confidence * 100)))

    @property
    def is_high_confidence(self) -> bool:
        """Whether categorization is high confidence (>80%).

        Returns:
            True if confidence exceeds 80%
        """
        return self.confidence >= 0.80

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            "location": self.location.value,
            "subject": self.subject.value,
            "confidence": self.confidence,
            "features_detected": self.features_detected,
            "alternative_categories": [
                {"subject": subj.value, "confidence": conf}
                for subj, conf in self.alternative_categories
            ],
            "model_version": self.model_version,
            "categorized_at": self.categorized_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CategoryResult":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            CategoryResult instance
        """
        return cls(
            location=ImageLocation.from_string(data.get("location", "exterior")),
            subject=ImageSubject.from_string(data.get("subject", "unknown")),
            confidence=data.get("confidence", 0.0),
            features_detected=data.get("features_detected", []),
            alternative_categories=[
                (ImageSubject.from_string(alt["subject"]), alt["confidence"])
                for alt in data.get("alternative_categories", [])
            ],
            model_version=data.get("model_version", "claude-haiku-4-5-20251001"),
            categorized_at=data.get("categorized_at"),
            error=data.get("error"),
        )

    @classmethod
    def unknown(cls, error: str | None = None) -> "CategoryResult":
        """Create an unknown/failed categorization result.

        Args:
            error: Optional error message

        Returns:
            CategoryResult with unknown subject and zero confidence
        """
        return cls(
            location=ImageLocation.EXTERIOR,
            subject=ImageSubject.UNKNOWN,
            confidence=0.0,
            error=error,
        )


class CategorizationError(Exception):
    """Raised when image categorization fails."""

    pass


class ImageCategorizer:
    """Categorize real estate images using Claude Vision.

    Uses Claude 3.5 Haiku for cost-effective batch categorization of
    property listing images. Supports both single image and batch
    processing with automatic rate limiting.
    """

    # Claude Vision categorization prompt
    CATEGORIZATION_PROMPT = """Analyze this real estate listing image and classify it.

Return JSON only (no markdown, no explanation):
{
    "location": "exterior" | "interior" | "systems" | "features",
    "subject": "<specific room/area type>",
    "confidence": 0.0-1.0,
    "features_detected": ["feature1", "feature2"],
    "alternatives": [{"subject": "other_type", "confidence": 0.5}]
}

Subject types by location:

EXTERIOR subjects:
- front: Front of house view
- rear: Back of house view
- pool: Swimming pool
- garage: Garage (interior or exterior)
- yard: Front or back yard
- aerial: Drone/satellite view
- driveway: Driveway view
- patio: Covered patio area
- courtyard: Enclosed courtyard

INTERIOR subjects:
- kitchen: Kitchen
- master: Master bedroom
- master_bath: Master bathroom
- bedroom: Other bedroom
- bathroom: Other bathroom
- living: Living room/family room
- dining: Dining room/area
- laundry: Laundry room
- office: Home office/den
- entry: Entry/foyer
- hallway: Hallway
- closet: Walk-in closet
- stairs: Staircase
- bonus: Bonus room/loft

SYSTEMS subjects (utility/mechanical):
- hvac: HVAC unit (full view)
- hvac_label: HVAC data label/sticker (useful for age estimation)
- electrical: Electrical panel
- water_heater: Water heater
- roof: Roof (close-up or detail)
- plumbing: Plumbing/pipes
- attic: Attic space

FEATURES subjects (special features):
- fireplace: Fireplace
- solar: Solar panels
- pool_equip: Pool equipment
- ceiling_fan: Ceiling fan detail
- built_in: Built-in shelving/cabinets
- flooring: Flooring detail

Rules:
1. "master" is master BEDROOM. "master_bath" is master BATHROOM.
2. For HVAC labels/stickers with model info, use "hvac_label" (valuable for age estimation).
3. Confidence should reflect certainty: clear shots = 0.9+, partial views = 0.6-0.8.
4. List 1-3 features detected (granite counters, stainless appliances, pool heater, etc.)
5. Include 1-2 alternative categories if uncertain.
6. Use "unknown" only when truly unidentifiable."""

    # Model configuration
    MODEL_ID = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 512
    API_BASE_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    # Rate limiting
    REQUESTS_PER_MINUTE = 50
    MIN_REQUEST_INTERVAL = 60.0 / REQUESTS_PER_MINUTE

    # Supported image formats
    SUPPORTED_MEDIA_TYPES = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model_id: str | None = None,
        max_concurrent: int = 5,
    ):
        """Initialize categorizer with API configuration.

        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
            model_id: Model to use (defaults to Claude 3.5 Haiku)
            max_concurrent: Maximum concurrent API requests
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_id = model_id or self.MODEL_ID
        self.max_concurrent = max_concurrent
        self._http_client: httpx.AsyncClient | None = None
        self._last_request_time: float = 0
        self._semaphore: asyncio.Semaphore | None = None

    @property
    def is_available(self) -> bool:
        """Check if categorization is available (API key present).

        Returns:
            True if API key is configured
        """
        return self.api_key is not None and len(self.api_key) > 0

    async def __aenter__(self) -> "ImageCategorizer":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "anthropic-version": self.API_VERSION,
                "x-api-key": self.api_key or "",
                "content-type": "application/json",
            },
        )
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def categorize(self, image_path: Path) -> CategoryResult:
        """Categorize a single image.

        Args:
            image_path: Path to image file

        Returns:
            CategoryResult with classification

        Raises:
            CategorizationError: If categorization fails
        """
        if not self.is_available:
            return CategoryResult.unknown("API key not configured - categorization disabled")

        if not image_path.exists():
            return CategoryResult.unknown(f"Image not found: {image_path}")

        # Validate file type
        suffix = image_path.suffix.lower()
        if suffix not in self.SUPPORTED_MEDIA_TYPES:
            return CategoryResult.unknown(f"Unsupported image format: {suffix}")

        try:
            # Encode image
            image_data = self._encode_image(image_path)
            media_type = self.SUPPORTED_MEDIA_TYPES[suffix]

            # Call Claude Vision API
            response = await self._call_vision_api(image_data, media_type)

            # Parse response
            return self._parse_response(response)

        except Exception as e:
            logger.error(f"Categorization failed for {image_path}: {e}")
            return CategoryResult.unknown(str(e))

    async def categorize_batch(
        self,
        image_paths: list[Path],
        progress_callback: Any | None = None,
    ) -> list[CategoryResult]:
        """Categorize multiple images efficiently.

        Uses concurrent API calls with rate limiting for batch processing.

        Args:
            image_paths: List of image file paths
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of CategoryResult in same order as input paths
        """
        if not self.is_available:
            logger.warning("API key not configured - returning unknown for all images")
            return [CategoryResult.unknown("API key not configured") for _ in image_paths]

        results: list[CategoryResult | None] = [None] * len(image_paths)
        completed = 0

        async def process_one(index: int, path: Path) -> None:
            nonlocal completed
            if self._semaphore:
                async with self._semaphore:
                    result = await self.categorize(path)
                    results[index] = result
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(image_paths))
            else:
                result = await self.categorize(path)
                results[index] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(image_paths))

        # Process all images concurrently (semaphore limits parallelism)
        tasks = [process_one(i, path) for i, path in enumerate(image_paths)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Replace None with unknown results (shouldn't happen, but safety)
        return [r if r is not None else CategoryResult.unknown("Processing error") for r in results]

    def _encode_image(self, path: Path) -> str:
        """Encode image file as base64.

        Args:
            path: Path to image file

        Returns:
            Base64 encoded string
        """
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    async def _call_vision_api(
        self,
        image_data: str,
        media_type: str,
    ) -> dict:
        """Call Claude Vision API with rate limiting.

        Args:
            image_data: Base64 encoded image
            media_type: MIME type of image

        Returns:
            API response dict

        Raises:
            CategorizationError: If API call fails
        """
        if not self._http_client:
            raise CategorizationError("HTTP client not initialized - use async context manager")

        # Rate limiting
        await self._rate_limit()

        # Build request
        payload = {
            "model": self.model_id,
            "max_tokens": self.MAX_TOKENS,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": self.CATEGORIZATION_PROMPT,
                        },
                    ],
                }
            ],
        }

        try:
            response = await self._http_client.post(
                self.API_BASE_URL,
                json=payload,
            )

            if response.status_code == 429:
                # Rate limited - wait and retry once
                retry_after = int(response.headers.get("retry-after", 60))
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                response = await self._http_client.post(
                    self.API_BASE_URL,
                    json=payload,
                )

            response.raise_for_status()
            from typing import cast

            return cast(dict[Any, Any], response.json())

        except httpx.HTTPStatusError as e:
            raise CategorizationError(
                f"API error {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise CategorizationError("API timeout") from e
        except Exception as e:
            raise CategorizationError(f"API call failed: {e}") from e

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        import time

        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            await asyncio.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.monotonic()

    def _parse_response(self, response: dict) -> CategoryResult:
        """Parse Claude API response into CategoryResult.

        Args:
            response: Raw API response

        Returns:
            CategoryResult parsed from response
        """
        try:
            # Extract text content from response
            content = response.get("content", [])
            if not content:
                return CategoryResult.unknown("Empty API response")

            text_content = ""
            for block in content:
                if block.get("type") == "text":
                    text_content = block.get("text", "")
                    break

            if not text_content:
                return CategoryResult.unknown("No text in API response")

            # Parse JSON from response (handle markdown code blocks)
            json_str = text_content.strip()
            if json_str.startswith("```"):
                # Remove markdown code fences
                lines = json_str.split("\n")
                json_str = "\n".join(line for line in lines if not line.strip().startswith("```"))

            data = json.loads(json_str)

            # Extract location and subject
            location = ImageLocation.from_string(data.get("location", "exterior"))
            subject = ImageSubject.from_string(data.get("subject", "unknown"))
            confidence = float(data.get("confidence", 0.5))

            # Extract features
            features = data.get("features_detected", [])
            if isinstance(features, str):
                features = [features]

            # Extract alternatives
            alternatives = []
            for alt in data.get("alternatives", []):
                alt_subject = ImageSubject.from_string(alt.get("subject", "unknown"))
                alt_conf = float(alt.get("confidence", 0.0))
                alternatives.append((alt_subject, alt_conf))

            return CategoryResult(
                location=location,
                subject=subject,
                confidence=confidence,
                features_detected=features,
                alternative_categories=alternatives,
                model_version=self.model_id,
                raw_response=data,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return CategoryResult.unknown(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return CategoryResult.unknown(str(e))


# Convenience function for standalone use
async def categorize_image(image_path: Path, api_key: str | None = None) -> CategoryResult:
    """Categorize a single image (convenience function).

    Args:
        image_path: Path to image file
        api_key: Optional API key (defaults to env var)

    Returns:
        CategoryResult with classification
    """
    async with ImageCategorizer(api_key=api_key) as categorizer:
        return await categorizer.categorize(image_path)
