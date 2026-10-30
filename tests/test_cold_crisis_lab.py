"""
Testes para o Laboratório de Crises da Cadeia Frio.

Testa:
- Acesso por perfil (Admin e Farmacêutico)
- Bloqueio de perfis não autorizados
- Cenários de simulação
- Reprodutibilidade com seed
- Validação de parâmetros
- Ausência de alterações em dados reais
"""

import pytest
from app import create_app
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


@pytest.fixture
def admin_user(app):
    """Cria usuário Admin para testes."""
    with app.app_context():
        admin = Usuario(
            nome='Admin Teste',
            cpf='12345678900',
            email='admin@teste.com',
            senha=criptografar_senha('Senha123!'),
            cargo='Admin',
            ativo=True,
            senha_trocada=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def farmaceutico_user(app):
    """Cria usuário Farmacêutico para testes."""
    with app.app_context():
        farmaceutico = Usuario(
            nome='Farmacêutico Teste',
            cpf='98765432100',
            email='farmaceutico@teste.com',
            senha=criptografar_senha('Senha123!'),
            cargo='Farmacêutico',
            ativo=True,
            senha_trocada=True
        )
        db.session.add(farmaceutico)
        db.session.commit()
        return farmaceutico


@pytest.fixture
def medico_user(app):
    """Cria usuário Médico para testes (não autorizado)."""
    with app.app_context():
        medico = Usuario(
            nome='Médico Teste',
            cpf='45678912300',
            email='medico@teste.com',
            senha=criptografar_senha('Senha123!'),
            cargo='Médico',
            ativo=True,
            senha_trocada=True
        )
        db.session.add(medico)
        db.session.commit()
        return medico


class TestAcessoLaboratorio:
    """Testa controle de acesso ao Laboratório de Crises."""

    def test_admin_acesso_página(self, client, admin_user):
        """Admin deve conseguir acessar a página do Laboratório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.get('/laboratorio-crise-cadeia-frio')
        assert response.status_code == 200
        assert 'Laboratório de Crises' in response.data.decode('utf-8')

    def test_farmaceutico_acesso_página(self, client, farmaceutico_user):
        """Farmacêutico deve conseguir acessar a página do Laboratório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(farmaceutico_user.id)
            sess['_fresh'] = True

        response = client.get('/laboratorio-crise-cadeia-frio')
        assert response.status_code == 200
        assert 'Laboratório de Crises' in response.data.decode('utf-8')

    def test_medico_sem_acesso_403(self, client, medico_user):
        """Médico não deve ter acesso e receber 403."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(medico_user.id)
            sess['_fresh'] = True

        response = client.get('/laboratorio-crise-cadeia-frio')
        assert response.status_code == 403

    def test_visitante_redirecionado_login(self, client):
        """Visitante não autenticado deve ser redirecionado ao login."""
        response = client.get('/laboratorio-crise-cadeia-frio')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_admin_acesso_api_cenarios(self, client, admin_user):
        """Admin deve conseguir acessar API de cenários."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.get('/api/laboratorio-crise-cadeia-frio/cenarios')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert 'cenarios' in data['dados']

    def test_farmaceutico_acesso_api_cenarios(self, client, farmaceutico_user):
        """Farmacêutico deve conseguir acessar API de cenários."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(farmaceutico_user.id)
            sess['_fresh'] = True

        response = client.get('/api/laboratorio-crise-cadeia-frio/cenarios')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True

    def test_medico_sem_acesso_api_cenarios_403(self, client, medico_user):
        """Médico não deve ter acesso à API e receber 403."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(medico_user.id)
            sess['_fresh'] = True

        response = client.get('/api/laboratorio-crise-cadeia-frio/cenarios')
        assert response.status_code == 403


class TestCenariosSimulacao:
    """Testa cenários de simulação."""

    def test_cenario_falha_energia(self, client, admin_user):
        """Cenário de falha de energia deve gerar dados corretos."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert data['dados']['cenario'] == 'falha_energia'
        assert data['dados']['simulado'] is True
        assert len(data['dados']['leituras']) > 0
        assert len(data['dados']['eventos']) > 0

    def test_cenario_falha_rede(self, client, admin_user):
        """Cenário de falha de rede deve gerar dados corretos."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_rede',
                                  'duracao_horas': 4,
                                  'intervalo_minutos': 10
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert data['dados']['cenario'] == 'falha_rede'
        assert data['dados']['leituras_pendentes'] > 0

    def test_cenario_falha_sensor(self, client, admin_user):
        """Cenário de falha de sensor deve gerar dados corretos."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_sensor',
                                  'duracao_horas': 5,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert data['dados']['cenario'] == 'falha_sensor'
        assert 'lacunas' in data['dados']

    def test_cenario_recuperacao(self, client, admin_user):
        """Cenário de recuperação deve gerar dados corretos."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'recuperacao',
                                  'duracao_horas': 8,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sucesso'] is True
        assert data['dados']['cenario'] == 'recuperacao'

    def test_cenario_invalido_erro(self, client, admin_user):
        """Cenário inválido deve retornar erro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'cenario_inexistente',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 400
        data = response.get_json()
        assert data['sucesso'] is False


class TestValidacaoParametros:
    """Testa validação de parâmetros da simulação."""

    def test_duracao_abaixo_minimo_erro(self, client, admin_user):
        """Duração abaixo do mínimo deve retornar erro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 0,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 400

    def test_duracao_acima_maximo_erro(self, client, admin_user):
        """Duração acima do máximo deve retornar erro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 25,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 400

    def test_intervalo_abaixo_minimo_erro(self, client, admin_user):
        """Intervalo abaixo do mínimo deve retornar erro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 0
                              },
                              content_type='application/json')
        assert response.status_code == 400

    def test_intervalo_acima_maximo_erro(self, client, admin_user):
        """Intervalo acima do máximo deve retornar erro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 61
                              },
                              content_type='application/json')
        assert response.status_code == 400

    def test_cenario_obrigatorio(self, client, admin_user):
        """Parâmetro cenario é obrigatório."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 400

    def test_seed_invalido_erro(self, client, admin_user):
        """Seed inválido deve retornar erro."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 15,
                                  'seed': 'invalido'
                              },
                              content_type='application/json')
        assert response.status_code == 400


class TestReprodutibilidade:
    """Testa reprodutibilidade da simulação com seed."""

    def test_mesma_seed_mesmo_resultado(self, client, admin_user):
        """Mesma seed deve produzir o mesmo resultado."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        seed = 12345

        # Primeira execução
        response1 = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                               json={
                                   'cenario': 'falha_energia',
                                   'duracao_horas': 6,
                                   'intervalo_minutos': 15,
                                   'seed': seed
                               },
                               content_type='application/json')
        data1 = response1.get_json()

        # Segunda execução com mesma seed
        response2 = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                               json={
                                   'cenario': 'falha_energia',
                                   'duracao_horas': 6,
                                   'intervalo_minutos': 15,
                                   'seed': seed
                               },
                               content_type='application/json')
        data2 = response2.get_json()

        # Mesmas temperaturas (determinístico)
        leituras1 = data1['dados']['leituras']
        leituras2 = data2['dados']['leituras']

        assert len(leituras1) == len(leituras2)
        for i in range(len(leituras1)):
            assert leituras1[i]['temperatura'] == leituras2[i]['temperatura']


