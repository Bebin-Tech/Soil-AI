from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.records import router as records_router
from app.api.v1.imports import router as imports_router
from app.api.v1.workspace import router as workspace_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.reports import router as reports_router
from app.middleware.security import SecurityMiddleware
from app.database.session import engine
from sqlalchemy import text
from fastapi.responses import JSONResponse

app = FastAPI(title="SoilAI", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings().cors_origins.split(','), allow_methods=['GET', 'POST', 'PUT', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
app.add_middleware(SecurityMiddleware)
app.include_router(auth_router, prefix='/api/v1', tags=['Authentication'])
app.include_router(records_router, prefix='/api/v1', tags=['Farm and soil records'])
app.include_router(imports_router, prefix='/api/v1', tags=['Validated imports'])
app.include_router(workspace_router, prefix='/api/v1', tags=['Workspace and administration'])
app.include_router(predictions_router, prefix='/api/v1', tags=['Prediction availability'])
app.include_router(reports_router, prefix='/api/v1', tags=['Private reports'])

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "SoilAI API"}


@app.get('/api/v1/health/ready')
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1 FROM alembic_version LIMIT 1'))
        return {'status':'ready'}
    except Exception:
        return JSONResponse({'status':'unavailable'},status_code=503)
