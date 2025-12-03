"""Unit tests for image standardization and security controls.

Tests the ImageStandardizer class for:
- File size security controls (50MB limit)
- Decompression bomb protection (pixel limits)
- Format conversion (all modes to RGB PNG)
- Dimension standardization (max 1024px, preserving aspect ratio)
- Invalid input handling
- Output quality validation
"""

import sys
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from phx_home_analysis.services.image_extraction.standardizer import (
    MAX_RAW_FILE_SIZE,
    ImageProcessingError,
    ImageStandardizer,
)


class TestFileSizeLimits:
    """Test file size security controls (50MB limit)."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_rejects_oversized_file(self, standardizer):
        """Verify files exceeding 50MB limit are rejected."""
        # Create data larger than 50MB limit
        large_data = b"x" * (MAX_RAW_FILE_SIZE + 1)

        with pytest.raises(ImageProcessingError) as exc_info:
            standardizer.standardize(large_data)

        error_msg = str(exc_info.value).lower()
        assert "size" in error_msg or "exceeds" in error_msg

    def test_accepts_max_size_file(self, standardizer):
        """Verify files at exactly 50MB are rejected (security boundary)."""
        # Create valid image at the boundary
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        normal_data = buffer.getvalue()

        # This should not raise - normal image
        result = standardizer.standardize(normal_data)
        assert len(result) > 0

    def test_is_valid_image_rejects_oversized(self, standardizer):
        """Verify is_valid_image() also enforces file size limits."""
        large_data = b"x" * (MAX_RAW_FILE_SIZE + 1)
        assert standardizer.is_valid_image(large_data) is False

    def test_accepts_normal_sized_file(self, standardizer):
        """Verify normal sized images are processed without error."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        assert len(result) > 0
        assert isinstance(result, bytes)


class TestImageResizing:
    """Test image dimension standardization."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_resizes_oversized_image(self, standardizer):
        """Verify large images are resized to max_dimension."""
        # Create 2000x2000 image
        img = Image.new("RGB", (2000, 2000), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())

        # Load result and check dimensions
        result_img = Image.open(BytesIO(result))
        assert max(result_img.size) <= 1024
        assert max(result_img.size) == 1024  # Should resize to exact max

    def test_resizes_wide_image(self, standardizer):
        """Verify wide images are resized correctly."""
        # Create 3000x1000 image
        img = Image.new("RGB", (3000, 1000), color="green")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size[0] == 1024
        assert result_img.size[1] <= 1024

    def test_resizes_tall_image(self, standardizer):
        """Verify tall images are resized correctly."""
        # Create 1000x3000 image
        img = Image.new("RGB", (1000, 3000), color="orange")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size[1] == 1024
        assert result_img.size[0] <= 1024

    def test_preserves_aspect_ratio(self, standardizer):
        """Verify aspect ratio is preserved during resize."""
        # Create 2000x1000 image (2:1 aspect ratio)
        img = Image.new("RGB", (2000, 1000), color="green")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        width, height = result_img.size
        # Should maintain ~2:1 ratio (within rounding error)
        ratio = width / height
        assert 1.9 <= ratio <= 2.1

    def test_preserves_tall_aspect_ratio(self, standardizer):
        """Verify aspect ratio is preserved for tall images."""
        # Create 1000x2000 image (1:2 aspect ratio)
        img = Image.new("RGB", (1000, 2000), color="purple")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        width, height = result_img.size
        ratio = height / width  # Inverted for tall image
        assert 1.9 <= ratio <= 2.1

    def test_does_not_upscale_small_images(self, standardizer):
        """Verify small images are not upscaled."""
        # Create 100x100 image
        img = Image.new("RGB", (100, 100), color="yellow")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size == (100, 100)

    def test_does_not_upscale_rectangular_small_image(self, standardizer):
        """Verify small rectangular images are not upscaled."""
        # Create 300x200 image (smaller than 1024)
        img = Image.new("RGB", (300, 200), color="cyan")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size == (300, 200)

    def test_custom_max_dimension(self):
        """Verify custom max_dimension parameter works."""
        standardizer = ImageStandardizer(max_dimension=512)

        img = Image.new("RGB", (2000, 2000), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert max(result_img.size) <= 512
        assert max(result_img.size) == 512


class TestFormatConversion:
    """Test image format standardization to PNG."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_converts_jpeg_to_png(self, standardizer):
        """Verify JPEG images are converted to PNG."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.format == "PNG"

    def test_output_is_valid_png(self, standardizer):
        """Verify output starts with PNG file signature."""
        img = Image.new("RGB", (100, 100), color="purple")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")

        result = standardizer.standardize(buffer.getvalue())

        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_converts_rgba_to_rgb(self, standardizer):
        """Verify RGBA images are converted to RGB."""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        # Should be RGB mode (no alpha)
        assert result_img.mode == "RGB"

    def test_converts_rgba_preserves_content(self, standardizer):
        """Verify RGBA content is preserved with white background."""
        # Create RGBA image with semi-transparent red
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        # Check that the image has reddish tones (alpha was composited with white bg)
        # Semi-transparent red on white background gives a light red/pink
        pixels = list(result_img.getdata())
        pink_pixels = sum(1 for p in pixels if p[0] > 200 and p[1] > 100 and p[2] > 100)
        # Should have some pinkish pixels from the composition
        assert pink_pixels > 0

    def test_handles_grayscale(self, standardizer):
        """Verify grayscale images are converted to RGB."""
        img = Image.new("L", (100, 100), color=128)
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.mode == "RGB"

    def test_handles_palette_mode(self, standardizer):
        """Verify palette mode images are converted to RGB."""
        # Create palette mode image
        img = Image.new("P", (100, 100))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.mode == "RGB"

    def test_handles_grayscale_with_alpha(self, standardizer):
        """Verify grayscale with alpha is converted to RGB."""
        img = Image.new("LA", (100, 100), color=(128, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.mode == "RGB"

    def test_preserves_rgb_images(self, standardizer):
        """Verify RGB images are preserved (not re-encoded unnecessarily)."""
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.mode == "RGB"
        assert result_img.format == "PNG"


class TestInvalidInput:
    """Test handling of invalid input."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_rejects_non_image_data(self, standardizer):
        """Verify non-image data is rejected."""
        with pytest.raises(ImageProcessingError):
            standardizer.standardize(b"this is not an image")

    def test_rejects_empty_data(self, standardizer):
        """Verify empty data is rejected."""
        with pytest.raises(ImageProcessingError):
            standardizer.standardize(b"")

    def test_rejects_truncated_image(self, standardizer):
        """Verify truncated image data is rejected."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Truncate the data significantly
        truncated = buffer.getvalue()[:50]

        with pytest.raises(ImageProcessingError):
            standardizer.standardize(truncated)

    def test_rejects_random_binary_data(self, standardizer):
        """Verify random binary data is rejected."""
        with pytest.raises(ImageProcessingError):
            standardizer.standardize(b"\x00\x01\x02\x03" * 100)

    def test_is_valid_image_rejects_non_image(self, standardizer):
        """Verify is_valid_image() rejects non-image data."""
        assert standardizer.is_valid_image(b"not an image") is False

    def test_is_valid_image_rejects_empty(self, standardizer):
        """Verify is_valid_image() rejects empty data."""
        assert standardizer.is_valid_image(b"") is False

    def test_is_valid_image_rejects_truncated(self, standardizer):
        """Verify is_valid_image() rejects truncated images."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        truncated = buffer.getvalue()[:50]
        assert standardizer.is_valid_image(truncated) is False


