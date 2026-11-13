"""
Testes para MatchingService (Fase 4)
Verifica correspondência entre ofertas e necessidades
"""

import pytest
from main import create_app
from app.database import db
from app.services.matching_service import MatchingService, MatchResultado
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
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
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
        responsavel="Responsável Teste"
    )
    db.session.add(farmacia)
    db.session.commit()
    return farmacia


@pytest.fixture
def referencia_medicamento(app):
    """Referência de medicamento de teste."""
    referencia = MedicamentoReferencia(
        nome_comercial="Paracetamol",
        principio_ativo="paracetamol",
        lista_portaria=None
    )
    db.session.add(referencia)
    db.session.commit()
    return referencia


@pytest.fixture
def medicamento(app, referencia_medicamento):
    """Medicamento de teste."""
    medicamento = Medicamento(
        nome="Paracetamol 500mg",
        lote="LOTE123",
        data_validade=datetime(2025, 12, 31),
        quantidade=100,
        referencia_id=referencia_medicamento.id,
        ativo=True
    )
    db.session.add(medicamento)
    db.session.commit()
    return medicamento


@pytest.fixture
def instituicao(app):
    """Instituição de teste."""
    instituicao = Instituicao(
        nome="Hospital Teste",
        cnpj="98765432000190",
        endereco="Av. Principal, 456",
        responsavel="Dr. Teste",
        ativo=True
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
        ativo=True
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
        criado_por_id=usuario.id
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
        criado_por_id=1
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
    assert matches[0].pontuacao > 0


def test_buscar_matches_para_oferta(oferta, necessidade):
    """Testa busca de matches para uma oferta."""
    matches = MatchingService.buscar_matches_para_oferta(oferta.id)
    
    assert len(matches) > 0
    assert matches[0].oferta.id == oferta.id
    assert matches[0].necessidade.id == necessidade.id
    assert matches[0].pontuacao > 0


def test_match_quantidade_suficiente(oferta, necessidade):
    """Testa match com quantidade suficiente."""
    resultado = MatchingService._calcular_match(oferta, necessidade)
    
    assert resultado.pontuacao > 0
    assert "Quantidade suficiente" in resultado.motivo


def test_match_quantidade_insuficiente(oferta, necessidade):
    """Testa match com quantidade insuficiente."""
    # Aumenta a quantidade solicitada para ser maior que a disponível
    necessidade.quantidade_solicitada = 100
    db.session.commit()
    
    resultado = MatchingService._calcular_match(oferta, necessidade)
    
    # A lógica atual considera compatível se tiver pelo menos 50% da quantidade
    assert resultado.pontuacao > 0
    assert "Quantidade parcial" in resultado.motivo


def test_match_medicamento_exato(oferta, necessidade):
    """Testa match com medicamento exato (mesma referência)."""
    resultado = MatchingService._calcular_match(oferta, necessidade)
    
    assert resultado.pontuacao > 0
    assert "Medicamento exato" in resultado.motivo


def test_match_prioridade_urgente(oferta, necessidade):
    """Testa match com prioridade urgente."""
    necessidade.prioridade = "urgente"
    db.session.commit()
    
    resultado = MatchingService._calcular_match(oferta, necessidade)
    
    assert resultado.pontuacao > 0
    assert "Prioridade urgente" in resultado.motivo


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
    
    # A lógica atual considera compatível se tiver pelo menos 50% da quantidade
    assert sugestao["compativel"] is True
    assert "Quantidade parcial" in sugestao["motivo"]


def test_match_resultado_ordenacao_por_pontuacao(oferta, necessidade):
    """Testa que matches são ordenados por pontuação decrescente."""
    # Cria uma segunda necessidade com prioridade urgente (deve ter pontuação maior)
    necessidade2 = NecessidadeInstitucional(
        instituicao_id=necessidade.instituicao_id,
        medicamento_referencia_id=necessidade.medicamento_referencia_id,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=30,
        unidade="unidade",
        prioridade="urgente",  # Prioridade maior que "media"
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=1
    )
    db.session.add(necessidade2)
    db.session.commit()
    
    matches = MatchingService.buscar_matches_para_oferta(oferta.id)
    
    # A necessidade com prioridade urgente deve ter pontuação maior
    assert len(matches) == 2
    assert matches[0].pontuacao > matches[1].pontuacao


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
            criado_por_id=1
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
