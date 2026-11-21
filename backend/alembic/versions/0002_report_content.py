"""Keep generated reports durable across serverless instances."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'


def upgrade():
    op.add_column('reports', sa.Column('content', sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column('reports', 'content')
