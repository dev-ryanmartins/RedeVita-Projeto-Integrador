"""
Testes para o Laboratório de Crises da Cadeia Frio.

Testa:
- Visitante redirecionado ao login
- Cenários de simulação (via serviço direto)
- Reprodutibilidade com seed
- Validação de parâmetros
- Ausência de alterações em dados reais
"""

import pytest
from main import create_app
from app.database import db
from app.models.usuario import Usuario
from app.core.security import criptografar_senha


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


@pytest.fixture
def client(app):
    """Cria cliente de teste."""
    return app.test_client()


class TestAcessoLaboratorio:
    """Testa controle de acesso ao Laboratório de Crises."""

    def test_visitante_redirecionado_login(self, client):
        """Visitante não autenticado deve ser redirecionado ao login."""
        response = client.get('/laboratorio-crise-cadeia-frio')
        assert response.status_code == 302
        assert '/login' in response.location


class TestCenariosSimulacao:
    """Testa cenários de simulação via serviço direto."""

    def test_cenario_falha_energia(self):
        """Cenário de falha de energia deve gerar dados corretos."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        assert resultado['cenario'] == 'falha_energia'
        assert resultado['simulado'] is True
        assert len(resultado['leituras']) > 0
        assert len(resultado['eventos']) > 0

    def test_cenario_falha_rede(self):
        """Cenário de falha de rede deve gerar dados corretos."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_rede(duracao_horas=4, intervalo_minutos=10)

        assert resultado['cenario'] == 'falha_rede'
        assert resultado['leituras_pendentes'] > 0

    def test_cenario_falha_sensor(self):
        """Cenário de falha de sensor deve gerar dados corretos."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_sensor(duracao_horas=5, intervalo_minutos=15)

        assert resultado['cenario'] == 'falha_sensor'
        assert 'lacunas' in resultado

    def test_cenario_recuperacao(self):
        """Cenário de recuperação deve gerar dados corretos."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_recuperacao(duracao_horas=8, intervalo_minutos=15)

        assert resultado['cenario'] == 'recuperacao'

    def test_cenario_invalido_erro(self):
        """Cenário inválido deve levantar ValueError."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator(seed=12345)

        with pytest.raises(ValueError):
            simulador.obter_cenario(tipo='cenario_invalido')


class TestValidacaoParametros:
    """Testa validação de parâmetros da simulação."""

    def test_obter_cenario_com_seed(self):
        """Seed deve ser aceita quando fornecida."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.obter_cenario(
            tipo='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15
        )
        assert resultado['simulado'] is True

    def test_obter_cenario_sem_seed(self):
        """Seed opcional deve funcionar quando não fornecida."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        simulador = ColdCrisisSimulator()
        resultado = simulador.obter_cenario(
            tipo='falha_energia',
            duracao_horas=6,
            intervalo_minutos=15
        )
        assert resultado['simulado'] is True


class TestReprodutibilidade:
    """Testa reprodutibilidade da simulação com seed."""

    def test_mesma_seed_mesmo_resultado(self):
        """Mesma seed deve produzir o mesmo resultado."""
        from app.services.cold_crisis_simulator import ColdCrisisSimulator
        seed = 12345

        simulador1 = ColdCrisisSimulator(seed=seed)
        resultado1 = simulador1.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        simulador2 = ColdCrisisSimulator(seed=seed)
        resultado2 = simulador2.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        # Mesmas temperaturas (determinístico)
        leituras1 = resultado1['leituras']
        leituras2 = resultado2['leituras']

        assert len(leituras1) == len(leituras2)
        for i in range(len(leituras1)):
            assert leituras1[i]['temperatura'] == leituras2[i]['temperatura']


class TestSemAlteracaoDadosReais:
    """Testa que simulação não altera dados reais."""

    def test_simulacao_nao_altera_leituras_iot(self, app):
        """Simulação não deve criar registros em LeituraIoT."""
        from app.models.iot import LeituraIoT
        from app.services.cold_crisis_simulator import ColdCrisisSimulator

        with app.app_context():
            leituras_antes = LeituraIoT.query.count()

        simulador = ColdCrisisSimulator(seed=12345)
        resultado = simulador.gerar_cenario_falha_energia(duracao_horas=6, intervalo_minutos=15)

        with app.app_context():
            leituras_depois = LeituraIoT.query.count()

        # Não deve haver alteração
        assert leituras_antes == leituras_depois
