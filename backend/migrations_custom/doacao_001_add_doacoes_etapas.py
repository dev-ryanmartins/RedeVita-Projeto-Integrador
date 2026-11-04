"""Add doacoes_etapas table

Revision ID: doacao_001
Revises: necessidade_001
Create Date: 2026-11-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'doacao_001'
down_revision = 'necessidade_001'
branch_labels = None
depends_on = None


def upgrade():
    """Create doacoes_etapas table"""
    op.create_table(
        'doacoes_etapas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('doacao_id', sa.Integer(), nullable=False),
        sa.Column('tipo_etapa', sa.String(50), nullable=False),
        sa.Column('data_hora', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('origem', sa.String(20), nullable=False, server_default='sistema'),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['doacao_id'], ['doacoes.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("origem IN ('sistema', 'usuario')", name='check_origem'),
        sa.Index('idx_doacao_id', 'doacao_id')
    )


def downgrade():
    """Drop doacoes_etapas table"""
    op.drop_table('doacoes_etapas')
