"""
Migration para adicionar coluna instituicao_id à tabela necessidades_institucionais
Permite vincular necessidades a instituições receptoras reais
"""

from app.database import db
from main import create_app


def migrate():
    """Adiciona coluna instituicao_id à tabela necessidades_institucionais"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a coluna já existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('necessidades_institucionais')]
        
        if 'instituicao_id' not in columns:
            # Adiciona a coluna instituicao_id como nullable
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE necessidades_institucionais ADD COLUMN instituicao_id INT NULL"))
                conn.commit()
        else:
            pass


def rollback():
    """Remove a coluna instituicao_id da tabela necessidades_institucionais"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a coluna existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('necessidades_institucionais')]
        
        if 'instituicao_id' in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE necessidades_institucionais DROP COLUMN instituicao_id"))
                conn.commit()
        else:
            pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
