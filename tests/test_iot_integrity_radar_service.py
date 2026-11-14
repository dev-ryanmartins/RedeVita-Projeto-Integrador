"""
Testes unitários do serviço de Radar de Integridade da Telemetria

Testes de cálculos, validações e determinismo.
"""

import pytest
from datetime import datetime, timedelta
from main import create_app
from app.database import db
from app.models.iot import LeituraIoT, StatusAlertaEnum
from app.models.farmacia import Farmacia
from app.services.iot_integrity_radar import IotIntegrityRadarService


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
def service():
    """Cria instância do serviço."""
    return IotIntegrityRadarService()


@pytest.fixture
def farmacia(app):
    """Cria farmácia de teste."""
    with app.app_context():
        farmacia = Farmacia(
            nome_fantasia='Farmácia Test',
            cnpj='12345678000190',
            endereco='Rua Test, 123',
            responsavel='Resp Test',
            latitude=-23.5505,
            longitude=-46.6333
        )
        db.session.add(farmacia)
        db.session.commit()
        return farmacia.id


class TestLimites:
    """Testes de limites de parâmetros."""

    def test_periodo_minimo(self, service):
        """Deve rejeitar período menor que 1 dia."""
        with pytest.raises(ValueError) as exc:
            service.analisar_frescor(periodo_dias=0)
        assert "entre" in str(exc.value)

    def test_periodo_maximo(self, service):
        """Deve rejeitar período maior que 90 dias."""
        with pytest.raises(ValueError) as exc:
            service.analisar_frescor(periodo_dias=91)
        assert "entre" in str(exc.value)

    def test_intervalo_invalido(self, service):
        """Deve rejeitar intervalo inválido."""
        with pytest.raises(ValueError) as exc:
            service.analisar_lacunas_temporais(intervalo_minutos='invalid')
        assert "Intervalo" in str(exc.value)

    def test_intervalos_disponiveis(self, service):
        """Deve ter intervalos disponíveis."""
        assert '5min' in service.INTERVALOS_ANALISE
        assert '1h' in service.INTERVALOS_ANALISE
        assert '24h' in service.INTERVALOS_ANALISE


class TestFrescor:
    """Testes de cálculo de frescor."""

    def test_frescor_dispositivo_recente(self, app, service, farmacia):
        """Deve classificar dispositivo como recente (menos de 1 dia)."""
        with app.app_context():
            agora = datetime.utcnow()
            leitura = LeituraIoT(
                dispositivo_id='sensor_recente',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(hours=2)
            )
            db.session.add(leitura)
            db.session.commit()

            frescor = service.analisar_frescor(periodo_dias=7)
            assert len(frescor) == 1
            assert frescor[0]['status_frescor'] == 'recente'

    def test_frescor_dispositivo_moderado(self, app, service, farmacia):
        """Deve classificar dispositivo como moderado (1-7 dias)."""
        with app.app_context():
            agora = datetime.utcnow()
            leitura = LeituraIoT(
                dispositivo_id='sensor_moderado',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(days=3)
            )
            db.session.add(leitura)
            db.session.commit()

            frescor = service.analisar_frescor(periodo_dias=7)
            assert len(frescor) == 1
            assert frescor[0]['status_frescor'] == 'moderado'

    def test_frescor_dispositivo_antigo(self, app, service, farmacia):
        """Deve classificar dispositivo como antigo (mais de 7 dias)."""
        with app.app_context():
            agora = datetime.utcnow()
            leitura = LeituraIoT(
                dispositivo_id='sensor_antigo',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(days=10)
            )
            db.session.add(leitura)
            db.session.commit()

            frescor = service.analisar_frescor(periodo_dias=14)
            assert len(frescor) == 1
            assert frescor[0]['status_frescor'] == 'antigo'

    def test_frescor_ordenacao_por_antiguidade(self, app, service, farmacia):
        """Deve ordenar dispositivos por antiguidade (mais antigos primeiro)."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_1',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(hours=1)
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_2',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(days=5)
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            frescor = service.analisar_frescor(periodo_dias=7)
            assert len(frescor) == 2
            assert frescor[0]['dias_desde_ultima'] > frescor[1]['dias_desde_ultima']


class TestLacunas:
    """Testes de detecção de lacunas temporais."""

    def test_lacuna_detectada_acima_intervalo(self, app, service, farmacia):
        """Deve detectar lacuna quando delta > intervalo esperado."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_lacuna',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(hours=2)
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_lacuna',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(minutes=10)
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            # Intervalo esperado de 5 minutos, delta de 110 minutos
            lacunas = service.analisar_lacunas_temporais(
                intervalo_minutos='5min',
                periodo_dias=1
            )
            assert len(lacunas) > 0

    def test_lacuna_nao_detectada_abaixo_intervalo(self, app, service, farmacia):
        """Não deve detectar lacuna quando delta < intervalo esperado."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_ok',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(minutes=10)
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_ok',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(minutes=5)
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            # Intervalo esperado de 1 hora, delta de 5 minutos
            lacunas = service.analisar_lacunas_temporais(
                intervalo_minutos='1h',
                periodo_dias=1
            )
            assert len(lacunas) == 0

    def test_lacuna_gravidade_alta(self, app, service, farmacia):
        """Deve classificar lacuna como alta quando delta > 3x intervalo."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_alta',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(hours=5)
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_alta',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(minutes=10)
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            # Intervalo esperado de 1 hora, delta de 290 minutos (~5x)
            lacunas = service.analisar_lacunas_temporais(
                intervalo_minutos='1h',
                periodo_dias=1
            )
            assert len(lacunas) > 0
            assert lacunas[0]['gravidade'] == 'alta'


