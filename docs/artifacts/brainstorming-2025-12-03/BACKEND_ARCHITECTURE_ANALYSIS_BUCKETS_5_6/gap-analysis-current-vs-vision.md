# Gap Analysis: Current vs. Vision

### BUCKET 5 Gaps: Image Pipeline

| Gap | Current | Vision | Priority |
|-----|---------|--------|----------|
| **Image Alerts** | Silent processing | Console warnings for large batches (>100 new images) | Medium |
| **Deduplication Alerts** | Logged to file only | Visible warnings on duplicate detection | Low |
| **Categorization** | Filename-encoded only | Separate metadata sidecar for richer tagging | Medium |
| **Storage Versioning** | Single version | Versioned snapshots for rollback | Low |
| **Retention Policy** | None | Auto-archive old images (>90 days) | Low |
| **Disk Usage Monitoring** | None | Threshold alerts when approaching quota | Medium |

### BUCKET 6 Gaps: Scraping & Automation

| Gap | Current | Vision | Priority |
|-----|---------|--------|----------|
| **Background Jobs** | **Missing** | Job queue + worker pool | **CRITICAL** |
| **Job Queuing** | **Missing** | Redis/RabbitMQ task queue | **CRITICAL** |
| **Worker Processes** | **Missing** | Dedicated workers for extraction/processing | **CRITICAL** |
| **User Isolation** | **None** | Per-user job tracking + request queuing | **HIGH** |
| **Job Monitoring** | Run history logs | Real-time dashboard + alerting | **MEDIUM** |
| **Job Cancellation** | No | Graceful cancellation + cleanup | **MEDIUM** |
| **Distributed Extraction** | Single process | Multi-machine distributed scraping | **LOW** |
| **Rate Limit Awareness** | Circuit breaker only | Adaptive rate limiting based on server response codes | **MEDIUM** |
| **Proxy Management** | Manual config | Automatic proxy rotation + health checks | **MEDIUM** |

---
