# Test Organization

### 11 Test Classes (53 Tests Total)

```
TestHashComputation (9 tests)
├── test_compute_hash_returns_perceptual_hash
├── test_phash_is_valid_hex_string
├── test_dhash_is_valid_hex_string
├── test_identical_images_produce_identical_hashes
├── test_different_images_produce_different_hashes
├── test_compute_hash_with_rgba_image
├── test_compute_hash_with_grayscale_image
├── test_compute_hash_with_invalid_image_data
└── test_compute_hash_with_empty_data

TestDuplicateDetection (6 tests)
├── test_detects_exact_duplicate
├── test_different_images_not_duplicate
├── test_no_duplicates_in_empty_index
├── test_duplicate_returns_correct_original_id
├── test_secondary_dhash_confirmation
└── test_lsh_candidates_optimization

TestLSHOptimization (9 tests)
├── test_lsh_buckets_initialized
├── test_band_size_computed_correctly
├── test_band_size_with_different_num_bands
├── test_compute_band_keys_correct_count
├── test_compute_band_keys_correct_substrings
├── test_lsh_buckets_populated_on_register
├── test_get_candidate_images_returns_set
├── test_get_candidate_images_empty_index
└── test_get_candidate_images_with_registered_hash

TestHashRegistration (6 tests)
├── test_register_hash_stores_data
├── test_register_multiple_hashes
├── test_remove_hash_success
├── test_remove_hash_nonexistent
├── test_remove_hash_cleans_lsh_buckets
└── test_register_overwrites_existing

TestPersistence (5 tests)
├── test_save_creates_file
├── test_load_existing_index
├── test_persistence_preserves_lsh_buckets
├── test_load_corrupted_index_returns_empty
└── test_load_nonexistent_path_creates_empty

TestStatistics (6 tests)
├── test_get_stats_returns_dict
├── test_stats_include_total_images
├── test_stats_include_by_source
├── test_stats_include_lsh_metrics
├── test_stats_threshold_included
└── test_stats_unique_properties_count

TestClearIndex (3 tests)
├── test_clear_index_removes_images
├── test_clear_index_resets_lsh
└── test_clear_index_persists

TestErrorHandling (4 tests)
├── test_deduplication_error_raised_on_invalid_image
├── test_invalid_hash_skipped_in_candidates
├── test_missing_phash_in_stored_skipped
└── test_is_duplicate_with_empty_candidates

TestThresholdBehavior (2 tests)
├── test_custom_similarity_threshold
└── test_threshold_parameter_stored

TestIntegration (3 tests)
├── test_full_workflow
├── test_persistence_workflow
└── test_lsh_performance_benefit
```

---
