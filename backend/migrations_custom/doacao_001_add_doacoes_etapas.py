"""Add doacoes_etapas table

Revision ID: doacao_001
Revises: necessidade_001
Create Date: 2026-11-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


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


def upgrade():
    """Cria tabela doacoes_etapas"""
    sql = """
    CREATE TABLE IF NOT EXISTS doacoes_etapas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        doacao_id INT NOT NULL,
        tipo_etapa VARCHAR(50) NOT NULL,
        data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        usuario_id INT,
        origem VARCHAR(20) NOT NULL DEFAULT 'sistema',
        observacao TEXT,
        criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doacao_id) REFERENCES doacoes(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        INDEX idx_doacao_id (doacao_id),
        CHECK (origem IN ('sistema', 'usuario'))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    db.session.execute(text(sql))
    db.session.commit()


def downgrade():
    """Remove tabela doacoes_etapas"""
    sql = "DROP TABLE IF EXISTS doacoes_etapas;"
    db.session.execute(text(sql))
    db.session.commit()
