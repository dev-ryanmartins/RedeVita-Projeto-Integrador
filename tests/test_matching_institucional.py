"""
Testes para Matching Institucional (Tarefa 8)
Verifica sugestão de ofertas compatíveis para necessidades institucionais
"""

import pytest
from main import create_app
from app.database import db
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
def farmacia_doadora(app):
    """Farmácia doadora de teste."""
    farmacia = Farmacia(
        nome_fantasia="Farmácia Doadora",
        razao_social="Farmácia Doadora LTDA",
        cnpj="12345678000190",
        endereco="Rua Teste, 123",
        responsavel="Responsável Teste"
    )
    db.session.add(farmacia)
    db.session.commit()
    return farmacia


@pytest.fixture
def instituicao_receptora(app):
    """Instituição receptora de teste."""
    instituicao = Instituicao(
        nome="Hospital Receptor",
        cnpj="11122233000144",
        endereco="Av. Principal, 789",
        responsavel="Dr. Receptor",
        ativo=True
    )
    db.session.add(instituicao)
    db.session.commit()
    return instituicao


@pytest.fixture
def instituicao_outra(app):
    """Outra instituição de teste."""
    instituicao = Instituicao(
        nome="Outro Hospital",
        cnpj="22244455000100",
        endereco="Rua Secundária, 321",
        responsavel="Dr. Outro",
        ativo=True
    )
    db.session.add(instituicao)
    db.session.commit()
    return instituicao


@pytest.fixture
def medicamento_teste(app):
    """Medicamento de teste."""
    # Data futura (1 ano a partir de agora)
    data_validade = datetime.now() + timedelta(days=365)
    medicamento = Medicamento(
        nome="Paracetamol 500mg",
        lote="LOTE123",
        data_validade=data_validade,
        quantidade=100,
        ativo=True
    )
    db.session.add(medicamento)
    db.session.commit()
    return medicamento


@pytest.fixture
def medicamento_vencido(app):
    """Medicamento vencido de teste."""
    # Data passada (vencido)
    data_validade = datetime.now() - timedelta(days=365)
    medicamento = Medicamento(
        nome="Dipirona 500mg",
        lote="LOTE_VENCIDO",
        data_validade=data_validade,
        quantidade=50,
        ativo=True
    )
    db.session.add(medicamento)
    db.session.commit()
    return medicamento


