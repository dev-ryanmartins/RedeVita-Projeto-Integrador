"""
Testes unitários do serviço LotRescueService.

Testa:
- Limites de parâmetros
- Cálculos de margem
- Determinismo
- Validations
"""

import pytest
from datetime import date, timedelta
from backend.main import create_app
from app.database import db
from app.models.medicamento import Medicamento
from app.services.lot_rescue_service import LotRescueService


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
def service(app):
    """Cria instância do serviço."""
    with app.app_context():
        return LotRescueService()


@pytest.fixture
def sample_lote(app):
    """Cria lote de exemplo."""
    with app.app_context():
        lote = Medicamento(
            nome='Medicamento Teste',
            lote='LOT001',
            data_validade=date.today() + timedelta(days=30),
            quantidade=100,
            ativo=True,
            status_semaforo=0,
            tarja='Branca',
            principio_ativo='Principio Ativo'
        )
        db.session.add(lote)
        db.session.commit()
        return lote


class TestLimitesParametros:
    """Testa limites de parâmetros."""

    def test_horizonte_minimo(self, service):
        """Testa horizonte mínimo."""
        with pytest.raises(ValueError, match="Horizonte deve ser entre"):
            service.listar_lotes_para_resgate(horizon_dias=0)

    def test_horizonte_maximo(self, service):
        """Testa horizonte máximo."""
        with pytest.raises(ValueError, match="Horizonte deve ser entre"):
            service.listar_lotes_para_resgate(horizon_dias=366)

    def test_etapa_duracao_minima(self, service, sample_lote):
        """Testa duração mínima de etapa."""
        with pytest.raises(ValueError, match="Duração da etapa deve ser entre"):
            service.simular_cenario_resgate(
                lote_id=sample_lote.id,
                etapas=[{'nome': 'Teste', 'duracao_dias': 0}]
            )

    def test_etapa_duracao_maxima(self, service, sample_lote):
        """Testa duração máxima de etapa."""
        with pytest.raises(ValueError, match="Duração da etapa deve ser entre"):
            service.simular_cenario_resgate(
                lote_id=sample_lote.id,
                etapas=[{'nome': 'Teste', 'duracao_dias': 91}]
            )

    def test_maximo_etapas(self, service, sample_lote):
        """Testa máximo de etapas."""
        etapas = [{'nome': f'Etapa{i}', 'duracao_dias': 1} for i in range(6)]
        with pytest.raises(ValueError, match="Máximo de 5 etapas"):
            service.simular_cenario_resgate(
                lote_id=sample_lote.id,
                etapas=etapas
            )

    def test_lista_vazia_etapas(self, service, sample_lote):
        """Testa lista vazia de etapas."""
        with pytest.raises(ValueError, match="Pelo menos uma etapa"):
            service.simular_cenario_resgate(
                lote_id=sample_lote.id,
                etapas=[]
            )


