"""QR nonce and approval fields migration

This migration adds QR nonce table and approval fields for P0.10.

Revision ID: qr_001
Revises: 
Create Date: 2024-10-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'qr_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add QR nonce table and approval fields."""
    # Create qr_nonces table
    op.create_table(
        'qr_nonces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nonce', sa.String(64), nullable=False),
        sa.Column('receita_id', sa.Integer(), nullable=False),
        sa.Column('gerado_por_id', sa.Integer(), nullable=True),
        sa.Column('expira_em', sa.DateTime(), nullable=False),
        sa.Column('usado', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('usado_em', sa.DateTime(), nullable=True),
        sa.Column('usado_por_id', sa.Integer(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['receita_id'], ['receitas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gerado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nonce')
    )
    op.create_index(op.f('ix_qr_nonces_receita_id'), 'qr_nonces', ['receita_id'], unique=False)


def downgrade():
    """Remove QR nonce table and approval fields."""
    op.drop_index(op.f('ix_qr_nonces_receita_id'), table_name='qr_nonces')
    op.drop_table('qr_nonces')
