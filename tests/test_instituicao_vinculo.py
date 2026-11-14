"""
Testes para vínculo Instituição-Usuario-Necessidade (Fase 1)
Verifica criação de instituições e vínculos com usuários e necessidades
"""

import pytest
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.instituicao import Instituicao
from app.models.necessidade_institucional import NecessidadeInstitucional
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
def instituicao(app):
    """Instituição de teste."""
    instituicao = Instituicao(
        nome="Instituição Teste",
        cnpj="12345678000190",
        endereco="Rua Teste, 123",
        responsavel="Responsável Teste",
        telefone="11999999999",
        email="instituicao@teste.com",
        ativo=True
    )
    db.session.add(instituicao)
    db.session.commit()
    return instituicao


@pytest.fixture
def usuario_instituicao(app):
    """Usuário vinculado à instituição de teste."""
    usuario = Usuario(
        nome="Usuário Instituição",
        cpf="11122233344",
        email="usuario_instituicao@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Operador",
        ativo=True
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def test_criar_instituicao(app):
    """Testa criação de instituição."""
    instituicao = Instituicao(
        nome="Hospital Teste",
        cnpj="98765432000190",
        endereco="Av. Principal, 456",
        responsavel="Dr. Teste",
        telefone="11888888888",
        email="hospital@teste.com",
        ativo=True
    )
    db.session.add(instituicao)
    db.session.commit()
    
    db.session.refresh(instituicao)
    assert instituicao.id is not None
    assert instituicao.nome == "Hospital Teste"
    assert instituicao.cnpj == "98765432000190"
    assert instituicao.ativo is True


def test_usuario_vinculado_instituicao(usuario_instituicao, instituicao):
    """Usuário vinculado deve receber a instituição correta."""
    usuario_instituicao.instituicao_id = instituicao.id
    db.session.commit()
    
    db.session.refresh(usuario_instituicao)
    assert usuario_instituicao.instituicao_id == instituicao.id
    assert usuario_instituicao.instituicao.nome == "Instituição Teste"


def test_usuario_sem_vinculo_instituicao(usuario_instituicao):
    """Usuário sem vínculo deve continuar sem instituição."""
    assert usuario_instituicao.instituicao_id is None
    assert usuario_instituicao.instituicao is None


def test_necessidade_vinculada_instituicao(app, instituicao):
    """Necessidade deve poder ser vinculada à instituição."""
    necessidade = NecessidadeInstitucional(
        nome_instituicao="Instituição Legado",
        instituicao_id=instituicao.id,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=100,
        unidade="unidade",
        prioridade="media",
        status="rascunho",
        criado_por_id=1
    )
    db.session.add(necessidade)
    db.session.commit()
    
    db.session.refresh(necessidade)
    assert necessidade.instituicao_id == instituicao.id
    assert necessidade.instituicao.nome == "Instituição Teste"


def test_migration_cria_tabela_instituicoes(app):
    """Migration deve criar tabela instituicoes."""
    from backend.migrations_custom.create_instituicao_table import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a tabela existe
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    assert 'instituicoes' in tables


def test_migration_adiciona_instituicao_id_usuario(app):
    """Migration deve adicionar coluna instituicao_id em usuarios."""
    from backend.migrations_custom.add_instituicao_id_usuario import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a coluna existe
    inspector = db.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('usuarios')]
    assert 'instituicao_id' in columns


def test_migration_adiciona_instituicao_id_necessidade(app):
    """Migration deve adicionar coluna instituicao_id em necessidades_institucionais."""
    from backend.migrations_custom.add_instituicao_id_necessidade import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a coluna existe
    inspector = db.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('necessidades_institucionais')]
    assert 'instituicao_id' in columns


def test_usuarios_existentes_sem_vinculo_instituicao(usuario_instituicao):
    """Usuários existentes devem permanecer sem vínculo após migration."""
    from backend.migrations_custom.add_instituicao_id_usuario import migrate
    
    # Executa migration
    migrate()
    
    # Verifica que usuários existentes ainda estão sem vínculo
    db.session.refresh(usuario_instituicao)
    assert usuario_instituicao.instituicao_id is None


def test_necessidades_existentes_sem_vinculo_instituicao(app):
    """Necessidades existentes devem permanecer sem vínculo após migration."""
    from backend.migrations_custom.add_instituicao_id_necessidade import migrate
    
    # Cria uma necessidade sem vínculo
    necessidade = NecessidadeInstitucional(
        nome_instituicao="Instituição Legado",
        produto_descritivo="Teste",
        quantidade_solicitada=10,
        unidade="unidade",
        prioridade="media",
        status="rascunho",
        criado_por_id=1
    )
    db.session.add(necessidade)
    db.session.commit()
    
    # Executa migration
    migrate()
    
    # Verifica que necessidades existentes ainda estão sem vínculo
    db.session.refresh(necessidade)
    assert necessidade.instituicao_id is None
    assert necessidade.nome_instituicao == "Instituição Legado"


def test_usuario_sem_permissao_nao_pode_associar_instituicao(client, usuario_instituicao, instituicao):
    """Usuário sem permissão não deve conseguir associar instituição."""
    # Tenta associar instituição sem estar logado (deve falhar por falta de permissão @admin_required)
    response = client.post(f'/usuario/{usuario_instituicao.id}/instituicao', data={
        'instituicao_id': instituicao.id,
        'csrf_token': 'test'
    })
    
    # Deve retornar redirecionamento ou erro (403 ou 302 para login)
    assert response.status_code in [302, 403]
