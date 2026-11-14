#!/usr/bin/env python3
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import create_app
from app.database import db
from app.models.usuario import Usuario

app = create_app()

with app.app_context():
    admin = Usuario.query.filter_by(cargo='Admin').first()
    if admin:
        print(f"Admin encontrado:")
        print(f"Nome: {admin.nome}")
        print(f"CPF: {admin.cpf}")
        print(f"Email: {admin.email}")
        print(f"Ativo: {admin.ativo}")
        print(f"Senha trocada: {admin.senha_trocada}")
    else:
        print("Nenhum admin encontrado")