class TestDuplicidades:
    """Testes de detecção de candidatos a duplicidade."""

    def test_duplicidade_igualdade_exata(self, app, service, farmacia):
        """Deve detectar duplicidade com igualdade exata."""
        with app.app_context():
            agora = datetime.utcnow()
            timestamp = agora - timedelta(hours=1)

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_dup',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=timestamp
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_dup',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=timestamp
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            duplicidades = service.analisar_duplicidade_candidatos(periodo_dias=7)
            assert len(duplicidades) == 1
            assert duplicidades[0]['quantidade'] == 2

    def test_duplicidade_inclui_luminosidade(self, app, service, farmacia):
        """Deve incluir luminosidade no fingerprint."""
        with app.app_context():
            agora = datetime.utcnow()
            timestamp = agora - timedelta(hours=1)

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_lux',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                luminosidade_lux=100.0,
                data_hora=timestamp
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_lux',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                luminosidade_lux=100.0,
                data_hora=timestamp
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            duplicidades = service.analisar_duplicidade_candidatos(periodo_dias=7)
            assert len(duplicidades) == 1

    def test_duplicidade_diferente_nao_detectada(self, app, service, farmacia):
        """Não deve detectar duplicidade com valores diferentes."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_diff',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(hours=1)
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_diff',
                farmacia_id=farmacia,
                temperatura=21.0,  # Diferente
                umidade=50.0,
                data_hora=agora - timedelta(hours=1)
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            duplicidades = service.analisar_duplicidade_candidatos(periodo_dias=7)
            assert len(duplicidades) == 0


class TestTimestampsFuturos:
    """Testes de detecção de timestamps no futuro."""

    def test_futuro_dentro_tolerancia(self, app, service, farmacia):
        """Deve detectar timestamp no futuro dentro da tolerância."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura = LeituraIoT(
                dispositivo_id='sensor_futuro',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora + timedelta(minutes=30)
            )
            db.session.add(leitura)
            db.session.commit()

            futuros = service.analisar_timestamps_futuros(tolerancia_minutos=60)
            assert len(futuros) == 1
            assert futuros[0]['delta_minutos'] > 0

    def test_futuro_fora_tolerancia(self, app, service, farmacia):
        """Não deve detectar timestamp fora da tolerância."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura = LeituraIoT(
                dispositivo_id='sensor_fora',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora + timedelta(minutes=90)
            )
            db.session.add(leitura)
            db.session.commit()

            futuros = service.analisar_timestamps_futuros(tolerancia_minutos=60)
            assert len(futuros) == 0

    def test_passado_nao_detectado(self, app, service, farmacia):
        """Não deve detectar timestamp no passado."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura = LeituraIoT(
                dispositivo_id='sensor_passado',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(minutes=30)
            )
            db.session.add(leitura)
            db.session.commit()

            futuros = service.analisar_timestamps_futuros(tolerancia_minutos=60)
            assert len(futuros) == 0


