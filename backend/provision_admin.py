#!/usr/bin/env python3
"""
Provisionamento do Primeiro Administrador

Este script cria o primeiro administrador do sistema quando o banco está vazio.
Só pode ser executado quando não há administradores existentes.
As credenciais são exibidas uma única vez no terminal.

Uso:
    python provision_admin.py
"""

import os
import sys
import secrets
import string
from getpass import getpass

# Adiciona o diretório backend ao path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha


def gerar_senha_forte(tamanho=16):
    """Gera uma senha forte aleatória"""
    alfabeto = string.ascii_letters + string.digits + "!@#$%^&*"
    senha = ''.join(secrets.choice(alfabeto) for _ in range(tamanho))
    return senha


def provisionar_admin():
    """Provisiona o primeiro administrador"""
    app = create_app()
    
    with app.app_context():
        # Verifica se já existe administrador
        admin_existente = Usuario.query.filter_by(cargo='Admin').first()
        if admin_existente:
            print("ERRO: Já existe um administrador no sistema.")
            print("Use a interface administrativa para criar novos administradores.")
            sys.exit(1)
        
        # Verifica se há qualquer usuário
        if Usuario.query.first():
            print("ERRO: O banco já contém usuários.")
            print("O provisionamento só é permitido em banco vazio.")
            sys.exit(1)
        
        print("\n=== Provisionamento do Primeiro Administrador ===\n")
        
        # Coleta dados do administrador
        nome = input("Nome completo do administrador: ").strip()
        while not nome:
            print("Nome é obrigatório.")
            nome = input("Nome completo do administrador: ").strip()
        
        cpf = input("CPF (apenas números): ").strip()
        while len(cpf) != 11 or not cpf.isdigit():
            print("CPF inválido. Deve conter 11 dígitos.")
            cpf = input("CPF (apenas números): ").strip()
        
        email = input("E-mail (opcional, pressione Enter para pular): ").strip()
        if email and '@' not in email:
            print("E-mail inválido. Usando sem e-mail.")
            email = None
        
        # Gera senha forte
        senha = gerar_senha_forte()
        senha_hash = criptografar_senha(senha)
        
        print("\nCriando administrador...")
        
        # Cria administrador com senha_trocada=False
        admin = Usuario(
            nome=nome,
            cpf=cpf,
            email=email if email else None,
            senha=senha_hash,
            cargo='Admin',
            ativo=True,
            senha_trocada=False  # Força troca no primeiro acesso
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"ERRO: Falha ao criar administrador: {e}")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("ADMINISTRADOR CRIADO COM SUCESSO")
        print("="*60)
        print(f"Nome: {nome}")
        print(f"CPF: {cpf}")
        if email:
            print(f"E-mail: {email}")
        print(f"Senha: {senha}")
        print("="*60)
        print("\n⚠️  IMPORTANTE:")
        print("1. Guarde estas credenciais com segurança.")
        print("2. Esta senha NÃO será exibida novamente.")
        print("3. No primeiro acesso, você será solicitado a alterar a senha.")
        print("="*60 + "\n")


if __name__ == '__main__':
    try:
        provisionar_admin()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERRO: {e}")
        sys.exit(1)
