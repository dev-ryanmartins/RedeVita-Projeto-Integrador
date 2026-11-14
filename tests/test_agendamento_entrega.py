import pytest
from datetime import datetime, timedelta
from backend.main import create_app
from app.database import db
from app.models import Usuario, AgendamentoEntrega
from app.models.farmacia import Farmacia
from app.core.decorators import admin_required


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_usuario_id(app):
    with app.app_context():
        admin = Usuario(
            nome='Admin Test',
            cpf='12345678900',
            email='admin@test.com',
            cargo='admin',
            senha='senha123'
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def farmacia_1_id(app):
    with app.app_context():
        farmacia = Farmacia(
            nome_fantasia='Farmacia Central',
            razao_social='Farmacia Central LTDA',
            cnpj='12345678000190',
            endereco='Rua A, 123',
            responsavel='João Silva',
            latitude=-23.5505,
            longitude=-46.6333
        )
        db.session.add(farmacia)
        db.session.commit()
        return farmacia.id


@pytest.fixture
def farmacia_2_id(app):
    with app.app_context():
        farmacia = Farmacia(
            nome_fantasia='Farmacia Norte',
            razao_social='Farmacia Norte LTDA',
            cnpj='98765432000190',
            endereco='Rua B, 456',
            responsavel='Maria Santos',
            latitude=-23.5605,
            longitude=-46.6433
        )
        db.session.add(farmacia)
        db.session.commit()
        return farmacia.id


@pytest.fixture
def agendamento_teste_id(app, admin_usuario_id, farmacia_1_id, farmacia_2_id):
    with app.app_context():
        agendamento = AgendamentoEntrega(
            farmacia_origem_id=farmacia_1_id,
            farmacia_destino_id=farmacia_2_id,
            data_hora_inicio=datetime.now() + timedelta(days=1),
            data_hora_fim=datetime.now() + timedelta(days=1, hours=2),
            criado_por_id=admin_usuario_id,
            estado='proposta'
        )
        db.session.add(agendamento)
        db.session.commit()
        return agendamento.id


def test_listar_agendamentos_sem_autenticacao(client):
    """Visitante não pode acessar a lista de agendamentos"""
    response = client.get('/agendamentos-entrega')
    assert response.status_code == 302  # Redireciona para login


def test_listar_agendamentos_com_admin(client, admin_usuario_id):
    """Admin pode acessar a lista de agendamentos"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    response = client.get('/agendamentos-entrega')
    assert response.status_code == 200
    assert b'Agendamento de Entrega' in response.data


def test_criar_agendamento_com_admin(client, admin_usuario_id, farmacia_1_id, farmacia_2_id):
    """Admin pode criar agendamento"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    data_inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    data_fim = (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')
    
    response = client.post('/agendamentos-entrega', data={
        'farmacia_origem_id': farmacia_1_id,
        'farmacia_destino_id': farmacia_2_id,
        'data_hora_inicio': data_inicio,
        'data_hora_fim': data_fim,
        'observacoes': 'Teste de agendamento'
    })
    assert response.status_code == 302  # Redireciona após criação


def test_criar_agendamento_mesma_farmacia(client, admin_usuario_id, farmacia_1_id):
    """Não pode criar agendamento com origem e destino iguais"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    data_inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    data_fim = (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')
    
    response = client.post('/agendamentos-entrega', data={
        'farmacia_origem_id': farmacia_1_id,
        'farmacia_destino_id': farmacia_1_id,
        'data_hora_inicio': data_inicio,
        'data_hora_fim': data_fim
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'diferentes' in response.data


def test_criar_agendamento_passado(client, admin_usuario_id, farmacia_1_id, farmacia_2_id):
    """Não pode criar agendamento no passado"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    data_inicio = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    data_fim = (datetime.now() - timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')
    
    response = client.post('/agendamentos-entrega', data={
        'farmacia_origem_id': farmacia_1_id,
        'farmacia_destino_id': farmacia_2_id,
        'data_hora_inicio': data_inicio,
        'data_hora_fim': data_fim
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'passado' in response.data.lower()


def test_confirmar_origem(client, admin_usuario_id, agendamento_teste_id):
    """Admin pode confirmar origem"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    response = client.post(f'/agendamentos-entrega/{agendamento_teste_id}/confirmar-origem')
    assert response.status_code == 302  # Redireciona após confirmação


def test_confirmar_destino(client, admin_usuario_id, agendamento_teste_id):
    """Admin pode confirmar destino"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    response = client.post(f'/agendamentos-entrega/{agendamento_teste_id}/confirmar-destino')
    assert response.status_code == 302


def test_cancelar_agendamento(client, admin_usuario_id, agendamento_teste_id):
    """Admin pode cancelar agendamento"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    response = client.post(f'/agendamentos-entrega/{agendamento_teste_id}/cancelar')
    assert response.status_code == 302


def test_agendamento_nao_altera_medicamentos(client, admin_usuario_id, farmacia_1_id, farmacia_2_id):
    """Agendamento não altera medicamentos"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    # Verificar que não há alteração em medicamentos
    from app.models.medicamento import Medicamento
    count_antes = Medicamento.query.count()
    
    data_inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    data_fim = (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')
    
    client.post('/agendamentos-entrega', data={
        'farmacia_origem_id': farmacia_1_id,
        'farmacia_destino_id': farmacia_2_id,
        'data_hora_inicio': data_inicio,
        'data_hora_fim': data_fim
    })
    
    count_depois = Medicamento.query.count()
    assert count_antes == count_depois


def test_agendamento_nao_altera_estoque(client, admin_usuario_id, farmacia_1_id, farmacia_2_id):
    """Agendamento não altera estoque"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    # Verificar que não há alteração em movimentos de estoque
    from app.models.movimento_estoque import MovimentoEstoque
    count_antes = MovimentoEstoque.query.count()
    
    data_inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    data_fim = (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')
    
    client.post('/agendamentos-entrega', data={
        'farmacia_origem_id': farmacia_1_id,
        'farmacia_destino_id': farmacia_2_id,
        'data_hora_inicio': data_inicio,
        'data_hora_fim': data_fim
    })
    
    count_depois = MovimentoEstoque.query.count()
    assert count_antes == count_depois


def test_agendamento_nao_altera_doacoes(client, admin_usuario_id, farmacia_1_id, farmacia_2_id):
    """Agendamento não altera doações"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    # Verificar que não há alteração em doações
    from app.models.doacao import Doacao
    count_antes = Doacao.query.count()
    
    data_inicio = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    data_fim = (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')
    
    client.post('/agendamentos-entrega', data={
        'farmacia_origem_id': farmacia_1_id,
        'farmacia_destino_id': farmacia_2_id,
        'data_hora_inicio': data_inicio,
        'data_hora_fim': data_fim
    })
    
    count_depois = Doacao.query.count()
    assert count_antes == count_depois


def test_aviso_persistente_na_interface(client, admin_usuario_id):
    """Aviso persistente está presente na interface"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_usuario_id)
        sess['_fresh'] = True
    
    response = client.get('/agendamentos-entrega')
    assert response.status_code == 200
    assert b'Agendamento operacional' in response.data
    assert b'estoque' in response.data.lower()