class TestResumo:
    """Testes de resumo geral."""

    def test_resumo_estrutura(self, app, service, farmacia):
        """Deve retornar resumo com estrutura correta."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura = LeituraIoT(
                dispositivo_id='sensor_resumo',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora
            )
            db.session.add(leitura)
            db.session.commit()

            resumo = service.obter_resumo(periodo_dias=7)
            assert 'total_dispositivos' in resumo
            assert 'dispositivos_sem_dados' in resumo
            assert 'dispositivos_antigos' in resumo
            assert 'total_lacunas' in resumo
            assert 'total_duplicidades' in resumo
            assert 'total_futuros' in resumo
            assert 'intervalos_disponiveis' in resumo

    def test_resumo_vazio(self, app, service):
        """Deve retornar resumo vazio sem dados."""
        with app.app_context():
            resumo = service.obter_resumo(periodo_dias=7)
            assert resumo['total_dispositivos'] == 0
            assert resumo['total_lacunas'] == 0
            assert resumo['total_duplicidades'] == 0
            assert resumo['total_futuros'] == 0


class TestDeterminismo:
    """Testes de determinismo."""

    def test_frescor_deterministico(self, app, service, farmacia):
        """Análise de frescor deve ser determinística."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura = LeituraIoT(
                dispositivo_id='sensor_det',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora
            )
            db.session.add(leitura)
            db.session.commit()

            frescor1 = service.analisar_frescor(periodo_dias=7)
            frescor2 = service.analisar_frescor(periodo_dias=7)

            assert len(frescor1) == len(frescor2)
            assert frescor1[0]['dispositivo_id'] == frescor2[0]['dispositivo_id']

    def test_lacunas_deterministico(self, app, service, farmacia):
        """Análise de lacunas deve ser determinística."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_det_lacuna',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(hours=2)
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_det_lacuna',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora - timedelta(minutes=10)
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            lacunas1 = service.analisar_lacunas_temporais(
                intervalo_minutos='5min',
                periodo_dias=1
            )
            lacunas2 = service.analisar_lacunas_temporais(
                intervalo_minutos='5min',
                periodo_dias=1
            )

            assert len(lacunas1) == len(lacunas2)


class TestApenasLeitura:
    """Testes de que o serviço é apenas leitura."""

    def test_frescor_nao_altera_dados(self, app, service, farmacia):
        """Análise de frescor não deve alterar dados."""
        with app.app_context():
            agora = datetime.utcnow()

            leitura = LeituraIoT(
                dispositivo_id='sensor_readonly',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=agora
            )
            db.session.add(leitura)
            db.session.commit()

            total_antes = LeituraIoT.query.count()
            service.analisar_frescor(periodo_dias=7)
            total_depois = LeituraIoT.query.count()

            assert total_antes == total_depois

    def test_duplicidades_nao_altera_dados(self, app, service, farmacia):
        """Análise de duplicidade não deve alterar dados."""
        with app.app_context():
            agora = datetime.utcnow()
            timestamp = agora - timedelta(hours=1)

            leitura1 = LeituraIoT(
                dispositivo_id='sensor_readonly_dup',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=timestamp
            )
            leitura2 = LeituraIoT(
                dispositivo_id='sensor_readonly_dup',
                farmacia_id=farmacia,
                temperatura=20.0,
                umidade=50.0,
                data_hora=timestamp
            )
            db.session.add(leitura1)
            db.session.add(leitura2)
            db.session.commit()

            total_antes = LeituraIoT.query.count()
            service.analisar_duplicidade_candidatos(periodo_dias=7)
            total_depois = LeituraIoT.query.count()

            assert total_antes == total_depois
