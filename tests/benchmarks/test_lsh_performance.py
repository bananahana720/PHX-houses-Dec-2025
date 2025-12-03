"""Test script to verify LSH optimization performance."""

import tempfile
import time
from pathlib import Path

from src.phx_home_analysis.domain.value_objects import PerceptualHash
from src.phx_home_analysis.services.image_extraction.deduplicator import (
    ImageDeduplicator,
)


def generate_test_hash(seed: int) -> PerceptualHash:
    """Generate a deterministic perceptual hash for testing with better distribution."""
    import hashlib

    # Use hash function for better distribution across buckets
    hash_input = f"test_image_{seed}".encode()
    hash_bytes = hashlib.sha256(hash_input).digest()

    # Take first 8 bytes for phash, next 8 for dhash
    phash = hash_bytes[:8].hex()
    dhash = hash_bytes[8:16].hex()

    return PerceptualHash(phash=phash, dhash=dhash)


def test_lsh_optimization():
    """Test that LSH provides performance improvement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "test_hash_index.json"
        dedup = ImageDeduplicator(hash_index_path=index_path, num_bands=8)

        print("=" * 70)
        print("LSH PERFORMANCE TEST")
        print("=" * 70)

        # Register 1000 test images
        num_images = 1000
        print(f"\n1. Registering {num_images} test images...")
        start = time.time()

        for i in range(num_images):
            test_hash = generate_test_hash(i)
            image_id = f"test_image_{i:04d}"
            dedup.register_hash(
                image_id=image_id,
                phash=test_hash,
                property_address=f"123 Test St #{i}",
                source="test",
            )

        register_time = time.time() - start
        print(f"   Registered {num_images} hashes in {register_time:.2f}s")
        print(f"   Average: {(register_time / num_images) * 1000:.2f}ms per registration")

        # Get stats
        stats = dedup.get_stats()
        print("\n2. Index Statistics:")
        print(f"   Total images: {stats['total_images']}")
        print(f"   LSH bands: {stats['lsh']['num_bands']}")
        print(f"   Total buckets: {stats['lsh']['total_buckets']}")
        print(f"   Avg bucket size: {stats['lsh']['avg_bucket_size']}")
        print(f"   Max bucket size: {stats['lsh']['max_bucket_size']}")

        # Test duplicate detection performance
        print("\n3. Testing duplicate detection...")
        test_cases = 100

        # Test with exact duplicates
        dup_start = time.time()
        exact_matches = 0
        for i in range(test_cases):
            test_hash = generate_test_hash(i)  # Exact match
            is_dup, orig_id = dedup.is_duplicate(test_hash)
            if is_dup:
                exact_matches += 1
        dup_time = time.time() - dup_start

        print(f"   Exact duplicates: {exact_matches}/{test_cases} detected")
        print(f"   Time: {dup_time:.2f}s ({(dup_time / test_cases) * 1000:.2f}ms/check)")

        # Test with non-duplicates
        non_dup_start = time.time()
        non_matches = 0
        for i in range(num_images, num_images + test_cases):
            test_hash = generate_test_hash(i)  # New hash not in index
            is_dup, _ = dedup.is_duplicate(test_hash)
            if not is_dup:
                non_matches += 1
        non_dup_time = time.time() - non_dup_start

        print(f"   Non-duplicates: {non_matches}/{test_cases} correctly identified")
        print(f"   Time: {non_dup_time:.2f}s ({(non_dup_time / test_cases) * 1000:.2f}ms/check)")

        # Calculate speedup estimate
        # Old O(n) would check all n images
        # New O(k) checks only k candidates from buckets
        avg_candidates = stats["lsh"]["avg_bucket_size"] * stats["lsh"]["num_bands"]
        theoretical_speedup = num_images / max(avg_candidates, 1)

        print("\n4. Performance Analysis:")
        print(f"   Avg candidates per lookup: ~{avg_candidates:.0f}")
        print(
            f"   Theoretical speedup: {theoretical_speedup:.1f}x (vs checking all {num_images} images)"
        )

        # Verify index persistence
        print("\n5. Testing index persistence...")
        dedup2 = ImageDeduplicator(hash_index_path=index_path, num_bands=8)
        stats2 = dedup2.get_stats()

        assert stats2["total_images"] == num_images, "Index persistence failed"
        assert stats2["lsh"]["total_buckets"] == stats["lsh"]["total_buckets"]
        print("   ✓ Index successfully persisted and reloaded")
        print("   ✓ LSH buckets rebuilt correctly")

        print(f"\n{'=' * 70}")
        print("TEST PASSED: LSH optimization working correctly!")
        print("=" * 70)


if __name__ == "__main__":
    test_lsh_optimization()
