"""
Testes para Janela de Resgate de Lotes.

Testa:
- Acesso autorizado e bloqueio de perfis não autorizados
- Listagem de lotes
- Simulação de cenários
- Validação de parâmetros
- Ausência de alterações em dados reais
"""

import pytest
from datetime import date, timedelta
from backend.main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.services.lot_rescue_service import LotRescueService
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Cria aplicação Flask para testes."""
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
    """Cria cliente de teste."""
    return app.test_client()


@pytest.fixture
def admin_user_id(app):
    """Cria usuário admin para testes e retorna ID."""
    with app.app_context():
        admin = Usuario(
            nome='Admin Teste',
            email='admin@teste.com',
            cpf='12345678901',
            senha=generate_password_hash('senha123'),
            cargo='Admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def farmaceutico_user_id(app):
    """Cria usuário farmacêutico para testes e retorna ID."""
    with app.app_context():
        farmaceutico = Usuario(
            nome='Farmacêutico Teste',
            email='farmaceutico@teste.com',
            cpf='12345678902',
            senha=generate_password_hash('senha123'),
            cargo='Farmacêutico',
            ativo=True
        )
        db.session.add(farmaceutico)
        db.session.commit()
        return farmaceutico.id


@pytest.fixture
def medico_user_id(app):
    """Cria usuário médico para testes e retorna ID."""
    with app.app_context():
        medico = Usuario(
            nome='Médico Teste',
            email='medico@teste.com',
            cpf='12345678903',
            senha=generate_password_hash('senha123'),
            cargo='Médico',
            ativo=True
        )
        db.session.add(medico)
        db.session.commit()
        return medico.id


@pytest.fixture
def sample_medicamentos(app):
    """Cria medicamentos de exemplo para testes."""
    with app.app_context():
        # Lote crítico (vence em 5 dias)
        lote1 = Medicamento(
            nome='Paracetamol',
            lote='LOT001',
            data_validade=date.today() + timedelta(days=5),
            quantidade=100,
            ativo=True,
            status_semaforo=1,
            tarja='Amarela',
            principio_ativo='Paracetamol'
        )
        # Lote atenção (vence em 15 dias)
        lote2 = Medicamento(
            nome='Ibuprofeno',
            lote='LOT002',
            data_validade=date.today() + timedelta(days=15),
            quantidade=50,
            ativo=True,
            status_semaforo=0,
            tarja='Branca',
            principio_ativo='Ibuprofeno'
        )
        # Lote normal (vence em 60 dias)
        lote3 = Medicamento(
            nome='Dipirona',
            lote='LOT003',
            data_validade=date.today() + timedelta(days=60),
            quantidade=200,
            ativo=True,
            status_semaforo=0,
            tarja='Branca',
            principio_ativo='Dipirona'
        )
        # Lote vencido
        lote4 = Medicamento(
            nome='Amoxicilina',
            lote='LOT004',
            data_validade=date.today() - timedelta(days=10),
            quantidade=30,
            ativo=True,
            status_semaforo=2,
            tarja='Branca',
            principio_ativo='Amoxicilina'
        )
        # Lote fora do horizonte (vence em 400 dias)
        lote5 = Medicamento(
            nome='Omeprazol',
            lote='LOT005',
            data_validade=date.today() + timedelta(days=400),
            quantidade=150,
            ativo=True,
            status_semaforo=0,
            tarja='Branca',
            principio_ativo='Omeprazol'
        )

        db.session.add_all([lote1, lote2, lote3, lote4, lote5])
        db.session.commit()


class TestAcesso:
    """Testa controle de acesso."""

    def test_visitante_redirecionado_para_login(self, client):
        """Visitante deve ser redirecionado para login."""
        response = client.get('/janela-resgate-lotes', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_admin_acesso_permitido(self, client, admin_user_id):
        """Admin deve ter acesso permitido."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)
        response = client.get('/janela-resgate-lotes')
        assert response.status_code == 200

    def test_farmaceutico_acesso_permitido(self, client, farmaceutico_user_id):
        """Farmacêutico deve ter acesso permitido."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(farmaceutico_user_id)
        response = client.get('/janela-resgate-lotes')
        assert response.status_code == 200

    def test_medico_acesso_negado(self, client, medico_user_id):
        """Médico deve receber 403."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(medico_user_id)
        response = client.get('/janela-resgate-lotes')
        assert response.status_code == 403


class TestAPIListarLotes:
    """Testa API de listagem de lotes."""

    def test_listar_lotes_sucesso(self, client, admin_user_id, sample_medicamentos):
        """Testa listagem de lotes com sucesso."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.get('/api/janela-resgate-lotes/lotes?horizon_dias=30')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert len(data['dados']['lotes']) == 2  # LOT001 e LOT002

    def test_listar_lotes_filtro_nome(self, client, admin_user_id, sample_medicamentos):
        """Testa filtro por nome do medicamento."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.get('/api/janela-resgate-lotes/lotes?horizon_dias=30&nome_medicamento=Paracetamol')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert len(data['dados']['lotes']) == 1
        assert data['dados']['lotes'][0]['nome'] == 'Paracetamol'

    def test_listar_lotes_horizonte_invalido(self, client, admin_user_id):
        """Testa validação de horizonte inválido."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.get('/api/janela-resgate-lotes/lotes?horizon_dias=500')
        assert response.status_code == 400
        data = response.get_json()
        assert data['sucesso'] is False


class TestAPIResumo:
    """Testa API de resumo."""

    def test_resumo_sucesso(self, client, admin_user_id, sample_medicamentos):
        """Testa cálculo de resumo com sucesso."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        response = client.get('/api/janela-resgate-lotes/resumo?horizon_dias=30')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert data['dados']['total_lotes'] == 2
        assert data['dados']['lotes_criticos'] == 1
        assert data['dados']['lotes_atencao'] == 1


