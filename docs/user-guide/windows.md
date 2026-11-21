# Windows PowerShell setup

From the repository directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if (-not (Test-Path backend\.env)) { Copy-Item .env.example backend\.env }
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Store that random value as JWT_SECRET in `backend/.env`. Do not commit `.env`. Set DATABASE_URL to your PostgreSQL database. The Compose database defaults to localhost port 5433. Set a separate PostgreSQL password and the same JWT secret in a root `.env`:

```text
POSTGRES_PASSWORD=your-random-database-password
JWT_SECRET=your-random-application-secret
```

Start Docker Desktop, then:

```powershell
docker compose up -d db
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe ..\scripts\create_admin.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal, from the repository:

```powershell
Set-Location frontend
npm install
npm run dev
```

If Windows blocks npm.ps1, use `npm.cmd`. In restricted execution environments, invoke `node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install` instead. Open http://127.0.0.1:5173 and register a farmer. No demonstration farms or invented measurements are seeded.

Run checks:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
$env:SOILAI_TEST_POSTGRES='1'
..\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:SOILAI_TEST_POSTGRES
Set-Location ..\frontend
npm run build
npm test
```

The PostgreSQL test option uses the backend `.env` and creates isolated test schemas. Its database account needs CREATE SCHEMA privileges. Development processes stop with Ctrl+C. Stop project containers with `docker compose stop`; do not remove volumes unless you intend to erase your records.

The recommended setup command is `.\scripts\setup.ps1`, which preserves existing environment files, installs locked Python dependencies and uses `npm ci`. Generated environment secrets are private and ignored by Git. Fonts are already included; if missing, run `.\.venv\Scripts\python.exe scripts\install_fonts.py` after installing Python dependencies. Report generation requires the bundled merged Noto font, fonttools and uharfbuzz for Tamil shaping.

For isolated browser tests, stop the normal port-8000 API and run `.\.venv\Scripts\python.exe scripts\qa_server.py` from the repository. This creates a dedicated PostgreSQL schema, applies the real migrations and launches the same application. The React proxy remains unchanged. Ctrl+C attempts cleanup; if the terminal forcibly kills the process, remove only the verified `soilai_qa_<uuid>` schema belonging to that test. Never remove application schemas or volumes for test cleanup.
