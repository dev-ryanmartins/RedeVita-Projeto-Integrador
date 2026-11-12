"""
Testes para OfertaMedicamento (Fase 2)
Verifica criação e gerenciamento de ofertas de medicamentos
"""

import pytest
from main import create_app
from app.database import db
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.medicamento import Medicamento
from app.models.farmacia import Farmacia
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


def test_criar_oferta(farmacia, medicamento, usuario):
    """Testa criação de oferta."""
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
    
    db.session.refresh(oferta)
    assert oferta.id is not None
    assert oferta.quantidade_ofertada == 50
    assert oferta.quantidade_reservada == 0
    assert oferta.quantidade_disponivel == 50
    assert oferta.status == StatusOferta.DISPONIVEL.value


def test_reservar_quantidade_disponivel(farmacia, medicamento, usuario):
    """Testa reserva de quantidade disponível."""
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
    
    # Reserva 20 unidades
    resultado = oferta.reservar(20)
    assert resultado is True
    assert oferta.quantidade_reservada == 20
    assert oferta.quantidade_disponivel == 30


def test_reservar_acima_disponivel(farmacia, medicamento, usuario):
    """Testa que não é possível reservar acima do disponível."""
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
    
    # Tenta reservar 60 unidades (tem apenas 50)
    resultado = oferta.reservar(60)
    assert resultado is False
    assert oferta.quantidade_reservada == 0
    assert oferta.quantidade_disponivel == 50


def test_reservar_quantidade_negativa(farmacia, medicamento, usuario):
    """Testa que não é possível reservar quantidade negativa."""
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
    
    # Tenta reservar quantidade negativa
    resultado = oferta.reservar(-10)
    assert resultado is False
    assert oferta.quantidade_reservada == 0


def test_liberar_reserva(farmacia, medicamento, usuario):
    """Testa liberação de reserva."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=20,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    # Libera 10 unidades
    oferta.liberar_reserva(10)
    assert oferta.quantidade_reservada == 10
    assert oferta.quantidade_disponivel == 40


def test_liberar_reserva_quantidade_negativa(farmacia, medicamento, usuario):
    """Testa liberação de quantidade negativa não altera reserva."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=20,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    reserva_original = oferta.quantidade_reservada
    oferta.liberar_reserva(-10)
    assert oferta.quantidade_reservada == reserva_original


def test_cancelar_oferta_disponivel(farmacia, medicamento, usuario):
    """Testa cancelamento de oferta disponível."""
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
    
    resultado = oferta.cancelar()
    assert resultado is True
    assert oferta.status == StatusOferta.CANCELADA.value
    assert oferta.quantidade_reservada == 0


def test_cancelar_oferta_reservada(farmacia, medicamento, usuario):
    """Testa cancelamento de oferta reservada."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=20,
        status=StatusOferta.RESERVADA.value,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    resultado = oferta.cancelar()
    assert resultado is True
    assert oferta.status == StatusOferta.CANCELADA.value
    assert oferta.quantidade_reservada == 0


def test_cancelar_oferta_confirmada(farmacia, medicamento, usuario):
    """Testa que não é possível cancelar oferta confirmada."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=50,
        status=StatusOferta.CONFIRMADA.value,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    resultado = oferta.cancelar()
    assert resultado is False
    assert oferta.status == StatusOferta.CONFIRMADA.value


def test_expirar_oferta(farmacia, medicamento, usuario):
    """Testa expiração de oferta."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=20,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    resultado = oferta.expirar()
    assert resultado is True
    assert oferta.status == StatusOferta.EXPIRADA.value
    assert oferta.quantidade_reservada == 0


def test_expirar_oferta_nao_disponivel(farmacia, medicamento, usuario):
    """Testa que não é possível expirar oferta não disponível."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=0,
        status=StatusOferta.RESERVADA.value,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    resultado = oferta.expirar()
    assert resultado is False
    assert oferta.status == StatusOferta.RESERVADA.value


def test_confirmar_oferta(farmacia, medicamento, usuario):
    """Testa confirmação de oferta."""
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=50,
        status=StatusOferta.APROVADA.value,  # Deve estar APROVADA antes de CONFIRMADA
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    resultado = oferta.confirmar()
    assert resultado is True
    assert oferta.status == StatusOferta.CONFIRMADA.value


def test_confirmar_oferta_nao_reservada(farmacia, medicamento, usuario):
    """Testa que não é possível confirmar oferta não reservada."""
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
    
    resultado = oferta.confirmar()
    assert resultado is False
    assert oferta.status == StatusOferta.DISPONIVEL.value


def test_migration_cria_tabela_ofertas(app):
    """Migration deve criar tabela ofertas_medicamentos."""
    from backend.migrations_custom.create_oferta_medicamento_table import migrate
    
    # Executa migration
    migrate()
    
    # Verifica se a tabela existe
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    assert 'ofertas_medicamentos' in tables


def test_data_expiracao(farmacia, medicamento, usuario):
    """Testa configuração de data de expiração."""
    data_expiracao = datetime(2025, 12, 31)
    oferta = OfertaMedicamento(
        farmacia_id=farmacia.id,
        medicamento_id=medicamento.id,
        quantidade_ofertada=50,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        data_expiracao=data_expiracao,
        criado_por_id=usuario.id
    )
    db.session.add(oferta)
    db.session.commit()
    
    db.session.refresh(oferta)
    assert oferta.data_expiracao == data_expiracao
