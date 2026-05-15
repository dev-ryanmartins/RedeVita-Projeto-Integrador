import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha

CPF_ALVO = '12345678901'
NOVA_SENHA = 'admin123'

app = create_app()

with app.app_context():
    usuario = Usuario.query.filter_by(cpf=CPF_ALVO).first()

    if usuario is None:
        print(f"[ERRO] Nenhum usuário encontrado com CPF: {CPF_ALVO}")
        print("CPFs cadastrados no banco:")
        todos = Usuario.query.all()
        if todos:
            for u in todos:
                print(f"  - CPF: {u.cpf} | Nome: {u.nome} | Ativo: {u.ativo} | Cargo: {u.cargo}")
        else:
            print("  (banco vazio)")
        sys.exit(1)

    print(f"Usuário encontrado: {usuario.nome} (CPF: {usuario.cpf})")
    print(f"  Ativo antes:  {usuario.ativo}")
    print(f"  Cargo:        {usuario.cargo}")

    usuario.senha = criptografar_senha(NOVA_SENHA)
    usuario.ativo = True

    db.session.commit()

    print(f"\nAtualizado com sucesso!")
    print(f"  Nova senha:   {NOVA_SENHA}")
    print(f"  Ativo depois: {usuario.ativo}")
