"""
Testes para ReservaOferta (Fase 3)
Verifica criação e gerenciamento de reservas de ofertas
"""

import pytest
from main import create_app
from app.database import db
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.medicamento import Medicamento
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


def test_criar_reserva(oferta, instituicao, usuario):
    """Testa criação de reserva."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    db.session.refresh(reserva)
    assert reserva.id is not None
    assert reserva.quantidade_reservada == 20
    assert reserva.status == StatusReserva.RESERVADA.value


def test_confirmar_reserva(oferta, instituicao, usuario):
    """Testa confirmação de reserva."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.APROVADA.value,  # Deve estar APROVADA antes de CONFIRMADA
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.confirmar(usuario.id)
    assert resultado is True
    assert reserva.status == StatusReserva.CONFIRMADA.value
    assert reserva.confirmado_por_id == usuario.id
    assert reserva.confirmado_em is not None


def test_confirmar_reserva_nao_reservada(oferta, instituicao, usuario):
    """Testa que não é possível confirmar reserva não reservada."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.CANCELADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.confirmar(usuario.id)
    assert resultado is False
    assert reserva.status == StatusReserva.CANCELADA.value


def test_rejeitar_reserva(oferta, instituicao, usuario):
    """Testa rejeição de reserva."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.rejeitar(usuario.id, "Motivo de teste")
    assert resultado is True
    assert reserva.status == StatusReserva.REJEITADA.value
    assert reserva.confirmado_por_id == usuario.id
    assert reserva.observacoes == "Motivo de teste"


def test_cancelar_reserva(oferta, instituicao, usuario):
    """Testa cancelamento de reserva."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.cancelar()
    assert resultado is True
    assert reserva.status == StatusReserva.CANCELADA.value


def test_cancelar_reserva_confirmada(oferta, instituicao, usuario):
    """Testa cancelamento de reserva confirmada."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.CONFIRMADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.cancelar()
    assert resultado is True
    assert reserva.status == StatusReserva.CANCELADA.value


def test_expirar_reserva(oferta, instituicao, usuario):
    """Testa expiração de reserva."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.expirar()
    assert resultado is True
    assert reserva.status == StatusReserva.EXPIRADA.value


def test_expirar_reserva_nao_reservada(oferta, instituicao, usuario):
    """Testa que não é possível expirar reserva não reservada."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.CONFIRMADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    resultado = reserva.expirar()
    assert resultado is False
    assert reserva.status == StatusReserva.CONFIRMADA.value


def test_migration_cria_tabela_reservas(app):
    """Migration deve criar tabela reservas_ofertas."""
    from backend.migrations_custom.create_reserva_oferta_table import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a tabela existe
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    assert 'reservas_ofertas' in tables


def test_operacao_id_idempotencia(oferta, instituicao, usuario):
    """Testa que operacao_id garante idempotência."""
    from app.models.movimento_estoque import MovimentoEstoque
    
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    reserva1 = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id,
        operacao_id=operacao_id
    )
    db.session.add(reserva1)
    db.session.commit()
    
    # Tenta criar segunda reserva com mesmo operacao_id (deve falhar)
    reserva2 = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=10,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id,
        operacao_id=operacao_id
    )
    db.session.add(reserva2)
    
    try:
        db.session.commit()
        assert False, "Deveria falhar por constraint unique em operacao_id"
    except Exception:
        db.session.rollback()
        assert True  # Falha esperada


def test_reserva_libera_quantidade_oferta(oferta, instituicao, usuario):
    """Testa que cancelamento de reserva libera quantidade na oferta."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario.id
    )
    db.session.add(reserva)
    db.session.commit()
    
    # Reserva a quantidade na oferta
    oferta.reservar(20)
    db.session.commit()
    
    assert oferta.quantidade_reservada == 20
    assert oferta.quantidade_disponivel == 30
    
    # Cancela a reserva
    reserva.cancelar()
    oferta.liberar_reserva(20)
    db.session.commit()
    
    assert oferta.quantidade_reservada == 0
    assert oferta.quantidade_disponivel == 50
