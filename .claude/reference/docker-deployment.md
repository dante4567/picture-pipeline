# Docker & Deployment Reference

**Load this when**: Working on Dockerfile, docker-compose, deployment, or infrastructure

---

## Philosophy

**Docker-First Development**:
- All Python runs in Docker containers
- Mount code with `-v $(pwd):/app`
- Mount data with `-v ~/data:/data`
- No local venv/virtualenv/conda

---

## Project Structure

```
project/
├── Dockerfile                # Application container
├── docker-compose.yml        # Local development
├── docker-compose.prod.yml   # Production (optional)
├── requirements.txt          # Python dependencies
├── .dockerignore            # Exclude from image
├── .env.example             # Template (committed)
├── .env                     # Actual secrets (gitignored)
└── run.sh                   # Entry point script
```

---

## Dockerfile Pattern

### Multi-stage build for Python

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key Principles

- ✅ Multi-stage build (smaller final image)
- ✅ Use slim/alpine base images
- ✅ Install dependencies in build stage
- ✅ Copy only necessary files
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ Run as non-root user (production)
- ✅ Use specific base image tags (not `latest`)

---

## .dockerignore

```
# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv
*.egg-info

# Git
.git
.gitignore

# IDE
.vscode
.idea
*.swp
*.swo

# Data
data/
logs/
*.log

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Docs
docs/
*.md

# Tests
tests/
pytest_cache/

# Environment
.env
.env.local
```

---

## docker-compose.yml

### Development Setup

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ${PROJECT_NAME:-myapp}
    ports:
      - "${APP_PORT:-8000}:8000"
    volumes:
      - .:/app                    # Mount code for hot reload
      - app-data:/data            # Persistent data
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LITELLM_BASE_URL=${LITELLM_BASE_URL:-http://litellm:4000}
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16
    container_name: ${PROJECT_NAME:-myapp}-db
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-postgres}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB:-myapp}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ${PROJECT_NAME:-myapp}-redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped

volumes:
  app-data:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
```

---

## Environment Variables

### .env.example (committed to git)

```bash
# Project
PROJECT_NAME=myapp
APP_PORT=8000

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=myapp
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:changeme@postgres:5432/myapp

# Redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# LiteLLM
LITELLM_BASE_URL=http://localhost:4000

# API Keys (DO NOT commit actual keys)
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
```

### .env (gitignored - actual secrets)

```bash
# Copy from .env.example and fill in real values
POSTGRES_PASSWORD=actual-secret-password
OPENAI_API_KEY=sk-actual-key
ANTHROPIC_API_KEY=sk-ant-actual-key
```

---

## run.sh Entry Point

### Single script for all operations

```bash
#!/bin/bash
set -e

PROJECT_NAME="${PROJECT_NAME:-myapp}"

case "$1" in
  start)
    echo "Starting $PROJECT_NAME..."
    docker-compose up -d
    docker-compose logs -f app
    ;;

  stop)
    echo "Stopping $PROJECT_NAME..."
    docker-compose down
    ;;

  restart)
    echo "Restarting $PROJECT_NAME..."
    docker-compose restart
    ;;

  build)
    echo "Building $PROJECT_NAME..."
    docker-compose build --no-cache
    ;;

  logs)
    docker-compose logs -f ${2:-app}
    ;;

  shell)
    docker-compose exec app /bin/bash
    ;;

  test)
    echo "Running tests..."
    docker-compose exec app pytest tests/
    ;;

  check)
    echo "Running linting and type checking..."
    docker-compose exec app ruff check src/
    docker-compose exec app mypy src/
    ;;

  clean)
    echo "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    ;;

  *)
    echo "Usage: ./run.sh {start|stop|restart|build|logs|shell|test|check|clean}"
    exit 1
    ;;
esac
```

---

## Common Commands

```bash
# Development
./run.sh start              # Start all services
./run.sh logs               # View logs
./run.sh logs postgres      # View specific service logs
./run.sh shell              # Get shell in app container
./run.sh test               # Run tests
./run.sh check              # Run linting

# Maintenance
./run.sh restart            # Restart services
./run.sh build              # Rebuild images
./run.sh clean              # Clean up volumes and images

# Direct docker-compose
docker-compose ps           # List running containers
docker-compose exec app bash  # Shell into app container
docker-compose down -v      # Stop and remove volumes
```

---

## Port Configuration

### Make ports configurable via .env

**Default Ports** (standard, avoid conflicts):
- App: 8000
- PostgreSQL: 5432
- Redis: 6379
- LiteLLM: 4000

**Custom Ports** (if needed):
```bash
# In .env
APP_PORT=8001
POSTGRES_PORT=5433
REDIS_PORT=6380
```

Then in docker-compose.yml:
```yaml
ports:
  - "${APP_PORT:-8000}:8000"
