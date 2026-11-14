"""Migration manual para adicionar campo senha_trocada."""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from backend.main import create_app
from app.database import db

def upgrade():
    """Adiciona campo senha_trocada à tabela usuarios."""
    app = create_app()
    with app.app_context():
        try:
            db.session.execute(text("""
                ALTER TABLE usuarios ADD COLUMN senha_trocada BOOLEAN DEFAULT 0
            """))
            db.session.commit()
            print("Migration aplicada: campo senha_trocada adicionado")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("Campo senha_trocada já existe")
            else:
                print(f"Erro na migration: {e}")
                db.session.rollback()

if __name__ == "__main__":
    upgrade()
