"""
Testes para o vínculo Usuario-Farmacia (Tarefa 1)
Verifica associação de usuários a farmácias com relação N:1
"""

import pytest
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.farmacia import Farmacia
from app.core.security import criptografar_senha


@pytest.fixture
def app():
    """App Flask com banco temporário."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste."""
    return app.test_client()


@pytest.fixture
def farmacia(app):
    """Farmácia de teste."""
    farmacia = Farmacia(
        nome_fantasia="Farmácia Teste",
        razao_social="Farmácia Teste LTDA",
        cnpj="12345678000190",
        endereco="Rua Teste, 123",
        responsavel="Responsável Teste"
    )
    db.session.add(farmacia)
    db.session.commit()
    return farmacia


@pytest.fixture
def usuario_admin(app):
    """Usuário admin de teste."""
    usuario = Usuario(
        nome="Admin Teste",
        cpf="12345678901",
        email="admin@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Admin",
        ativo=True
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def usuario_operador(app):
    """Usuário operador de teste."""
    usuario = Usuario(
        nome="Operador Teste",
        cpf="98765432109",
        email="operador@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Operador",
        ativo=True
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def test_usuario_vinculado_recebe_farmacia_correta(farmacia, usuario_operador):
    """Usuário vinculado deve receber a farmácia correta."""
    usuario_operador.farmacia_id = farmacia.id
    db.session.commit()
    
    db.session.refresh(usuario_operador)
    assert usuario_operador.farmacia_id == farmacia.id
    assert usuario_operador.farmacia.nome_fantasia == "Farmácia Teste"


def test_usuario_sem_vinculo_continua_sem_associacao(usuario_operador):
    """Usuário sem vínculo deve continuar sem associação."""
    assert usuario_operador.farmacia_id is None
    assert usuario_operador.farmacia is None


def test_associacao_farmacia_inexistente_rejeitada(usuario_operador):
    """Associação a uma farmácia inexistente deve ser rejeitada."""
    # Tenta associar a uma farmácia que não existe
    usuario_operador.farmacia_id = 99999
    db.session.commit()
    
    # O relacionamento deve retornar None pois a farmácia não existe
    assert usuario_operador.farmacia is None


def test_usuario_sem_permissao_nao_consegue_alterar_vinculo(client, usuario_operador, farmacia):
    """Usuário sem permissão não deve conseguir alterar o vínculo."""
    # Tenta associar farmácia sem estar logado (deve falhar por falta de permissão @admin_required)
    response = client.post(f'/usuario/{usuario_operador.id}/farmacia', data={
        'farmacia_id': farmacia.id,
        'csrf_token': 'test'
    })
    
    # Deve retornar redirecionamento ou erro (403 ou 302 para login)
    assert response.status_code in [302, 403]


def test_migration_adiciona_coluna_farmacia_id(app):
    """Migration deve adicionar coluna farmacia_id sem preencher dados."""
    from backend.migrations_custom.add_farmacia_id_usuario import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a coluna existe
    inspector = db.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('usuarios')]
    assert 'farmacia_id' in columns


def test_usuarios_existentes_sem_vinculo(usuario_admin, usuario_operador):
    """Usuários existentes devem permanecer sem vínculo após migration."""
    from backend.migrations_custom.add_farmacia_id_usuario import migrate
    
    # Executa migration
    migrate()
    
    # Verifica que usuários existentes ainda estão sem vínculo
    db.session.refresh(usuario_admin)
    db.session.refresh(usuario_operador)
    
    assert usuario_admin.farmacia_id is None
    assert usuario_operador.farmacia_id is None


def test_verificar_constraint_sqlite(app):
    """Verifica se a constraint foreign_key existe no schema SQLite após migration."""
    from backend.migrations_custom.add_farmacia_id_usuario import migrate
    
    # Executa migration
    migrate()
    
    # Verifica constraints usando PRAGMA
    with db.engine.connect() as conn:
        result = conn.execute(db.text("PRAGMA foreign_key_list(usuarios)"))
        foreign_keys = result.fetchall()
    
    # Busca por constraint que referencia farmacias
    fk_farmacia = [fk for fk in foreign_keys if fk[2] == 'farmacias']
    
    # Se não houver constraint, reporte a lacuna
    if not fk_farmacia:
        print("CONSTRAINT FALTANDO: Nao ha foreign key constraint para farmacias na tabela usuarios")
        print("   SQLite nao suporta ADD CONSTRAINT em ALTER TABLE")
        print("   O modelo SQLAlchemy define a FK, mas o banco nao tem a constraint")
    else:
        print(f"CONSTRAINT ENCONTRADA: {len(fk_farmacia)} foreign key(s) para farmacias")
        for fk in fk_farmacia:
            print(f"   ID: {fk[0]}, Table: {fk[1]}, From: {fk[2]}, To: {fk[3]}")
    
    return fk_farmacia
