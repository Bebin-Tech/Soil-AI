"""Initial normalized application schema."""
from alembic import op
from pathlib import Path

revision = '0001'
down_revision = None


def upgrade():
    source=Path(__file__).resolve().parents[1]/'schema_0001.sql'
    for statement in source.read_text(encoding='utf-8').split(';'):
        if statement.strip():op.execute(statement)


def downgrade():
    source=Path(__file__).resolve().parents[1]/'drop_0001.sql'
    for statement in source.read_text(encoding='utf-8').split(';'):
        if statement.strip():op.execute(statement)
