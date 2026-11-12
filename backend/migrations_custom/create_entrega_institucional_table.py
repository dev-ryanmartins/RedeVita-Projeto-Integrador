"""
Migration para criar a tabela entregas_institucionais
"""

from app.database import db
from main import create_app


def migrate():
    """Cria a tabela entregas_institucionais"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a tabela já existe
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'entregas_institucionais' not in tables:
            # Cria a tabela usando SQLAlchemy
            from app.models.entrega_institucional import EntregaInstitucional
            EntregaInstitucional.__table__.create(db.engine, checkfirst=True)
        else:
            pass


def rollback():
    """Remove a tabela entregas_institucionais"""
    app = create_app()
    
    with app.app_context():
        # Verifica se a tabela existe
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'entregas_institucionais' in tables:
            from app.models.entrega_institucional import EntregaInstitucional
            EntregaInstitucional.__table__.drop(db.engine, checkfirst=True)
        else:
            pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
