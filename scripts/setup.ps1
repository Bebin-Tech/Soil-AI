$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r backend/requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& '.\.venv\Scripts\python.exe' scripts/init_env.py
if ($LASTEXITCODE -ne 0) { throw 'Environment setup failed.' }
if (-not (Test-Path -LiteralPath 'backend/app/assets/fonts/SoilAI-Regular.ttf')) {
    & '.\.venv\Scripts\python.exe' scripts/install_fonts.py
    if ($LASTEXITCODE -ne 0) { throw 'Report font installation failed.' }
}
$nodeDirectory = Split-Path -Parent (Get-Command node).Source
$npmCli = Join-Path $nodeDirectory 'node_modules/npm/bin/npm-cli.js'
Push-Location -LiteralPath frontend
try {
    if (Test-Path -LiteralPath $npmCli) { node $npmCli ci }
    else { npm.cmd ci }
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
} finally { Pop-Location }
Write-Output 'Setup complete. Start Docker Desktop, run docker compose up -d db, then apply Alembic migrations.'
