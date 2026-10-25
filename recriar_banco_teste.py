"""Script para recriar banco de teste com schema atualizado."""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.main import create_app
from app.database import db

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_redevita.db'

with app.app_context():
    # Recria todas as tabelas com schema atualizado
    db.create_all()
    print("Banco de teste recriado com schema atualizado")
