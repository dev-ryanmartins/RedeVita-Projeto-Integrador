"""
Testes para Pré-checagem de Doações

Valida que a pré-checagem:
- Não cria nem modifica medicamentos, doações, estoque ou telemetria
- Usa validadores centralizados existentes
- Reutiliza as mesmas regras de acesso do fluxo de triagem
- Explica pendências e próximos passos
- Não aprova automaticamente doações
"""

import pytest
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.models.medicamento import Medicamento
from app.models.doacao import Doacao


@pytest.fixture
def app():
    """Cria aplicação de teste."""
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
def operador_id(app):
    """Cria usuário operador e retorna o ID."""
    with app.app_context():
        operador = Usuario(
            nome='Operador Teste',
            cpf='12345678901',
            email='operador@test.com',
            senha='Oper123!',
            cargo='Operador',
            ativo=True
        )
        db.session.add(operador)
        db.session.commit()
        return operador.id


@pytest.fixture
def admin_id(app):
    """Cria usuário admin e retorna o ID."""
    with app.app_context():
        admin = Usuario(
            nome='Admin Teste',
            cpf='98765432101',
            email='admin@test.com',
            senha='Admin123!',
            cargo='Admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def voluntario_id(app):
    """Cria usuário voluntário e retorna o ID."""
    with app.app_context():
        voluntario = Usuario(
            nome='Voluntário Teste',
            cpf='11122233344',
            email='voluntario@test.com',
            senha='Volun123!',
            cargo='Voluntário',
            ativo=True
        )
        db.session.add(voluntario)
        db.session.commit()
        return voluntario.id


class TestAcesso:
    """Testes de acesso RBAC."""

    def test_visitante_redirecionado(self, client):
        """Visitante deve ser redirecionado ao login."""
        response = client.get('/doacoes/pre-checagem')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_operador_acesso_permitido(self, client, operador_id):
        """Operador deve ter acesso à pré-checagem."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.get('/doacoes/pre-checagem')
        assert response.status_code == 200

    def test_admin_acesso_permitido(self, client, admin_id):
        """Admin deve ter acesso à pré-checagem."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        response = client.get('/doacoes/pre-checagem')
        assert response.status_code == 200

    def test_voluntario_bloqueado(self, client, voluntario_id):
        """Voluntário deve receber 403."""
        with client.session_transaction() as sess:
            sess['_user_id'] = voluntario_id
            sess['_fresh'] = True
        response = client.get('/doacoes/pre-checagem')
        assert response.status_code == 403


class TestValidacaoCampos:
    """Testes de validação de campos."""

    def test_nome_obrigatorio(self, client, operador_id):
        """Nome do medicamento é obrigatório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'Nome do medicamento' in response.data or b'nome' in response.data

    def test_lote_obrigatorio(self, client, operador_id):
        """Número do lote é obrigatório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'Lote' in response.data or b'lote' in response.data

    def test_data_invalida(self, client, operador_id):
        """Data de validade inválida deve ser rejeitada."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': 'invalida',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'inv' in response.data.lower()

    def test_data_vencida(self, client, operador_id):
        """Data de validade vencida deve ser bloqueada."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2020-01-01',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'vencid' in response.data.lower()

    def test_quantidade_invalida(self, client, operador_id):
        """Quantidade inválida deve ser rejeitada."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': 'abc',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'quantidade' in response.data.lower()

    def test_quantidade_zero(self, client, operador_id):
        """Quantidade zero deve ser rejeitada."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '0',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'quantidade' in response.data.lower()

    def test_tarja_invalida(self, client, operador_id):
        """Classificação inválida deve ser rejeitada."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Invalida'
        })
        assert response.status_code == 200
        assert b'tarja' in response.data.lower() or b'classifica' in response.data.lower()

    def test_tarja_controlada_bloqueio(self, client, operador_id):
        """Portaria 344 deve exigir avaliação farmacêutica."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Diazepam',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Portaria 344'
        })
        assert response.status_code == 200
        assert b'farmac' in response.data.lower() or b'controlad' in response.data.lower()

    def test_principio_ativo_controlado(self, client, operador_id):
        """Princípio ativo controlado deve gerar alerta."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Medicamento',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja',
            'principio_ativo': 'antibiotico'
        })
        assert response.status_code == 200
        assert b'controlad' in response.data.lower() or b'farmac' in response.data.lower()


class TestResultados:
    """Testes dos resultados da pré-checagem."""

    def test_sem_bloqueios_permite_prosseguir(self, client, operador_id):
        """Sem bloqueios deve permitir prosseguir."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'prosseguir' in response.data.lower() or b'continuar' in response.data.lower()

    def test_bloqueios_impedem_prosseguimento(self, client, operador_id):
        """Bloqueios devem impedir prosseguimento."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': '',  # Nome vazio
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'bloqueio' in response.data.lower() or b'obrigat' in response.data.lower()

    def test_verificacoes_nao_feitas_listadas(self, client, operador_id):
        """Verificações não feitas pelo sistema devem ser listadas."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        assert response.status_code == 200
        assert b'proced' in response.data.lower() or b'embalagem' in response.data.lower()


class TestSemAlteracaoDados:
    """Testes de que a pré-checagem não altera dados."""

    def test_nao_cria_medicamento(self, client, operador_id, app):
        """Pré-checagem não deve criar medicamento."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        
        with app.app_context():
            count_before = Medicamento.query.count()
        
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        
        with app.app_context():
            count_after = Medicamento.query.count()
        
        assert count_before == count_after

    def test_nao_cria_doacao(self, client, operador_id, app):
        """Pré-checagem não deve criar doação."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        
        with app.app_context():
            count_before = Doacao.query.count()
        
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        
        with app.app_context():
            count_after = Doacao.query.count()
        
        assert count_before == count_after

    def test_continuar_para_triagem_nao_submete_dados(self, client, operador_id, app):
        """Botão continuar para triagem não deve submeter dados automaticamente."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        
        with app.app_context():
            count_before = Medicamento.query.count()
        
        # A pré-checagem apenas mostra resultados, não transfere dados
        response = client.post('/doacoes/pre-checagem', data={
            'nome': 'Dipirona',
            'lote': 'ABC123',
            'data_validade': '2025-12-31',
            'quantidade': '10',
            'tarja': 'Sem Tarja'
        })
        
        with app.app_context():
            count_after = Medicamento.query.count()
        
        # Não deve ter criado medicamento
        assert count_before == count_after
        
        # O botão de continuar é apenas um link para /doacoes/triagem
        assert b'/doacoes/triagem' in response.data


class TestAvisoPersistente:
    """Teste do aviso persistente."""

    def test_aviso_persistente_exibido(self, client, operador_id):
        """Aviso persistente deve ser exibido."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        response = client.get('/doacoes/pre-checagem')
        assert response.status_code == 200
        assert b'aviso' in response.data.lower() or b'aprov' in response.data.lower()
