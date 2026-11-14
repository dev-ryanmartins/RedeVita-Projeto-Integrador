"""
Script de Configuração de Usuários de Teste (APENAS PARA DESENVOLVIMENTO)

ATENÇÃO: Este script não deve ser usado em produção.
Para produção, use backend/provision_admin.py para criar o primeiro administrador.

Uso:
    python setup_users.py <senha>
"""

from app.core.security import criptografar_senha
from app.models.usuario import Usuario
from app.database import db
from main import create_app
import sys
import os
import secrets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if len(sys.argv) < 2:
    print("ERRO: Senha não fornecida.")
    print("Uso: python setup_users.py <senha>")
    sys.exit(1)

SENHA = sys.argv[1]

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
    print('  ATENÇÃO: APENAS PARA DESENVOLVIMENTO')
    print('=' * 55)

    for dados in USUARIOS_TESTE:
        usuario = Usuario.query.filter_by(cpf=dados['cpf']).first()

        if usuario:
            usuario.nome = dados['nome']
            usuario.email = dados['email']
            usuario.senha = criptografar_senha(SENHA)
            usuario.cargo = dados['cargo']
            usuario.ativo = True
            usuario.senha_trocada = True  # Marca como já trocado para desenvolvimento
            acao = 'ATUALIZADO'
        else:
            usuario = Usuario(
                nome=dados['nome'],
                cpf=dados['cpf'],
                email=dados['email'],
                senha=criptografar_senha(SENHA),
                cargo=dados['cargo'],
                ativo=True,
                senha_trocada=True  # Marca como já trocado para desenvolvimento
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
    print(f'  Senha de todos os usuários: {SENHA}')
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
