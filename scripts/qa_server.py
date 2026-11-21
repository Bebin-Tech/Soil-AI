"""Isolated PostgreSQL schema for browser QA. Ctrl+C removes only the owned schema."""
import os
import subprocess
import sys
import uuid
from pathlib import Path
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from dotenv import dotenv_values

root=Path(__file__).resolve().parents[1]
env=dict(os.environ)
env.update({k:v for k,v in dotenv_values(root/'backend/.env').items() if v is not None})
url=make_url(env['DATABASE_URL'])
schema='soilai_qa_'+uuid.uuid4().hex
engine=create_engine(url,connect_args={'connect_timeout':5})
with engine.begin() as connection:connection.execute(text('CREATE SCHEMA '+schema))
env['DATABASE_URL']=url.update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
env['ENVIRONMENT']='development'
try:
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=root/'backend',env=env,check=True)
    print('Isolated browser QA schema ready. No production records are changed.',flush=True)
    subprocess.run([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],cwd=root/'backend',env=env,check=True)
finally:
    with engine.begin() as connection:connection.execute(text('DROP SCHEMA '+schema+' CASCADE'))
    engine.dispose()
