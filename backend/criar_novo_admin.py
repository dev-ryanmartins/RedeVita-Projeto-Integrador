#!/usr/bin/env python3
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha

app = create_app()

with app.app_context():
    # Verifica se já existe admin com CPF 11111111111
    admin_existente = Usuario.query.filter_by(cpf='11111111111').first()
    if admin_existente:
        print("Admin já existe com CPF 11111111111")
        print("Senha: admin123")
    else:
        # Cria novo admin
        senha_hash = criptografar_senha("admin123")
        admin = Usuario(
            nome="Admin Principal",
            cpf="11111111111",
            email="admin@redevita.com",
            senha=senha_hash,
            cargo="Admin",
            ativo=True,
            senha_trocada=False
        )
        db.session.add(admin)
        db.session.commit()
        print("Novo admin criado com sucesso!")
        print("CPF: 11111111111")
        print("Senha: admin123")
