"""Image standardization service for format conversion and resizing.

Converts all property images to a consistent format (PNG) and dimensions
(max 1024x1024) for uniform AI model input.

Security: Includes image bomb (decompression bomb) protection.
"""

import logging
from io import BytesIO

from PIL import Image

# Security: Limit maximum image pixels to prevent decompression bombs
# 15000 x 15000 = 225 million pixels is a reasonable upper bound
# This must be set BEFORE any Image.open() calls
Image.MAX_IMAGE_PIXELS = 178956970  # ~15000 x 12000 pixels

logger = logging.getLogger(__name__)

# Security: Maximum raw file size before processing (50MB)
MAX_RAW_FILE_SIZE = 50 * 1024 * 1024


class ImageProcessingError(Exception):
    """Raised when image processing fails."""

    pass


class ImageStandardizer:
    """PNG conversion and size standardization service.

    Converts all images to PNG format with maximum dimension of 1024px
    while preserving aspect ratio. This ensures consistent input for
    AI model processing.
    """

    MAX_DIMENSION = 1024
    OUTPUT_FORMAT = "PNG"
    JPEG_QUALITY = 85  # For intermediate processing if needed

    def __init__(
        self,
        max_dimension: int = 1024,
        output_format: str = "PNG",
    ):
        """Initialize standardizer with configuration.

        Args:
            max_dimension: Maximum width or height in pixels
            output_format: Output image format (PNG recommended)
        """
        self.max_dimension = max_dimension
        self.output_format = output_format

    def standardize(self, image_data: bytes) -> bytes:
        """Convert image to standard format and size.

        Security controls:
        - File size check: Rejects files > 50MB before processing
        - Pixel limit: PIL.Image.MAX_IMAGE_PIXELS prevents decompression bombs

        Args:
            image_data: Raw image bytes in any supported format

        Returns:
            Standardized image as PNG bytes

        Raises:
            ImageProcessingError: If image cannot be processed or exceeds security limits
        """
        # Security: Check raw file size BEFORE opening
        if len(image_data) > MAX_RAW_FILE_SIZE:
            raise ImageProcessingError(
                f"File size {len(image_data)} bytes exceeds maximum "
                f"of {MAX_RAW_FILE_SIZE} bytes (50MB)"
            )

        try:
            # Note: PIL.Image.MAX_IMAGE_PIXELS (set at module level) provides
            # additional protection against decompression bombs
            img = Image.open(BytesIO(image_data))

            # Convert color mode
            img = self._convert_color_mode(img)

            # Resize if needed
            img = self._resize_if_needed(img)

            # Convert to PNG
            output = BytesIO()
            img.save(output, format=self.output_format, optimize=True)

            result = output.getvalue()
            logger.debug(
                f"Standardized image: {len(image_data)} -> {len(result)} bytes, "
                f"{img.size[0]}x{img.size[1]}"
            )

            return result

        except Exception as e:
            raise ImageProcessingError(f"Failed to standardize image: {e}") from e

    def _convert_color_mode(self, img: Image.Image) -> Image.Image:
        """Convert image to RGB color mode.

        Handles RGBA (with alpha), P (palette), L (grayscale), and other modes.

        Args:
            img: PIL Image object

        Returns:
            Image in RGB mode
        """
        if img.mode == "RGB":
            return img

        if img.mode == "RGBA":
            # Create white background and paste image with alpha
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            return background

        if img.mode == "P":
            # Palette mode - may have transparency
            if "transparency" in img.info:
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                return background
            return img.convert("RGB")

        if img.mode == "L":
            # Grayscale - convert to RGB
            return img.convert("RGB")

        if img.mode == "LA":
            # Grayscale with alpha
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background

        # Default: try direct conversion
        return img.convert("RGB")

    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimension.

        Preserves aspect ratio using high-quality Lanczos resampling.

        Args:
            img: PIL Image object

        Returns:
            Resized image (or original if within bounds)
        """
        width, height = img.size

        if max(width, height) <= self.max_dimension:
            return img

        # Calculate new dimensions preserving aspect ratio
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))

        logger.debug(f"Resizing: {width}x{height} -> {new_width}x{new_height}")

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def is_valid_image(self, image_data: bytes) -> bool:
        """Validate that bytes represent a valid image.

        Includes security checks for file size limits.

        Args:
            image_data: Raw bytes to validate

        Returns:
            True if valid image, False otherwise (including security failures)
        """
        # Security: Reject oversized files
        if len(image_data) > MAX_RAW_FILE_SIZE:
            return False

        try:
            img = Image.open(BytesIO(image_data))
            img.verify()
            return True
        except Exception:
            return False

    def get_dimensions(self, image_data: bytes) -> tuple[int, int]:
        """Get image width and height.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (width, height)

        Raises:
            ImageProcessingError: If image cannot be read
        """
        try:
            img = Image.open(BytesIO(image_data))
            return img.size
        except Exception as e:
            raise ImageProcessingError(f"Failed to get dimensions: {e}") from e

    def get_format(self, image_data: bytes) -> str | None:
        """Detect image format from bytes.

        Args:
            image_data: Raw image bytes

        Returns:
            Format string (e.g., "JPEG", "PNG", "WEBP") or None
        """
        try:
            img = Image.open(BytesIO(image_data))
            return img.format
        except Exception:
            return None

    def get_info(self, image_data: bytes) -> dict:
        """Get comprehensive image information.

        Args:
            image_data: Raw image bytes

        Returns:
            Dict with image metadata
        """
        try:
            img = Image.open(BytesIO(image_data))
            return {
                "format": img.format,
                "mode": img.mode,
                "width": img.size[0],
                "height": img.size[1],
                "size_bytes": len(image_data),
                "has_alpha": img.mode in ("RGBA", "LA", "PA"),
                "is_animated": getattr(img, "is_animated", False),
                "needs_resize": max(img.size) > self.max_dimension,
            }
        except Exception as e:
            return {"error": str(e)}
