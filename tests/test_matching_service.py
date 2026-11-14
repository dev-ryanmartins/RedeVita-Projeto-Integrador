"""
Testes para MatchingService (Fase 4)
Verifica correspondência entre ofertas e necessidades
"""

import pytest
from main import create_app
from app.database import db
from app.services.matching_service import MatchingService
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.necessidade_institucional import NecessidadeInstitucional, StatusNecessidade
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.models.farmacia import Farmacia
from app.models.instituicao import Instituicao
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """App Flask com banco temporário."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def farmacia(app):
    """Farmácia de teste."""
    farmacia = Farmacia(
        nome_fantasia="Farmácia Teste",
        razao_social="Farmácia Teste LTDA",
        cnpj="12345678000190",
        endereco="Rua Teste, 123",
        responsavel="Responsável Teste",
    )
    db.session.add(farmacia)
    db.session.commit()
    return farmacia


@pytest.fixture
def referencia_medicamento(app):
    """Referência de medicamento de teste."""
    referencia = MedicamentoReferencia(nome_comercial="Paracetamol", principio_ativo="paracetamol", lista_portaria=None)
    db.session.add(referencia)
    db.session.commit()
    return referencia


@pytest.fixture
def medicamento(app, referencia_medicamento):
    """Medicamento de teste."""
    medicamento = Medicamento(
        nome="Paracetamol 500mg",
        lote="LOTE123",
        data_validade=datetime.now() + timedelta(days=365),
        quantidade=100,
        referencia_id=referencia_medicamento.id,
        ativo=True,
    )
    db.session.add(medicamento)
    db.session.commit()
    return medicamento


@pytest.fixture
def instituicao(app):
    """Instituição de teste."""
    instituicao = Instituicao(
        nome="Hospital Teste", cnpj="98765432000190", endereco="Av. Principal, 456", responsavel="Dr. Teste", ativo=True
    )
    db.session.add(instituicao)
    db.session.commit()
    return instituicao


@pytest.fixture
def usuario(app):
    """Usuário de teste."""
    usuario = Usuario(
        nome="Usuário Teste",
        cpf="12345678901",
        email="usuario@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Admin",
        ativo=True,
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def oferta(farmacia, medicamento, usuario):
    """Oferta de teste."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario.id,
    )
    db.session.add(oferta)
    db.session.commit()
    return oferta


@pytest.fixture
def necessidade(instituicao, referencia_medicamento):
    """Necessidade de teste."""
    necessidade = NecessidadeInstitucional(
        instituicao_id=instituicao.id,
        medicamento_referencia_id=referencia_medicamento.id,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=30,
        unidade="unidade",
        prioridade="media",
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=1,
    )
    db.session.add(necessidade)
    db.session.commit()
    return necessidade


def test_buscar_matches_para_necessidade(oferta, necessidade):
    """Testa busca de matches para uma necessidade."""
    matches = MatchingService.buscar_matches_para_necessidade(necessidade.id)

    assert len(matches) > 0
    assert matches[0].oferta.id == oferta.id
    assert matches[0].necessidade.id == necessidade.id
    assert matches[0].compativel is True


def test_buscar_matches_para_oferta(oferta, necessidade):
    """Testa busca de matches para uma oferta."""
    matches = MatchingService.buscar_matches_para_oferta(oferta.id)

    assert len(matches) > 0
    assert matches[0].oferta.id == oferta.id
    assert matches[0].necessidade.id == necessidade.id
    assert matches[0].compativel is True


def test_match_quantidade_suficiente(oferta, necessidade):
    """Testa match com quantidade suficiente."""
    resultado = MatchingService._calcular_match(oferta, necessidade)

    assert resultado.compativel is True
    assert "Quantidade suficiente" in resultado.motivo


def test_match_quantidade_insuficiente(oferta, necessidade):
    """Testa match com quantidade insuficiente."""
    # Aumenta a quantidade solicitada para ser maior que a disponível
    necessidade.quantidade_solicitada = 100
    db.session.commit()

    resultado = MatchingService._calcular_match(oferta, necessidade)

    # Oferta com quantidade menor que a solicitada não é compatível
    assert resultado.compativel is False
    assert "Quantidade insuficiente" in resultado.motivo


