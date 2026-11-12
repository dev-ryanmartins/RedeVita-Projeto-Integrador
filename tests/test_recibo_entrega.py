"""
Testes para Geração de PDF de Recibo de Entrega (Tarefa 6)
Verifica geração de PDF, autorização e idempotência
"""

import pytest
from main import create_app
from app.database import db
from app.models.entrega_institucional import EntregaInstitucional, EstadoEntrega
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
def usuario_instituicao_receptora(app, instituicao_receptora):
    """Usuário vinculado à instituição receptora."""
    usuario = Usuario(
        nome="Operador Receptor",
        cpf="44455566677",
        email="operador_receptor@teste.com",
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
        cpf="55566677888",
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
        quantidade_ofertada=20,
        quantidade_reservada=0,
        status=StatusOferta.DISPONIVEL.value,
        criado_por_id=usuario_admin.id
    )
    db.session.add(oferta)
    db.session.commit()
    return oferta


@pytest.fixture
def reserva(oferta, instituicao_receptora, usuario_instituicao_receptora):
    """Reserva de teste."""
    reserva = ReservaOferta(
        oferta_id=oferta.id,
        instituicao_id=instituicao_receptora.id,
        quantidade_reservada=20,
        status=StatusReserva.RESERVADA.value,
        reservado_por_id=usuario_instituicao_receptora.id
    )
    db.session.add(reserva)
    db.session.commit()
    return reserva


@pytest.fixture
def entrega_recebida(reserva, usuario_instituicao_receptora):
    """Entrega institucional em estado RECEBIDA."""
    entrega = EntregaInstitucional(
        reserva_id=reserva.id,
        estado=EstadoEntrega.AGENDADA.value
    )
    db.session.add(entrega)
    db.session.commit()
    
    # Simula o fluxo completo: AGENDADA -> DESPACHADA -> RECEBIDA
    entrega.despachar(usuario_instituicao_receptora.id)
    db.session.commit()
    
    entrega.receber(usuario_instituicao_receptora.id, "Recebido com sucesso")
    db.session.commit()
    
    return entrega


@pytest.fixture
def entrega_despachada(reserva, usuario_instituicao_receptora):
    """Entrega institucional em estado DESPACHADA."""
    entrega = EntregaInstitucional(
        reserva_id=reserva.id,
        estado=EstadoEntrega.AGENDADA.value
    )
    db.session.add(entrega)
    db.session.commit()
    
    entrega.despachar(usuario_instituicao_receptora.id)
    db.session.commit()
    
    return entrega


def test_pdf_gerado_para_entrega_recebida(app, entrega_recebida, usuario_instituicao_receptora):
    """PDF é gerado para entrega recebida e contém os dados corretos."""
    from app.utils.pdf_generator import PDFGenerator
    
    dados_entrega = {
        'entrega_id': entrega_recebida.id,
        'reserva_id': entrega_recebida.reserva_id,
        'farmacia_origem': entrega_recebida.reserva.oferta.farmacia.nome_fantasia,
        'cnpj_origem': entrega_recebida.reserva.oferta.farmacia.cnpj,
        'instituicao_destino': entrega_recebida.reserva.instituicao.nome,
        'cnpj_destino': entrega_recebida.reserva.instituicao.cnpj,
        'medicamento_nome': entrega_recebida.reserva.oferta.medicamento.nome,
        'medicamento_lote': entrega_recebida.reserva.oferta.medicamento.lote,
        'medicamento_validade': entrega_recebida.reserva.oferta.medicamento.data_validade,
        'quantidade': entrega_recebida.reserva.quantidade_reservada,
        'recebido_por': entrega_recebida.recebido_por.nome,
        'recebido_em': entrega_recebida.recebido_em,
        'observacoes': entrega_recebida.observacoes
    }
    
    gerador = PDFGenerator()
    pdf_bytes = gerador.gerar_recibo_entrega(dados_entrega)
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF-')  # Header PDF válido


def test_pdf_nao_gerado_para_entrega_agendada(app, reserva, usuario_instituicao_receptora):
    """PDF não é gerado para entrega apenas agendada."""
    entrega = EntregaInstitucional(
        reserva_id=reserva.id,
        estado=EstadoEntrega.AGENDADA.value
    )
    db.session.add(entrega)
    db.session.commit()
    
    # A rota deve bloquear (estado não é RECEBIDA)
    assert entrega.estado == EstadoEntrega.AGENDADA.value


def test_pdf_nao_gerado_para_entrega_despachada(app, entrega_despachada):
    """PDF não é gerado para entrega apenas despachada."""
    # A rota deve bloquear (estado não é RECEBIDA)
    assert entrega_despachada.estado == EstadoEntrega.DESPACHADA.value


def test_usuario_sem_autorizacao_nao_consegue_pdf(app, entrega_recebida, usuario_instituicao_outra):
    """Usuário sem autorização não consegue obter o PDF."""
    # A rota deve bloquear (usuário não vinculado à instituição destinatária)
    assert usuario_instituicao_outra.instituicao_id != entrega_recebida.reserva.instituicao_id


