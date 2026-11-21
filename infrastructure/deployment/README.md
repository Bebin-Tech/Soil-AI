# Deployment and operations

## Local container deployment

Start Docker Desktop. Use a private root `.env` with POSTGRES_PASSWORD and JWT_SECRET (32+ random characters). Those credentials must match `backend/.env` for local development. Do not publish either file.

```powershell
docker compose up -d --build
docker compose ps
docker compose logs backend
```

The app is available at http://localhost:8080, with `/api/v1/health` and `/api/v1/health/ready` checks. Nginx proxies `/api`; the API container is not directly exposed. PostgreSQL binds only to local port 5433 for development. Uploaded files, report snapshots and database state have persistent volumes. Fonts are open-licensed and bundled with the backend source. No sample passwords, users, farms or prediction statistics are seeded.

The backend installs the tested versions in `backend/requirements-lock.txt`. If Docker Desktop downloads are slow, use the optional cache before building:

```powershell
.\.venv\Scripts\python.exe scripts\cache_docker_wheels.py
docker compose up -d --build
```

The cache contains Linux x86-64/Python 3.13 wheels, is ignored by Git, and installs without network access inside the image. On other architectures, leave `backend/wheels` empty (apart from `.gitkeep`) and let pip select the platform's wheels normally. A partial cache intentionally fails instead of silently installing different dependency versions.

Run the administrator bootstrap interactively inside the API container (or use the local bootstrap script against the same database). Keep the bootstrap script in the deployment image only when needed; limit shell access to administrators.

```powershell
docker compose exec backend python create_admin.py
```

## Cloud deployment checklist

Use a managed PostgreSQL database with TLS, a private network and restricted database role. Point DATABASE_URL at that database and run Alembic as a single release job. Deploy the backend image and the frontend image behind an HTTPS ingress. Terminate TLS at a trusted reverse proxy. Set the actual frontend origin in CORS_ORIGINS. Store JWT/database/SMTP credentials in a secret manager; never bake them into frontend builds.

The checked-in Nginx config is an HTTP localhost configuration. A public deployment still requires provider-specific DNS, certificates, ingress configuration and a tested backup/restore process. This repository has not been deployed publicly.

Use shared auth rate limiting at the gateway for multiple API workers. Request and upload limits must also be enforced at the ingress. The included limiter is process-local and does not trust forwarded IPs. Add structured logging/monitoring, centralized audit retention and alerting for production operations. The current browser stores credentials in sessionStorage; an HttpOnly-cookie BFF is recommended for a hardened public installation.

Do not expose private reports as a static storage bucket. Every download goes through resource authorization. Mount durable storage for reports. Add retention and quota policies before high-volume use. SMTP delivery must be configured and independently tested for password recovery.

## Backup

Use `pg_dump` with a private connection configuration, encrypt and back up reports alongside database records, and regularly restore into an isolated environment. Never test restores against the live database. Do not run `docker compose down -v` unless you intend to erase application data.

## Scientific deployment gate

The application currently has no approved ML model. Prediction routes deliberately return HTTP 503 with MODEL_NOT_VALIDATED after authorization. Model training, nutrient interpretations and crop/fertilizer engines require verified public datasets and regional agronomic validation. This is a stated, tested unavailability state, not a completed prediction implementation.
