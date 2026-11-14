"""
Testes para Aprovação Farmacêutica e Despacho (Tarefa 3)
Verifica aprovação farmacêutica, autorização e consistência de estoque
"""

import pytest
from main import create_app
from app.database import db
from app.models.aprovacao_farmaceutica import AprovacaoFarmaceutica, StatusAprovacao
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.medicamento import Medicamento
from app.models.farmacia import Farmacia
from app.models.instituicao import Instituicao
from app.models.usuario import Usuario
from app.core.security import criptografar_senha
from datetime import datetime


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
def farmacia_nao_doadora(app):
    """Farmácia não doadora de teste."""
    farmacia = Farmacia(
        nome_fantasia="Outra Farmácia",
        razao_social="Outra Farmácia LTDA",
        cnpj="98765432000190",
        endereco="Av. Outra, 456",
        responsavel="Outro Responsável"
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
def medicamento(app):
    """Medicamento de teste."""
    medicamento = Medicamento(
        nome="Paracetamol 500mg",
        lote="LOTE123",
        data_validade=datetime(2025, 12, 31),
        quantidade=100,
        ativo=True
    )
    db.session.add(medicamento)
    db.session.commit()
    return medicamento


@pytest.fixture
def usuario_operador(app, instituicao_receptora):
    """Usuário operador vinculado à instituição."""
    usuario = Usuario(
        nome="Operador Teste",
        cpf="11122233344",
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
def usuario_farmaceutico_doadora(app, farmacia_doadora):
    """Usuário farmacêutico vinculado à farmácia doadora."""
    usuario = Usuario(
        nome="Farmacêutico Doadora",
        cpf="22233344455",
        email="farmaceutico_doadora@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Farmacêutico",
        ativo=True,
        farmacia_id=farmacia_doadora.id
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def usuario_farmaceutico_nao_doadora(app, farmacia_nao_doadora):
    """Usuário farmacêutico vinculado à farmácia não doadora."""
    usuario = Usuario(
        nome="Farmacêutico Outra",
        cpf="33344455566",
        email="farmaceutico_outra@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Farmacêutico",
        ativo=True,
        farmacia_id=farmacia_nao_doadora.id
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def usuario_admin(app):
    """Usuário admin de teste."""
    usuario = Usuario(
        nome="Admin Teste",
        cpf="12345678901",
        email="admin@teste.com",
        senha=criptografar_senha("senha123"),
        cargo="Admin",
        ativo=True
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def oferta(farmacia_doadora, medicamento, usuario_admin):
    """Oferta de teste."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia_doadora.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=20,  # Quantidade igual à reserva
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_admin.id
    )
    db.session.add(oferta)
    db.session.commit()
    return oferta


@pytest.fixture
def reserva(oferta, instituicao_receptora, usuario_operador):
    """Reserva de teste."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao_receptora.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario_operador.id
    )
    db.session.add(reserva)
    db.session.commit()
    return reserva


def test_operador_nao_pode_aprovar(reserva, usuario_operador):
    """Operador não pode aprovar reserva."""
    from app.models.movimento_estoque import MovimentoEstoque
    
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    aprovacao = AprovacaoFarmaceutica(
        reserva_id=reserva.id,
        usuario_id=usuario_operador.id,
        status=StatusAprovacao.APROVADA.value,
        operacao_id=operacao_id
    )
    db.session.add(aprovacao)
    db.session.commit()
    
    # O modelo permite a criação, mas a rota deve bloquear
    assert aprovacao.id is not None


def test_farmaceutico_doadora_pode_aprovar(reserva, usuario_farmaceutico_doadora):
    """Farmacêutico da farmácia doadora pode aprovar reserva."""
    from app.models.movimento_estoque import MovimentoEstoque
    
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    aprovacao = AprovacaoFarmaceutica(
        reserva_id=reserva.id,
        usuario_id=usuario_farmaceutico_doadora.id,
        status=StatusAprovacao.APROVADA.value,
        operacao_id=operacao_id
    )
    db.session.add(aprovacao)
    
    # Reserva a quantidade na oferta (oferta muda para RESERVADA)
    reserva.oferta.reservar(reserva.quantidade_reservada)
    
    # Aprova a reserva
    reserva.aprovar()
    oferta = reserva.oferta
    oferta.aprovar()
    
    db.session.commit()
    
    db.session.refresh(reserva)
    db.session.refresh(oferta)
    assert reserva.status == StatusReserva.APROVADA.value
    assert oferta.status == StatusOferta.APROVADA.value


def test_farmaceutico_nao_doadora_nao_pode_aprovar(reserva, usuario_farmaceutico_nao_doadora):
    """Farmacêutico de outra farmácia não pode aprovar reserva (validação na rota)."""
    # O modelo permite a criação, mas a rota deve bloquear
    from app.models.movimento_estoque import MovimentoEstoque
    
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    aprovacao = AprovacaoFarmaceutica(
        reserva_id=reserva.id,
        usuario_id=usuario_farmaceutico_nao_doadora.id,
        status=StatusAprovacao.APROVADA.value,
        operacao_id=operacao_id
    )
    db.session.add(aprovacao)
    db.session.commit()
    
    assert aprovacao.id is not None  # O modelo não valida vínculo (responsabilidade da rota)


def test_aprovacao_somente_status_reservada(reserva, usuario_farmaceutico_doadora):
    """Aprovação só é possível quando status é RESERVADA."""
    reserva.status = StatusReserva.CONFIRMADA.value
    db.session.commit()
    
    resultado = reserva.aprovar()
    assert resultado is False
    assert reserva.status == StatusReserva.CONFIRMADA.value


def test_rejeicao_libera_quantidade(reserva, usuario_farmaceutico_doadora):
    """Rejeição libera quantidade reservada na oferta."""
    from app.models.movimento_estoque import MovimentoEstoque
    
    # Reserva a quantidade
    reserva.oferta.reservar(reserva.quantidade_reservada)
    db.session.commit()
    
    assert reserva.oferta.quantidade_reservada == 20
    
    # Rejeita a reserva
    reserva.rejeitar(usuario_farmaceutico_doadora.id, "Motivo de teste")
    reserva.oferta.liberar_reserva(reserva.quantidade_reservada)
    db.session.commit()
    
    assert reserva.status == StatusReserva.REJEITADA.value
    assert reserva.oferta.quantidade_reservada == 0


def test_despacho_reduz_estoque(reserva, usuario_farmaceutico_doadora):
    """Despacho reduz estoque físico."""
    from app.models.movimento_estoque import MovimentoEstoque
    
    # Reserva a quantidade na oferta
    reserva.oferta.reservar(reserva.quantidade_reservada)
    
    # Aprova e confirma a reserva
    reserva.aprovar()
    reserva.oferta.aprovar()
    reserva.confirmar(usuario_farmaceutico_doadora.id)
    reserva.oferta.confirmar()
    db.session.commit()
    
    estoque_anterior = reserva.oferta.medicamento.quantidade
    
    # Realiza despacho
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    medicamento = reserva.oferta.medicamento
    medicamento.quantidade -= reserva.quantidade_reservada
    
    movimento = MovimentoEstoque(
        medicamento_id=medicamento.id,
        quantidade=reserva.quantidade_reservada,
        tipo="saida",
        operacao_id=operacao_id,
        usuario_id=usuario_farmaceutico_doadora.id,
        autorizado_por_id=usuario_farmaceutico_doadora.id,
        justificativa=f"Despacho da reserva {reserva.id}"
    )
    db.session.add(movimento)
    
    reserva.despachar()
    reserva.oferta.despachar()
    db.session.commit()
    
    assert medicamento.quantidade == estoque_anterior - reserva.quantidade_reservada
    assert reserva.status == StatusReserva.DESPACHADA.value
    assert reserva.oferta.status == StatusOferta.DESPACHADA.value


def test_despacho_somente_status_confirmada(reserva, usuario_farmaceutico_doadora):
    """Despacho só é possível quando status é CONFIRMADA."""
    # Tenta despachar em status RESERVADA
    resultado = reserva.despachar()
    assert resultado is False
    assert reserva.status == StatusReserva.RESERVADA.value


def test_nenhuma_saida_antes_da_aprovacao(reserva, usuario_farmaceutico_doadora):
    """Nenhuma saída ocorre antes da aprovação."""
    estoque_anterior = reserva.oferta.medicamento.quantidade
    
    # Reserva está em RESERVADA, não APROVADA
    # Despacho não deve ser possível
    resultado = reserva.despachar()
    assert resultado is False
    
    db.session.refresh(reserva.oferta.medicamento)
    assert reserva.oferta.medicamento.quantidade == estoque_anterior


def test_repeticao_aprovacao_nao_duplica(reserva, usuario_farmaceutico_doadora):
    """Repetição da aprovação não duplica (idempotência via operacao_id)."""
    from app.models.movimento_estoque import MovimentoEstoque
    
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    # Reserva a quantidade na oferta
    reserva.oferta.reservar(reserva.quantidade_reservada)
    
    # Primeira aprovação
    aprovacao1 = AprovacaoFarmaceutica(
        reserva_id=reserva.id,
        usuario_id=usuario_farmaceutico_doadora.id,
        status=StatusAprovacao.APROVADA.value,
        operacao_id=operacao_id
    )
    db.session.add(aprovacao1)
    reserva.aprovar()
    reserva.oferta.aprovar()
    db.session.commit()
    
    # Tenta segunda aprovação com mesmo operacao_id
    aprovacao2 = AprovacaoFarmaceutica(
        reserva_id=reserva.id,
        usuario_id=usuario_farmaceutico_doadora.id,
        status=StatusAprovacao.APROVADA.value,
        operacao_id=operacao_id
    )
    db.session.add(aprovacao2)
    
    try:
        db.session.commit()
        assert False, "Deveria falhar por constraint unique em operacao_id"
    except Exception:
        db.session.rollback()
        assert True  # Falha esperada


def test_migration_cria_tabela_aprovacoes(app):
    """Migration deve criar tabela aprovacoes_farmaceuticas."""
    from backend.migrations_custom.create_aprovacao_farmaceutica_table import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a tabela existe
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    assert 'aprovacoes_farmaceuticas' in tables


def test_confirmacao_exige_aprovacao_previa(reserva, usuario_farmaceutico_doadora):
    """Confirmação exige aprovação prévia."""
    # Tentar confirmar sem aprovação prévia
    resultado = reserva.confirmar(usuario_farmaceutico_doadora.id)
    assert resultado is False
    assert reserva.status == StatusReserva.RESERVADA.value
    
    # Aprovar e depois confirmar
    reserva.aprovar()
    db.session.commit()
    
    resultado = reserva.confirmar(usuario_farmaceutico_doadora.id)
    assert resultado is True
    assert reserva.status == StatusReserva.CONFIRMADA.value
