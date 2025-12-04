# Cost & Resource Implications

### Infrastructure Additions

| Component | Cost (AWS) | Purpose |
|-----------|-----------|---------|
| **Redis** (Elasticache small) | $15/mo | Job queue + state |
| **Additional EC2** (t3.medium) | $30/mo | Worker #1 |
| **Prometheus + Grafana** | $10/mo | Monitoring |
| **S3 storage** (500GB images) | $12/mo | Offsite backup |
| **Total** | ~$67/mo | vs. current $0 (local only) |

### Resource Usage

**Per Extraction Job** (5 properties):
- CPU: 40% utilization (async I/O heavy)
- Memory: 500MB (browser, images in RAM)
- Disk I/O: 1GB written
- Network: 200MB downloaded + 100MB upstream
- Duration: 12-18 minutes

**Scaling** (10 concurrent jobs):
- Need: 2x t3.medium workers + Redis
- Total cost: ~$100/month for infrastructure

---
