"""
Migração para adicionar coluna farmacia_id à tabela usuarios
Permite vincular usuários a farmácias (relação N:1)
"""

from app.database import db
from main import create_app

def migrate():
    """Adiciona coluna farmacia_id à tabela usuarios"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a coluna já existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('usuarios')]
        
        if 'farmacia_id' not in columns:
            # Adiciona a coluna farmacia_id como nullable
            # SQLite não suporta ADD CONSTRAINT FOREIGN KEY em ALTER TABLE
            # O SQLAlchemy vai gerenciar a foreign key através do modelo
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN farmacia_id INT NULL"))
                conn.commit()
        else:
            pass

def rollback():
    """Remove a coluna farmacia_id da tabela usuarios"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a coluna existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('usuarios')]
        
        if 'farmacia_id' in columns:
            # SQLite não suporta DROP FOREIGN KEY
            # Apenas remove a coluna
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE usuarios DROP COLUMN farmacia_id"))
                conn.commit()
            
            print("✅ Coluna 'farmacia_id' removida da tabela usuarios")
        else:
            print("ℹ️ Coluna 'farmacia_id' não existe na tabela usuarios")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