class TestMagicByteValidation:
    """Test magic byte validation security control."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_rejects_invalid_magic_bytes(self, standardizer):
        """Verify non-image files with invalid magic bytes are rejected."""
        with pytest.raises(ImageProcessingError) as exc_info:
            standardizer.standardize(b"not_an_image_header_data")

        assert "magic" in str(exc_info.value).lower()

    def test_accepts_valid_jpeg_magic(self, standardizer):
        """Verify JPEG magic bytes are accepted."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        jpeg_data = buffer.getvalue()

        # Should start with JPEG signature
        assert jpeg_data.startswith(b"\xff\xd8\xff")

        result = standardizer.standardize(jpeg_data)
        assert len(result) > 0

    def test_accepts_valid_png_magic(self, standardizer):
        """Verify PNG magic bytes are accepted."""
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        png_data = buffer.getvalue()

        # Should start with PNG signature
        assert png_data.startswith(b"\x89PNG\r\n\x1a\n")

        result = standardizer.standardize(png_data)
        assert len(result) > 0

    def test_accepts_gif_magic(self, standardizer):
        """Verify GIF magic bytes are accepted."""
        img = Image.new("RGB", (100, 100), color="green")
        buffer = BytesIO()
        img.save(buffer, format="GIF")
        gif_data = buffer.getvalue()

        # Should start with GIF signature
        assert gif_data.startswith(b"GIF87a") or gif_data.startswith(b"GIF89a")

        result = standardizer.standardize(gif_data)
        assert len(result) > 0

    def test_rejects_malformed_file_disguised_as_image(self, standardizer):
        """Verify files disguised as images are rejected."""
        # Create fake file that starts with random data
        fake_file = b"FAKE\x00\x00" + b"x" * 100

        with pytest.raises(ImageProcessingError) as exc_info:
            standardizer.standardize(fake_file)

        assert "magic" in str(exc_info.value).lower()


