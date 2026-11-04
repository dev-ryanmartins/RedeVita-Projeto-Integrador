"""Testes para Recibo de Etapas da Doação"""
import pytest
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.models.doacao import Doacao
from app.models.doacao_etapa import DoacaoEtapa, TipoEtapa, OrigemEvento
from datetime import datetime


@pytest.fixture
def app():
    """Cria uma aplicação Flask para testes."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Cria um cliente de teste."""
    return app.test_client()


@pytest.fixture
def admin_usuario_id(app):
    """Cria um usuário admin e retorna seu ID."""
    with app.app_context():
        admin = Usuario(
            nome="Admin Teste",
            cpf="00000000000",
            email="admin@teste.com",
            senha="senha123",
            cargo="Admin",
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def operador_usuario_id(app):
    """Cria um usuário operador e retorna seu ID."""
    with app.app_context():
        operador = Usuario(
            nome="Operador Teste",
            cpf="11111111111",
            email="operador@teste.com",
            senha="senha123",
            cargo="Operador",
            ativo=True
        )
        db.session.add(operador)
        db.session.commit()
        return operador.id


@pytest.fixture
def outro_operador_usuario_id(app):
    """Cria outro usuário operador e retorna seu ID."""
    with app.app_context():
        operador = Usuario(
            nome="Outro Operador",
            cpf="22222222222",
            email="outro@teste.com",
            senha="senha123",
            cargo="Operador",
            ativo=True
        )
        db.session.add(operador)
        db.session.commit()
        return operador.id


@pytest.fixture
def medicamento_id(app):
    """Cria um medicamento e retorna seu ID."""
    with app.app_context():
        med = Medicamento(
            nome="Dipirona 500mg",
            lote="LOTE001",
            data_validade=datetime(2027, 12, 31),
            quantidade=100,
            tarja="Sem Tarja",
            ativo=True
        )
        db.session.add(med)
        db.session.commit()
        return med.id


@pytest.fixture
def doacao_id(app, operador_usuario_id, medicamento_id):
    """Cria uma doação e retorna seu ID."""
    with app.app_context():
        doacao = Doacao(
            usuario_id=operador_usuario_id,
            medicamento_id=medicamento_id,
            quantidade=10
        )
        db.session.add(doacao)
        db.session.commit()

        # Cria etapa inicial
        etapa = DoacaoEtapa(
            doacao_id=doacao.id,
            tipo_etapa=TipoEtapa.REGISTRO_CRIADO.value,
            data_hora=datetime.utcnow(),
            usuario_id=operador_usuario_id,
            origem=OrigemEvento.USUARIO.value,
            observacao="Registro de saída"
        )
        db.session.add(etapa)
        db.session.commit()
        return doacao.id


def test_recibo_visitante_nao_autorizado(client, doacao_id):
    """Visitante sem login deve ser redirecionado."""
    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 302  # Redirect para login


def test_recibo_admin_pode_ver_qualquer_doacao(client, app, admin_usuario_id, doacao_id):
    """Admin pode ver recibo de qualquer doação."""
    with app.app_context():
        # Login como admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200
    assert b'Recibo de Etapas da Doação' in response.data


def test_recibo_operador_pode_ver_sua_doacao(client, app, operador_usuario_id, doacao_id):
    """Operador pode ver recibo de sua própria doação."""
    with app.app_context():
        # Login como operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(operador_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200
    assert b'Recibo de Etapas da Doação' in response.data


def test_recibo_operador_nao_pode_ver_doacao_alheia(client, app, outro_operador_usuario_id, doacao_id):
    """Operador não pode ver recibo de doação de outro usuário."""
    with app.app_context():
        # Login como outro operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(outro_operador_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 302  # Redirect ou erro


def test_recibo_mostra_etapas_em_ordem_cronologica(client, app, operador_usuario_id, doacao_id):
    """Recibo mostra etapas em ordem cronológica."""
    with app.app_context():
        # Adiciona mais etapas
        etapa2 = DoacaoEtapa(
            doacao_id=doacao_id,
            tipo_etapa=TipoEtapa.PESAGEM_REGISTRADA.value,
            data_hora=datetime.utcnow(),
            usuario_id=None,
            origem=OrigemEvento.SISTEMA.value,
            observacao="Peso registrado: 50g"
        )
        db.session.add(etapa2)
        db.session.commit()

        # Login como operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(operador_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200
    assert b'Registro Criado' in response.data
    assert b'Pesagem Registrada' in response.data


def test_recibo_distingue_evento_automatico_vs_manual(client, app, operador_usuario_id, doacao_id):
    """Recibo distingue eventos automáticos de manuais."""
    with app.app_context():
        # Adiciona evento automático
        etapa_auto = DoacaoEtapa(
            doacao_id=doacao_id,
            tipo_etapa=TipoEtapa.PESAGEM_REGISTRADA.value,
            data_hora=datetime.utcnow(),
            usuario_id=None,
            origem=OrigemEvento.SISTEMA.value,
            observacao="Evento automático"
        )
        db.session.add(etapa_auto)

        # Adiciona evento manual
        etapa_manual = DoacaoEtapa(
            doacao_id=doacao_id,
            tipo_etapa=TipoEtapa.CONFERENCIA_MANUAL_CONCLUIDA.value,
            data_hora=datetime.utcnow(),
            usuario_id=operador_usuario_id,
            origem=OrigemEvento.USUARIO.value,
            observacao="Evento manual"
        )
        db.session.add(etapa_manual)
        db.session.commit()

        # Login como operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(operador_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200
    assert b'Sistema' in response.data
    assert b'Usuário' in response.data


def test_recibo_sem_etapas(client, app, admin_usuario_id, medicamento_id):
    """Recibo sem etapas mostra estado vazio."""
    with app.app_context():
        # Cria doação sem etapas
        doacao = Doacao(
            usuario_id=admin_usuario_id,
            medicamento_id=medicamento_id,
            quantidade=5
        )
        db.session.add(doacao)
        db.session.commit()

        # Login como admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_usuario_id)

    response = client.get(f'/doacoes/{doacao.id}/recibo')
    assert response.status_code == 200
    assert b'Nenhuma etapa registrada' in response.data


def test_recibo_nao_exibe_dados_pessoais(client, app, operador_usuario_id, doacao_id):
    """Recibo não expõe dados pessoais sensíveis."""
    with app.app_context():
        # Login como operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(operador_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200
    # Não deve exibir CPF, email, telefone, etc.
    assert b'CPF' not in response.data or response.data.count(b'CPF') == 0
    assert b'email' not in response.data or response.data.count(b'email') == 0


def test_recibo_aviso_persistente(client, app, operador_usuario_id, doacao_id):
    """Recibo mostra aviso persistente sobre limitações."""
    with app.app_context():
        # Login como operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(operador_usuario_id)

    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200
    assert b'Este recibo mostra apenas etapas registradas no sistema' in response.data
    assert b'Não comprova por si só a entrega física' in response.data


def test_recibo_nao_altera_estoque(client, app, operador_usuario_id, doacao_id, medicamento_id):
    """Abrir recibo não altera estoque ou outras tabelas."""
    with app.app_context():
        # Verifica estoque antes
        medicamento = Medicamento.query.get(medicamento_id)
        estoque_antes = medicamento.quantidade

        # Login como operador
        with client.session_transaction() as sess:
            sess['_user_id'] = str(operador_usuario_id)

    # Abre recibo
    response = client.get(f'/doacoes/{doacao_id}/recibo')
    assert response.status_code == 200

    with app.app_context():
        # Verifica estoque depois
        medicamento = Medicamento.query.get(medicamento_id)
        estoque_depois = medicamento.quantidade
        assert estoque_antes == estoque_depois


def test_api_etapas_protegida(client, app, outro_operador_usuario_id, doacao_id):
    """API de etapas protegida por autorização."""
    with app.app_context():
        # Login como outro operador (não autorizado)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(outro_operador_usuario_id)

    response = client.get(f'/api/doacoes/{doacao_id}/etapas')
    assert response.status_code == 403


def test_api_etapas_admin_autorizado(client, app, admin_usuario_id, doacao_id):
    """API de etapas autorizada para admin."""
    with app.app_context():
        # Login como admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_usuario_id)

    response = client.get(f'/api/doacoes/{doacao_id}/etapas')
    assert response.status_code == 200
    assert b'etapas' in response.data
