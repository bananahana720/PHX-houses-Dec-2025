# Monitoring & Alerting Strategy

### Key Metrics

| Metric | Type | Alert Threshold | Owner |
|--------|------|-----------------|-------|
| Queue depth | Gauge | > 50 jobs | Ops |
| Job duration | Histogram | > 60 min (p95) | Dev |
| Success rate | Counter | < 90% | Dev |
| Source circuit status | Gauge | Open > 2h | Ops |
| Disk usage | Gauge | > 85% quota | Ops |
| New images batch size | Gauge | > 100 | Dev/QA |

### Alert Examples

```yaml
# Prometheus alerting rules
alert: ImageExtractionQueueLarge
  expr: image_extraction_queue_depth > 50
  for: 5m
  action: Notify #ops, page oncall if > 100

alert: ExtractionWorkerDown
  expr: up{job="extraction_worker"} == 0
  for: 1m
  action: Page oncall

alert: SourceCircuitOpen
  expr: extraction_source_circuit_open > 2h
  action: Notify #ops
```

---
