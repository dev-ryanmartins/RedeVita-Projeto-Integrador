import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha

CPF_ALVO   = '12345678901'
NOVA_SENHA  = 'admin123'
NOME_PADRAO = 'Administrador Teste'
EMAIL_PADRAO = 'admin.teste@redevita.local'

app = create_app()

with app.app_context():
    usuario = Usuario.query.filter_by(cpf=CPF_ALVO).first()

    if usuario:
        print(f"Usuário encontrado: {usuario.nome} (CPF: {usuario.cpf})")

        usuario.senha = criptografar_senha(NOVA_SENHA)
        usuario.ativo = True
        usuario.cargo = 'Admin'

        db.session.commit()

        print("Dados atualizados com sucesso:")
        print(f"  Senha:  {NOVA_SENHA}")
        print(f"  Ativo:  {usuario.ativo}")
        print(f"  Cargo:  {usuario.cargo}")

    else:
        print(f"Nenhum usuário com CPF {CPF_ALVO} encontrado. Criando novo usuário...")

        novo = Usuario(
            nome=NOME_PADRAO,
            cpf=CPF_ALVO,
            email=EMAIL_PADRAO,
            senha=criptografar_senha(NOVA_SENHA),
            cargo='Admin',
            ativo=True
        )
        db.session.add(novo)
        db.session.commit()

        print("Novo usuário administrador criado com sucesso:")
        print(f"  Nome:   {NOME_PADRAO}")
        print(f"  CPF:    {CPF_ALVO}")
        print(f"  Senha:  {NOVA_SENHA}")
        print(f"  Cargo:  Admin")
        print(f"  Ativo:  True")

    print("\nUsuários atualmente no banco:")
    for u in Usuario.query.all():
        print(f"  CPF: {u.cpf} | Nome: {u.nome} | Cargo: {u.cargo} | Ativo: {u.ativo}")
