from app.core.security import criptografar_senha
from app.models.usuario import Usuario
from app.database import db
from main import create_app
import sys
import os
import secrets
import string
from getpass import getpass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def gerar_senha_forte(tamanho=12):
    """Gera uma senha forte aleatória"""
    alfabeto = string.ascii_letters + string.digits + "!@#$%^&*"
    senha = ''.join(secrets.choice(alfabeto) for _ in range(tamanho))
    return senha


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

print('=' * 55)
print('  RedeVita — Configuração de Usuários de Teste')
print('=' * 55)
print()

# Gera senha para todos os usuários
senha = gerar_senha_forte()
print(f'  Senha gerada para todos os usuários: {senha}')
print('  Guarde esta senha com segurança.')
print()

app = create_app()

with app.app_context():
    for dados in USUARIOS_TESTE:
        usuario = Usuario.query.filter_by(cpf=dados['cpf']).first()

        if usuario:
            usuario.nome = dados['nome']
            usuario.email = dados['email']
            usuario.senha = criptografar_senha(senha)
            usuario.cargo = dados['cargo']
            usuario.ativo = True
            usuario.senha_trocada = True
            acao = 'ATUALIZADO'
        else:
            usuario = Usuario(
                nome=dados['nome'],
                cpf=dados['cpf'],
                email=dados['email'],
                senha=criptografar_senha(senha),
                cargo=dados['cargo'],
                ativo=True,
                senha_trocada=True
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
    print(f'  Senha de todos os usuários: {senha}')
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
