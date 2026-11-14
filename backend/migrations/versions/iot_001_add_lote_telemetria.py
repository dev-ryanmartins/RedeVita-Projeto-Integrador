"""IoT batch telemetry tracking migration

This migration adds the lotes_telemetria table for tracking IoT batch processing.
Stores operational metadata only, not full payloads or sensitive data.

Revision ID: iot_001
Revises: qr_002
Create Date: 2024-10-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'iot_001'
down_revision = 'qr_002'
branch_labels = None
depends_on = None


def upgrade():
    """Add lotes_telemetria table for IoT batch tracking."""
    op.create_table(
        'lotes_telemetria',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lote_id', sa.String(36), nullable=False, comment='UUID interno gerado no servidor'),
        sa.Column('data_recebimento', sa.DateTime(), nullable=False, comment='Timestamp de recebimento no servidor (UTC)'),
        sa.Column('total_recebidas', sa.Integer(), nullable=False, comment='Total de leituras recebidas no lote'),
        sa.Column('total_processadas', sa.Integer(), nullable=False, comment='Total de leituras processadas com sucesso'),
        sa.Column('total_rejeitadas', sa.Integer(), nullable=False, comment='Total de leituras rejeitadas'),
        sa.Column('resultado', sa.Enum('COMPLETO', 'PARCIAL', 'REJEITADO', name='resultadoloteenum'), nullable=False, comment='Resultado agregado do processamento'),
        sa.Column('qtd_dispositivos', sa.Integer(), nullable=False, comment='Quantidade de dispositivos distintos no lote'),
        sa.Column('dispositivo_principal', sa.String(50), nullable=True, comment='ID do dispositivo quando há apenas um no lote (não autenticado)'),
        sa.Column('erros_por_categoria', sa.JSON(), nullable=True, comment='Categorias e quantidades de erros, sem mensagens brutas'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lote_id')
    )
    op.create_index(op.f('ix_lotes_telemetria_lote_id'), 'lotes_telemetria', ['lote_id'], unique=False)
    op.create_index(op.f('ix_lotes_telemetria_data_recebimento'), 'lotes_telemetria', ['data_recebimento'], unique=False)


def downgrade():
    """Remove lotes_telemetria table."""
    op.drop_index(op.f('ix_lotes_telemetria_data_recebimento'), table_name='lotes_telemetria')
    op.drop_index(op.f('ix_lotes_telemetria_lote_id'), table_name='lotes_telemetria')
    op.drop_table('lotes_telemetria')
