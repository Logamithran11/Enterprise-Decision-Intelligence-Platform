# Deployment Guide

This guide details how to deploy the Enterprise Decision Intelligence Platform in a production-ready containerized environment.

## Docker Compose Deployment
The entire platform is orchestratable via Docker Compose, including:
1. **PostgreSQL**: Relational database storage.
2. **Redis**: Cache, session management, and Celery broker.
3. **Backend API**: FastAPI application server.
4. **Celery Worker**: Background task worker for heavy processing (re-training, rekomendations).
5. **Frontend UI**: React + Vite application served via Nginx.

To spin up the complete platform:
```bash
docker-compose up --build -d
```

## Production Configuration
- Ensure to change the `APP_JWT_SECRET_KEY` in `.env` to a strong unique key.
- Setup Postgres backups by mapping the volume `/var/lib/postgresql/data`.
- Configure the frontend environment variable `API_BASE_URL` if serving on a custom domain.

## Health Checks
- Backend health checks are configured to poll `/api/v1/health/health`.
- Redis health checks run `redis-cli ping`.
- Postgres checks run `pg_isready`.
