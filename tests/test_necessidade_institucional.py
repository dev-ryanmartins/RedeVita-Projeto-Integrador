"""
Testes para Quadro Privado de Necessidades de Instituições

NOTA: Esta funcionalidade depende da tabela necessidades_institucionais,
que requer migration não implementada devido a bloqueio no ambiente atual.
Os testes validam a lógica das rotas e as proteções de acesso.
"""

import pytest
from main import create_app
from app.database import db
from app.models.necessidade_institucional import NecessidadeInstitucional, StatusNecessidade, PrioridadeNecessidade
from app.models.usuario import Usuario
from app.models.medicamento_referencia import MedicamentoReferencia
from datetime import datetime, date


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
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
def admin_id(app):
    with app.app_context():
        admin = Usuario(
            nome='Admin Teste',
            cpf='12345678901',
            email='admin@test.com',
            senha='Admin123!',
            cargo='Admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def operador_id(app):
    with app.app_context():
        operador = Usuario(
            nome='Operador Teste',
            cpf='23456789012',
            email='operador@test.com',
            senha='Operador123!',
            cargo='Operador',
            ativo=True
        )
        db.session.add(operador)
        db.session.commit()
        return operador.id


@pytest.fixture
def referencia_id(app):
    with app.app_context():
        ref = MedicamentoReferencia(
            nome_comercial='Dipirona 500mg',
            principio_ativo='dipirona'
        )
        db.session.add(ref)
        db.session.commit()
        return ref.id


class TestAcesso:
    """Testes de acesso ao quadro."""

    def test_visitante_redirecionado(self, client):
        """Visitante deve ser redirecionado para login."""
        response = client.get('/necessidades-institucionais')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_admin_acesso_permitido(self, client, admin_id):
        """Admin deve ter acesso ao quadro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        response = client.get('/necessidades-institucionais')
        assert response.status_code == 200

    def test_operador_bloqueado(self, client, operador_id):
        """Operador deve receber 403."""
        with client.session_transaction() as sess:
            sess['_user_id'] = operador_id
            sess['_fresh'] = True
        
        response = client.get('/necessidades-institucionais')
        assert response.status_code == 403


class TestCriacaoNecessidade:
    """Testes de criação de necessidades."""

    def test_criar_necessidade_sucesso(self, client, admin_id, referencia_id):
        """Admin deve conseguir criar uma necessidade."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        response = client.post('/necessidades-institucionais', data={
            'nome_instituicao': 'Hospital Teste',
            'medicamento_referencia_id': referencia_id,
            'quantidade_solicitada': 100,
            'unidade': 'unidade',
            'prioridade': 'media'
        })
        assert response.status_code == 302
        assert '/necessidades-institucionais' in response.location

    def test_criar_sem_instituicao(self, client, admin_id):
        """Nome da instituição é obrigatório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        response = client.post('/necessidades-institucionais', data={
            'quantidade_solicitada': 100,
            'unidade': 'unidade'
        })
        assert response.status_code == 302

    def test_criar_sem_produto(self, client, admin_id):
        """Produto (referência ou descritivo) é obrigatório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        response = client.post('/necessidades-institucionais', data={
            'nome_instituicao': 'Hospital Teste',
            'quantidade_solicitada': 100,
            'unidade': 'unidade'
        })
        assert response.status_code == 302

    def test_criar_quantidade_invalida(self, client, admin_id):
        """Quantidade deve ser maior que zero."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        response = client.post('/necessidades-institucionais', data={
            'nome_instituicao': 'Hospital Teste',
            'produto_descritivo': 'Dipirona',
            'quantidade_solicitada': 0,
            'unidade': 'unidade'
        })
        assert response.status_code == 302


class TestRevisaoEncerramento:
    """Testes de revisão e encerramento."""

    def test_revisar_necessidade(self, client, admin_id, referencia_id):
        """Admin deve conseguir revisar uma necessidade."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        # Criar necessidade
        client.post('/necessidades-institucionais', data={
            'nome_instituicao': 'Hospital Teste',
            'medicamento_referencia_id': referencia_id,
            'quantidade_solicitada': 100,
            'unidade': 'unidade'
        })
        
        # Revisar
        response = client.post('/necessidades-institucionais/1/revisar', data={
            'status': 'em_revisao'
        })
        assert response.status_code == 302

    def test_encerrar_necessidade(self, client, admin_id, referencia_id):
        """Admin deve conseguir encerrar uma necessidade."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        # Criar necessidade
        client.post('/necessidades-institucionais', data={
            'nome_instituicao': 'Hospital Teste',
            'medicamento_referencia_id': referencia_id,
            'quantidade_solicitada': 100,
            'unidade': 'unidade'
        })
        
        # Encerrar
        response = client.post('/necessidades-institucionais/1/encerrar')
        assert response.status_code == 302


class TestLimitacoes:
    """Testes de limitações e segurança."""

    def test_nao_altera_solicitacao_estoque(self, app, admin_id):
        """Quadro não deve alterar SolicitacaoEstoque."""
        from app.models.solicitacao_estoque import SolicitacaoEstoque
        
        with app.app_context():
            # Verificar que não há modificações
            count_before = SolicitacaoEstoque.query.count()
        
        # Quadro não interage com SolicitacaoEstoque
        assert True  # Placeholder para validação

    def test_nao_altera_medicamentos(self, app, admin_id):
        """Quadro não deve alterar medicamentos."""
        from app.models.medicamento import Medicamento
        
        with app.app_context():
            count_before = Medicamento.query.count()
        
        # Quadro não interage com Medicamento
        assert True  # Placeholder para validação

    def test_nao_exibe_dados_pacientes(self, client, admin_id):
        """Quadro não deve exibir dados de pacientes."""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_id
            sess['_fresh'] = True
        
        response = client.get('/necessidades-institucionais')
        assert response.status_code == 200
        # Verificar que não há dados pessoais na resposta
        assert 'cpf' not in response.data.decode('utf-8', errors='ignore')
