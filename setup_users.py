"""
Script para criar/atualizar um usuário de teste para cada cargo do sistema RedeVita.

Cargos criados:
  Admin        — CPF: 00000000000  senha: admin123
  Operador     — CPF: 11111111111  senha: admin123
  Médico       — CPF: 22222222222  senha: admin123
  Farmacêutico — CPF: 33333333333  senha: admin123
  Voluntário   — CPF: 44444444444  senha: admin123

Como rodar:
  uv run python setup_users.py
"""

from app.core.security import criptografar_senha
from app.models.usuario import Usuario
from app.database import db
from main import create_app
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


SENHA_PADRAO = 'admin123'

USUARIOS_TESTE = [
    {
        'nome': 'Administrador',
        'cpf': '00000000000',
        'email': 'admin@redevita.local',
        'cargo': 'Admin',
    },
    {
        'nome': 'Operador Teste',
        'cpf': '11111111111',
        'email': 'operador@redevita.local',
        'cargo': 'Operador',
    },
    {
        'nome': 'Dr. Médico Teste',
        'cpf': '22222222222',
        'email': 'medico@redevita.local',
        'cargo': 'Médico',
    },
    {
        'nome': 'Farmacêutico Teste',
        'cpf': '33333333333',
        'email': 'farmaceutico@redevita.local',
        'cargo': 'Farmacêutico',
    },
    {
        'nome': 'Voluntário Teste',
        'cpf': '44444444444',
        'email': 'voluntario@redevita.local',
        'cargo': 'Voluntário',
    },
]

app = create_app()

with app.app_context():
    print('=' * 55)
    print('  RedeVita — Configuração de Usuários de Teste')
    print('=' * 55)

    for dados in USUARIOS_TESTE:
        usuario = Usuario.query.filter_by(cpf=dados['cpf']).first()

        if usuario:
            usuario.nome = dados['nome']
            usuario.email = dados['email']
            usuario.senha = criptografar_senha(SENHA_PADRAO)
            usuario.cargo = dados['cargo']
            usuario.ativo = True
            acao = 'ATUALIZADO'
        else:
            usuario = Usuario(
                nome=dados['nome'],
                cpf=dados['cpf'],
                email=dados['email'],
                senha=criptografar_senha(SENHA_PADRAO),
                cargo=dados['cargo'],
                ativo=True,
            )
            db.session.add(usuario)
            acao = 'CRIADO   '

        db.session.commit()
        print(
            f'  [{acao}] {
                dados["cargo"]:<14} | CPF: {
                dados["cpf"]} | {
                dados["nome"]}')

    print('=' * 55)
    print(f'  Senha de todos os usuários: {SENHA_PADRAO}')
    print('=' * 55)
    print()
    print('  Resumo de permissões por cargo:')
    print()
    print('  Admin        → Acesso total ao sistema')
    print('  Operador     → CRUD completo (sem excluir registros e sem gerenciar usuários/logs)')
    print('  Médico       → Pacientes, Receituário (emitir), Médicos (visualizar), Bula, Mapa')
    print('  Farmacêutico → Inventário, Doações, Dispensar receitas, Farmácias, Bula, Mapa')
    print('  Voluntário   → Doações, Inventário (visualizar), Mapa, Bula')
    print('=' * 55)