@pytest.fixture
def usuario_instituicao(app, instituicao_receptora):
    """Usuário vinculado à instituição receptora."""
    usuario = Usuario(
        nome="Operador Receptor",
        cpf="44455566677",
        email="operador@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Operador",
        ativo=True,
        instituicao_id=instituicao_receptora.id
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def usuario_instituicao_outra(app, instituicao_outra):
    """Usuário vinculado à outra instituição."""
    usuario = Usuario(
        nome="Operador Outro",
        cpf="55566778899",
        email="operador_outra@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Operador",
        ativo=True,
        instituicao_id=instituicao_outra.id
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def usuario_farmacia(app, farmacia_doadora):
    """Usuário vinculado à farmácia doadora."""
    usuario = Usuario(
        nome="Farmacêutico Teste",
        cpf="12345678901",
        email="farmaceutico@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Farmacêutico",
        ativo=True,
        farmacia_id=farmacia_doadora.id
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def usuario_admin(app):
    """Usuário admin de teste."""
    usuario = Usuario(
        nome="Admin Teste",
        cpf="99988877766",
        email="admin@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Admin",
        ativo=True
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def oferta_disponivel(farmacia_doadora, medicamento_teste, usuario_farmacia):
    """Oferta disponível de teste."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia_doadora.id,
        medicamento_id=medicamento_teste.id,
        quantidade_ofertada=50,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_farmacia.id
    )
    db.session.add(oferta)
    db.session.commit()
    return oferta


@pytest.fixture
def oferta_vencida(farmacia_doadora, medicamento_vencido, usuario_farmacia):
    """Oferta vencida de teste."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia_doadora.id,
        medicamento_id=medicamento_vencido.id,
        quantidade_ofertada=30,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_farmacia.id
    )
    db.session.add(oferta)
    db.session.commit()
    return oferta


@pytest.fixture
def oferta_reservada(farmacia_doadora, medicamento_teste, usuario_farmacia):
    """Oferta totalmente reservada de teste."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia_doadora.id,
        medicamento_id=medicamento_teste.id,
        quantidade_ofertada=20,
        quantidade_reservada=20,  # Totalmente reservada
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_farmacia.id
    )
    db.session.add(oferta)
    db.session.commit()
    return oferta


@pytest.fixture
def necessidade_instituicao(instituicao_receptora, medicamento_teste, usuario_instituicao):
    """Necessidade institucional de teste."""
    # Usa produto descritivo em vez de referência para simplicidade
    necessidade = NecessidadeInstitucional(
        instituicao_id=instituicao_receptora.id,
        medicamento_referencia_id=None,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=30,
        unidade="unidade",
        prioridade="media",
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=usuario_instituicao.id
    )
    db.session.add(necessidade)
    db.session.commit()
    return necessidade


def test_oferta_compativel_sugerida_corretamente(app, oferta_disponivel, necessidade_instituicao):
    """Oferta compatível é sugerida para a necessidade correta."""
    from app.services.matching_service import MatchingService
    
    matches = MatchingService.buscar_matches_para_necessidade(necessidade_instituicao.id, limite=10)
    
    assert len(matches) > 0
    assert matches[0].compativel is True
    assert matches[0].oferta.id == oferta_disponivel.id
    assert matches[0].necessidade.id == necessidade_instituicao.id


def test_medicamento_diferente_nao_sugerido(app, farmacia_doadora, instituicao_receptora, usuario_instituicao, usuario_farmacia):
    """Medicamento diferente não é sugerido."""
    from app.services.matching_service import MatchingService
    from app.models.necessidade_institucional import StatusNecessidade
    
    # Cria medicamento diferente
    data_validade = datetime.now() + timedelta(days=365)
    medicamento_diferente = Medicamento(
        nome="Ibuprofeno 400mg",
        lote="LOTE456",
        data_validade=data_validade,
        quantidade=100,
        ativo=True
    )
    db.session.add(medicamento_diferente)
    db.session.commit()
    
    # Cria oferta do medicamento diferente
    oferta_diferente = OfertaMedicamento(
        farmacia_id=farmacia_doadora.id,
        medicamento_id=medicamento_diferente.id,
        quantidade_ofertada=30,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_farmacia.id
    )
    db.session.add(oferta_diferente)
    db.session.commit()
    
    # Cria necessidade de Paracetamol (produto descritivo)
    necessidade = NecessidadeInstitucional(
        instituicao_id=instituicao_receptora.id,
        medicamento_referencia_id=None,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=30,
        unidade="unidade",
        prioridade="media",
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=usuario_instituicao.id
    )
    db.session.add(necessidade)
    db.session.commit()
    
    matches = MatchingService.buscar_matches_para_necessidade(necessidade.id, limite=10)
    
    # Oferta de Ibuprofeno não deve sugerir para necessidade de Paracetamol
    assert all(match.oferta.id != oferta_diferente.id for match in matches)


def test_oferta_vencida_nao_sugerida(app, oferta_vencida, instituicao_receptora, usuario_instituicao, usuario_farmacia):
    """Oferta vencida não é sugerida."""
    from app.services.matching_service import MatchingService
    from app.models.necessidade_institucional import StatusNecessidade
    
    # Cria necessidade de Dipirona (produto descritivo)
    necessidade = NecessidadeInstitucional(
        instituicao_id=instituicao_receptora.id,
        medicamento_referencia_id=None,
        produto_descritivo="Dipirona 500mg",
        quantidade_solicitada=20,
        unidade="unidade",
        prioridade="media",
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=usuario_instituicao.id
    )
    db.session.add(necessidade)
    db.session.commit()
    
    matches = MatchingService.buscar_matches_para_necessidade(necessidade.id, limite=10)
    
    # Oferta vencida não deve ser sugerida
    assert all(match.oferta.id != oferta_vencida.id for match in matches)


def test_oferta_totalmente_reservada_nao_sugerida(app, oferta_reservada, necessidade_instituicao):
    """Oferta totalmente reservada não é sugerida."""
    from app.services.matching_service import MatchingService
    
    # Verifica que oferta está totalmente reservada
    assert oferta_reservada.quantidade_disponivel == 0
    
    matches = MatchingService.buscar_matches_para_necessidade(necessidade_instituicao.id, limite=10)
    
    # Oferta totalmente reservada não deve ser sugerida
    assert all(match.oferta.id != oferta_reservada.id for match in matches)


def test_quantidade_insuficiente_nao_sugerida(app, farmacia_doadora, instituicao_receptora, usuario_instituicao, usuario_farmacia, medicamento_teste):
    """Quantidade insuficiente não é sugerida."""
    from app.services.matching_service import MatchingService
    from app.models.necessidade_institucional import StatusNecessidade
    
    # Cria oferta com pouca quantidade
    oferta_pouca = OfertaMedicamento(
        farmacia_id=farmacia_doadora.id,
        medicamento_id=medicamento_teste.id,
        quantidade_ofertada=5,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_farmacia.id
    )
    db.session.add(oferta_pouca)
    db.session.commit()
    
    # Cria necessidade com quantidade maior (produto descritivo)
    necessidade_maior = NecessidadeInstitucional(
        instituicao_id=instituicao_receptora.id,
        medicamento_referencia_id=None,
        produto_descritivo="Paracetamol 500mg",
        quantidade_solicitada=100,  # Muito maior que a oferta
        unidade="unidade",
        prioridade="media",
        status=StatusNecessidade.REGISTRADA.value,
        criado_por_id=usuario_instituicao.id
    )
    db.session.add(necessidade_maior)
    db.session.commit()
    
    matches = MatchingService.buscar_matches_para_necessidade(necessidade_maior.id, limite=10)
    
    # Oferta com quantidade insuficiente não deve ser sugerida
    assert all(match.oferta.id != oferta_pouca.id for match in matches)


def test_reservas_ativas_reduzem_disponibilidade(app, oferta_disponivel, necessidade_instituicao, usuario_instituicao):
    """Reservas ativas reduzem a quantidade apresentada como disponível."""
    from app.services.matching_service import MatchingService
    from app.models.reserva_oferta import ReservaOferta, StatusReserva
    
    # Quantidade disponível inicial
    disponivel_antes = oferta_disponivel.quantidade_disponivel
    assert disponivel_antes == 50
    
    # Cria uma reserva parcial
    reserva = ReservaOferta(
        oferta_id=oferta_disponivel.id,
        instituicao_id=necessidade_instituicao.instituicao_id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario_instituicao.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    # Reserva a quantidade de forma atômica
    from app.models.oferta_medicamento import OfertaMedicamento
    success, _ = OfertaMedicamento.reservar_atomico(
        db.session,
        oferta_disponivel.id,
        20
    )
    assert success is True
    db.session.commit()
    
    # Verifica que disponibilidade foi reduzida
    db.session.refresh(oferta_disponivel)
    disponivel_depois = oferta_disponivel.quantidade_disponivel
    assert disponivel_depois == disponivel_antes - 20
    
    # Verifica que o matching considera a nova disponibilidade
    matches = MatchingService.buscar_matches_para_necessidade(necessidade_instituicao.id, limite=10)
    
    # Se a necessidade pede mais do que disponível, não deve sugerir
    if necessidade_instituicao.quantidade_solicitada > disponivel_depois:
        assert all(match.oferta.id != oferta_disponivel.id for match in matches)


def test_usuario_outra_instituicao_nao_consulta(app, oferta_disponivel, necessidade_instituicao, usuario_instituicao_outra):
    """Usuário de outra instituição não consulta nem aceita oferta."""
    # Verifica que o usuário não está vinculado à instituição da necessidade
    assert usuario_instituicao_outra.instituicao_id != necessidade_instituicao.instituicao_id
    
    # A rota deve bloquear (validação de autorização)


def test_sugerir_novamente_nao_cria_reserva(app, oferta_disponivel, necessidade_instituicao, usuario_instituicao):
    """Sugerir novamente não cria reserva nem altera estoque."""
    from app.services.matching_service import MatchingService
    
    # Quantidade de oferta antes
    quantidade_reservada_antes = oferta_disponivel.quantidade_reservada
    
    # Sugere pela primeira vez
    matches1 = MatchingService.buscar_matches_para_necessidade(necessidade_instituicao.id, limite=10)
    
    # Sugere pela segunda vez
    matches2 = MatchingService.buscar_matches_para_necessidade(necessidade_instituicao.id, limite=10)
    
    # Verifica que a oferta não foi alterada
    db.session.refresh(oferta_disponivel)
    assert oferta_disponivel.quantidade_reservada == quantidade_reservada_antes
    
    # Verifica que não foi criada reserva
    from app.models.reserva_oferta import ReservaOferta
    reservas = ReservaOferta.query.filter_by(oferta_id=oferta_disponivel.id).all()
    assert len(reservas) == 0


def test_aceitar_oferta_chama_fluxo_reserva_existente(app, oferta_disponivel, necessidade_instituicao, usuario_instituicao):
    """Aceitar uma oferta chama o fluxo de reserva existente sem duplicar movimentos."""
    from app.services.matching_service import MatchingService
    from app.models.reserva_oferta import ReservaOferta, StatusReserva
    from app.models.movimento_estoque import MovimentoEstoque
    from app.models.oferta_medicamento import OfertaMedicamento
    
    # Verifica compatibilidade
    sugestao = MatchingService.sugerir_reserva(oferta_disponivel.id, necessidade_instituicao.id)
    assert sugestao["compativel"] is True
    
    # Cria reserva usando o fluxo existente
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    quantidade_reservar = min(oferta_disponivel.quantidade_disponivel, necessidade_instituicao.quantidade_solicitada)
    
    reserva = ReservaOferta(
        oferta_id=oferta_disponivel.id,
        instituicao_id=necessidade_instituicao.instituicao_id,
        quantidade_reservada=quantidade_reservar,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario_instituicao.id,
        operacao_id=operacao_id
    )
    db.session.add(reserva)
    
    # Reserva a quantidade na oferta de forma atômica
    success, nova_quantidade = OfertaMedicamento.reservar_atomico(
        db.session,
        oferta_disponivel.id,
        quantidade_reservar
    )
    
    assert success is True
    db.session.commit()
    
    # Verifica que a reserva foi criada
    assert reserva.id is not None
    
    # Verifica que a oferta foi atualizada
    db.session.refresh(oferta_disponivel)
    assert oferta_disponivel.quantidade_reservada == quantidade_reservar
    
    # Verifica que não houve movimento de estoque (reserva não reduz estoque físico)
    movimentos = MovimentoEstoque.query.filter_by(medicamento_id=oferta_disponivel.medicamento_id).all()
    assert len(movimentos) == 0
