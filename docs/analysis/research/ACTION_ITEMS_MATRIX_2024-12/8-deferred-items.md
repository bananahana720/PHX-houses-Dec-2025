# 8. Deferred Items

Items explicitly NOT recommended for now, with rationale:

| ID | Item | Rationale | Revisit When |
|----|------|-----------|--------------|
| DEF-01 | NeighborhoodScout integration ($5K/year) | Cost prohibitive for current scale | Processing >500 properties/month |
| DEF-02 | UtilityAPI integration (paid) | Requires customer authorization | B2B use case emerges |
| DEF-03 | Arcadia enterprise integration | Overkill for single-user pipeline | Multi-tenant deployment |
| DEF-04 | Celery migration | RQ sufficient for current scale | Queue backups >30 seconds consistent |
| DEF-05 | DOE Home Energy Score | Requires assessor certification | Professional service offering |
| DEF-06 | Multi-machine worker pool | Current workload fits single machine | >1000 properties/batch |
| DEF-07 | Real-time appreciation tracking | Historical data sufficient | Investment analysis feature request |
| DEF-08 | Machine learning price prediction | Complexity vs value unclear | After core pipeline stable |

---
