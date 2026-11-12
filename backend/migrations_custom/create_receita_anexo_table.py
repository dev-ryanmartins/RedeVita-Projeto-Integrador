"""
Migration para criar tabela receitas_anexos.
Tabela para armazenar anexos de receitas digitalizadas vinculadas a reservas.
"""

from app.database import db
from datetime import datetime


def upgrade():
    """Cria a tabela receitas_anexos."""
    with db.engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receitas_anexos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reserva_id INT NOT NULL UNIQUE,
                nome_arquivo_original VARCHAR(255) NOT NULL,
                nome_arquivo_interno VARCHAR(255) NOT NULL UNIQUE,
                caminho_arquivo VARCHAR(512) NOT NULL,
                tamanho_bytes INT NOT NULL,
                tipo_mime VARCHAR(100) NOT NULL,
                validado BOOLEAN DEFAULT FALSE NOT NULL,
                uploadado_por_id INT NOT NULL,
                uploadado_em DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                observacoes TEXT NULL,
                CONSTRAINT fk_receitas_anexos_reserva FOREIGN KEY (reserva_id) REFERENCES reservas_ofertas(id) ON DELETE CASCADE,
                CONSTRAINT fk_receitas_anexos_usuario FOREIGN KEY (uploadado_por_id) REFERENCES usuarios(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()


def downgrade():
    """Remove a tabela receitas_anexos."""
    with db.engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS receitas_anexos")
        conn.commit()


if __name__ == "__main__":
    from main import create_app
    app = create_app()
    with app.app_context():
        upgrade()
        print("Migration executada com sucesso.")
