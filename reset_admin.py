import sys
import os

# Adiciona a pasta 'backend' ao caminho de busca do Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha

app = create_app()

with app.app_context():
    try:
        # Remove usuários antigos para evitar conflitos de CPF
        num_deleted = Usuario.query.delete()
        db.session.commit()
        
        # Cria o novo usuário com senha criptografada
        admin = Usuario(
            nome="Administrador",
            cpf="12345678901",
            email="admin@redevita.com",
            senha=criptografar_senha("admin123"), # Criptografia correta
            cargo="Admin",
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Sucesso! {num_deleted} usuários antigos removidos.")
        print("Novo Usuário Admin criado:")
        print("CPF: 12345678901")
        print("Senha: admin123")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao configurar usuário: {e}")