# Production Deployment Guide

This guide covers deploying the Email Agent system using Docker in a production environment.

## Overview

The production setup uses Docker Compose to orchestrate the following services:
- **PostgreSQL** (with pgvector extension)
- **Redis** (Celery broker/backend)
- **FastAPI API Server**
- **Celery Worker** (background task processing)
- **Celery Beat** (task scheduler)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- 2GB+ RAM
- 10GB+ disk space

## Quick Start

### 1. Clone Repository and Configure Environment

```bash
# Clone repository
git clone <repository-url>
cd EmailAgent

# Copy and configure production environment
cp .env.prod.example .env.prod

# Edit .env.prod with your production values
nano .env.prod
```

### 2. Build and Start Services

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Verify Deployment

```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# Test API health endpoint
curl http://localhost:8000/health

# Test API root endpoint
curl http://localhost:8000/
```

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_PASSWORD` | PostgreSQL password | `secure-password-123` |
| `SECRET_KEY` | JWT signing key | Generate with `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `S3_BUCKET` | S3 bucket name | `emailagent-docs` |
| `S3_ACCESS_KEY` | S3 access key | AWS access key |
| `S3_SECRET_KEY` | S3 secret key | AWS secret key |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_NAME` | Database name | `emailagent` |
| `DATABASE_USER` | Database user | `emailagent` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `REDIS_PORT` | Redis port | `6379` |
| `API_PORT` | API server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## Service Architecture

### API Server (`api`)
- **Image**: Multi-stage Python 3.11 slim
- **Size**: ~250MB
- **Workers**: 2 Uvicorn workers
- **Health Check**: `/health` endpoint (30s interval)
- **Auto-restart**: Yes
- **Runs migrations on startup**

### Celery Worker (`celery_worker`)
- **Image**: Multi-stage Python 3.11 slim
- **Size**: ~250MB
- **Concurrency**: 2 workers
- **Auto-restart**: Yes
- **Processes**: Email polling, batch processing, document ingestion

### Celery Beat (`celery_beat`)
- **Image**: Multi-stage Python 3.11 slim
- **Size**: ~250MB
- **Auto-restart**: Yes
- **Schedules**: Gmail polling (10min), batch processing (5min)

### PostgreSQL (`postgres`)
- **Image**: ankane/pgvector:v0.5.1
- **Extensions**: pgvector for vector similarity search
- **Health Check**: `pg_isready` (10s interval)
- **Persistent Volume**: `postgres_data`

### Redis (`redis`)
- **Image**: redis:7-alpine
- **Size**: ~30MB
- **Health Check**: `redis-cli ping` (10s interval)
- **Persistent Volume**: `redis_data`

## Operations

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# Filter logs by level (using jq for JSON logs)
docker-compose -f docker-compose.prod.yml logs -f api | jq 'select(.level == "ERROR")'
```

### Run Database Migrations

```bash
# Migrations run automatically on API startup
# To run manually:
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Check current migration version
docker-compose -f docker-compose.prod.yml exec api alembic current
```

### Scale Workers

```bash
# Scale Celery workers to 3 instances
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=3
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart api

# Restart without downtime (recreate)
docker-compose -f docker-compose.prod.yml up -d --force-recreate --no-deps api
```

### Stop Services

```bash
# Stop all services (preserves volumes)
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.prod.yml down -v
```

### Database Backups

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U emailagent emailagent > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U emailagent emailagent < backup_20240101_120000.sql
```

## Security Best Practices

### 1. Use Secrets Management
- **DO NOT** commit `.env.prod` to version control
- Use Docker secrets or environment variable injection
- Rotate `SECRET_KEY` regularly

### 2. Network Security
- Use internal Docker network (done by default)
- Only expose necessary ports
- Use reverse proxy (nginx/Traefik) with HTTPS

### 3. Container Security
- Images run as non-root user (`appuser`)
- Multi-stage builds minimize attack surface
- Regular image updates for security patches

### 4. Database Security
- Strong password (20+ characters)
- Restrict PostgreSQL to internal network
- Regular backups

## Monitoring

### Health Checks

All services include health checks:
- API: HTTP GET `/health` (30s interval)
- PostgreSQL: `pg_isready` (10s interval)
- Redis: `redis-cli ping` (10s interval)

### Logging

All services log to stdout in JSON format:
```json
{
  "timestamp": "2024-01-17 10:00:00",
  "level": "INFO",
  "service": "email-agent-backend",
  "message": "Request completed",
  "request_id": "uuid",
  "broker_id": "uuid",
  "duration_ms": 45.2
}
```

Ship logs to external service:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- CloudWatch

### Metrics

Monitor these key metrics:
- API response time (p50, p95, p99)
- Celery task queue length
- Database connection pool usage
- Memory and CPU usage per service

## Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs for errors
docker-compose -f docker-compose.prod.yml logs api

# Check health
docker-compose -f docker-compose.prod.yml exec api curl localhost:8000/health
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U emailagent -d emailagent -c "SELECT version();"

# Check DATABASE_URL in API container
docker-compose -f docker-compose.prod.yml exec api env | grep DATABASE_URL
```

### Celery Tasks Not Running

```bash
# Check worker logs
docker-compose -f docker-compose.prod.yml logs celery_worker

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Inspect Celery queue
docker-compose -f docker-compose.prod.yml exec celery_worker \
  celery -A app.workers.celery_app inspect active
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Reduce Uvicorn workers (edit docker-compose.prod.yml)
# Change: --workers 2 → --workers 1

# Reduce Celery concurrency (edit docker-compose.prod.yml)
# Change: --concurrency=2 → --concurrency=1
```

## Image Size Optimization

Current image sizes:
- API/Worker/Beat: ~250MB each (multi-stage build)
- PostgreSQL: ~380MB
- Redis: ~30MB
- **Total**: ~940MB

Further optimizations:
- Use alpine-based Python images (~150MB reduction)
- Remove unnecessary dependencies
- Layer caching optimization

## Production Checklist

Before deploying to production:

- [ ] Environment variables configured in `.env.prod`
- [ ] `SECRET_KEY` generated with `openssl rand -hex 32`
- [ ] Strong `DATABASE_PASSWORD` set
- [ ] Valid `OPENAI_API_KEY` configured
- [ ] S3 credentials and bucket configured
- [ ] `CORS_ORIGINS` set to frontend domain
- [ ] Firewall rules configured
- [ ] HTTPS reverse proxy configured (nginx/Traefik)
- [ ] Database backups scheduled
- [ ] Log shipping configured
- [ ] Monitoring alerts configured
- [ ] Health check endpoints tested
- [ ] Migrations tested
- [ ] Smoke tests passed

## Updating

To update to a new version:

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Restart services with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api

# Migrations run automatically on API startup
```

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Review [CLAUDE.md](./CLAUDE.md) for system architecture
- Review [memory.md](./memory.md) for implementation details
