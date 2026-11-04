#!/usr/bin/env python3
"""
Script simples para criar usuário admin para teste
"""

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
    # Verifica se já existe admin
    admin_existente = Usuario.query.filter_by(cargo='Admin').first()
    if admin_existente:
        print("Admin já existe. CPF:", admin_existente.cpf)
        print("Senha: admin123")
    else:
        # Cria admin
        senha_hash = criptografar_senha("admin123")
        admin = Usuario(
            nome="Admin Teste",
            cpf="12345678900",
            email="admin@teste.com",
            senha=senha_hash,
            cargo="Admin",
            ativo=True,
            senha_trocada=False
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin criado com sucesso!")
        print("CPF: 12345678900")
        print("Senha: admin123")
