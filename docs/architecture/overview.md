# Architecture

Vite serves React in development and proxies `/api` to FastAPI. Production Nginx serves the built frontend and proxies the API inside the Docker network. FastAPI uses SQLAlchemy transactions and Alembic migrations against PostgreSQL 17. Uploads and reports are private backend storage, not public web files. ML training is isolated from serving; a model must pass dataset compatibility checks and explicit administrative approval before activation.

Registration creates only a FARMER role. Bootstrap an administrator using `scripts/create_admin.py` after migrations. Administrators assign officers; an officer can read only explicitly assigned farms (plus any farm they own). Only owners and administrators may change farm/sample records. Resource authorization is enforced on each API request. Deleted farms are archived and excluded from ordinary queries.

JWT access tokens refer to a database session, enabling immediate revocation. Refresh tokens are random values stored only as SHA-256 hashes and rotated with row locks. Reuse revokes every user session. Browser credentials live in sessionStorage; use an HttpOnly-cookie BFF for a hardened Internet-facing installation. SMTP is required for reset delivery. Auth endpoint throttling is process-local; multi-worker deployments require shared gateway rate limiting.

SQLite is a fast test adapter only; production explicitly requires PostgreSQL. PostgreSQL integration tests create unique schemas and drop only those test schemas.
