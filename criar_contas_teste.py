"""Script para criar contas de teste isoladas."""
import sys
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_redevita.db'

with app.app_context():
    # Limpar usuários de teste existentes
    db.session.query(Usuario).filter(Usuario.email.like('%@teste.local')).delete()
    db.session.commit()
    print("Usuarios de teste anteriores removidos")

    # Gerar senhas aleatórias seguras (novas, pois as anteriores foram expostas)
    senha_admin = secrets.token_urlsafe(16)
    senha_farma = secrets.token_urlsafe(16)
    senha_paciente = secrets.token_urlsafe(16)

    # Administrador de teste (CPF único e sintético - NOVO)
    admin = Usuario(
        nome='Administrador Teste',
        cpf='11223344556',  # Novo CPF sintético
        email='admin@teste.local',
        senha=criptografar_senha(senha_admin),
        cargo='Admin',
        ativo=True,
        senha_trocada=False
    )

    # Farmacêutico de teste (CPF único e sintético - NOVO)
    farmaceutico = Usuario(
        nome='Farmaceutico Teste',
        cpf='77889900112',  # Novo CPF sintético
        email='farmaceutico@teste.local',
        senha=criptografar_senha(senha_farma),
        cargo='Farmaceutico',
        ativo=True,
        senha_trocada=False
    )

    # Paciente de teste (CPF único e sintético - NOVO)
    paciente = Usuario(
        nome='Paciente Teste',
        cpf='3344556677',  # Novo CPF sintético
        email='paciente@teste.local',
        senha=criptografar_senha(senha_paciente),
        cargo='Paciente',
        ativo=True,
        senha_trocada=False
    )

    db.session.add_all([admin, farmaceutico, paciente])
    db.session.commit()

    print('=== CREDENCIAIS DE TESTE ===')
    print(f'ADMIN: admin@teste.local / {senha_admin}')
    print(f'FARMACEUTICO: farmaceutico@teste.local / {senha_farma}')
    print(f'PACIENTE: paciente@teste.local / Temp123!')
    print('=============================')
    print('A aplicacao esta rodando em http://localhost:5000')
    print('As contas forcarao troca de senha no primeiro acesso.')
