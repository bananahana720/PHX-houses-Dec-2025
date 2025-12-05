"""Image standardization service for format conversion and resizing.

Converts all property images to a consistent format (PNG) and dimensions
(max 1024x1024) for uniform AI model input.

Security: Includes image bomb (decompression bomb) protection.
"""

import logging
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    pass

# Security: Limit maximum image pixels to prevent decompression bombs
# 15000 x 15000 = 225 million pixels is a reasonable upper bound
# This must be set BEFORE any Image.open() calls
Image.MAX_IMAGE_PIXELS = 178956970  # ~15000 x 12000 pixels

logger = logging.getLogger(__name__)

# Security: Maximum raw file size before processing (50MB)
MAX_RAW_FILE_SIZE = 50 * 1024 * 1024

# Security: Magic byte signatures for supported image formats
MAGIC_SIGNATURES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
}


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

    def _validate_magic_bytes(self, data: bytes) -> str:
        """Validate file content matches expected image format.

        Security control: Verifies magic bytes before PIL processing to prevent
        malicious content disguised as images from bypassing validation.

        Args:
            data: Raw image bytes

        Returns:
            Detected MIME type

        Raises:
            ImageProcessingError: If magic bytes don't match known image formats
        """
        # Check standard signatures
        for magic, mime_type in MAGIC_SIGNATURES.items():
            if data.startswith(magic):
                return mime_type

        # WebP special case: RIFF container with WEBP identifier
        if len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return 'image/webp'

        # Log rejected file for security audit
        logger.warning(
            "Rejected file with invalid magic bytes: first 16 bytes = %s",
            data[:16].hex() if len(data) >= 16 else data.hex()
        )

        raise ImageProcessingError(
            "Invalid magic bytes - file content does not match recognized image format"
        )

    def standardize(self, image_data: bytes) -> bytes:
        """Convert image to standard format and size.

        Security controls:
        - File size check: Rejects files > 50MB before processing
        - Magic byte validation: Verifies file content matches image format
        - Pixel limit: PIL.Image.MAX_IMAGE_PIXELS prevents decompression bombs
        - EXIF stripping: Removes all metadata to prevent GPS leaks and injection attacks

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

        # Security: Validate magic bytes BEFORE PIL processing
        detected_mime = self._validate_magic_bytes(image_data)
        logger.debug(f"Magic byte validation passed: {detected_mime}")

        try:
            # Note: PIL.Image.MAX_IMAGE_PIXELS (set at module level) provides
            # additional protection against decompression bombs
            img: Image.Image = Image.open(BytesIO(image_data))

            # Convert color mode
            img = self._convert_color_mode(img)

            # Security: Strip all EXIF/metadata
            img = self._strip_metadata(img)

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

    def _strip_metadata(self, img: Image.Image) -> Image.Image:
        """Remove all EXIF and metadata from image.

        Creates a clean copy of the image with no embedded metadata,
        preventing privacy leaks (GPS data) and potential injection attacks.

        Args:
            img: PIL Image object (may contain EXIF data)

        Returns:
            New PIL Image with all metadata removed
        """
        # Check if image had EXIF data before stripping
        had_exif = False
        if hasattr(img, '_getexif') and img._getexif():
            had_exif = True
        elif hasattr(img, 'info') and img.info:
            had_exif = True

        # Get raw pixel data
        data = list(img.getdata())

        # Create new image with same mode and size but no metadata
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)

        if had_exif:
            logger.debug("Stripped EXIF metadata from image")

        return clean_img

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

        Includes security checks for file size limits and magic bytes.

        Args:
            image_data: Raw bytes to validate

        Returns:
            True if valid image, False otherwise (including security failures)
        """
        # Security: Reject oversized files
        if len(image_data) > MAX_RAW_FILE_SIZE:
            return False

        try:
            # Security: Validate magic bytes first
            self._validate_magic_bytes(image_data)

            # Verify PIL can parse the image
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
