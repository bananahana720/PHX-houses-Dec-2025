# Performance Optimization

### Profiling

```bash
# Profile script execution
python -m cProfile -o profile.stats scripts/phx_home_analyzer.py

# Visualize with snakeviz
snakeviz profile.stats
```

### Benchmarking

```bash
# Run benchmark tests
pytest tests/benchmarks/ -v

# Specific benchmark
pytest tests/benchmarks/test_lsh_performance.py -v
```

### Optimization Tips

1. **Batch operations**
   - Extract all properties in one session (saves API calls)
   - Use parallel processing for independent tasks

2. **Cache expensive operations**
   - Cache geocoding results
   - Cache API responses

3. **Use efficient data structures**
   - Consider migrating to database for >1000 properties
   - Use pandas for bulk operations

---