class TestCalculosMargem:
    """Testa cálculos de margem."""

    def test_margem_positiva(self, service, sample_lote):
        """Testa margem positiva."""
        resultado = service.simular_cenario_resgate(
            lote_id=sample_lote.id,
            etapas=[{'nome': 'Teste', 'duracao_dias': 10}]
        )
        assert resultado['margem_dias'] == 20  # 30 - 10
        assert resultado['resultado'] == 'compativel'

    def test_margem_zero(self, app):
        """Testa margem zero."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento(
                nome='Teste',
                lote='LOT001',
                data_validade=date.today() + timedelta(days=10),
                quantidade=100,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            db.session.add(lote)
            db.session.commit()

            resultado = service.simular_cenario_resgate(
                lote_id=lote.id,
                etapas=[{'nome': 'Teste', 'duracao_dias': 10}]
            )
            assert resultado['margem_dias'] == 0
            assert resultado['resultado'] == 'margem_reduzida'

    def test_margem_negativa(self, service, sample_lote):
        """Testa margem negativa."""
        resultado = service.simular_cenario_resgate(
            lote_id=sample_lote.id,
            etapas=[{'nome': 'Teste', 'duracao_dias': 40}]
        )
        assert resultado['margem_dias'] == -10  # 30 - 40
        assert resultado['resultado'] == 'prazo_nao_compativel'

    def test_margem_reduzida_limite(self, app):
        """Testa limite de margem reduzida (6 dias)."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento(
                nome='Teste',
                lote='LOT001',
                data_validade=date.today() + timedelta(days=10),
                quantidade=100,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            db.session.add(lote)
            db.session.commit()

            resultado = service.simular_cenario_resgate(
                lote_id=lote.id,
                etapas=[{'nome': 'Teste', 'duracao_dias': 4}]
            )
            assert resultado['margem_dias'] == 6
            assert resultado['resultado'] == 'margem_reduzida'

    def test_margem_compativel_limite(self, app):
        """Testa limite de compatível (7 dias)."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento(
                nome='Teste',
                lote='LOT001',
                data_validade=date.today() + timedelta(days=10),
                quantidade=100,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            db.session.add(lote)
            db.session.commit()

            resultado = service.simular_cenario_resgate(
                lote_id=lote.id,
                etapas=[{'nome': 'Teste', 'duracao_dias': 3}]
            )
            assert resultado['margem_dias'] == 7
            assert resultado['resultado'] == 'compativel'


class TestDeterminismo:
    """Testa determinismo dos resultados."""

    def test_mesma_entrada_mesma_saida(self, service, sample_lote):
        """Testa que mesma entrada produz mesma saída."""
        etapas = [{'nome': 'Triagem', 'duracao_dias': 5}]

        resultado1 = service.simular_cenario_resgate(
            lote_id=sample_lote.id,
            etapas=etapas
        )

        resultado2 = service.simular_cenario_resgate(
            lote_id=sample_lote.id,
            etapas=etapas
        )

        assert resultado1['margem_dias'] == resultado2['margem_dias']
        assert resultado1['resultado'] == resultado2['resultado']
        assert resultado1['total_duracao_dias'] == resultado2['total_duracao_dias']

    def test_seed_ignorada_se_somente_para_validacao(self, service, sample_lote):
        """Testa que seed não afeta resultado (só validação)."""
        etapas = [{'nome': 'Triagem', 'duracao_dias': 5}]

        resultado1 = service.simular_cenario_resgate(
            lote_id=sample_lote.id,
            etapas=etapas,
            seed=123
        )

        resultado2 = service.simular_cenario_resgate(
            lote_id=sample_lote.id,
            etapas=etapas,
            seed=456
        )

        # Seed não deve afetar resultado (só validação)
        assert resultado1['margem_dias'] == resultado2['margem_dias']


class TestValidations:
    """Testa validações adicionais."""

    def test_lote_inexistente(self, service):
        """Testa lote inexistente."""
        with pytest.raises(ValueError, match="Lote não encontrado"):
            service.simular_cenario_resgate(
                lote_id=99999,
                etapas=[{'nome': 'Teste', 'duracao_dias': 5}]
            )

    def test_lote_inativo_nao_listado(self, app):
        """Testa que lote inativo não é listado."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento(
                nome='Teste',
                lote='LOT001',
                data_validade=date.today() + timedelta(days=30),
                quantidade=100,
                ativo=False,  # Inativo
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            db.session.add(lote)
            db.session.commit()

            lotes = service.listar_lotes_para_resgate(horizon_dias=30)
            assert len(lotes) == 0

    def test_lote_vencido_nao_listado(self, app):
        """Testa que lote vencido não é listado."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento(
                nome='Teste',
                lote='LOT001',
                data_validade=date.today() - timedelta(days=10),  # Vencido
                quantidade=100,
                ativo=True,
                status_semaforo=2,
                tarja='Branca',
                principio_ativo='Teste'
            )
            db.session.add(lote)
            db.session.commit()

            lotes = service.listar_lotes_para_resgate(horizon_dias=30)
            assert len(lotes) == 0

    def test_lote_fora_horizonte_nao_listado(self, app):
        """Testa que lote fora do horizonte não é listado."""
        with app.app_context():
            service = LotRescueService()
            lote = Medicamento(
                nome='Teste',
                lote='LOT001',
                data_validade=date.today() + timedelta(days=400),  # Fora do horizonte
                quantidade=100,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            db.session.add(lote)
            db.session.commit()

            lotes = service.listar_lotes_para_resgate(horizon_dias=30)
            assert len(lotes) == 0


class TestResumo:
    """Testa cálculo de resumo."""

    def test_resumo_vazio(self, service):
        """Testa resumo quando não há lotes."""
        resumo = service.calcular_resumo_lotes(horizon_dias=30)
        assert resumo['total_lotes'] == 0
        assert resumo['total_quantidade'] == 0
        assert resumo['lotes_criticos'] == 0
        assert resumo['lotes_atencao'] == 0
        assert resumo['lotes_normais'] == 0

    def test_resumo_classificacao(self, app):
        """Testa classificação no resumo."""
        with app.app_context():
            service = LotRescueService()

            # Lote crítico
            lote1 = Medicamento(
                nome='Teste1',
                lote='LOT001',
                data_validade=date.today() + timedelta(days=5),
                quantidade=100,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            # Lote atenção
            lote2 = Medicamento(
                nome='Teste2',
                lote='LOT002',
                data_validade=date.today() + timedelta(days=15),
                quantidade=50,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )
            # Lote normal
            lote3 = Medicamento(
                nome='Teste3',
                lote='LOT003',
                data_validade=date.today() + timedelta(days=60),
                quantidade=200,
                ativo=True,
                status_semaforo=0,
                tarja='Branca',
                principio_ativo='Teste'
            )

            db.session.add_all([lote1, lote2, lote3])
            db.session.commit()

            resumo = service.calcular_resumo_lotes(horizon_dias=30)
            assert resumo['total_lotes'] == 2  # lote3 fora do horizonte
            assert resumo['lotes_criticos'] == 1
            assert resumo['lotes_atencao'] == 1
            assert resumo['lotes_normais'] == 0
            assert resumo['total_quantidade'] == 150  # 100 + 50
