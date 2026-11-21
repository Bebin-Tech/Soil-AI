FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements-lock.txt requirements.txt
RUN --mount=type=bind,source=backend/wheels,target=/wheels if ls /wheels/*.whl >/dev/null 2>&1; then pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt; else pip install --no-cache-dir -r requirements.txt; fi
COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini .
COPY scripts/create_admin.py /app/create_admin.py
RUN useradd --create-home soilai && mkdir -p storage && chown -R soilai:soilai /app
USER soilai
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