def test_match_medicamento_exato(oferta, necessidade):
    """Testa match com medicamento exato (mesma referência)."""
    resultado = MatchingService._calcular_match(oferta, necessidade)

    assert resultado.compativel is True
    assert "Medicamento exato" in resultado.motivo


def test_match_prioridade_urgente(oferta, necessidade):
    """Testa match quando a necessidade tem prioridade urgente.

    O matching é informativo e não atribui pontuação/peso por prioridade,
    portanto a compatibilidade independe do nível de prioridade registrado.
    """
    necessidade.prioridade = "urgente"
    db.session.commit()

    resultado = MatchingService._calcular_match(oferta, necessidade)

    assert resultado.compativel is True


def test_sugerir_reserva_compativel(oferta, necessidade):
    """Testa sugestão de reserva compatível."""
    sugestao = MatchingService.sugerir_reserva(oferta.id, necessidade.id)

    assert sugestao["compativel"] is True
    assert sugestao["quantidade_sugerida"] == 30
    assert sugestao["oferta"]["id"] == oferta.id
    assert sugestao["necessidade"]["id"] == necessidade.id


def test_sugerir_reserva_incompativel(oferta, necessidade):
    """Testa sugestão de reserva incompatível."""
    # Aumenta a quantidade solicitada para ser maior que a disponível
    necessidade.quantidade_solicitada = 100
    db.session.commit()

    sugestao = MatchingService.sugerir_reserva(oferta.id, necessidade.id)

    # Sem quantidade suficiente, a reserva não é sugerida
    assert sugestao["compativel"] is False
    assert "Quantidade insuficiente" in sugestao["motivo"]


def test_buscar_matches_retorna_todas_necessidades_compativeis(oferta, necessidade):
    """Testa que todas as necessidades compatíveis são retornadas."""
    # Cria uma segunda necessidade para o mesmo medicamento
    necessidade2 = NecessidadeInstitucional(
        instituicao_id=necessidade.instituicao_id,
        medicamento_referencia_id=necessidade.medicamento_referencia_id,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=30,
        unidade="unidade",
        prioridade="urgente",
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=1,
    )
    db.session.add(necessidade2)
    db.session.commit()

    matches = MatchingService.buscar_matches_para_oferta(oferta.id)

    # As duas necessidades são compatíveis com a oferta
    assert len(matches) == 2
    assert all(match.compativel for match in matches)


def test_limite_matches(oferta, necessidade):
    """Testa que limite de matches é respeitado."""
    # Cria ofertas adicionais
    for i in range(10):
        oferta_extra = OfertaMedicamento(
            farmacia_id=oferta.farmacia_id,
            medicamento_id=oferta.medicamento_id,
            quantidade_ofertada=50,
            quantidade_reservada=0,
            status=StatusOferta.DISPONIVEL.value,
            criado_por_id=1,
        )
        db.session.add(oferta_extra)
    db.session.commit()

    matches = MatchingService.buscar_matches_para_necessidade(necessidade.id, limite=5)

    assert len(matches) <= 5


def test_match_oferta_nao_disponivel(oferta, necessidade):
    """Testa que ofertas não disponíveis não são retornadas."""
    oferta.status = StatusOferta.CANCELADA.value
    db.session.commit()

    matches = MatchingService.buscar_matches_para_necessidade(necessidade.id)

    # Não deve retornar a oferta cancelada
    for match in matches:
        assert match.oferta.status == StatusOferta.DISPONIVEL.value


def test_match_necessidade_nao_ativa(oferta, necessidade):
    """Testa que necessidades não ativas não são retornadas."""
    necessidade.status = StatusNecessidade.ENCERRADA.value
    db.session.commit()

    matches = MatchingService.buscar_matches_para_oferta(oferta.id)

    # Não deve retornar a necessidade encerrada
    for match in matches:
        assert match.necessidade.status in [StatusNecessidade.REGISTRADA.value, StatusNecessidade.EM_REVISAO.value]
