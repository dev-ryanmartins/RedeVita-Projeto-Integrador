"""
Migration manual para criar tabela agendamentos_entrega

Uso:
    python -c "from backend.app.database import db, app; from backend.migrations_custom.agendamento_001_add_agendamentos_entrega import upgrade; app.app_context().push(); upgrade()"

Para reverter:
    python -c "from backend.app.database import db, app; from backend.migrations_custom.agendamento_001_add_agendamentos_entrega import downgrade; app.app_context().push(); downgrade()"
"""

from sqlalchemy import text
from backend.app.database import db


def upgrade():
    """Cria tabela agendamentos_entrega"""
    sql = """
    CREATE TABLE IF NOT EXISTS agendamentos_entrega (
        id INT AUTO_INCREMENT PRIMARY KEY,
        farmacia_origem_id INT NOT NULL,
        farmacia_destino_id INT NOT NULL,
        data_hora_inicio DATETIME NOT NULL,
        data_hora_fim DATETIME NOT NULL,
        estado VARCHAR(50) NOT NULL DEFAULT 'proposta',
        observacoes TEXT,
        criado_por_id INT NOT NULL,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
        confirmado_origem_por_id INT,
        confirmado_origem_em DATETIME,
        confirmado_destino_por_id INT,
        confirmado_destino_em DATETIME,
        cancelado_por_id INT,
        cancelado_em DATETIME,
        motivo_cancelamento TEXT,
        FOREIGN KEY (farmacia_origem_id) REFERENCES farmacias(id),
        FOREIGN KEY (farmacia_destino_id) REFERENCES farmacias(id),
        FOREIGN KEY (criado_por_id) REFERENCES usuarios(id),
        FOREIGN KEY (confirmado_origem_por_id) REFERENCES usuarios(id),
        FOREIGN KEY (confirmado_destino_por_id) REFERENCES usuarios(id),
        FOREIGN KEY (cancelado_por_id) REFERENCES usuarios(id),
        CHECK (farmacia_origem_id != farmacia_destino_id),
        CHECK (data_hora_fim > data_hora_inicio),
        CHECK (estado IN ('proposta', 'aguardando_confirmacao_origem', 'aguardando_confirmacao_destino', 'confirmado', 'cancelado', 'encerrado_sem_confirmacao'))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    db.session.execute(text(sql))
    db.session.commit()


def downgrade():
    """Remove tabela agendamentos_entrega"""
    sql = "DROP TABLE IF EXISTS agendamentos_entrega;"
    db.session.execute(text(sql))
    db.session.commit()