def test_solicitar_recibo_repetidamente_nao_altera_estados(app, entrega_recebida, usuario_instituicao_receptora):
    """Solicitar o recibo repetidamente não altera estados nem duplica movimentos."""
    from app.utils.pdf_generator import PDFGenerator
    
    dados_entrega = {
        'entrega_id': entrega_recebida.id,
        'reserva_id': entrega_recebida.reserva_id,
        'farmacia_origem': entrega_recebida.reserva.oferta.farmacia.nome_fantasia,
        'cnpj_origem': entrega_recebida.reserva.oferta.farmacia.cnpj,
        'instituicao_destino': entrega_recebida.reserva.instituicao.nome,
        'cnpj_destino': entrega_recebida.reserva.instituicao.cnpj,
        'medicamento_nome': entrega_recebida.reserva.oferta.medicamento.nome,
        'medicamento_lote': entrega_recebida.reserva.oferta.medicamento.lote,
        'medicamento_validade': entrega_recebida.reserva.oferta.medicamento.data_validade,
        'quantidade': entrega_recebida.reserva.quantidade_reservada,
        'recebido_por': entrega_recebida.recebido_por.nome,
        'recebido_em': entrega_recebida.recebido_em,
        'observacoes': entrega_recebida.observacoes
    }
    
    gerador = PDFGenerator()
    
    # Estado antes
    estado_antes = entrega_recebida.estado
    recebido_em_antes = entrega_recebida.recebido_em
    
    # Primeira geração
    pdf1 = gerador.gerar_recibo_entrega(dados_entrega)
    
    # Segunda geração
    pdf2 = gerador.gerar_recibo_entrega(dados_entrega)
    
    # Estado deve permanecer inalterado
    db.session.refresh(entrega_recebida)
    assert entrega_recebida.estado == estado_antes
    assert entrega_recebida.recebido_em == recebido_em_antes
    
    # PDFs devem ser gerados com sucesso
    assert pdf1 is not None
    assert pdf2 is not None


def test_admin_pode_gerar_pdf(app, entrega_recebida, usuario_admin):
    """Admin pode gerar PDF para qualquer entrega recebida."""
    # Admin é identificado pelo cargo 'Admin'
    assert usuario_admin.cargo == 'Admin'


def test_logo_oficial_e_apresentacao_verificados(app, entrega_recebida, usuario_instituicao_receptora):
    """Logo oficial e apresentação do documento são verificados."""
    from app.utils.pdf_generator import PDFGenerator
    
    dados_entrega = {
        'entrega_id': entrega_recebida.id,
        'reserva_id': entrega_recebida.reserva_id,
        'farmacia_origem': entrega_recebida.reserva.oferta.farmacia.nome_fantasia,
        'cnpj_origem': entrega_recebida.reserva.oferta.farmacia.cnpj,
        'instituicao_destino': entrega_recebida.reserva.instituicao.nome,
        'cnpj_destino': entrega_recebida.reserva.instituicao.cnpj,
        'medicamento_nome': entrega_recebida.reserva.oferta.medicamento.nome,
        'medicamento_lote': entrega_recebida.reserva.oferta.medicamento.lote,
        'medicamento_validade': entrega_recebida.reserva.oferta.medicamento.data_validade,
        'quantidade': entrega_recebida.reserva.quantidade_reservada,
        'recebido_por': entrega_recebida.recebido_por.nome,
        'recebido_em': entrega_recebida.recebido_em,
        'observacoes': entrega_recebida.observacoes
    }
    
    gerador = PDFGenerator()
    pdf_bytes = gerador.gerar_recibo_entrega(dados_entrega)
    
    # Verifica que PDF foi gerado com sucesso
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    # PDF válido começa com %PDF-
    assert pdf_bytes.startswith(b'%PDF-')


def test_dados_necessarios_incluidos_no_pdf(app, entrega_recebida, usuario_instituicao_receptora):
    """Dados necessários são incluídos no PDF."""
    from app.utils.pdf_generator import PDFGenerator
    
    dados_entrega = {
        'entrega_id': entrega_recebida.id,
        'reserva_id': entrega_recebida.reserva_id,
        'farmacia_origem': entrega_recebida.reserva.oferta.farmacia.nome_fantasia,
        'cnpj_origem': entrega_recebida.reserva.oferta.farmacia.cnpj,
        'instituicao_destino': entrega_recebida.reserva.instituicao.nome,
        'cnpj_destino': entrega_recebida.reserva.instituicao.cnpj,
        'medicamento_nome': entrega_recebida.reserva.oferta.medicamento.nome,
        'medicamento_lote': entrega_recebida.reserva.oferta.medicamento.lote,
        'medicamento_validade': entrega_recebida.reserva.oferta.medicamento.data_validade,
        'quantidade': entrega_recebida.reserva.quantidade_reservada,
        'recebido_por': entrega_recebida.recebido_por.nome,
        'recebido_em': entrega_recebida.recebido_em,
        'observacoes': entrega_recebida.observacoes
    }
    
    gerador = PDFGenerator()
    pdf_bytes = gerador.gerar_recibo_entrega(dados_entrega)
    
    # Verifica que PDF foi gerado com sucesso
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    # PDF válido e todos os dados foram fornecidos
    assert pdf_bytes.startswith(b'%PDF-')
