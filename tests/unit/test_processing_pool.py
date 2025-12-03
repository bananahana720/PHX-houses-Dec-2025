"""Unit tests for multiprocess image processing pool."""
from io import BytesIO

import pytest
from PIL import Image

from src.phx_home_analysis.services.image_extraction.processing_pool import (
    ImageProcessingPool,
    ProcessedImage,
)


@pytest.mark.asyncio
async def test_process_single_image():
    """Test processing a single image."""
    # Create test image
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_data = buffer.getvalue()

    async with ImageProcessingPool(max_workers=2) as pool:
        result = await pool.process_image(image_data)

    assert isinstance(result, ProcessedImage)
    assert len(result.phash) == 16  # 64-bit hash as hex
    assert len(result.dhash) == 16
    assert result.width == 100
    assert result.height == 100
    assert result.processing_time_ms > 0
    assert result.original_size > 0
    assert len(result.standardized_data) > 0


@pytest.mark.asyncio
async def test_process_oversized_image():
    """Test that large images are resized."""
    img = Image.new("RGB", (2000, 2000), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    async with ImageProcessingPool(max_workers=2, max_dimension=1024) as pool:
        result = await pool.process_image(buffer.getvalue())

    assert max(result.width, result.height) <= 1024
    assert result.width == result.height  # Should maintain aspect ratio (square input)


@pytest.mark.asyncio
async def test_process_rgba_image():
    """Test that RGBA images are converted to RGB."""
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    async with ImageProcessingPool(max_workers=2) as pool:
        result = await pool.process_image(buffer.getvalue())

    # Should succeed without error
    assert isinstance(result, ProcessedImage)
    assert result.width == 100
    assert result.height == 100


@pytest.mark.asyncio
async def test_process_batch():
    """Test batch processing multiple images."""
    images = []
    for i in range(5):
        img = Image.new("RGB", (50, 50), color=("red", "blue", "green", "yellow", "purple")[i])
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        images.append(buffer.getvalue())

    completed_count = 0

    def on_complete(result: ProcessedImage):
        nonlocal completed_count
        completed_count += 1

    async with ImageProcessingPool(max_workers=2) as pool:
        results = await pool.process_batch(images, on_complete=on_complete)

    assert len(results) == 5
    assert completed_count == 5
    assert all(isinstance(r, ProcessedImage) for r in results)


@pytest.mark.asyncio
async def test_pool_context_manager_required():
    """Test that pool must be used with context manager."""
    pool = ImageProcessingPool(max_workers=2)

    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    with pytest.raises(RuntimeError, match="Pool not started"):
        await pool.process_image(buffer.getvalue())


@pytest.mark.asyncio
async def test_hash_consistency():
    """Test that identical images produce identical hashes."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_data = buffer.getvalue()

    async with ImageProcessingPool(max_workers=2) as pool:
        result1 = await pool.process_image(image_data)
        result2 = await pool.process_image(image_data)

    assert result1.phash == result2.phash
    assert result1.dhash == result2.dhash


@pytest.mark.asyncio
async def test_different_images_different_hashes():
    """Test that different images produce different hashes."""
    # Create more complex images with patterns (solid colors can produce same hashes)
    img1 = Image.new("RGB", (100, 100))
    for x in range(100):
        for y in range(100):
            img1.putpixel((x, y), (x * 2, y * 2, 0))
    buffer1 = BytesIO()
    img1.save(buffer1, format="PNG")

    img2 = Image.new("RGB", (100, 100))
    for x in range(100):
        for y in range(100):
            img2.putpixel((x, y), (0, x * 2, y * 2))
    buffer2 = BytesIO()
    img2.save(buffer2, format="PNG")

    async with ImageProcessingPool(max_workers=2) as pool:
        result1 = await pool.process_image(buffer1.getvalue())
        result2 = await pool.process_image(buffer2.getvalue())

    # Different images with patterns should have different hashes
    assert result1.phash != result2.phash or result1.dhash != result2.dhash


@pytest.mark.asyncio
async def test_processing_time_recorded():
    """Test that processing time is recorded."""
    img = Image.new("RGB", (500, 500), color="red")
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    async with ImageProcessingPool(max_workers=2) as pool:
        result = await pool.process_image(buffer.getvalue())

    assert result.processing_time_ms > 0
    # Should take at least some minimal time
    assert result.processing_time_ms > 0.001  # More than 1 microsecond