```

---

## Volumes Best Practices

### Types of Volumes

**Bind Mounts** (development):
```yaml
volumes:
  - .:/app  # Code changes reflected immediately
```

**Named Volumes** (data persistence):
```yaml
volumes:
  - postgres-data:/var/lib/postgresql/data  # Persists across restarts
```

**Anonymous Volumes** (temporary):
```yaml
volumes:
  - /app/node_modules  # Don't override with bind mount
```

### When to Use Each

- **Code**: Bind mount for hot reload
- **Database**: Named volume for persistence
- **Build artifacts**: Anonymous volume
- **User data**: Named volume or bind to host path

---

## Networking

### Internal Communication

Services in same docker-compose can reference by service name:

```python
# In app container
DATABASE_URL = "postgresql://postgres:password@postgres:5432/db"
REDIS_URL = "redis://redis:6379"
LITELLM_URL = "http://litellm:4000"
```

### External Access

```yaml
ports:
  - "8000:8000"  # Host:Container
```

Only expose ports you need to access from host.

---

## Development vs Production

### Development (docker-compose.yml)

```yaml
services:
  app:
    volumes:
      - .:/app  # Hot reload
    environment:
      - DEBUG=true
    command: uvicorn src.main:app --reload --host 0.0.0.0
```

### Production (docker-compose.prod.yml or separate deployment)

```yaml
services:
  app:
    # No volume mounts (code baked into image)
    environment:
      - DEBUG=false
    command: gunicorn src.main:app --workers 4 --bind 0.0.0.0:8000
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

---

## Database Migrations

### Using Alembic with Docker

```bash
# Generate migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec app alembic upgrade head

# Rollback
docker-compose exec app alembic downgrade -1
```

### Include in Dockerfile (optional)

```dockerfile
# Run migrations on startup
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0"]
```

---

## Health Checks

### In docker-compose.yml

```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## Logging

### Container Logs

```bash
# View logs
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Logs for all services
docker-compose logs -f
```

### Application Logging

Use structured logging (see testing-patterns.md):
```python
import structlog

logger = structlog.get_logger()
logger.info("request_processed", user_id=123, duration_ms=45)
```

Logs go to stdout/stderr, Docker captures them.

---

## Security

### DO NOT

❌ Commit .env with secrets
❌ Run as root in production
❌ Expose unnecessary ports
❌ Use `latest` tag in production
❌ Include secrets in Dockerfile
❌ Commit API keys

### DO

✅ Use .env.example as template
✅ Run as non-root user
✅ Only expose needed ports
✅ Pin specific image versions
✅ Use environment variables
✅ Add .env to .gitignore

### Non-root User (Production)

```dockerfile
# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

---

## Connecting to Shared Infrastructure

### Using External Services

If using shared litellm/postgres/redis from another machine:

```yaml
# Remove local service definitions
# Use external URLs in .env

# .env
DATABASE_URL=postgresql://user:pass@192.168.1.155:5432/db
REDIS_URL=redis://192.168.1.155:6379
LITELLM_BASE_URL=http://192.168.1.155:4000
```

No need to define those services in docker-compose.yml.

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs app

# Check if port is already in use
lsof -i :8000

# Remove and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Database connection failed

```bash
# Check if postgres is running
docker-compose ps

# Check postgres logs
docker-compose logs postgres

# Verify connection string
docker-compose exec app env | grep DATABASE_URL
```

### Permission denied

```bash
# Fix volume permissions
docker-compose exec app chown -R $(id -u):$(id -g) /app

# Or run as root temporarily
docker-compose exec -u root app bash
```

### Out of disk space

```bash
# Clean up
docker system prune -a --volumes

# Check disk usage
docker system df
```

---

## Quick Reference

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Shell into container
docker-compose exec app bash

# Run command
docker-compose exec app python script.py

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild
docker-compose build --no-cache

# Check status
docker-compose ps

# View resource usage
docker stats
```

---

## Checklist

When setting up Docker for a new project:

- [ ] Create Dockerfile with multi-stage build
- [ ] Create docker-compose.yml with all services
- [ ] Create .env.example with all variables
- [ ] Add .env to .gitignore
- [ ] Create .dockerignore
- [ ] Create run.sh entry point
- [ ] Test: ./run.sh start
- [ ] Test: ./run.sh test
- [ ] Test: ./run.sh shell
- [ ] Document ports in README
- [ ] Add health check endpoint
