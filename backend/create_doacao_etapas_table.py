#!/usr/bin/env python3
"""Script para criar a tabela doacoes_etapas usando db.create_all()"""
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import create_app
from app.database import db

app = create_app()

with app.app_context():
    # Cria apenas a tabela doacoes_etapas se não existir
    inspector = db.inspect(db.engine)
    if inspector.has_table('doacoes_etapas'):
        print("Tabela 'doacoes_etapas' já existe.")
    else:
        db.create_all()
        print("Tabela 'doacoes_etapas' criada com sucesso.")
