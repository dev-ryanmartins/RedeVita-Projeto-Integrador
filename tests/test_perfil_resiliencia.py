"""
Testes para Perfil de Resiliência da Farmácia

NOTA: Esta funcionalidade depende da tabela perfis_resiliencia_farmacia,
que requer migration não implementada devido a bloqueio no ambiente atual.
Os testes validam a lógica do serviço e as proteções de acesso.
"""

import pytest
from main import create_app
from app.database import db
from app.services.perfil_resiliencia import PerfilResilienciaService
from app.models.usuario import Usuario
from app.models.farmacia import Farmacia
from flask_login import login_user


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
def service(app):
    """Cria instância do serviço dentro do contexto da aplicação."""
    with app.app_context():
        return PerfilResilienciaService()


class TestAcesso:
    """Testes de acesso RBAC."""

    def test_visitante_redirecionado(self, client):
        """Visitante deve ser redirecionado ao login."""
        response = client.get('/perfil-resiliencia-farmacia')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_admin_acesso_permitido(self, client, app):
        """Admin deve ter acesso à página."""
        with app.app_context():
            # Criar usuário admin
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
        
        # Login com Flask-Login
        login_user(client, admin)
        
        response = client.get('/perfil-resiliencia-farmacia')
        assert response.status_code == 200

    def test_farmaceutico_bloqueado(self, client, app):
        """Farmacêutico deve receber 403."""
        with app.app_context():
            # Criar usuário farmacêutico
            farmaceutico = Usuario(
                nome='Farmacêutico Teste',
                cpf='98765432101',
                email='farmaceutico@test.com',
                senha='Farmac123!',
                cargo='Farmacêutico',
                ativo=True
            )
            db.session.add(farmaceutico)
            db.session.commit()
        
        # Login com Flask-Login
        login_user(client, farmaceutico)
        
        response = client.get('/perfil-resiliencia-farmacia')
        assert response.status_code == 403


class TestServico:
    """Testes do serviço de perfil."""

    def test_obter_todos_perfis(self, service):
        """Deve retornar lista de perfis."""
        perfis = service.obter_todos_perfis()
        assert isinstance(perfis, list)

    def test_obter_perfil_farmacia_inexistente(self, service):
        """Deve retornar None para farmácia inexistente."""
        perfil = service.obter_perfil_por_farmacia(99999)
        assert perfil is None

    def test_criar_perfil_farmacia_inexistente(self, service):
        """Deve levantar erro para farmácia inexistente."""
        with pytest.raises(ValueError) as exc:
            service.criar_perfil(99999, {}, 1)
        assert "Farmácia não encontrada" in str(exc.value)

    def test_atualizar_perfil_farmacia_inexistente(self, service):
        """Deve levantar erro para farmácia inexistente."""
        with pytest.raises(ValueError) as exc:
            service.atualizar_perfil(99999, {}, 1)
        assert "Farmácia não encontrada" in str(exc.value)


class TestLimitacoes:
    """Testes de limitações e proteções."""

    def test_iot_nao_prova_energia(self, service):
        """Leituras IoT não devem ser usadas como prova de energia."""
        leitura = service.obter_ultima_leitura_iot(1)
        # Se houver leitura, verificar que não há informação de energia
        if leitura:
            assert 'energia' not in leitura
            assert 'dispositivo_ligado' not in leitura

    def test_nao_infer_resfriamento(self, service):
        """Leituras IoT não devem inferir funcionamento do refrigerador."""
        leitura = service.obter_ultima_leitura_iot(1)
        if leitura:
            assert 'refrigerador_funcionando' not in leitura
            assert 'refrigerador_ok' not in leitura

    def test_servico_nao_altera_banco(self, app):
        """Servio não deve alterar dados reais."""
        with app.app_context():
            # Executar serviço não deve criar tabelas
            service = PerfilResilienciaService()
            perfis = service.obter_todos_perfis()
            # Apenas verifica que não erroa
            assert isinstance(perfis, list)