class TestAPISimular:
    """Testa API de simulação."""

    def test_simular_sucesso(self, client, admin_user_id, sample_medicamentos):
        """Testa simulação com sucesso."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        # Buscar o ID do lote LOT001
        with client.application.app_context():
            lote = Medicamento.query.filter_by(lote='LOT001').first()
            lote_id = lote.id

        payload = {
            'lote_id': lote_id,
            'etapas': [
                {'nome': 'Triagem', 'duracao_dias': 2},
                {'nome': 'Aprovação', 'duracao_dias': 1}
            ]
        }

        response = client.post(
            '/api/janela-resgate-lotes/simular',
            json=payload,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert data['dados']['simulado'] is True
        assert data['dados']['total_duracao_dias'] == 3
        assert data['dados']['margem_dias'] == 2  # 5 dias - 3 dias

    def test_simular_lote_nao_encontrado(self, client, admin_user_id):
        """Testa simulação com lote inexistente."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        payload = {
            'lote_id': 99999,
            'etapas': [{'nome': 'Triagem', 'duracao_dias': 2}]
        }

        response = client.post(
            '/api/janela-resgate-lotes/simular',
            json=payload,
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['sucesso'] is False

    def test_simular_sem_etapas(self, client, admin_user_id):
        """Testa simulação sem etapas."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        payload = {
            'lote_id': 1,
            'etapas': []
        }

        response = client.post(
            '/api/janela-resgate-lotes/simular',
            json=payload,
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['sucesso'] is False

    def test_simular_duracao_invalida(self, client, admin_user_id):
        """Testa simulação com duração inválida."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user_id)

        payload = {
            'lote_id': 1,
            'etapas': [{'nome': 'Triagem', 'duracao_dias': 100}]
        }

        response = client.post(
            '/api/janela-resgate-lotes/simular',
            json=payload,
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['sucesso'] is False


class TestService:
    """Testa o serviço de simulação."""

    def test_listar_lotes_horizonte(self, app, sample_medicamentos):
        """Testa listagem de lotes por horizonte."""
        with app.app_context():
            service = LotRescueService()
            lotes = service.listar_lotes_para_resgate(horizon_dias=30)
            assert len(lotes) == 2  # LOT001 e LOT002

    def test_listar_lotes_ordem_cronologica(self, app, sample_medicamentos):
        """Testa ordenação por dias para vencer."""
        with app.app_context():
            service = LotRescueService()
            lotes = service.listar_lotes_para_resgate(horizon_dias=30)
            assert lotes[0]['dias_para_vencer'] <= lotes[1]['dias_para_vencer']

    def test_simular_cenario_compativel(self, app, sample_medicamentos):
        """Testa cenário compatível."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento.query.filter_by(lote='LOT001').first()
            lote_id = lote.id

            resultado = service.simular_cenario_resgate(
                lote_id=lote_id,
                etapas=[{'nome': 'Triagem', 'duracao_dias': 2}]
            )

            assert resultado['margem_dias'] == 3  # 5 - 2
            assert resultado['resultado'] == 'compativel'

    def test_simular_cenario_margem_reduzida(self, app, sample_medicamentos):
        """Testa cenário com margem reduzida."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento.query.filter_by(lote='LOT001').first()
            lote_id = lote.id

            resultado = service.simular_cenario_resgate(
                lote_id=lote_id,
                etapas=[{'nome': 'Triagem', 'duracao_dias': 4}]
            )

            assert resultado['margem_dias'] == 1  # 5 - 4
            assert resultado['resultado'] == 'margem_reduzida'

    def test_simular_cenario_incompativel(self, app, sample_medicamentos):
        """Testa cenário incompatível."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento.query.filter_by(lote='LOT001').first()
            lote_id = lote.id

            resultado = service.simular_cenario_resgate(
                lote_id=lote_id,
                etapas=[{'nome': 'Triagem', 'duracao_dias': 10}]
            )

            assert resultado['margem_dias'] == -5  # 5 - 10
            assert resultado['resultado'] == 'prazo_nao_compativel'

    def test_simular_limitacoes_documentadas(self, app, sample_medicamentos):
        """Testa que limitações são documentadas no resultado."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento.query.filter_by(lote='LOT001').first()
            lote_id = lote.id

            resultado = service.simular_cenario_resgate(
                lote_id=lote_id,
                etapas=[{'nome': 'Triagem', 'duracao_dias': 2}]
            )

            assert len(resultado['limitacoes']) > 0
            assert any('ledger' in lim.lower() for lim in resultado['limitacoes'])

    def test_nao_altera_dados_reais(self, app, sample_medicamentos):
        """Testa que simulação não altera dados reais."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento.query.filter_by(lote='LOT001').first()
            lote_id = lote.id
            quantidade_original = lote.quantidade

            service.simular_cenario_resgate(
                lote_id=lote_id,
                etapas=[{'nome': 'Triagem', 'duracao_dias': 2}]
            )

            # Recarregar do banco
            lote = Medicamento.query.get(lote_id)
            assert lote.quantidade == quantidade_original

    def test_quantidade_cadastrada_nao_disponivel(self, app, sample_medicamentos):
        """Testa que quantidade é rotulada como cadastrada, não disponível."""
        with app.app_context():
            service = LotRescueService()
            lotes = service.listar_lotes_para_resgate(horizon_dias=30)

            for lote in lotes:
                assert 'quantidade_cadastrada' in lote
                assert 'quantidade_disponivel' not in lote
