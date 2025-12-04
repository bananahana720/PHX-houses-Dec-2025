# Deployment

### Docker Compose (Development)

**File**: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  worker:
    build:
      context: ..
      dockerfile: docker/worker.Dockerfile
    depends_on:
      redis:
        condition: service_healthy
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      LOG_LEVEL: INFO
    volumes:
      - ../data:/app/data
      - ../src:/app/src
    restart: always

  rq-dashboard:
    image: eoranged/rq-dashboard:latest
    ports:
      - "9181:9181"
    depends_on:
      - redis
    environment:
      RQ_DASHBOARD_REDIS_URL: redis://redis:6379

volumes:
  redis_data:
```

**File**: `docker/worker.Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src /app/src
COPY scripts /app/scripts
COPY data /app/data

# Set Python path
ENV PYTHONPATH=/app

# Start worker
CMD ["python", "-m", "phx_home_analysis.workers.image_extraction", "docker-worker"]
```

**Usage**:
```bash
# Start stack
docker-compose -f docker/docker-compose.yml up

# View RQ Dashboard
# http://localhost:9181

# Stop
docker-compose -f docker/docker-compose.yml down
```

---
