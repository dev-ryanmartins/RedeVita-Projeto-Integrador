"""Add necessidades_institucionais table

Revision ID: necessidade_001
Revises: qr_002
Create Date: 2026-10-30 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'necessidade_001'
down_revision = 'qr_002'
branch_labels = None
depends_on = None


def upgrade():
    """Create necessidades_institucionais table"""
    op.create_table(
        'necessidades_institucionais',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome_instituicao', sa.String(200), nullable=False),
        sa.Column('medicamento_referencia_id', sa.Integer(), nullable=True),
        sa.Column('produto_descritivo', sa.String(200), nullable=True),
        sa.Column('quantidade_solicitada', sa.Integer(), nullable=False),
        sa.Column('unidade', sa.String(20), nullable=False, server_default='unidade'),
        sa.Column('data_desejada', sa.Date(), nullable=True),
        sa.Column('prioridade', sa.String(20), nullable=False, server_default='media'),
        sa.Column('status', sa.String(20), nullable=False, server_default='rascunho'),
        sa.Column('criado_por_id', sa.Integer(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('revisado_por_id', sa.Integer(), nullable=True),
        sa.Column('revisado_em', sa.DateTime(), nullable=True),
        sa.Column('encerrado_por_id', sa.Integer(), nullable=True),
        sa.Column('encerrado_em', sa.DateTime(), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['medicamento_referencia_id'], ['medicamentos_referencia.id'], ),
        sa.ForeignKeyConstraint(['criado_por_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['revisado_por_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['encerrado_por_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Drop necessidades_institucionais table"""
    op.drop_table('necessidades_institucionais')
