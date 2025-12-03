"""Multiprocess image processing pool for CPU-bound operations.

Offloads hash computation and image standardization to worker processes,
keeping the main event loop responsive for I/O operations.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ProcessedImage:
    """Result of processing an image in worker process."""

    phash: str
    dhash: str
    standardized_data: bytes
    width: int
    height: int
    original_size: int
    processing_time_ms: float


class ImageProcessingPool:
    """Process pool for CPU-bound image operations.

    Uses ProcessPoolExecutor to parallelize:
    - Perceptual hash computation (pHash + dHash)
    - Image standardization (format conversion, resize)

    This keeps the async event loop responsive for network I/O
    while CPU-intensive work runs on separate cores.

    Example:
        ```python
        async with ImageProcessingPool(max_workers=4) as pool:
            result = await pool.process_image(image_bytes)
            print(f"pHash: {result.phash}, size: {result.width}x{result.height}")
        ```
    """

    def __init__(self, max_workers: int | None = None, max_dimension: int = 1024):
        """Initialize the processing pool.

        Args:
            max_workers: Number of worker processes. Defaults to CPU count - 1.
            max_dimension: Maximum dimension for standardized images.
        """
        self.max_workers = max_workers or max(2, os.cpu_count() - 1)
        self.max_dimension = max_dimension
        self._executor: ProcessPoolExecutor | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        logger.info(
            "ImageProcessingPool initialized with %d workers, max_dimension=%d",
            self.max_workers,
            self.max_dimension,
        )

    async def __aenter__(self) -> ImageProcessingPool:
        """Start the process pool."""
        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self._loop = asyncio.get_event_loop()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Shutdown the process pool."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        self._loop = None

    async def process_image(self, image_data: bytes) -> ProcessedImage:
        """Process an image in a worker process.

        Computes perceptual hashes and standardizes the image format.

        Args:
            image_data: Raw image bytes (JPEG, PNG, WebP, GIF)

        Returns:
            ProcessedImage with hashes, standardized data, and dimensions

        Raises:
            ValueError: If image data is invalid
            RuntimeError: If pool is not started
        """
        if not self._executor or not self._loop:
            raise RuntimeError("Pool not started. Use 'async with' context manager.")

        result = await self._loop.run_in_executor(
            self._executor,
            _process_image_worker,
            image_data,
            self.max_dimension,
        )

        return result

    async def process_batch(
        self,
        images: list[bytes],
        on_complete: Callable | None = None,
    ) -> list[ProcessedImage]:
        """Process multiple images concurrently.

        Args:
            images: List of raw image bytes
            on_complete: Optional callback called after each image completes

        Returns:
            List of ProcessedImage results (same order as input)
        """
        tasks = [self.process_image(img) for img in images]
        results = []

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            if on_complete:
                on_complete(result)

        return results


def _process_image_worker(image_data: bytes, max_dimension: int) -> ProcessedImage:
    """Worker function - runs in separate process.

    IMPORTANT: This function must be at module level (not a method)
    to be picklable for multiprocessing.
    """
    start = time.perf_counter()

    import imagehash
    from PIL import Image

    original_size = len(image_data)

    # Open image
    img = Image.open(BytesIO(image_data))

    # Compute perceptual hashes (CPU-intensive)
    phash = str(imagehash.phash(img))
    dhash = str(imagehash.dhash(img))

    # Standardize image
    # Convert color mode
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode not in ("RGB",):
        img = img.convert("RGB")

    # Strip metadata by copying pixel data
    data = list(img.getdata())
    clean_img = Image.new("RGB", img.size)
    clean_img.putdata(data)
    img = clean_img

    # Resize if needed
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Save as PNG
    output = BytesIO()
    img.save(output, format="PNG", optimize=True)
    standardized_data = output.getvalue()

    elapsed_ms = (time.perf_counter() - start) * 1000

    return ProcessedImage(
        phash=phash,
        dhash=dhash,
        standardized_data=standardized_data,
        width=img.size[0],
        height=img.size[1],
        original_size=original_size,
        processing_time_ms=elapsed_ms,
    )


# Shared pool instance
_default_pool: ImageProcessingPool | None = None


async def get_processing_pool() -> ImageProcessingPool:
    """Get or create the default processing pool.

    Returns a shared pool instance for the application.
    """
    global _default_pool
    if _default_pool is None:
        _default_pool = ImageProcessingPool()
        await _default_pool.__aenter__()
    return _default_pool


async def shutdown_processing_pool() -> None:
    """Shutdown the default processing pool."""
    global _default_pool
    if _default_pool:
        await _default_pool.__aexit__(None, None, None)
        _default_pool = None
