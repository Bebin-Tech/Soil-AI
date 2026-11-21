import os
os.environ['JWT_SECRET'] = 'test-only-secret-do-not-deploy-' + 'x' * 32
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['ENVIRONMENT'] = 'test'

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.session import Base, get_db
from app.models.entities import Role
from app.main import app


@pytest.fixture
def client():
    pg = os.environ.get('SOILAI_TEST_POSTGRES') == '1'
    schema_name = 'test_' + uuid.uuid4().hex
    if pg:
        from dotenv import dotenv_values
        from pathlib import Path
        url = dotenv_values(Path(__file__).resolve().parents[1] / '.env')['DATABASE_URL']
        base_engine = create_engine(url, connect_args={'connect_timeout': 5})
        with base_engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA {schema_name}'))
        engine = base_engine.execution_options(schema_translate_map={None: schema_name})
    else:
        engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        from sqlalchemy import event
        @event.listens_for(engine, 'connect')
        def fk(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add_all([Role(name=r) for r in ['FARMER', 'ADMIN', 'AGRICULTURAL_OFFICER']])
        db.commit()
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app,client=(schema_name,50000)) as test:
        test.db_factory = factory
        yield test
    app.dependency_overrides.clear()
    if pg:
        with base_engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA {schema_name} CASCADE'))
    engine.dispose()


def register(client, email='farmer@example.com'):
    response = client.post('/api/v1/auth/register', json={'name': 'Test Farmer', 'email': email, 'password': 'LongSecurePassword123!'})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def account(client):
    data = register(client)
    return data, {'Authorization': 'Bearer ' + data['access_token']}
