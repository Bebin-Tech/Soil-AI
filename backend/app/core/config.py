from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://soilai:soilai@localhost:5432/soilai'
    jwt_secret: str
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    environment: str = 'development'
    storage_dir: str = 'storage'
    max_upload_bytes: int = 5 * 1024 * 1024
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = 'noreply@example.com'
    frontend_url: str = 'http://localhost:5173'

    @model_validator(mode='after')
    def secure_config(self):
        if len(self.jwt_secret) < 32 or self.jwt_secret.startswith('replace-'):
            raise ValueError('JWT_SECRET must contain at least 32 random characters')
        if self.environment == 'production' and not self.database_url.startswith('postgresql'):
            raise ValueError('Production requires PostgreSQL')
        return self


@lru_cache
def settings():
    return Settings()
