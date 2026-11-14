"""
Migração para adicionar coluna 'ativo' à tabela medicamentos
Soft delete: medicamentos com doações vinculadas são arquivados em vez de excluídos
"""

from app.database import db
from app import create_app

def migrate():
    """Adiciona coluna ativo à tabela medicamentos"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a coluna já existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('medicamentos')]
        
        if 'ativo' not in columns:
            # Adiciona a coluna ativo com valor padrão True
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE medicamentos ADD COLUMN ativo BOOLEAN DEFAULT 1 NOT NULL"))
                conn.commit()
            
            print("✅ Coluna 'ativo' adicionada à tabela medicamentos")
            print("   Todos os medicamentos existentes foram marcados como ativos")
        else:
            print("ℹ️ Coluna 'ativo' já existe na tabela medicamentos")

if __name__ == "__main__":
    migrate()
