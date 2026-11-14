"""
Migration para criar a tabela instituicoes
"""

from app.database import db
from main import create_app


def migrate():
    """Cria a tabela instituicoes"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a tabela já existe
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'instituicoes' not in tables:
            # Cria a tabela usando SQLAlchemy
            from app.models.instituicao import Instituicao
            Instituicao.__table__.create(db.engine, checkfirst=True)
        else:
            pass


def rollback():
    """Remove a tabela instituicoes"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a tabela existe
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'instituicoes' in tables:
            from app.models.instituicao import Instituicao
            Instituicao.__table__.drop(db.engine, checkfirst=True)
        else:
            pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