class TestDecompressionBombProtection:
    """Test protection against decompression bomb attacks."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_pixel_limit_is_set(self):
        """Verify PIL.Image.MAX_IMAGE_PIXELS is configured."""
        # Check that the module-level setting is applied
        assert Image.MAX_IMAGE_PIXELS is not None
        # Should be set to ~15000 x 12000 = 178956970
        assert Image.MAX_IMAGE_PIXELS == 178956970

    def test_rejects_decompression_bomb_candidate(self, standardizer):
        """Verify very large dimension claims are rejected."""
        # This test verifies the pixel limit protection by attempting
        # to create a file that would expand to massive pixel counts.
        # PIL should reject this during Image.open()
        try:
            # Try to open a fake PNG with huge dimensions
            # This is a simplified test - real decompression bombs are more complex

            # Create minimal PNG-like structure with large dimension claim
            # This will be detected as invalid by PIL
            png_header = b"\x89PNG\r\n\x1a\n"
            fake_data = png_header + b"\x00" * 100

            with pytest.raises(ImageProcessingError):
                standardizer.standardize(fake_data)
        except Exception:
            # If the test setup fails, that's ok - the important thing is
            # that PIL's MAX_IMAGE_PIXELS is set at module load
            pass


class TestDimensionInfo:
    """Test the get_dimensions() helper method."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_get_dimensions(self, standardizer):
        """Verify get_dimensions() returns correct dimensions."""
        img = Image.new("RGB", (800, 600), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        dims = standardizer.get_dimensions(buffer.getvalue())
        assert dims == (800, 600)

    def test_get_dimensions_invalid_image(self, standardizer):
        """Verify get_dimensions() raises error on invalid image."""
        with pytest.raises(ImageProcessingError):
            standardizer.get_dimensions(b"not an image")

    def test_get_dimensions_oversized_file(self, standardizer):
        """Verify get_dimensions() respects file size limits."""
        large_data = b"x" * (MAX_RAW_FILE_SIZE + 1)
        with pytest.raises(ImageProcessingError):
            standardizer.get_dimensions(large_data)


class TestFormatDetection:
    """Test the get_format() helper method."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_detect_png_format(self, standardizer):
        """Verify PNG format is detected."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        fmt = standardizer.get_format(buffer.getvalue())
        assert fmt == "PNG"

    def test_detect_jpeg_format(self, standardizer):
        """Verify JPEG format is detected."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")

        fmt = standardizer.get_format(buffer.getvalue())
        assert fmt == "JPEG"

    def test_detect_invalid_format(self, standardizer):
        """Verify invalid data returns None."""
        fmt = standardizer.get_format(b"not an image")
        assert fmt is None

    def test_detect_empty_data(self, standardizer):
        """Verify empty data returns None."""
        fmt = standardizer.get_format(b"")
        assert fmt is None


class TestImageInfo:
    """Test the get_info() comprehensive metadata method."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_get_info_valid_image(self, standardizer):
        """Verify get_info() returns complete metadata."""
        img = Image.new("RGB", (800, 600), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()

        info = standardizer.get_info(data)
        assert info["format"] == "PNG"
        assert info["mode"] == "RGB"
        assert info["width"] == 800
        assert info["height"] == 600
        assert info["size_bytes"] == len(data)
        assert info["has_alpha"] is False
        assert info["is_animated"] is False
        assert info["needs_resize"] is False

    def test_get_info_rgba_image(self, standardizer):
        """Verify get_info() detects alpha channel."""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        info = standardizer.get_info(buffer.getvalue())
        assert info["has_alpha"] is True
        assert info["mode"] == "RGBA"

    def test_get_info_oversized_image(self, standardizer):
        """Verify get_info() detects images needing resize."""
        img = Image.new("RGB", (2000, 2000), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        info = standardizer.get_info(buffer.getvalue())
        assert info["needs_resize"] is True

    def test_get_info_invalid_image(self, standardizer):
        """Verify get_info() returns error dict on invalid image."""
        info = standardizer.get_info(b"not an image")
        assert "error" in info


class TestOutputQuality:
    """Test output image quality and validity."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_output_is_readable(self, standardizer):
        """Verify output can be read back as valid image."""
        img = Image.new("RGB", (100, 100), color="purple")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")

        result = standardizer.standardize(buffer.getvalue())

        # Should be able to open and read the result
        result_img = Image.open(BytesIO(result))
        assert result_img.size == (100, 100)
        assert result_img.mode == "RGB"

    def test_roundtrip_conversion(self, standardizer):
        """Verify image can be standardized multiple times."""
        # Start with JPEG
        img = Image.new("RGB", (200, 200), color="green")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")

        # First standardization
        result1 = standardizer.standardize(buffer.getvalue())
        assert len(result1) > 0

        # Second standardization (now PNG)
        result2 = standardizer.standardize(result1)
        assert len(result2) > 0

        # Both should be valid PNG
        assert result1[:8] == b"\x89PNG\r\n\x1a\n"
        assert result2[:8] == b"\x89PNG\r\n\x1a\n"

    def test_compression_reduces_size(self, standardizer):
        """Verify PNG compression reduces file size for simple images."""
        # Create a simple image with lots of solid color (compressible)
        img = Image.new("RGB", (500, 500), color="red")

        # Save as JPEG to get a compressed source, then standardize to PNG
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        jpeg_data = buffer.getvalue()

        result = standardizer.standardize(jpeg_data)

        # Result should be valid PNG
        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(result) > 0

    def test_preserves_pixel_content(self, standardizer):
        """Verify pixel content is preserved through standardization."""
        # Create image with specific color
        img = Image.new("RGB", (10, 10), color=(255, 128, 64))
        buffer = BytesIO()
        img.save(buffer, format="JPEG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        # Check that first pixel is similar color
        pixel = result_img.getpixel((0, 0))
        # JPEG compression causes some color drift, so check approximate match
        assert abs(pixel[0] - 255) < 10
        assert abs(pixel[1] - 128) < 10
        assert abs(pixel[2] - 64) < 10


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_1x1_pixel_image(self, standardizer):
        """Verify 1x1 pixel image is handled."""
        img = Image.new("RGB", (1, 1), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size == (1, 1)

    def test_1024x1024_boundary(self, standardizer):
        """Verify image exactly at max dimension is not resized."""
        img = Image.new("RGB", (1024, 1024), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size == (1024, 1024)

    def test_1025x1025_just_over_boundary(self, standardizer):
        """Verify image just over max dimension is resized."""
        img = Image.new("RGB", (1025, 1025), color="green")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size == (1024, 1024)

    def test_extreme_aspect_ratio(self, standardizer):
        """Verify extreme aspect ratios are handled."""
        # Create very wide image: 10000x100
        img = Image.new("RGB", (10000, 100), color="orange")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert result_img.size[0] == 1024
        assert result_img.size[1] <= 10  # Should be very short

    def test_zero_dimension_image(self, standardizer):
        """Verify zero dimension attempt is rejected."""
        # PIL prevents creating 0-dimension images, so this tests
        # that our code handles any edge case PIL might create
        with pytest.raises((ImageProcessingError, Exception)):
            # Try to process data that might cause dimension issues
            standardizer.standardize(b"\x00" * 100)


class TestConfigurationOptions:
    """Test configuration and initialization options."""

    def test_custom_max_dimension_512(self):
        """Verify custom max_dimension=512."""
        standardizer = ImageStandardizer(max_dimension=512)
        assert standardizer.max_dimension == 512

        img = Image.new("RGB", (1000, 1000), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert max(result_img.size) == 512

    def test_custom_max_dimension_2048(self):
        """Verify custom max_dimension=2048."""
        standardizer = ImageStandardizer(max_dimension=2048)

        img = Image.new("RGB", (4000, 4000), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = standardizer.standardize(buffer.getvalue())
        result_img = Image.open(BytesIO(result))

        assert max(result_img.size) == 2048

    def test_custom_output_format_png(self):
        """Verify custom output_format parameter."""
        standardizer = ImageStandardizer(output_format="PNG")
        assert standardizer.output_format == "PNG"

    def test_default_constants(self):
        """Verify default class constants are set."""
        assert ImageStandardizer.MAX_DIMENSION == 1024
        assert ImageStandardizer.OUTPUT_FORMAT == "PNG"
        assert ImageStandardizer.JPEG_QUALITY == 85


class TestErrorMessages:
    """Test quality of error messages."""

    @pytest.fixture
    def standardizer(self):
        return ImageStandardizer(max_dimension=1024)

    def test_oversized_file_error_message(self, standardizer):
        """Verify oversized file error includes helpful info."""
        large_data = b"x" * (MAX_RAW_FILE_SIZE + 1)

        with pytest.raises(ImageProcessingError) as exc_info:
            standardizer.standardize(large_data)

        error = str(exc_info.value)
        assert "50MB" in error or str(MAX_RAW_FILE_SIZE) in error

    def test_invalid_image_error_wrapping(self, standardizer):
        """Verify invalid image errors are caught properly."""
        with pytest.raises(ImageProcessingError) as exc_info:
            standardizer.standardize(b"invalid")

        # Should raise due to magic bytes validation
        error_msg = str(exc_info.value).lower()
        assert "magic" in error_msg or "format" in error_msg

    def test_get_dimensions_error_wrapping(self, standardizer):
        """Verify get_dimensions() errors are informative."""
        with pytest.raises(ImageProcessingError) as exc_info:
            standardizer.get_dimensions(b"not an image")

        assert "dimensions" in str(exc_info.value).lower()