class TestSemAlteracaoDadosReais:
    """Testa que simulação não altera dados reais."""

    def test_simulacao_nao_cria_leituras_iot(self, client, admin_user):
        """Simulação não deve criar registros em LeituraIoT."""
        from app.models.iot import LeituraIoT

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        # Contar leituras antes
        with client.application.app_context():
            leituras_antes = LeituraIoT.query.count()

        # Executar simulação
        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 200

        # Contar leituras depois
        with client.application.app_context():
            leituras_depois = LeituraIoT.query.count()

        # Não deve haver alteração
        assert leituras_antes == leituras_depois

    def test_simulacao_nao_altera_estoque(self, client, admin_user):
        """Simulação não deve alterar estoque."""
        from app.models.medicamento import Medicamento

        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        # Contar medicamentos antes
        with client.application.app_context():
            medicamentos_antes = Medicamento.query.count()

        # Executar simulação
        response = client.post('/api/laboratorio-crise-cadeia-frio/simular',
                              json={
                                  'cenario': 'falha_energia',
                                  'duracao_horas': 6,
                                  'intervalo_minutos': 15
                              },
                              content_type='application/json')
        assert response.status_code == 200

        # Contar medicamentos depois
        with client.application.app_context():
            medicamentos_depois = Medicamento.query.count()

        # Não deve haver alteração
        assert medicamentos_antes == medicamentos_depois
