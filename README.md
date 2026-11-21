# SoilAI

React/TypeScript and FastAPI agricultural record and decision support platform, backed by PostgreSQL 17. Implemented: registration/login, session security and roles; farms/fields; validated soil samples and drafts; CSV/XLSX preview, mapping and atomic imports; database-driven dashboards; officer reviews; administration/auditing; English/Tamil interface; private bilingual PDF/Excel laboratory records; Docker/Nginx deployment.

**This is a working application under development, not the completed twelve-phase enterprise platform.** ML training, SHAP, scientifically validated fertility/crop predictions, agronomic deficiency interpretations, fertilizer engines and background retraining are not implemented. As requested, predictions remain unavailable until suitable public data and models are validated. The dataset source register, audit tool, remaining work and exact verification evidence are documented below. No accuracy scores, farm statistics or training results are fabricated.

## Quick start

Existing environment: `docker compose up -d --build`, then open http://localhost:8080. Start Docker Desktop first. Compose reads private generated secrets from the root `.env`; it does not seed users or demonstration data.

For a fresh Windows checkout, run from the repository in PowerShell:

```powershell
.\scripts\setup.ps1
docker compose up -d db
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe ..\scripts\create_admin.py
Set-Location ..
.\scripts\start-backend.ps1
```

In a second terminal, from the repository:

```powershell
.\scripts\start-frontend.ps1
```

Register a farmer at http://127.0.0.1:5173. Use the interactively created administrator to assign officer roles and farms. There are no default credentials. The database binds to **5433** because 5432 was already in use on the development computer. API docs: http://127.0.0.1:8000/docs. Readiness: `/api/v1/health/ready`.

## Windows development

Run from this repository in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if (-not (Test-Path backend\.env)) { Copy-Item .env.example backend\.env }
# Edit backend\.env: configure PostgreSQL and generate a JWT secret below.
python -c "import secrets; print(secrets.token_urlsafe(48))"
Set-Location frontend
npm install
npm run dev
```

In another terminal:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend: http://localhost:5173. API docs: http://localhost:8000/docs.

Phase completion and validation evidence are maintained in `docs/implementation.md`.

Full setup and checks: [Windows guide](docs/user-guide/windows.md). The local PostgreSQL container uses port **5433**. Run `alembic upgrade head` in `backend` before the API, then bootstrap an administrator with `python ../scripts/create_admin.py`. Public registration always creates a farmer.

## Documentation

- [Implementation and remaining work](docs/implementation.md)
- [Windows commands](docs/user-guide/windows.md)
- [Architecture and security boundaries](docs/architecture/overview.md)
- [Dataset provenance, downloads and audit contract](docs/dataset/README.md)
- [Container and cloud operations](infrastructure/deployment/README.md)

Configure SMTP before password recovery can send mail. The standard interface and report labels support English/Tamil; dynamic server validation messages and some administrative metadata remain English. Full localization and public-production hardening remain open acceptance items. Cloud DNS/HTTPS deployment is documented but has not been performed.
