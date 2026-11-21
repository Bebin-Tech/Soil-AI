"""Create local secrets only when files are absent; preserve existing settings."""
from pathlib import Path
import secrets
from dotenv import dotenv_values

root=Path(__file__).resolve().parents[1]
compose=root/'.env';backend=root/'backend/.env'
if compose.exists():
    values=dotenv_values(compose)
    password,secret=values.get('POSTGRES_PASSWORD'),values.get('JWT_SECRET')
elif backend.exists():
    print('Existing backend environment preserved. Configure the root Compose .env separately if using Docker.')
    raise SystemExit(0)
else:
    password,secret=secrets.token_hex(24),secrets.token_urlsafe(48)
    compose.write_text('POSTGRES_PASSWORD='+password+'\nJWT_SECRET='+secret+'\n',encoding='utf-8')
    print('Created private root .env with generated secrets.')
if not backend.exists():
    if not password or not secret:
        raise SystemExit('Root .env requires POSTGRES_PASSWORD and JWT_SECRET before backend configuration can be created.')
    backend.write_text(f'DATABASE_URL=postgresql+psycopg://soilai:{password}@localhost:5433/soilai\nJWT_SECRET={secret}\nCORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173\n',encoding='utf-8')
    print('Created private backend/.env.')
else:
    print('Existing backend/.env preserved.')
